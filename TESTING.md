# Testovací postup v0.4.2

## 1. Ověření discovery

```bash
curl --digest -u foxtrot:foxtrotAP1 "http://IP_REGULATORU/tecoapi/getlist"
```

Home Assistant vytvoří pouze entity odpovídající objektům, které jsou v této odpovědi.

## 2. Ověření vybraných hodnot

```bash
curl --digest -u foxtrot:foxtrotAP1 "http://IP_REGULATORU/tecoapi/getobject?tvenek"
curl --digest -u foxtrot:foxtrotAP1 "http://IP_REGULATORU/tecoapi/getobject?NeoEkvValue"
curl --digest -u foxtrot:foxtrotAP1 "http://IP_REGULATORU/tecoapi/getobject?heating_int"
curl --digest -u foxtrot:foxtrotAP1 "http://IP_REGULATORU/tecoapi/getobject?OuPWM1"
curl --digest -u foxtrot:foxtrotAP1 "http://IP_REGULATORU/tecoapi/getobject?pow1st"
curl --digest -u foxtrot:foxtrotAP1 "http://IP_REGULATORU/tecoapi/getobject?PLCPrgInfo"
curl --digest -u foxtrot:foxtrotAP1 "http://IP_REGULATORU/tecoapi/getobject?PLCInfo"
curl --digest -u foxtrot:foxtrotAP1 "http://IP_REGULATORU/tecoapi/getobject?BazDef"
curl --digest -u foxtrot:foxtrotAP1 "http://IP_REGULATORU/tecoapi/getobject?InTbaz"
curl --digest -u foxtrot:foxtrotAP1 "http://IP_REGULATORU/tecoapi/getobject?bazenmainon"
curl --digest -u foxtrot:foxtrotAP1 "http://IP_REGULATORU/tecoapi/getobject?bazenon"
```

## 3. Bezpečný test zápisu

Použijte jen tehdy, když je změna na testovacím TČ žádoucí. Příklad přepnutí hlavního povolení:

```bash
curl --digest -u foxtrot:foxtrotAP1 "http://IP_REGULATORU/tecoapi/setobject?chodhlavni=1"
```

Ekvitermní bod se zapisuje například:

```bash
curl --digest -u foxtrot:foxtrotAP1 "http://IP_REGULATORU/tecoapi/setobject?NeoEkvValue.TempEkvA=35.0"
```

## 4. Kontrola v Home Assistantu

Po restartu otevřete **Nastavení → Zařízení a služby → NeoRé → Zařízení**.

Očekávání:
- existuje jedno zařízení NeoRé,
- detailní informace zařízení nadále zobrazují `Verze: 0.4.2`,
- karta **Zařízení – informace** (v mobilní aplikaci) zobrazuje u pole
  „Firmware“ hodnotu `PLCPrgInfo.progVersion` a u pole „Hardware“
  nezměněnou hodnotu `PLCInfo.version`, pokud regulátor tyto struktury
  nabízí; popisky polí „Firmware“/„Hardware“ jsou dané Home Assistantem a
  integrace je nemění,
- samostatné diagnostické entity **Software** (`PLCPrgInfo.progVersion`) a
  **Firmware** (`PLCInfo.version`) se zobrazují v seznamu entit zařízení,
- systémové informace zařízení obsahují typ a sériové číslo PLC,
- zobrazí se jen proměnné přítomné v `getlist`,
- `sazba` je v diagnostice a ve výchozím stavu zakázaná,
- žádný čtecí teplotní senzor se nevytvoří, pokud je při načtení integrace jeho hodnota `> 100 °C`,
- `tobjekreq` se nevytvoří, pokud je při načtení integrace `tobj > 100`,
- `OuPWM1` se zobrazuje jako požadovaný výkon oběhového čerpadla,
- `pow1st` se zobrazuje jako požadovaný výkon TČ,
- `ActFlow` se ve výchozím stavu zobrazuje na dvě desetinná místa,
- `korekce` se zobrazuje jako posuvník s názvem „Korekce“,
- pokud je `BazDef` nepravdivé, zobrazí se dostupné bazénové prvky
  `InTbaz`, `bazenmainon`, `tbazenwat`, `tbazenreq` a `bazenon`,
- pokud je `BazDef` pravdivé, nezobrazí se žádný bazénový prvek,
- při odpojení PLC se zařízení/entity stanou nedostupné,
- dočasná chyba jedné proměnné neshodí ostatní entity.

## 5. Ukázkový graf ekvitermní křivky

Nainstalujte Plotly Graph Card přes HACS, otevřete `examples/ekvitermni_krivka_plotly.yaml`, nahraďte čtyři zástupné `entity_id` skutečnými entitami `TempEkvA…D` a vložte YAML jako ruční kartu do dashboardu.

Očekávání:
- osa X obsahuje body −20 / −7 / +6 / +19 °C,
- osa Y zobrazuje aktuální nastavení `TempEkvA…D`,
- změna kteréhokoli ze čtyř `number` prvků překreslí graf.
