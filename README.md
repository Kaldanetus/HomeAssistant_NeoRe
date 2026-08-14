# NeoRé NeoApi v2 – Home Assistant custom integration

**English** | [Čeština](README.cs.md)

Version **0.4.4**.

## What changed in 0.4.4

Fixed a display inconsistency between controllers on different NeoApi SW versions: some controllers advertise `InTobj` (raw room input temperature) in `getlist` and keep answering `getobject` for it even though no room sensor is wired, mirroring `tobj` instead of reporting a real reading. `InTobj` (and, for the same reason, `InTtuv`) is now only created when the corresponding documented "not connected" flag (`ObjDef`/`TuvDef`) does not report `True`; a controller SW old enough to not expose the flag at all is still treated as wired, matching the API manual's note that a name missing from `getlist` just means "not yet supported by this SW", not "disconnected". The **Firmware** field on the device information card now shows `NA` when the controller does not expose `PLCPrgInfo.progVersion`, instead of silently substituting the integration's own release number (which is not the device's firmware and misrepresented it). The device-info fields built in `__init__.py` and in every entity's `device_info` property are now assembled by one shared `NeoReCoordinator.device_info_kwargs()` so the two card sources cannot drift apart again.

## What changed in 0.4.3

Added GitHub Actions CI: `.github/workflows/test.yml` runs the new `pytest` suite in `tests/` on every push/PR (Python 3.12 and 3.13), and `.github/workflows/validate.yml` runs the official `hassfest` and `hacs/action` checks (plus a weekly schedule so rule changes upstream get caught even without a new commit). `api.py` — the NeoApi v2 client (URL/auth handling, `getobject`/`setobject`, device-metadata parsing) — is now covered by an offline unit test suite (`tests/test_api.py`, no network, no `homeassistant` dependency). See `TESTING.md` for how to run it locally and what is intentionally still manual. `find_object_name`/`resolve_object_name` (the case-insensitive object-name lookup added in 0.4.2) moved from private helpers into small, independently tested functions in `api.py`, reused by both the API client and the coordinator.

## What changed in 0.4.2

Project review fixes: the Czech `sazba` binary sensor translation ("Nízká"/"Blokován") no longer contradicts its own documented meaning and the English translation — it now reads "Povoleno"/"Blokováno" (Permitted/Blocked), matching this README. Writes to switches, the operating-mode select, and writable numbers now resolve the controller's actual object-name capitalization from `getlist` first, the same tolerance already applied when reading values, instead of always sending the hardcoded name. `manifest.json` gained `documentation`, `issue_tracker`, and `codeowners`. The duplicate `ekvitermni_krivka_plotly.yaml` copy at the repository root was removed (the canonical file lives in `examples/`). Unused `software_version`/`firmware_version` translation entries were removed from `strings.json`/translations, since those diagnostic sensors already set their name directly in code.

## What changed in 0.4.1

The **Device – information** card (the one shown in the mobile companion app, with the "Firmware"/"Hardware"/serial-number fields) now carries PLC data instead of the integration release. Home Assistant fixes the labels on that card to "Firmware" and "Hardware" and the integration cannot rename them, so the values underneath were remapped instead: "Firmware" now shows `PLCPrgInfo.progVersion` (the control-program/software version), and "Hardware" continues to show the same `PLCInfo.version` value as before. The integration release is still available as `Version: 0.4.1` in the detailed device information, and the separate **Software**/**Firmware** diagnostic sensor entities are unchanged.

## What changed in 0.4.0

The diagnostic entries in the **Device – information** card now also set their names directly in executable code: **Software** displays `PLCPrgInfo.progVersion`, while **Firmware** continues to display the unchanged `PLCInfo.version`. The integration release remains separate in the detailed device information as `Version: 0.4.0`.

## What changed in 0.3.9

Version 0.3.9 remains visible as `Version: 0.3.9` in the detailed device information. In the **Device – information** card, `PLCPrgInfo.progVersion` is shown as **Software**. The unchanged `PLCInfo.version` value, formerly labelled **Hardware**, is shown as **Firmware**.

## What changed in 0.3.7

Version 0.3.7 reads the new `PLCPrgInfo` and `PLCInfo` structures documented by Neo API. They add the PLC type and serial number, control-program version, and PLC version to the Home Assistant device system information. The data remains optional, so older controllers that do not expose these structures continue to work unchanged.

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
- `InTtuv` – DHW temperature (created only while `TuvDef` does not report `True`)
- `InTobj` – raw room/object input temperature (created only while `ObjDef` does not report `True`)
- `InTbaz` – pool temperature (optional; available only when pool support is enabled)
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
- `tbazenwat` – pool heating-water temperature, 10…40 °C (optional)
- `tbazenreq` – pool temperature setpoint, 10…40 °C (optional)
- `NeoEkvValue.TempEkvA` – curve point for −20 °C, 20…60 °C
- `NeoEkvValue.TempEkvB` – curve point for −7 °C, 20…60 °C
- `NeoEkvValue.TempEkvC` – curve point for +6 °C, 20…60 °C
- `NeoEkvValue.TempEkvD` – curve point for +19 °C, 20…60 °C

Only the four writable `TempEkvA…D` fields are exposed from `NeoEkvValue`.

### Controls
- `chodhlavni` – switch: enable heating/cooling operation
- `tuvmainon` – switch: enable DHW heating
- `bazenmainon` – switch: enable pool heating (optional)
- `heating_int` – select: Heating / Cooling (`1 = heating`)

### Errors / diagnostics
- `errorblock` – binary problem sensor; ON means a serious error blocks operation
- `sazba` – diagnostic binary sensor, **disabled by default**; ON means tariff-controlled processes are permitted, OFF means they are blocked
- `bazenon` – binary heat sensor: pool heating is active (optional)

## Discovery behavior

`getlist` is queried only when the integration is loaded/reloaded, not every 15-second polling cycle. Therefore, after a NeoRé software update that adds/removes NeoApi objects, reload the integration or restart Home Assistant.

Pool entities are created only when `BazDef` is false. Each pool entity must also be present in `getlist`; controllers without pool support therefore do not receive empty or unavailable pool controls.

`InTobj` and `InTtuv` follow the same principle through `ObjDef`/`TuvDef`: getlist advertising the name is not by itself enough, because some controller SW keeps answering `getobject` for a sensor that is not actually wired. A controller old enough to not expose the flag at all is treated as wired, per the API manual's note that a missing getlist entry means "added in a newer SW", not "disconnected".

The device information card's **Firmware** field shows `NA` when the controller does not expose `PLCPrgInfo.progVersion` (older SW). It never falls back to the integration's own release number, which is not the device's firmware.

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
