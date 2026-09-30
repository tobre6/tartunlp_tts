# Tartu NLP Text-to-Speech

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Home Assistant integratsioon Tartu NLP tekst-kõneks teenuse jaoks.

## Omadused

- Toetab eestikeelset tekst-kõneks sünteesi
- Võimaldab valida erinevate häälte vahel
- Lihtne seadistamine läbi Home Assistant UI
- Täielik integratsioon Home Assistant TTS süsteemiga
- Konfigureeritav API URL

## Installeerimine

1. Veendu, et sul on [HACS](https://hacs.xyz/) installeeritud
2. Lisa see repositoorium HACS-i kui kohandatud repositoorium:
   - HACS -> Integrations -> 3 täppi üleval paremal -> Custom repositories
   - Lisa URL: `https://github.com/tsebukas/tartunlp_tts`
   - Kategooria: Integration
3. Kliki "Install"
4. Taaskäivita Home Assistant
5. Lisa integratsioon läbi Home Assistant UI
   - Settings -> Devices & Services -> Add Integration
   - Otsi "Tartu NLP"

## Kasutamine

Pärast installeerimist saad kasutada teenust läbi Home Assistant TTS teenuse:

```yaml
service: tts.speak
data:
  entity_id: media_player.sinu_meediamängija
  message: "Tere, see on testiks!"
  engine: tartunlp_tts
  options:
    voice: "mari"
    speed: 1.2
```

`voice` ja `speed` on valikulised. Kui neid ei anta, kasutatakse integratsiooni seadetes määratud väärtusi.

## Seadistamine

### API URL
Vaikimisi kasutatakse URL-i `https://api.tartunlp.ai/text-to-speech/v2`. Kui soovid kasutada teist API URL-i, saad seda muuta:
1. Integratsiooni lisamisel
2. Või hiljem seadete alt:
   - Settings -> Devices & Services -> Tartu NLP TTS -> Configure

### Kõne kiirus
Kõne kiirus on kordaja vahemikus `0.5` kuni `2`, kus `1` on tavaline kiirus (vaikimisi). Kiirust saab määrata integratsiooni lisamisel ja hiljem seadete alt (Configure). Üksikpäringu jaoks saab selle üle kirjutada `tts.speak` teenuse `options.speed` väärtusega.

### Saadaolevad hääled

- albert
- indrek
- kalev
- kylli
- lee
- liivika
- luukas
- mari (vaikimisi)
- meelis
- peeter
- tambet
- vesta

## Kaastöötajad

- [Tõnis Tobre (@tobre6)](https://github.com/tobre6): kõne kiiruse valik ja Configure-dialoogi parandus ([#1](https://github.com/tsebukas/tartunlp_tts/pull/1))

## Litsents

[MIT](LICENSE)

## Probleemidest teatamine

Kui leiad vea või sul on soovitusi, palun [ava uus Issue GitHubis](https://github.com/tsebukas/tartunlp_tts/issues).
