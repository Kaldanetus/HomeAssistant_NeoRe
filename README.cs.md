# NeoRé NeoApi v2 – vlastní integrace pro Home Assistant

[English](README.md) | **Čeština**

Verze **0.4.1**.

## Co se změnilo ve verzi 0.4.1

Karta **Zařízení – informace** (ta, kterou zobrazuje mobilní aplikace s poli „Firmware“/„Hardware“/sériové číslo) nyní místo verze integrace zobrazuje údaje z PLC. Home Assistant má popisky této karty pevně dané jako „Firmware“ a „Hardware“ a integrace je nemůže přejmenovat, takže se přemapovaly hodnoty pod nimi: „Firmware“ nyní zobrazuje `PLCPrgInfo.progVersion` (verzi řídicího programu/softwaru) a „Hardware“ nadále zobrazuje stejnou hodnotu `PLCInfo.version` jako dříve. Verze integrace zůstává dostupná jako `Verze: 0.4.1` v detailních informacích zařízení a samostatné diagnostické entity **Software**/**Firmware** se nemění.

## Co se změnilo ve verzi 0.4.0

Diagnostické položky na kartě **Zařízení – informace** nyní nastavují názvy také přímo ve výkonném kódu: **Software** zobrazuje `PLCPrgInfo.progVersion` a **Firmware** zobrazuje beze změny `PLCInfo.version`. Verze integrace v detailních informacích zařízení zůstává zobrazena samostatně jako `Verze: 0.4.0`.

## Co se změnilo ve verzi 0.3.9

Verze integrace z GitHubu se nadále zobrazuje v detailních informacích zařízení jako `Verze: 0.3.9`. Na kartě **Zařízení – informace** se verze `PLCPrgInfo.progVersion` zobrazuje pod názvem **Software**. Hodnota `PLCInfo.version`, dříve uvedená jako **Hardware**, zůstává beze změny a zobrazuje se pod názvem **Firmware**.

## Co se změnilo ve verzi 0.3.7

Verze 0.3.7 načítá nové struktury `PLCPrgInfo` a `PLCInfo` popsané v Neo API. V systémových informacích zařízení Home Assistantu se díky nim zobrazí typ a sériové číslo PLC, verze řídicího programu a verze PLC. Údaje zůstávají volitelné, takže starší regulátory bez těchto struktur fungují beze změny.

Integrace při každém načtení nebo opětovném načtení integrace v Home Assistantu zjišťuje dostupné funkce z `/tecoapi/getlist`. Vytvoří pouze entity, které připojený regulátor skutečně poskytuje. Jedna verze integrace tak podporuje různé generace regulátorů a softwaru NeoRé.

Lokální grafické prvky značky NeoRé zůstávají součástí adresáře `brand/`.

Pokud regulátor přestane být dostupný, koordinátor označí entity NeoRé jako nedostupné. Jestliže dočasně selže pouze jeden inzerovaný objekt, zatímco komunikace s regulátorem nadále funguje, zbytek zařízení se dál aktualizuje a pouze chybějící hodnota se změní na neznámou.

Všechny entity zůstávají seskupené právě pod jedním zařízením Home Assistantu: **NeoRé tepelné čerpadlo**.

## Podporované entity

### Senzory

- `tvenek` – venkovní teplota
- `tvrat` – teplota vratné vody (volitelná; vytvoří se pouze tehdy, pokud ji regulátor inzeruje)
- `tobj` – pokojová teplota / teplota objektu
- `InTtopv` – teplota topné vody
- `InTtuv` – teplota teplé užitkové vody (TUV)
- `InTobj` – nezpracovaná vstupní pokojová teplota / teplota objektu
- `InTbaz` – teplota bazénu (volitelná; pouze při povolené podpoře bazénu)
- `ActFlow` – průtok topné vody, m³/h
- `ActHeaPow` – topný výkon, kW
- `HeatSumCnt` – dodaná tepelná energie, kWh; dlouhodobé statistiky jsou povoleny
- `OuPWM1` – požadovaný výkon oběhového čerpadla, %
- `pow1st` – požadovaný výkon tepelného čerpadla, %
- `errcode` – chybový/stavový kód

Senzory teploty určené pouze ke čtení se vytvoří jen tehdy, pokud je jejich hodnota při načtení nebo opětovném načtení integrace **≤ 100 °C**. Hodnoty nad 100 °C se považují za nepoužitý nebo nepřipojený senzor. Případný záznam v registru, který zůstal ze starší verze integrace, integrace skryje. Pokud již vytvořený senzor teploty později překročí 100 °C, stane se nedostupným a neplatná hodnota se nezveřejní. Po změně konfigurace senzoru integraci znovu načtěte nebo restartujte.

### Zapisovatelná nastavení teploty

- `ttuvreqmain` – požadovaná teplota TUV, 30…60 °C
- `tobjekreq` – požadovaná pokojová teplota, 10…30 °C; vytvoří se pouze při `tobj <= 100`
- `korekce` – korekce teploty vody, ±9 °C při vytápění a ±3 °C při chlazení
- `tempcoolw` – požadovaná teplota chladicí vody, 15…20 °C
- `tbazenwat` – teplota vody pro ohřev bazénu, 10…40 °C (volitelná)
- `tbazenreq` – požadovaná teplota bazénu, 10…40 °C (volitelná)
- `NeoEkvValue.TempEkvA` – bod křivky pro −20 °C, 20…60 °C
- `NeoEkvValue.TempEkvB` – bod křivky pro −7 °C, 20…60 °C
- `NeoEkvValue.TempEkvC` – bod křivky pro +6 °C, 20…60 °C
- `NeoEkvValue.TempEkvD` – bod křivky pro +19 °C, 20…60 °C

Z objektu `NeoEkvValue` jsou zpřístupněna pouze čtyři zapisovatelná pole `TempEkvA…D`.

### Ovládací prvky

- `chodhlavni` – přepínač: povolení vytápění/chlazení
- `tuvmainon` – přepínač: povolení ohřevu TUV
- `bazenmainon` – přepínač: povolení ohřevu bazénu (volitelný)
- `heating_int` – výběr: Vytápění / Chlazení (`1 = vytápění`)

### Chyby a diagnostika

- `errorblock` – binární senzor problému; zapnutý stav znamená, že vážná chyba blokuje provoz
- `sazba` – diagnostický binární senzor, **ve výchozím nastavení vypnutý**; zapnutý stav znamená, že jsou procesy řízené tarifem povoleny, vypnutý stav znamená, že jsou blokovány
- `bazenon` – binární senzor ohřevu; zapnutý stav znamená, že právě probíhá ohřev bazénu (volitelný)

## Zjišťování dostupných funkcí

Dotaz `getlist` se provádí pouze při načtení nebo opětovném načtení integrace, nikoli v každém patnáctisekundovém cyklu aktualizace. Po aktualizaci softwaru NeoRé, která přidá nebo odebere objekty NeoApi, proto integraci znovu načtěte nebo restartujte Home Assistant.

Bazénové entity se vytvoří pouze tehdy, když je `BazDef` nepravdivé. Každá bazénová entita musí být současně přítomná v `getlist`, takže regulátory bez podpory bazénu nedostanou prázdné ani nedostupné bazénové ovládací prvky.

## Instalace / aktualizace

1. Nahraďte adresář `/config/custom_components/neore` adresářem `custom_components/neore` z tohoto balíčku.
2. Restartujte Home Assistant.
3. Jedinečné identifikátory entit `tvenek` a `chodhlavni` zůstávají zachovány z verzí v0.1/v0.2.

Konfigurace v YAML není potřeba.

## Ukázkový Lovelace dashboard

Balíček obsahuje:

- `examples/ekvitermni_krivka_plotly.yaml` – jednoduchý graf čtyřbodové topné křivky
- `examples/README.md` – pokyny k nastavení

Ukázkový dashboard je volitelný a samotnou integraci nijak neovlivňuje. Vyžaduje kartu Plotly Graph Card od třetí strany. Nahraďte čtyři zástupné identifikátory entit `number.NAHRADIT_...` skutečnými identifikátory entit NeoRé z vaší instalace Home Assistantu.
