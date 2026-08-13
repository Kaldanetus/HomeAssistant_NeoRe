"""Unit tests for custom_components/neore/api.py.

Every test here is offline: `NeoApiClient._open`/`get_object` are monkeypatched
so no real HTTP request is ever made.
"""

from __future__ import annotations

from urllib.error import HTTPError, URLError

import pytest

from custom_components.neore import api
from custom_components.neore.const import (
    BOOLEAN_OBJECTS,
    DATA_API_VERSION,
    DATA_FW_VERSION,
    DATA_MODEL,
    DATA_PLC_TYPE,
    DATA_SERIAL_NUMBER,
    DATA_SW_VERSION,
    OBJECT_DHW_TEMPERATURE,
    OBJECT_ERROR_CODE,
    OBJECT_HEATING_CURVE,
    OBJECT_MAIN_ENABLE,
    OBJECT_NEORE_INFO,
    OBJECT_OUTDOOR_TEMPERATURE,
    OBJECT_PLC_INFO,
    OBJECT_PLC_PROGRAM_INFO,
    OBJECT_SIMPLY_NEO_VERSION,
)


def make_client() -> api.NeoApiClient:
    """Build a client without touching the network."""
    return api.NeoApiClient("192.168.1.50", "foxtrot", "foxtrotAP1")


# --- normalize_base_url -----------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("192.168.1.10", "http://192.168.1.10"),
        ("192.168.1.10:8080", "http://192.168.1.10:8080"),
        ("  192.168.1.10  ", "http://192.168.1.10"),
        ("http://192.168.1.10/", "http://192.168.1.10"),
        ("https://neore.local:443/some/path", "https://neore.local:443"),
        ("http://neore.local///", "http://neore.local"),
    ],
)
def test_normalize_base_url(raw: str, expected: str) -> None:
    assert api.normalize_base_url(raw) == expected


@pytest.mark.parametrize("raw", ["", "   ", "ftp://192.168.1.10", "://nohost"])
def test_normalize_base_url_rejects_invalid_input(raw: str) -> None:
    with pytest.raises(ValueError):
        api.normalize_base_url(raw)


# --- controller_id -----------------------------------------------------------


def test_controller_id_is_lowercase_netloc() -> None:
    base_url = api.normalize_base_url("HTTP://MyController.Local:8080")
    assert api.controller_id(base_url) == "mycontroller.local:8080"


# --- as_bool -------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (True, True),
        (False, False),
        (1, True),
        (0, False),
        (1.0, True),
        (0.0, False),
        (-1, True),
        ("1", True),
        ("0", False),
        ("true", True),
        ("False", False),
        ("On", True),
        ("off", False),
        ("YES", True),
        ("no", False),
        (" true ", True),
    ],
)
def test_as_bool_accepts_common_representations(value, expected) -> None:
    assert api.as_bool(value) is expected


@pytest.mark.parametrize("value", ["maybe", None, [], {}, "2"])
def test_as_bool_rejects_unknown_values(value) -> None:
    with pytest.raises(api.NeoApiError):
        api.as_bool(value)


# --- find_object_name / resolve_object_name ----------------------------------


def test_find_object_name_matches_exact_name() -> None:
    assert api.find_object_name(["Tvenek", "InTtuv"], "Tvenek") == "Tvenek"


def test_find_object_name_is_case_insensitive() -> None:
    assert api.find_object_name(["Tvenek", "InTtuv"], "tvenek") == "Tvenek"


def test_find_object_name_returns_none_when_missing() -> None:
    assert api.find_object_name(["Tvenek"], "tvrat") is None
    assert api.find_object_name([], "tvenek") is None


def test_resolve_object_name_recases_root_and_keeps_suffix() -> None:
    available = ["NeoEkvValue", "chodhlavni"]
    assert (
        api.resolve_object_name(available, "neoekvvalue.TempEkvA")
        == "NeoEkvValue.TempEkvA"
    )


def test_resolve_object_name_recases_root_without_suffix() -> None:
    assert api.resolve_object_name(["ChodHlavni"], "chodhlavni") == "ChodHlavni"


def test_resolve_object_name_falls_back_to_requested_when_root_unknown() -> None:
    assert api.resolve_object_name([], "Foo.Bar") == "Foo.Bar"
    assert api.resolve_object_name(["SomethingElse"], "Foo.Bar") == "Foo.Bar"


# --- NeoApiClient._open error mapping ----------------------------------------


def test_open_maps_401_to_auth_error(monkeypatch: pytest.MonkeyPatch) -> None:
    client = make_client()

    def raise_401(*_args, **_kwargs):
        raise HTTPError("http://x", 401, "unauthorized", None, None)

    monkeypatch.setattr(client._opener, "open", raise_401)
    with pytest.raises(api.NeoApiAuthError):
        client._open("http://192.168.1.50/tecoapi/getlist")


