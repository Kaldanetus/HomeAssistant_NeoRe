"""Switch platform for NeoRé."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import NeoReConfigEntry
from .const import OBJECT_DHW_ENABLE, OBJECT_MAIN_ENABLE, OBJECT_POOL_ENABLE
from .entity import NeoReEntity, pool_is_exposed


async def async_setup_entry(
    hass: HomeAssistant,
    entry: NeoReConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up only switches exposed by this controller."""
    coordinator = entry.runtime_data
    entities = []
    if coordinator.has_object(OBJECT_MAIN_ENABLE):
        entities.append(
            NeoReBooleanSwitch(entry, coordinator, OBJECT_MAIN_ENABLE, "main_enable")
        )
    if coordinator.has_object(OBJECT_DHW_ENABLE):
        entities.append(
            NeoReBooleanSwitch(entry, coordinator, OBJECT_DHW_ENABLE, "dhw_enable")
        )
    if coordinator.has_object(OBJECT_POOL_ENABLE) and pool_is_exposed(coordinator):
        entities.append(
            NeoReBooleanSwitch(entry, coordinator, OBJECT_POOL_ENABLE, "pool_enable")
        )
    async_add_entities(entities)


class NeoReBooleanSwitch(NeoReEntity, SwitchEntity):
    """Writable NeoApi boolean switch."""

    def __init__(
        self, entry, coordinator, object_name: str, translation_key: str
    ) -> None:
        super().__init__(entry, coordinator)
        self._object_name = object_name
        self._attr_unique_id = f"{entry.entry_id}_{object_name}"
        self._attr_translation_key = translation_key

    @property
    def is_on(self) -> bool | None:
        value = self.coordinator.data.get(self._object_name)
        return value if isinstance(value, bool) else None

    async def async_turn_on(self, **kwargs) -> None:
        await self.hass.async_add_executor_job(
            self.coordinator.api.set_object, self._object_name, True
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await self.hass.async_add_executor_job(
            self.coordinator.api.set_object, self._object_name, False
        )
        await self.coordinator.async_request_refresh()
