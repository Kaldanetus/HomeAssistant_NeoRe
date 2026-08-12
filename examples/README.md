# Ukázkový dashboard NeoRé

## Ekvitermní křivka

Soubor `ekvitermni_krivka_plotly.yaml` vykreslí čtyři nastavitelné body NeoRé:

- `NeoEkvValue.TempEkvA` při −20 °C
- `NeoEkvValue.TempEkvB` při −7 °C
- `NeoEkvValue.TempEkvC` při +6 °C
- `NeoEkvValue.TempEkvD` při +19 °C

Graf používá doplňkovou Lovelace kartu **Plotly Graph Card**. Nainstalujte ji přes HACS a poté:

1. V Home Assistantu zjistěte skutečná `entity_id` všech čtyř bodů ekvitermní křivky.
2. V ukázkovém YAML nahraďte `number.NAHRADIT_TEMP_EKV_A` až `number.NAHRADIT_TEMP_EKV_D`. Každé ID je v souboru uvedeno dvakrát.
3. Přidejte ruční kartu do dashboardu a vložte obsah YAML.

Čtyři `internal: true` entity jsou v kartě pouze jako zdroj změn. Samotný graf se sestaví z aktuálních stavů těchto entit a po jejich změně se překreslí.

Tento soubor je pouze ukázkový dashboard a není potřeba jej kopírovat do `custom_components/neore`.