def test_open_maps_other_http_errors_to_http_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = make_client()

    def raise_500(*_args, **_kwargs):
        raise HTTPError("http://x", 500, "boom", None, None)

    monkeypatch.setattr(client._opener, "open", raise_500)
    with pytest.raises(api.NeoApiHttpError):
        client._open("http://192.168.1.50/tecoapi/getlist")


def test_open_maps_transport_errors_to_connection_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = make_client()

    def raise_urlerror(*_args, **_kwargs):
        raise URLError("no route to host")

    monkeypatch.setattr(client._opener, "open", raise_urlerror)
    with pytest.raises(api.NeoApiConnectionError):
        client._open("http://192.168.1.50/tecoapi/getlist")


def test_decode_json_rejects_invalid_json() -> None:
    with pytest.raises(api.NeoApiError):
        api.NeoApiClient._decode_json(b"not json")


# --- get_list -----------------------------------------------------------


def test_get_list_from_dict_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    client = make_client()
    monkeypatch.setattr(client, "_open", lambda url: b'{"tvenek": 5, "tvrat": 1}')
    assert client.get_list() == {"tvenek", "tvrat"}


def test_get_list_from_list_of_dicts(monkeypatch: pytest.MonkeyPatch) -> None:
    client = make_client()
    monkeypatch.setattr(
        client, "_open", lambda url: b'[{"tvenek": 5}, {"tvrat": 1}]'
    )
    assert client.get_list() == {"tvenek", "tvrat"}


def test_get_list_raises_when_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    client = make_client()
    monkeypatch.setattr(client, "_open", lambda url: b"{}")
    with pytest.raises(api.NeoApiError):
        client.get_list()


# --- get_object / try_get_object ---------------------------------------------


def test_get_object_exact_key(monkeypatch: pytest.MonkeyPatch) -> None:
    client = make_client()
    monkeypatch.setattr(client, "_open", lambda url: b'{"tvenek": 5.3}')
    assert client.get_object("tvenek") == 5.3


