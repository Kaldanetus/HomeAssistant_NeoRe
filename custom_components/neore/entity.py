"""Base entity helpers for NeoRé."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import NeoReConfigEntry
from .const import (
    CONF_BASE_URL,
    DATA_MODEL,
    DOMAIN,
    OBJECT_POOL_DEFINITION,
    POOL_OBJECTS,
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
        model = self.coordinator.metadata.get(DATA_MODEL) or "NeoApi v2"
        return DeviceInfo(
            identifiers={(DOMAIN, entry_identifier(self._entry))},
            name="NeoRé tepelné čerpadlo",
            manufacturer="NeoRé",
            model=str(model),
            configuration_url=self._entry.data[CONF_BASE_URL],
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


def pool_is_exposed(coordinator: NeoReCoordinator) -> bool:
    """Return whether pool entities should be exposed for this controller."""
    return coordinator.data.get(OBJECT_POOL_DEFINITION) is not True


def controller_has_pool(coordinator: NeoReCoordinator) -> bool:
    """Return whether the controller advertises at least one pool object."""
    return any(coordinator.has_object(object_name) for object_name in POOL_OBJECTS)
