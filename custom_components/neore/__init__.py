"""NeoRé integration for Home Assistant."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .api import NeoApiClient
from .const import (
    CONF_BASE_URL,
    DATA_FW_VERSION,
    DATA_MODEL,
    DATA_PLC_TYPE,
    DATA_SERIAL_NUMBER,
    DATA_SW_VERSION,
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
        # HA's device card always labels sw_version "Firmware" and hw_version
        # "Hardware" (fixed frontend strings, not overridable by the
        # integration). Use those fixed slots for the PLC's own versions
        # instead of the integration release: PLCPrgInfo.progversion (the
        # control-program/software version) under "Firmware", and
        # PLCInfo.version (the PLC's firmware version) under "Hardware".
        sw_version=coordinator.metadata.get(DATA_SW_VERSION) or INTEGRATION_VERSION,
        hw_version=coordinator.metadata.get(DATA_FW_VERSION),
        serial_number=coordinator.metadata.get(DATA_SERIAL_NUMBER),
        configuration_url=entry.data[CONF_BASE_URL],
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: NeoReConfigEntry) -> bool:
    """Unload NeoRé config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
