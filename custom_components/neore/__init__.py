"""NeoRé integration for Home Assistant."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .api import NeoApiClient
from .const import (
    CONF_BASE_URL,
    DATA_MODEL,
    DATA_PLC_TYPE,
    DATA_SERIAL_NUMBER,
    DOMAIN,
    INTEGRATION_VERSION,
)
from .coordinator import NeoReCoordinator

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.NUMBER,
    Platform.SELECT,
]

NeoReConfigEntry = ConfigEntry[NeoReCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: NeoReConfigEntry) -> bool:
    """Set up NeoRé from a config entry."""
    api = NeoApiClient(
        entry.data[CONF_BASE_URL],
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
    )
    coordinator = NeoReCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    # Register one physical NeoRé device. Every platform uses this identifier.
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        name="NeoRé tepelné čerpadlo",
        manufacturer="NeoRé",
        model=str(coordinator.metadata.get(DATA_MODEL) or "NeoApi v2"),
        model_id=coordinator.metadata.get(DATA_PLC_TYPE),
        # Keep the integration release in the device-detail "Version" field.
        # PLC software and firmware are exposed as separate diagnostic entities.
        sw_version=INTEGRATION_VERSION,
        serial_number=coordinator.metadata.get(DATA_SERIAL_NUMBER),
        configuration_url=entry.data[CONF_BASE_URL],
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: NeoReConfigEntry) -> bool:
    """Unload NeoRé config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
