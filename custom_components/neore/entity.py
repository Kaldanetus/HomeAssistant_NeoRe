"""Base entity helpers for NeoRé."""

from __future__ import annotations

from typing import Any, Callable

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import NeoReConfigEntry
from .const import (
    CONF_BASE_URL,
    DOMAIN,
    OBJECT_DHW_DEFINITION,
    OBJECT_DHW_TEMPERATURE,
    OBJECT_POOL_DEFINITION,
    OBJECT_POOL_TEMPERATURE,
    OBJECT_ROOM_DEFINITION,
    OBJECT_ROOM_TEMPERATURE,
)
from .coordinator import NeoReCoordinator


class NeoReEntity(CoordinatorEntity[NeoReCoordinator]):
    """Base class linking all NeoRé entities to one HA device."""

    _attr_has_entity_name = True

    def __init__(self, entry: NeoReConfigEntry, coordinator: NeoReCoordinator) -> None:
        super().__init__(coordinator)
        self._entry = entry

    @property
    def device_info(self) -> DeviceInfo:
        """Return the single physical NeoRé device represented by this config entry."""
        return DeviceInfo(
            identifiers={(DOMAIN, entry_identifier(self._entry))},
            name="NeoRé tepelné čerpadlo",
            **self.coordinator.device_info_kwargs(self._entry.data[CONF_BASE_URL]),
        )


def entry_identifier(entry: NeoReConfigEntry) -> str:
    """Return the identifier shared by the device and all its entities."""
    # Keep v0.1/v0.2 identity for upgrades without duplicate devices.
    return entry.entry_id


def float_or_none(value: Any) -> float | None:
    """Return a float for a NeoApi numeric value, otherwise None."""
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def temperature_is_exposable(value: Any) -> bool:
    """Return False only for NeoRé's sentinel temperature values above 100 °C.

    Shared by the sensor and number platforms so a temperature reading and
    any writable set-point tied to it agree on what counts as a real value.
    """
    numeric = float_or_none(value)
    return numeric is None or numeric <= 100.0


def _sensor_is_wired(coordinator: NeoReCoordinator, definition_object_name: str) -> bool:
    """Return whether a NeoApi "*Def" flag confirms its physical sensor is wired.

    Each flag reports True when the sensor is *not* connected, so the input
    is considered present unless it is explicitly True. A controller whose SW
    does not (yet) expose the flag reports neither True nor False for it —
    `coordinator.data` simply has no entry — and is treated as wired, since
    the API manual documents a missing getlist entry as belonging to a newer
    SW version, not as "disconnected".
    """
    return coordinator.data.get(definition_object_name) is not True


def pool_is_exposed(coordinator: NeoReCoordinator) -> bool:
    """Return whether pool entities should be exposed for this controller."""
    return _sensor_is_wired(coordinator, OBJECT_POOL_DEFINITION)


def room_temperature_is_exposed(coordinator: NeoReCoordinator) -> bool:
    """Return whether the room/object temperature sensor (`tobj`) is really wired.

    `tobj` is the only object used to display the room/object temperature;
    `InTobj` (the raw, uncorrected input) is never used, even when a
    controller advertises it in getlist. `ObjDef` is the documented signal
    for a missing physical sensor.
    """
    return _sensor_is_wired(coordinator, OBJECT_ROOM_DEFINITION)


def dhw_is_exposed(coordinator: NeoReCoordinator) -> bool:
    """Return whether the DHW temperature sensor (`InTtuv`) is really wired."""
    return _sensor_is_wired(coordinator, OBJECT_DHW_DEFINITION)


# Read-only temperature objects whose physical sensor presence is confirmed
# by a documented NeoApi "*Def" flag rather than by getlist alone. Shared by
# the sensor platform (entity creation) and by any writable number tied to
# the same input (e.g. the room setpoint).
DEF_GATED_TEMPERATURE_OBJECTS: dict[str, Callable[[NeoReCoordinator], bool]] = {
    OBJECT_ROOM_TEMPERATURE: room_temperature_is_exposed,
    OBJECT_DHW_TEMPERATURE: dhw_is_exposed,
    OBJECT_POOL_TEMPERATURE: pool_is_exposed,
}
