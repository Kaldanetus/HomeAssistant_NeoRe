"""Sensor platform for NeoRé."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import (
    PERCENTAGE,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfVolumeFlowRate,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import NeoReConfigEntry
from .const import (
    DOMAIN,
    OBJECT_DHW_TEMPERATURE,
    OBJECT_ERROR_CODE,
    OBJECT_FLOW_RATE,
    OBJECT_FLOW_TEMPERATURE,
    OBJECT_HEAT_ENERGY,
    OBJECT_HEATING_POWER,
    OBJECT_CIRCULATION_PUMP_REQUESTED_POWER,
    OBJECT_HEAT_PUMP_REQUESTED_POWER,
    OBJECT_OUTDOOR_TEMPERATURE,
    OBJECT_RETURN_TEMPERATURE,
    OBJECT_ROOM_INPUT_TEMPERATURE,
    OBJECT_ROOM_TEMPERATURE,
)
from .entity import NeoReEntity, float_or_none


@dataclass(frozen=True)
class NeoReSensorDefinition:
    """Definition of one NeoRé sensor."""

    object_name: str
    translation_key: str
    device_class: SensorDeviceClass | None = None
    state_class: SensorStateClass | None = SensorStateClass.MEASUREMENT
    unit: str | None = None


SENSOR_DEFINITIONS: tuple[NeoReSensorDefinition, ...] = (
    NeoReSensorDefinition(
        OBJECT_OUTDOOR_TEMPERATURE,
        "outdoor_temperature",
        SensorDeviceClass.TEMPERATURE,
        unit=UnitOfTemperature.CELSIUS,
    ),
    NeoReSensorDefinition(
        OBJECT_RETURN_TEMPERATURE,
        "return_temperature",
        SensorDeviceClass.TEMPERATURE,
        unit=UnitOfTemperature.CELSIUS,
    ),
    NeoReSensorDefinition(
        OBJECT_ROOM_TEMPERATURE,
        "room_temperature",
        SensorDeviceClass.TEMPERATURE,
        unit=UnitOfTemperature.CELSIUS,
    ),
    NeoReSensorDefinition(
        OBJECT_FLOW_TEMPERATURE,
        "flow_temperature",
        SensorDeviceClass.TEMPERATURE,
        unit=UnitOfTemperature.CELSIUS,
    ),
    NeoReSensorDefinition(
        OBJECT_DHW_TEMPERATURE,
        "dhw_temperature",
        SensorDeviceClass.TEMPERATURE,
        unit=UnitOfTemperature.CELSIUS,
    ),
    NeoReSensorDefinition(
        OBJECT_ROOM_INPUT_TEMPERATURE,
        "room_input_temperature",
        SensorDeviceClass.TEMPERATURE,
        unit=UnitOfTemperature.CELSIUS,
    ),
    NeoReSensorDefinition(
        OBJECT_FLOW_RATE,
        "flow_rate",
        SensorDeviceClass.VOLUME_FLOW_RATE,
        unit=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
    ),
    NeoReSensorDefinition(
        OBJECT_HEATING_POWER,
        "heating_power",
        SensorDeviceClass.POWER,
        unit=UnitOfPower.KILO_WATT,
    ),
    NeoReSensorDefinition(
        OBJECT_HEAT_ENERGY,
        "heat_energy",
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL_INCREASING,
        UnitOfEnergy.KILO_WATT_HOUR,
    ),
    NeoReSensorDefinition(
        OBJECT_CIRCULATION_PUMP_REQUESTED_POWER,
        "circulation_pump_requested_power",
        state_class=SensorStateClass.MEASUREMENT,
        unit=PERCENTAGE,
    ),
    NeoReSensorDefinition(
        OBJECT_HEAT_PUMP_REQUESTED_POWER,
        "heat_pump_requested_power",
        state_class=SensorStateClass.MEASUREMENT,
        unit=PERCENTAGE,
    ),
    NeoReSensorDefinition(
        OBJECT_ERROR_CODE,
        "error_code",
        state_class=None,
    ),
)


def _temperature_is_exposable(value) -> bool:
    """Return False only for NeoRé's sentinel temperature values above 100 °C."""
    numeric = float_or_none(value)
    return numeric is None or numeric <= 100.0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: NeoReConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up only valid sensors advertised by this controller's getlist."""
    coordinator = entry.runtime_data
    entities: list[NeoReSensor] = []
    registry = er.async_get(hass)

    for definition in SENSOR_DEFINITIONS:
        if not coordinator.has_object(definition.object_name):
            continue

        unique_id = f"{entry.entry_id}_{definition.object_name}"
        registered_entity_id = registry.async_get_entity_id(
            "sensor", DOMAIN, unique_id
        )
        registered_entry = (
            registry.async_get(registered_entity_id) if registered_entity_id else None
        )

        if definition.device_class == SensorDeviceClass.TEMPERATURE:
            valid_temperature = _temperature_is_exposable(
                coordinator.data.get(definition.object_name)
            )
            if not valid_temperature:
                # NeoRé uses values above 100 °C as a sentinel for an unused or
                # disconnected temperature input. Hide an entry left over from
                # an older integration version and do not add it to Home Assistant.
                if (
                    registered_entry is not None
                    and registered_entry.hidden_by is None
                ):
                    registry.async_update_entity(
                        registered_entry.entity_id,
                        hidden_by=er.RegistryEntryHider.INTEGRATION,
                    )
                continue

            # If the temperature input became valid again, undo only hiding that
            # was previously applied by this integration. Never override a user's
            # own hidden setting.
            if (
                registered_entry is not None
                and registered_entry.hidden_by == er.RegistryEntryHider.INTEGRATION
            ):
                registry.async_update_entity(registered_entry.entity_id, hidden_by=None)

        entities.append(NeoReSensor(entry, coordinator, definition))

    async_add_entities(entities)


class NeoReSensor(NeoReEntity, SensorEntity):
    """Generic NeoRé sensor."""

    def __init__(self, entry, coordinator, definition: NeoReSensorDefinition) -> None:
        super().__init__(entry, coordinator)
        self._definition = definition
        self._attr_unique_id = f"{entry.entry_id}_{definition.object_name}"
        self._attr_translation_key = definition.translation_key
        self._attr_device_class = definition.device_class
        self._attr_state_class = definition.state_class
        self._attr_native_unit_of_measurement = definition.unit

    @property
    def native_value(self):
        value = self.coordinator.data.get(self._definition.object_name)
        if self._definition.object_name == OBJECT_ERROR_CODE:
            if value is None:
                return None
            return str(value)
        numeric = float_or_none(value)
        if (
            self._definition.device_class == SensorDeviceClass.TEMPERATURE
            and numeric is not None
            and numeric > 100.0
        ):
            return None
        return numeric

    @property
    def available(self) -> bool:
        """Mark a temperature entity unavailable if it later exceeds 100 °C."""
        if not super().available:
            return False
        if self._definition.device_class != SensorDeviceClass.TEMPERATURE:
            return True
        return _temperature_is_exposable(
            self.coordinator.data.get(self._definition.object_name)
        )
