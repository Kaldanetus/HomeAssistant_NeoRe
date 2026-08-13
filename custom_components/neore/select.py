"""Select platform for NeoRé."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import NeoReConfigEntry
from .const import OBJECT_HEATING_MODE
from .entity import NeoReEntity

OPTION_HEATING = "heating"
OPTION_COOLING = "cooling"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: NeoReConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up heating/cooling mode when supported."""
    coordinator = entry.runtime_data
    if coordinator.has_object(OBJECT_HEATING_MODE):
        async_add_entities([NeoReOperatingModeSelect(entry, coordinator)])


class NeoReOperatingModeSelect(NeoReEntity, SelectEntity):
    """Select heating or cooling mode (heating_int: 1 = heating)."""

    _attr_translation_key = "operating_mode"
    _attr_options = [OPTION_HEATING, OPTION_COOLING]

    def __init__(self, entry, coordinator) -> None:
        super().__init__(entry, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_{OBJECT_HEATING_MODE}"

    @property
    def current_option(self) -> str | None:
        value = self.coordinator.data.get(OBJECT_HEATING_MODE)
        if value is True:
            return OPTION_HEATING
        if value is False:
            return OPTION_COOLING
        return None

    async def async_select_option(self, option: str) -> None:
        if option not in self.options:
            raise ValueError(f"Unsupported NeoRé operating mode: {option}")
        name = self.coordinator.resolve_write_name(OBJECT_HEATING_MODE)
        await self.hass.async_add_executor_job(
            self.coordinator.api.set_object,
            name,
            option == OPTION_HEATING,
        )
        await self.coordinator.async_request_refresh()
