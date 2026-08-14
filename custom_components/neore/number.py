"""Number platform for NeoRé writable temperature parameters."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import NeoReConfigEntry
from .const import (
    HEATING_CURVE_FIELDS,
    OBJECT_COOLING_WATER_SETPOINT,
    OBJECT_DHW_SETPOINT,
    OBJECT_HEATING_CURVE,
    OBJECT_HEATING_MODE,
    OBJECT_POOL_SETPOINT,
    OBJECT_POOL_WATER_TEMPERATURE,
    OBJECT_ROOM_SETPOINT,
    OBJECT_ROOM_TEMPERATURE,
    OBJECT_WATER_CORRECTION,
)
from .entity import (
    NeoReEntity,
    float_or_none,
    pool_is_exposed,
    room_temperature_is_exposed,
    temperature_is_exposable,
)


@dataclass(frozen=True)
class NeoReNumberDefinition:
    """Definition of a writable NeoApi temperature number."""

    object_name: str
    translation_key: str
    min_value: float
    max_value: float
    step: float = 1.0
    mode: NumberMode = NumberMode.BOX
    entity_category: EntityCategory | None = None


NUMBER_DEFINITIONS: tuple[NeoReNumberDefinition, ...] = (
    NeoReNumberDefinition(OBJECT_DHW_SETPOINT, "dhw_setpoint", 30.0, 60.0),
    NeoReNumberDefinition(OBJECT_ROOM_SETPOINT, "room_setpoint", 10.0, 30.0, 0.5),
    NeoReNumberDefinition(
        OBJECT_WATER_CORRECTION,
        "water_correction",
        -9.0,
        9.0,
        mode=NumberMode.SLIDER,
    ),
    NeoReNumberDefinition(
        OBJECT_COOLING_WATER_SETPOINT, "cooling_water_setpoint", 15.0, 20.0
    ),
    NeoReNumberDefinition(
        OBJECT_POOL_WATER_TEMPERATURE, "pool_water_temperature", 10.0, 40.0
    ),
    NeoReNumberDefinition(OBJECT_POOL_SETPOINT, "pool_setpoint", 10.0, 40.0),
    NeoReNumberDefinition(
        f"{OBJECT_HEATING_CURVE}.{HEATING_CURVE_FIELDS[0]}",
        "heating_curve_a",
        20.0,
        60.0,
        entity_category=EntityCategory.CONFIG,
    ),
    NeoReNumberDefinition(
        f"{OBJECT_HEATING_CURVE}.{HEATING_CURVE_FIELDS[1]}",
        "heating_curve_b",
        20.0,
        60.0,
        entity_category=EntityCategory.CONFIG,
    ),
    NeoReNumberDefinition(
        f"{OBJECT_HEATING_CURVE}.{HEATING_CURVE_FIELDS[2]}",
        "heating_curve_c",
        20.0,
        60.0,
        entity_category=EntityCategory.CONFIG,
    ),
    NeoReNumberDefinition(
        f"{OBJECT_HEATING_CURVE}.{HEATING_CURVE_FIELDS[3]}",
        "heating_curve_d",
        20.0,
        60.0,
        entity_category=EntityCategory.CONFIG,
    ),
)


def _room_setpoint_should_be_exposed(entry: NeoReConfigEntry) -> bool:
    """Expose the room setpoint only while `tobj` is a real, wired reading."""
    coordinator = entry.runtime_data
    if not temperature_is_exposable(coordinator.data.get(OBJECT_ROOM_TEMPERATURE)):
        return False
    return room_temperature_is_exposed(coordinator)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: NeoReConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up writable numbers discovered through getlist."""
    coordinator = entry.runtime_data
    entities: list[NeoReTemperatureNumber] = []

    for definition in NUMBER_DEFINITIONS:
        if not coordinator.has_object(definition.object_name):
            continue
        if definition.object_name in (
            OBJECT_POOL_WATER_TEMPERATURE,
            OBJECT_POOL_SETPOINT,
        ) and not pool_is_exposed(coordinator):
            continue
        # Requirement from NeoRé: tobjekreq is displayed only while tobj is a
        # real, wired reading (tobj <= 100 and ObjDef does not report missing).
        if (
            definition.object_name == OBJECT_ROOM_SETPOINT
            and not _room_setpoint_should_be_exposed(entry)
        ):
            continue
        entities.append(NeoReTemperatureNumber(entry, coordinator, definition))

    async_add_entities(entities)


class NeoReTemperatureNumber(NeoReEntity, NumberEntity):
    """Writable NeoRé temperature/set-point."""

    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, entry, coordinator, definition: NeoReNumberDefinition) -> None:
        super().__init__(entry, coordinator)
        self._definition = definition
        self._attr_unique_id = f"{entry.entry_id}_{definition.object_name}"
        self._attr_translation_key = definition.translation_key
        self._attr_native_min_value = definition.min_value
        self._attr_native_max_value = definition.max_value
        self._attr_native_step = definition.step
        self._attr_mode = definition.mode
        self._attr_entity_category = definition.entity_category

    @property
    def native_min_value(self) -> float:
        """Use a narrower correction range while the unit is in cooling mode."""
        if self._definition.object_name == OBJECT_WATER_CORRECTION:
            mode = self.coordinator.data.get(OBJECT_HEATING_MODE)
            return -9.0 if mode is not False else -3.0
        return self._definition.min_value

    @property
    def native_max_value(self) -> float:
        """Use a narrower correction range while the unit is in cooling mode."""
        if self._definition.object_name == OBJECT_WATER_CORRECTION:
            mode = self.coordinator.data.get(OBJECT_HEATING_MODE)
            return 9.0 if mode is not False else 3.0
        return self._definition.max_value

    @property
    def native_value(self) -> float | None:
        return float_or_none(self.coordinator.data.get(self._definition.object_name))

    @property
    def available(self) -> bool:
        """Hide room setpoint as unavailable once `tobj` is no longer a real reading."""
        if not super().available:
            return False
        if self._definition.object_name != OBJECT_ROOM_SETPOINT:
            return True
        if not temperature_is_exposable(
            self.coordinator.data.get(OBJECT_ROOM_TEMPERATURE)
        ):
            return False
        return room_temperature_is_exposed(self.coordinator)

    async def async_set_native_value(self, value: float) -> None:
        min_value = self.native_min_value
        max_value = self.native_max_value
        if value < min_value or value > max_value:
            raise ValueError(
                f"Value {value} is outside NeoRé range {min_value}..{max_value}"
            )
        name = self.coordinator.resolve_write_name(self._definition.object_name)
        await self.hass.async_add_executor_job(
            self.coordinator.api.set_object, name, value
        )
        await self.coordinator.async_request_refresh()
