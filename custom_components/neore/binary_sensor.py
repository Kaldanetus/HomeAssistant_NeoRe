"""Binary sensor platform for NeoRé."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import NeoReConfigEntry
from .const import OBJECT_ERROR_BLOCK, OBJECT_TARIFF_PERMISSION
from .entity import NeoReEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: NeoReConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up NeoRé binary sensors discovered through getlist."""
    coordinator = entry.runtime_data
    entities = []
    if coordinator.has_object(OBJECT_ERROR_BLOCK):
        entities.append(NeoReErrorBlockBinarySensor(entry, coordinator))
    if coordinator.has_object(OBJECT_TARIFF_PERMISSION):
        entities.append(NeoReTariffPermissionBinarySensor(entry, coordinator))
    async_add_entities(entities)


class NeoReErrorBlockBinarySensor(NeoReEntity, BinarySensorEntity):
    """Serious NeoRé error which blocks operation."""

    _attr_translation_key = "error_block"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, entry, coordinator) -> None:
        super().__init__(entry, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_{OBJECT_ERROR_BLOCK}"

    @property
    def is_on(self) -> bool | None:
        value = self.coordinator.data.get(OBJECT_ERROR_BLOCK)
        return value if isinstance(value, bool) else None


class NeoReTariffPermissionBinarySensor(NeoReEntity, BinarySensorEntity):
    """Whether tariff-controlled processes are currently permitted."""

    _attr_translation_key = "tariff_permission"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(self, entry, coordinator) -> None:
        super().__init__(entry, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_{OBJECT_TARIFF_PERMISSION}"

    @property
    def is_on(self) -> bool | None:
        value = self.coordinator.data.get(OBJECT_TARIFF_PERMISSION)
        return value if isinstance(value, bool) else None
