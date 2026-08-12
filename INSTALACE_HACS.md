# Instalace HACS, repozitáře NeoRé a karty v Home Assistantu

Tento návod vás provede celou instalací: od HACS přes přidání vlastního GitHub
repozitáře a integrace **NeoRé** až po přiřazení zařízení do oblasti a vytvoření
karty na dashboardu. Konfiguraci není nutné zapisovat do
`configuration.yaml`.

> [!IMPORTANT]
> HACS i NeoRé jsou komunitní projekty, které nejsou součástí standardní
> instalace Home Assistantu. Před změnami vytvořte zálohu v **Nastavení → Systém
> → Zálohy** a ověřte, že znáte IP adresu regulátoru NeoRé.

## 1. Co budete potřebovat

- funkční Home Assistant s přístupem do složky `/config`;
- účet na [GitHubu](https://github.com/) pro prvotní autorizaci HACS;
- URL GitHub repozitáře s touto integrací (adresa stránky, na které právě čtete
  tento soubor);
- IP adresu regulátoru NeoRé dostupného ze stejné sítě jako Home Assistant;
- oprávnění správce v Home Assistantu.

## 2. Instalace HACS

Pokud již v levém panelu Home Assistantu položku **HACS** máte, pokračujte
rovnou na [přidání repozitáře](#3-přidání-vlastního-repozitáře-z-githubu).

### Doporučený způsob: aplikace HACS

1. Otevřete **Nastavení → Aplikace → Obchod s aplikacemi** (ve starších
   verzích se nabídka může jmenovat **Doplňky → Obchod s doplňky**).
2. V nabídce **⋮** vyberte **Repozitáře** a přidejte:

   ```text
   https://github.com/hacs/addons
   ```

3. V obchodě vyhledejte **Get HACS**, nainstalujte jej a spusťte.
4. Po dokončení instalace **restartujte Home Assistant** přes **Nastavení →
   Systém → Restartovat Home Assistant**. Nestačí pouze restartovat aplikaci
   Get HACS.

### Alternativa: instalační skript

Máte-li instalaci bez obchodu s aplikacemi (například Home Assistant
Container), otevřete terminál v konfiguračním adresáři Home Assistantu a
spusťte oficiální instalační příkaz HACS:

```bash
wget -O - https://get.hacs.xyz | bash -
```

Poté restartujte Home Assistant. Skript spouštějte pouze tehdy, pokud
důvěřujete adrese `get.hacs.xyz`; aktuální postup si můžete ověřit v
[oficiální dokumentaci HACS](https://www.hacs.xyz/docs/use/download/download/).

### Aktivace integrace HACS

1. Po restartu otevřete **Nastavení → Zařízení a služby**.
2. Klikněte na **Přidat integraci**, vyhledejte **HACS** a potvrďte zobrazené
   podmínky.
3. Home Assistant zobrazí jednorázový kód a odkaz na GitHub. Přihlaste se na
   GitHub, kód vložte a autorizaci potvrďte.
4. Po dokončení se v levém panelu objeví **HACS**. První načtení repozitářů
   může několik minut trvat.

> [!TIP]
> Pokud HACS po restartu nelze mezi integracemi najít, obnovte stránku
> prohlížeče bez použití mezipaměti a zkontrolujte v `/config/custom_components`,
> že existuje adresář `hacs`.

## 3. Přidání vlastního repozitáře z GitHubu

1. Otevřete **HACS** a zvolte kategorii **Integrace**.
2. Otevřete nabídku **⋮** vpravo nahoře a zvolte **Vlastní repozitáře**
   (*Custom repositories*).
3. Do pole **Repozitář** vložte URL tohoto GitHub repozitáře, například:

   ```text
   https://github.com/UZIVATEL/HomeAssistant_NeoRe
   ```

   `UZIVATEL` nahraďte vlastníkem repozitáře. Použijte adresu repozitáře,
   nikoli odkaz na ZIP, konkrétní soubor nebo větev.
4. Jako **Typ** vyberte **Integrace** a klikněte na **Přidat**.
5. V HACS vyhledejte **NeoRé NeoApi**, otevřete jej a klikněte na
   **Stáhnout**. Pokud HACS nabídne výběr verze, ponechte nejnovější stabilní
   verzi.
6. Po stažení znovu **restartujte Home Assistant**.

Úspěšná instalace vytvoří adresář
`/config/custom_components/neore`. Při aktualizaci později stačí v HACS otevřít
NeoRé, zvolit dostupnou aktualizaci a po stažení Home Assistant restartovat.

## 4. Přidání integrace NeoRé

1. Otevřete **Nastavení → Zařízení a služby**.
2. Klikněte na **Přidat integraci** a vyhledejte **NeoRé**.
3. Zadejte IP adresu regulátoru NeoRé (například `192.168.1.50`) a průvodce
   dokončete.
4. Po úspěšném spojení vznikne zařízení **NeoRé tepelné čerpadlo** a dostupné
   senzory i ovládací prvky. Integrace automaticky vytvoří pouze entity, které
   daný regulátor skutečně nabízí.

Pokud NeoRé ve vyhledávání není, zkontrolujte restart Home Assistantu a adresář
`/config/custom_components/neore`. Při chybě spojení ověřte IP adresu a ze sítě
Home Assistantu otevřete:

```text
http://IP_ADRESA_REGULATORU/tecoapi/getlist
```

## 5. Přiřazení zařízení do oblasti

Oblast v Home Assistantu představuje fyzické místo, například **Technická
místnost**. Její nastavení usnadní filtrování entit a umožní Home Assistantu
nabízet zařízení v automaticky sestavených přehledech.

1. V **Nastavení → Oblasti, štítky a zóny → Oblasti** vytvořte tlačítkem
   **Přidat oblast** například oblast **Technická místnost**. Pokud již vhodná
   oblast existuje, tento krok přeskočte.
2. Otevřete **Nastavení → Zařízení a služby → Zařízení** a vyberte
   **NeoRé tepelné čerpadlo**.
3. Klikněte na ikonu tužky, v poli **Oblast** zvolte požadovanou oblast a změnu
   uložte.

> [!NOTE]
> Přiřazení zařízení k oblasti samo o sobě nemusí vložit kartu na ručně
> spravovaný dashboard. Kartu přidejte podle následující kapitoly.

## 6. Přidání karty do oblasti dashboardu

Následující postup platí pro dashboard používající moderní rozvržení
**Oblasti** (*Sections*). U staršího rozvržení přidejte stejnou kartu přímo do
příslušného pohledu.

1. Otevřete požadovaný dashboard (například **Přehled**).
2. V nabídce **⋮** vyberte **Upravit dashboard**. Pokud je dashboard spravovaný
   automaticky, nejprve potvrďte **Převzít kontrolu**.
3. Tlačítkem **Přidat oblast** vytvořte oblast s názvem **NeoRé** nebo
   **Technická místnost**.
4. V této oblasti klikněte na **Přidat kartu** a vyberte kartu **Dlaždice**.
5. Vyberte některou z entit NeoRé, například venkovní teplotu, požadovanou
   teplotu TUV nebo hlavní vypínač. Nastavte název, ikonu a případné funkce
   dlaždice a kartu uložte.
6. Pro další důležité entity krok opakujte. Karty lze v režimu úprav přetáhnout
   a seřadit.

Praktické základní rozložení může obsahovat:

- **Venkovní teplotu** a **pokojovou teplotu** jako dlaždice;
- **teplotu topné vody** a **teplotu TUV** jako dlaždice;
- **požadovanou teplotu TUV** jako dlaždici s ovládáním;
- **vytápění/chlazení** a **ohřev TUV** jako ovládací dlaždice;
- **chybový stav** jako výrazně barevnou dlaždici.

Konkrétní `entity_id` se mohou mezi instalacemi lišit. Správné ID zjistíte v
**Nastavení → Zařízení a služby → Entity** po vyfiltrování integrace NeoRé.

## 7. Volitelně: karta ekvitermní křivky

Repozitář obsahuje také hotový příklad grafu
`examples/ekvitermni_krivka_plotly.yaml`. Graf vyžaduje doplněk **Plotly Graph
Card**:

1. V **HACS → Rozhraní** (*Frontend*) vyhledejte a stáhněte **Plotly Graph
   Card**; podle výzvy obnovte prohlížeč.
2. U čtyř bodů ekvitermní křivky zjistěte jejich skutečná `entity_id`.
3. V ukázkovém YAML nahraďte všechny hodnoty
   `number.NAHRADIT_TEMP_EKV_A` až `number.NAHRADIT_TEMP_EKV_D`.
4. V požadované oblasti dashboardu zvolte **Přidat kartu → Ruční**, vložte
   upravený YAML a kartu uložte.

Podrobnosti jsou v souboru [`examples/README.md`](examples/README.md).

## Nejčastější potíže

| Potíž | Doporučené řešení |
| --- | --- |
| HACS nebo NeoRé není v seznamu integrací | Restartujte celý Home Assistant a proveďte tvrdé obnovení stránky. |
| HACS odmítne vlastní repozitář | Ověřte URL, veřejnou dostupnost repozitáře a typ **Integrace**. |
| Integraci lze přidat, ale regulátor neodpovídá | Ověřte IP adresu, síť/VLAN, firewall a odpověď endpointu `getlist`. |
| Některé entity chybějí | NeoRé vytváří pouze funkce inzerované regulátorem; po změně jeho konfigurace integraci znovu načtěte. |
| Karta hlásí, že entita neexistuje | V editoru nahraďte ukázkové ID skutečným `entity_id` z vaší instalace. |
| Po instalaci karty se nic nezměnilo | Obnovte stránku bez mezipaměti nebo restartujte doprovodnou mobilní aplikaci. |

Po dokončení máte HACS připravený pro aktualizace, integraci NeoRé připojenou k
regulátoru, zařízení zařazené do fyzické oblasti a jeho nejdůležitější údaje na
dashboardu.
