"""Data coordinator for NeoRé."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import NeoApiClient, NeoApiError, find_object_name, resolve_object_name
from .const import (
    DATA_FW_VERSION,
    DATA_MODEL,
    DATA_PLC_TYPE,
    DATA_SERIAL_NUMBER,
    DATA_SW_VERSION,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    SUPPORTED_ROOT_OBJECTS,
    UNKNOWN_FIRMWARE_VERSION,
)

_LOGGER = logging.getLogger(__name__)


class NeoReCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Poll NeoApi and share the result with all NeoRé entities."""

    def __init__(self, hass: HomeAssistant, api: NeoApiClient) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.api = api
        self.metadata: dict[str, Any] = {}
        self.available_objects: set[str] = set()
        self._discovery_loaded = False
        self._metadata_loaded = False

    def actual_object_name(self, requested: str) -> str | None:
        """Return the actual controller object name, case-insensitively."""
        return find_object_name(self.available_objects, requested)

    def has_object(self, requested: str) -> bool:
        """Return whether the controller advertised a root NeoApi object."""
        root = requested.split(".", 1)[0]
        return self.actual_object_name(root) is not None

    def resolve_write_name(self, requested: str) -> str:
        """Return `requested` with its root object cased as the controller advertised it.

        Reads already tolerate capitalization differences in the controller's
        responses (see NeoApiClient.get_object). Writes must send a name the
        controller recognizes too, so resolve the root object through the same
        case-insensitive lookup before building the setobject query.
        """
        return resolve_object_name(self.available_objects, requested)

    def device_info_kwargs(self, base_url: str) -> dict[str, Any]:
        """Build the physical NeoRé device's identity fields from read metadata.

        Used by both `__init__.py` (device registry) and every entity's
        `device_info` property so the two never drift apart. Home Assistant's
        device card always labels `sw_version` "Firmware" and `hw_version`
        "Hardware" (fixed frontend strings the integration cannot rename), so
        the PLC's own versions are placed under those fixed slots instead of
        the integration release: PLCPrgInfo.progVersion (the control-program
        version) as "Firmware", and PLCInfo.version (the PLC's own firmware)
        as "Hardware". Older controller SW does not expose PLCPrgInfo at all;
        report `UNKNOWN_FIRMWARE_VERSION` ("NA") for Firmware in that case
        instead of silently substituting the integration's own release
        number, which is not the device's and previously misrepresented it.
        """
        return {
            "manufacturer": "NeoRé",
            "model": str(self.metadata.get(DATA_MODEL) or "NeoApi v2"),
            "model_id": self.metadata.get(DATA_PLC_TYPE),
            "sw_version": self.metadata.get(DATA_SW_VERSION) or UNKNOWN_FIRMWARE_VERSION,
            "hw_version": self.metadata.get(DATA_FW_VERSION),
            "serial_number": self.metadata.get(DATA_SERIAL_NUMBER),
            "configuration_url": base_url,
        }

    @property
    def supported_object_count(self) -> int:
        """Count supported root objects present on this controller."""
        return sum(1 for name in SUPPORTED_ROOT_OBJECTS if self.has_object(name))

    @property
    def unknown_object_count(self) -> int:
        """Count controller objects not yet used by this integration."""
        supported_lower = {name.lower() for name in SUPPORTED_ROOT_OBJECTS}
        return sum(1 for name in self.available_objects if name.lower() not in supported_lower)

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            if not self._discovery_loaded:
                self.available_objects = await self.hass.async_add_executor_job(
                    self.api.get_list
                )
                self._discovery_loaded = True

            if not self._metadata_loaded:
                self.metadata = await self.hass.async_add_executor_job(
                    self.api.read_device_metadata, self.available_objects
                )
                self._metadata_loaded = True

            return await self.hass.async_add_executor_job(
                self.api.read_data, self.available_objects
            )
        except NeoApiError as exc:
            raise UpdateFailed(str(exc)) from exc
