"""Sensor platform for NeoRé."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfVolumeFlowRate,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import NeoReConfigEntry
from .const import (
    DATA_FW_VERSION,
    DATA_SW_VERSION,
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
    OBJECT_POOL_TEMPERATURE,
    OBJECT_RETURN_TEMPERATURE,
    OBJECT_ROOM_TEMPERATURE,
)
from .entity import (
    DEF_GATED_TEMPERATURE_OBJECTS,
    NeoReEntity,
    float_or_none,
    temperature_is_exposable,
)


@dataclass(frozen=True)
class NeoReSensorDefinition:
    """Definition of one NeoRé sensor."""

    object_name: str
    translation_key: str
    device_class: SensorDeviceClass | None = None
    state_class: SensorStateClass | None = SensorStateClass.MEASUREMENT
    unit: str | None = None


@dataclass(frozen=True)
class NeoReMetadataSensorDefinition:
    """Definition of a version shown in the device diagnostics."""

    metadata_key: str
    name: str


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
        OBJECT_POOL_TEMPERATURE,
        "pool_temperature",
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

METADATA_SENSOR_DEFINITIONS: tuple[NeoReMetadataSensorDefinition, ...] = (
    # PLCPrgInfo.progVersion is presented as Software; PLCInfo.version keeps
    # its value but is presented as Firmware in the device information card.
    NeoReMetadataSensorDefinition(DATA_SW_VERSION, "Software"),
    NeoReMetadataSensorDefinition(DATA_FW_VERSION, "Firmware"),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: NeoReConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up only valid sensors advertised by this controller's getlist."""
    coordinator = entry.runtime_data
    entities: list[NeoReSensor | NeoReMetadataSensor] = []
    registry = er.async_get(hass)

    for definition in SENSOR_DEFINITIONS:
        if not coordinator.has_object(definition.object_name):
            continue
        exposure_check = DEF_GATED_TEMPERATURE_OBJECTS.get(definition.object_name)
        if exposure_check is not None and not exposure_check(coordinator):
            # The matching *Def flag (ObjDef/TuvDef/BazDef, per manual-neo-api)
            # reports this input's physical sensor as not connected. getlist
            # may still advertise the name on this controller SW, but the
            # reading behind it does not really exist.
            continue

        unique_id = f"{entry.entry_id}_{definition.object_name}"
        registered_entity_id = registry.async_get_entity_id("sensor", DOMAIN, unique_id)
        registered_entry = (
            registry.async_get(registered_entity_id) if registered_entity_id else None
        )

        if definition.device_class == SensorDeviceClass.TEMPERATURE:
            valid_temperature = temperature_is_exposable(
                coordinator.data.get(definition.object_name)
            )
            if not valid_temperature:
                # NeoRé uses values above 100 °C as a sentinel for an unused or
                # disconnected temperature input. Hide an entry left over from
                # an older integration version and do not add it to Home Assistant.
                if registered_entry is not None and registered_entry.hidden_by is None:
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

    entities.extend(
        NeoReMetadataSensor(entry, coordinator, definition)
        for definition in METADATA_SENSOR_DEFINITIONS
        if coordinator.metadata.get(definition.metadata_key) is not None
    )

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
        if definition.object_name == OBJECT_FLOW_RATE:
            self._attr_suggested_display_precision = 2

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
        """Mark unavailable once >100 °C or a matching *Def flag reports missing."""
        if not super().available:
            return False
        if self._definition.device_class != SensorDeviceClass.TEMPERATURE:
            return True
        if not temperature_is_exposable(
            self.coordinator.data.get(self._definition.object_name)
        ):
            return False
        exposure_check = DEF_GATED_TEMPERATURE_OBJECTS.get(self._definition.object_name)
        return exposure_check is None or exposure_check(self.coordinator)


class NeoReMetadataSensor(NeoReEntity, SensorEntity):
    """A static software or firmware version diagnostic."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self, entry, coordinator, definition: NeoReMetadataSensorDefinition
    ) -> None:
        super().__init__(entry, coordinator)
        self._definition = definition
        self._attr_unique_id = f"{entry.entry_id}_{definition.metadata_key.lstrip('_')}"
        # Keep the requested labels independent of a stale translation cache in HA.
        self._attr_name = definition.name

    @property
    def native_value(self) -> str | None:
        """Return the version read during integration setup."""
        return self.coordinator.metadata.get(self._definition.metadata_key)
