"""Base entity helpers for NeoRé."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import NeoReConfigEntry
from .const import (
    CONF_BASE_URL,
    DOMAIN,
    OBJECT_DHW_DEFINITION,
    OBJECT_POOL_DEFINITION,
    OBJECT_ROOM_DEFINITION,
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


def room_input_is_exposed(coordinator: NeoReCoordinator) -> bool:
    """Return whether the raw (uncorrected) room input sensor is really wired.

    Some controller SW advertises `InTobj` in getlist and keeps answering
    `getobject` for it even without a physical sensor attached, mirroring
    `tobj` instead. `ObjDef` is the documented signal for that case, so only
    it - not getlist presence - decides whether `InTobj` is exposed.
    """
    return _sensor_is_wired(coordinator, OBJECT_ROOM_DEFINITION)


def dhw_is_exposed(coordinator: NeoReCoordinator) -> bool:
    """Return whether the DHW temperature sensor (`InTtuv`) is really wired."""
    return _sensor_is_wired(coordinator, OBJECT_DHW_DEFINITION)
