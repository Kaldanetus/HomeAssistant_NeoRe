# NeoRé NeoApi v2 – Home Assistant custom integration

**English** | [Čeština](README.cs.md)

Version **0.3.4**.

## What changed in 0.3.4

Version 0.3.4 keeps the existing integration behavior and adds an example Lovelace dashboard card for the four-point NeoRé heating curve. The example is stored in `examples/ekvitermni_krivka_plotly.yaml` and uses Plotly Graph Card so the x-axis can represent the actual outdoor-temperature points −20 / −7 / +6 / +19 °C.

The integration discovers capabilities from `/tecoapi/getlist` on every Home Assistant integration load/reload. Only entities actually exposed by the connected controller are created. This allows one integration version to support different NeoRé controller/software generations.

Local NeoRé brand assets remain included in `brand/`.

If the controller becomes unreachable, the coordinator makes the NeoRé entities unavailable. If one advertised object temporarily fails while the controller still communicates, the rest of the device continues to update and only the missing value becomes unknown.

All entities remain grouped below exactly one Home Assistant device: **NeoRé tepelné čerpadlo**.

## Supported entities

### Sensors
- `tvenek` – outdoor temperature
- `tvrat` – return water temperature (optional; created only if advertised by the controller)
- `tobj` – room/object temperature
- `InTtopv` – flow water temperature
- `InTtuv` – DHW temperature
- `InTobj` – raw room/object input temperature
- `ActFlow` – heating water flow, m³/h
- `ActHeaPow` – heating power, kW
- `HeatSumCnt` – delivered heat energy, kWh, long-term statistics enabled
- `OuPWM1` – requested circulation-pump output, %
- `pow1st` – requested heat-pump output, %
- `errcode` – error/status code

Read-only temperature sensors are created only when their value at integration load/reload is **≤ 100 °C**. Values above 100 °C are treated as an unused/not connected sensor. Any registry entry left from an older integration version is hidden by the integration. If an already-created temperature sensor later rises above 100 °C, it becomes unavailable and the invalid value is not published. Reload/restart the integration after a sensor configuration change.

### Writable temperature numbers
- `ttuvreqmain` – DHW setpoint, 30…60 °C
- `tobjekreq` – room setpoint, 10…30 °C; created only when `tobj <= 100`
- `korekce` – water correction, ±9 °C in heating and ±3 °C in cooling
- `tempcoolw` – cooling-water setpoint, 15…20 °C
- `NeoEkvValue.TempEkvA` – curve point for −20 °C, 20…60 °C
- `NeoEkvValue.TempEkvB` – curve point for −7 °C, 20…60 °C
- `NeoEkvValue.TempEkvC` – curve point for +6 °C, 20…60 °C
- `NeoEkvValue.TempEkvD` – curve point for +19 °C, 20…60 °C

Only the four writable `TempEkvA…D` fields are exposed from `NeoEkvValue`.

### Controls
- `chodhlavni` – switch: enable heating/cooling operation
- `tuvmainon` – switch: enable DHW heating
- `heating_int` – select: Heating / Cooling (`1 = heating`)

### Errors / diagnostics
- `errorblock` – binary problem sensor; ON means a serious error blocks operation
- `sazba` – diagnostic binary sensor, **disabled by default**; ON means tariff-controlled processes are permitted, OFF means they are blocked

## Discovery behavior

`getlist` is queried only when the integration is loaded/reloaded, not every 15-second polling cycle. Therefore, after a NeoRé software update that adds/removes NeoApi objects, reload the integration or restart Home Assistant.

## Install / upgrade

1. Replace `/config/custom_components/neore` with the `custom_components/neore` directory from this package.
2. Restart Home Assistant.
3. Existing `tvenek` and `chodhlavni` unique IDs are preserved from v0.1/v0.2.

No YAML configuration is required.

## Example Lovelace dashboard

The package contains:

- `examples/ekvitermni_krivka_plotly.yaml` – simple four-point heating-curve graph
- `examples/README.md` – setup instructions

The dashboard example is optional and does not affect the integration itself. It requires the third-party Plotly Graph Card. Replace the four placeholder `number.NAHRADIT_...` entity IDs with the actual NeoRé entity IDs from your Home Assistant installation.
