"""NeoApi v2 client used by the NeoRé Home Assistant integration."""

from __future__ import annotations

import json
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit, urlunsplit
from urllib.request import (
    HTTPBasicAuthHandler,
    HTTPDigestAuthHandler,
    HTTPPasswordMgrWithDefaultRealm,
    Request,
    build_opener,
)

from .const import (
    BOOLEAN_OBJECTS,
    DATA_API_VERSION,
    DATA_MODEL,
    HEATING_CURVE_FIELDS,
    OBJECT_HEATING_CURVE,
    OBJECT_NEORE_INFO,
    OBJECT_POOL_ENABLE,
    OBJECT_SIMPLY_NEO_VERSION,
    POOL_OBJECTS,
    POLL_OBJECTS,
)


class NeoApiError(Exception):
    """Base NeoApi error."""


class NeoApiConnectionError(NeoApiError):
    """Raised when the controller cannot be reached."""


class NeoApiAuthError(NeoApiError):
    """Raised when authentication fails."""


class NeoApiHttpError(NeoApiError):
    """Raised when one NeoApi request returns an HTTP error."""


def normalize_base_url(host: str) -> str:
    """Normalize an IP/hostname/URL to a controller base URL."""
    value = host.strip().rstrip("/")
    if not value:
        raise ValueError("Host is empty")
    if "://" not in value:
        value = f"http://{value}"

    parsed = urlsplit(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("Invalid controller address")

    # NeoApi lives below the host root. Ignore an accidentally entered path.
    return urlunsplit((parsed.scheme, parsed.netloc, "", "", "")).rstrip("/")


def controller_id(base_url: str) -> str:
    """Return a controller ID based on host:port."""
    return urlsplit(base_url).netloc.lower()


def as_bool(value: Any) -> bool:
    """Convert common PLC/JSON bool representations to bool."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "on", "yes"}:
            return True
        if lowered in {"0", "false", "off", "no"}:
            return False
    raise NeoApiError(f"Unexpected boolean value: {value!r}")


def _find_name(names: Iterable[str], requested: str) -> str | None:
    """Find the controller's actual object name case-insensitively."""
    requested_lower = requested.lower()
    for name in names:
        if name == requested or name.lower() == requested_lower:
            return name
    return None


class NeoApiClient:
    """Synchronous NeoApi v2 client.

    urllib is deliberately used because it supports both HTTP Digest and HTTP
    Basic authentication without an extra Python package. Home Assistant calls
    these blocking methods in its executor.
    """

    def __init__(
        self, base_url: str, username: str, password: str, timeout: float = 5.0
    ) -> None:
        self.base_url = normalize_base_url(base_url)
        self.timeout = timeout

        password_mgr = HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None, self.base_url, username, password)

        # NeoApi documentation lists Digest and Basic authentication.
        self._opener = build_opener(
            HTTPDigestAuthHandler(password_mgr),
            HTTPBasicAuthHandler(password_mgr),
        )

    def _open(self, url: str) -> bytes:
        request = Request(url, method="GET", headers={"Accept": "application/json"})
        try:
            with self._opener.open(request, timeout=self.timeout) as response:
                return response.read()
        except HTTPError as exc:
            if exc.code == 401:
                raise NeoApiAuthError("NeoApi authentication failed") from exc
            # The controller may return an HTTP error for a single object while
            # the rest of NeoApi remains reachable. Keep this distinct from a
            # transport error so one optional value cannot take down all entities.
            raise NeoApiHttpError(f"NeoApi HTTP error {exc.code}") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise NeoApiConnectionError("NeoApi controller is unreachable") from exc

    @staticmethod
    def _decode_json(raw: bytes) -> Any:
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise NeoApiError("NeoApi returned invalid JSON") from exc

    def get_list(self) -> set[str]:
        """Return object names exposed by /tecoapi/getlist."""
        raw = self._open(f"{self.base_url}/tecoapi/getlist")
        payload = self._decode_json(raw)

        names: set[str] = set()
        if isinstance(payload, dict):
            names.update(str(key) for key in payload)
        elif isinstance(payload, list):
            for item in payload:
                if isinstance(item, str):
                    names.add(item)
                elif isinstance(item, dict):
                    names.update(str(key) for key in item)

        if not names:
            raise NeoApiError("NeoApi getlist returned no object names")
        return names

    def get_object(self, name: str) -> Any:
        """Read one NeoApi object using /tecoapi/getobject?<name>."""
        url = f"{self.base_url}/tecoapi/getobject?{quote(name, safe='._')}"
        payload = self._decode_json(self._open(url))

        if isinstance(payload, dict):
            if name in payload:
                return payload[name]
            # Tolerate capitalization differences in the controller response.
            lowered = name.lower()
            for key, value in payload.items():
                if str(key).lower() == lowered:
                    return value

        # Some firmware may return a scalar directly for scalar objects.
        if not isinstance(payload, (dict, list)):
            return payload

        raise NeoApiError(f"Object {name!r} missing in NeoApi response")

    def try_get_object(self, name: str) -> Any | None:
        """Read optional metadata without breaking normal entity updates."""
        try:
            return self.get_object(name)
        except NeoApiError:
            return None

    def set_object(self, name: str, value: Any) -> None:
        """Write one NeoApi object using the setobject query syntax from the manual."""
        if isinstance(value, bool):
            value = 1 if value else 0
        encoded_value = quote(str(value), safe=".-_")
        url = (
            f"{self.base_url}/tecoapi/setobject?"
            f"{quote(name, safe='._')}={encoded_value}"
        )
        # The NeoApi manual's curl example performs this as a GET request.
        self._open(url)

    def read_data(self, available_objects: set[str]) -> dict[str, Any]:
        """Read all supported objects which this particular controller exposes.

        A transport/authentication failure fails the whole update. An error in a
        single object is intentionally skipped, leaving only that entity in an
        unknown state while the remaining device continues to update.
        """
        data: dict[str, Any] = {}
        attempted = 0
        successful = 0
        pool_is_advertised = any(
            _find_name(available_objects, object_name) is not None
            for object_name in POOL_OBJECTS
        )

        for canonical_name in POLL_OBJECTS:
            actual_name = _find_name(available_objects, canonical_name)
            if (
                actual_name is None
                and canonical_name == OBJECT_POOL_ENABLE
                and pool_is_advertised
            ):
                # Some firmware supports this object but omits it from getlist.
                actual_name = canonical_name
            if actual_name is None:
                continue

            attempted += 1
            try:
                value = self.get_object(actual_name)
            except (NeoApiAuthError, NeoApiConnectionError):
                raise
            except NeoApiError:
                # Per-object failure: keep the coordinator update alive.
                continue

            successful += 1
            if canonical_name == OBJECT_HEATING_CURVE:
                if isinstance(value, dict):
                    for field in HEATING_CURVE_FIELDS:
                        field_value = None
                        for key, raw_value in value.items():
                            if str(key).lower() == field.lower():
                                field_value = raw_value
                                break
                        if field_value is not None:
                            data[f"{OBJECT_HEATING_CURVE}.{field}"] = field_value
                continue

            if canonical_name in BOOLEAN_OBJECTS:
                try:
                    data[canonical_name] = as_bool(value)
                except NeoApiError:
                    # Bad value from one object should not invalidate other data.
                    continue
            else:
                data[canonical_name] = value

        if attempted and successful == 0:
            raise NeoApiError("None of the supported NeoApi objects could be read")
        return data

    def read_device_metadata(self, available_objects: set[str]) -> dict[str, Any]:
        """Read optional, mostly static NeoRé metadata once at setup."""
        metadata: dict[str, Any] = {}

        # NeoApi v2 documents IniNeoRe.ProDescr as the heat-pump type.
        actual_info = _find_name(available_objects, OBJECT_NEORE_INFO)
        if actual_info is not None:
            neore_info = self.try_get_object(actual_info)
            if isinstance(neore_info, dict):
                for key, value in neore_info.items():
                    if str(key).lower() == "prodescr" and value not in (None, ""):
                        metadata[DATA_MODEL] = str(value)
                        break

        # SimplyNeoVer is the API version for the SimplyNeo application. It is
        # deliberately NOT used as Home Assistant's device firmware version.
        actual_api_version = _find_name(available_objects, OBJECT_SIMPLY_NEO_VERSION)
        if actual_api_version is not None:
            api_version = self.try_get_object(actual_api_version)
            if api_version not in (None, ""):
                metadata[DATA_API_VERSION] = str(api_version)

        return metadata

    def validate_connection(self) -> set[str]:
        """Validate credentials/connectivity and return the discovered object list."""
        return self.get_list()

    # Kept for backwards compatibility with early tests/tools.
    def read_trial_data(self) -> set[str]:
        """Validate the connection."""
        return self.validate_connection()