def test_get_object_tolerates_response_key_case(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = make_client()
    monkeypatch.setattr(client, "_open", lambda url: b'{"TVENEK": 5.3}')
    assert client.get_object("tvenek") == 5.3


def test_get_object_accepts_scalar_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    client = make_client()
    monkeypatch.setattr(client, "_open", lambda url: b"5.3")
    assert client.get_object("tvenek") == 5.3


def test_get_object_raises_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    client = make_client()
    monkeypatch.setattr(client, "_open", lambda url: b'{"other": 1}')
    with pytest.raises(api.NeoApiError):
        client.get_object("tvenek")


def test_try_get_object_returns_none_on_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = make_client()

    def raise_error(_name):
        raise api.NeoApiError("boom")

    monkeypatch.setattr(client, "get_object", raise_error)
    assert client.try_get_object("tvenek") is None


def test_try_get_object_passes_through_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = make_client()
    monkeypatch.setattr(client, "get_object", lambda name: 42)
    assert client.try_get_object("tvenek") == 42


# --- set_object ---------------------------------------------------------


def test_set_object_encodes_bool_as_0_or_1(monkeypatch: pytest.MonkeyPatch) -> None:
    client = make_client()
    calls: list[str] = []
    monkeypatch.setattr(client, "_open", lambda url: calls.append(url) or b"")

    client.set_object("chodhlavni", True)
    client.set_object("chodhlavni", False)

    assert calls[0].endswith("setobject?chodhlavni=1")
    assert calls[1].endswith("setobject?chodhlavni=0")


def test_set_object_keeps_dotted_field_name_and_negative_numbers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = make_client()
    calls: list[str] = []
    monkeypatch.setattr(client, "_open", lambda url: calls.append(url) or b"")

    client.set_object("NeoEkvValue.TempEkvA", 35.5)
    client.set_object("korekce", -9.0)

    assert calls[0].endswith("setobject?NeoEkvValue.TempEkvA=35.5")
    assert calls[1].endswith("setobject?korekce=-9.0")


# --- read_data ------------------------------------------------------------


def test_read_data_only_reads_advertised_objects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = make_client()
    available = {OBJECT_OUTDOOR_TEMPERATURE, OBJECT_MAIN_ENABLE}

    def fake_get_object(name: str):
        return {"tvenek": 3.5, "chodhlavni": 1}[name]

    monkeypatch.setattr(client, "get_object", fake_get_object)
    data = client.read_data(available)

    assert data == {OBJECT_OUTDOOR_TEMPERATURE: 3.5, OBJECT_MAIN_ENABLE: True}
    # DHW temperature was never advertised, so it must not appear at all.
    assert OBJECT_DHW_TEMPERATURE not in data


def test_read_data_converts_boolean_objects(monkeypatch: pytest.MonkeyPatch) -> None:
    client = make_client()
    available = set(BOOLEAN_OBJECTS)
    monkeypatch.setattr(client, "get_object", lambda name: "on")

    data = client.read_data(available)
    assert all(value is True for value in data.values())


def test_read_data_flattens_heating_curve(monkeypatch: pytest.MonkeyPatch) -> None:
    client = make_client()
    available = {OBJECT_HEATING_CURVE}
    curve = {"tempekva": 30, "TEMPEKVB": 35, "TempEkvC": 40, "tempekvd": 45}
    monkeypatch.setattr(client, "get_object", lambda name: curve)

    data = client.read_data(available)

    assert data == {
        f"{OBJECT_HEATING_CURVE}.TempEkvA": 30,
        f"{OBJECT_HEATING_CURVE}.TempEkvB": 35,
        f"{OBJECT_HEATING_CURVE}.TempEkvC": 40,
        f"{OBJECT_HEATING_CURVE}.TempEkvD": 45,
    }


def test_read_data_skips_single_object_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = make_client()
    available = {OBJECT_OUTDOOR_TEMPERATURE, OBJECT_ERROR_CODE}

    def fake_get_object(name: str):
        if name == OBJECT_ERROR_CODE:
            raise api.NeoApiError("temporary glitch")
        return 3.5

    monkeypatch.setattr(client, "get_object", fake_get_object)
    data = client.read_data(available)

    assert data == {OBJECT_OUTDOOR_TEMPERATURE: 3.5}


@pytest.mark.parametrize("error_cls", [api.NeoApiAuthError, api.NeoApiConnectionError])
def test_read_data_propagates_transport_and_auth_errors(
    monkeypatch: pytest.MonkeyPatch, error_cls
) -> None:
    client = make_client()
    available = {OBJECT_OUTDOOR_TEMPERATURE}

    def fake_get_object(_name: str):
        raise error_cls("controller unreachable")

    monkeypatch.setattr(client, "get_object", fake_get_object)
    with pytest.raises(error_cls):
        client.read_data(available)


def test_read_data_raises_when_every_object_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = make_client()
    available = {OBJECT_OUTDOOR_TEMPERATURE, OBJECT_ERROR_CODE}

    def fake_get_object(_name: str):
        raise api.NeoApiError("controller confused")

    monkeypatch.setattr(client, "get_object", fake_get_object)
    with pytest.raises(api.NeoApiError):
        client.read_data(available)


def test_read_data_returns_empty_when_nothing_advertised() -> None:
    client = make_client()
    assert client.read_data(set()) == {}


# --- read_device_metadata -----------------------------------------------


def test_read_device_metadata_collects_documented_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = make_client()
    available = {
        OBJECT_NEORE_INFO,
        OBJECT_SIMPLY_NEO_VERSION,
        OBJECT_PLC_PROGRAM_INFO,
        OBJECT_PLC_INFO,
    }

    responses = {
        OBJECT_NEORE_INFO: {"ProDescr": "NeoRé XYZ 12"},
        OBJECT_SIMPLY_NEO_VERSION: "2.3.1",
        OBJECT_PLC_PROGRAM_INFO: {
            "ProgName": "neore.plc",
            "ProgVersion": "1.4.0",
            "Compiled": "2026-01-01",
            "Stamp": "abc123",
        },
        OBJECT_PLC_INFO: {
            "Family": "Tecomat",
            "PlcType": "Foxtrot",
            "Specif": "CP-1000",
            "Version": "5.1.2",
            "SerialNum": "SN-42",
        },
    }
    monkeypatch.setattr(client, "try_get_object", lambda name: responses[name])

    metadata = client.read_device_metadata(available)

    assert metadata[DATA_MODEL] == "NeoRé XYZ 12"
    assert metadata[DATA_API_VERSION] == "2.3.1"
    assert metadata[DATA_SW_VERSION] == "1.4.0"
    assert metadata[DATA_FW_VERSION] == "5.1.2"
    assert metadata[DATA_PLC_TYPE] == "Foxtrot"
    assert metadata[DATA_SERIAL_NUMBER] == "SN-42"


def test_read_device_metadata_skips_objects_not_advertised(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = make_client()

    def fail_if_called(_name: str):
        raise AssertionError("try_get_object should not be called")

    monkeypatch.setattr(client, "try_get_object", fail_if_called)
    assert client.read_device_metadata(set()) == {}


# --- validate_connection --------------------------------------------------


def test_validate_connection_delegates_to_get_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = make_client()
    monkeypatch.setattr(client, "get_list", lambda: {"tvenek"})
    assert client.validate_connection() == {"tvenek"}
