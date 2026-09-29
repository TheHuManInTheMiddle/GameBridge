# G.A.M.E. B.R.I.D.G.E.
## Översiktsmanual

**Generalized Asynchronous Modular Extension — Bidirectional Runtime Interaction Dialogue Guidance Environment**

---

## 1. Översikt

G.A.M.E. B.R.I.D.G.E. är ett modulärt integrationslager för interaktion mellan **människa, AI och externa applikationer**.

Systemets grundidé är inte att ersätta människan med en autonom agent, och inte heller att bygga en specifik AI för en specifik applikation.

I stället fungerar GameBridge som ett gemensamt runtime-lager där:

- människan kan kommunicera med AI:n,
- AI:n kan få information om en extern applikation,
- AI:n kan interagera med applikationen genom ett definierat adapterkontrakt,
- och nya målmiljöer kan läggas till utan att GameBridge-kärnan behöver skrivas om.

Den centrala modellen är därför:

```text
Human
   │
   │ Dialogue / Input
   ▼
┌─────────────────────┐
│     GameBridge      │
│                     │
│  Channel 1          │◄────► AI
│  Dialogue           │
│                     │
│  Channel 2          │
│  Runtime Interaction│
└──────────┬──────────┘
           │
           ▼
        Adapter
           │
           ▼
     Application
```

GameBridge är alltså bron mellan deltagarna i interaktionen.

---

# 2. Akronymen

Namnet beskriver systemets arkitektur:

## Generalized

GameBridge är inte bundet till ett enskilt spel, program eller AI-system.

Kärnan är byggd för att kunna arbeta med olika målmiljöer genom adapters.

En adapter kan exempelvis koppla GameBridge till:

- ett spel,
- en desktopapplikation,
- ett utvecklingsverktyg,
- en lokal tjänst,
- ett nätverksgränssnitt,
- eller en annan extern runtime-miljö.

---

## Asynchronous

Flera delar av systemet arbetar separat från GUI:ts huvudflöde.

Det gäller bland annat:

- telemetri,
- AI-anrop,
- interaktionsflöden,
- röstfunktioner,
- hårdvaruinput,
- och vissa externa operationer.

Syftet är att en långsam extern operation inte automatiskt ska blockera hela användargränssnittet.

---

## Modular Extension

GameBridge är byggt kring en utbytbar kärna och externa adapters.

Kärnan känner inte till detaljerna om varje målprogram.

I stället beskriver adaptern:

- hur applikationen startas eller ansluts,
- vilken information som kan läsas,
- vilka handlingar som stöds,
- vilka begränsningar som finns,
- och hur GameBridge ska interagera med målmiljön.

Detta gör att en ny integration kan byggas utan att hårdkoda applikationsspecifik logik i GameBridge-kärnan.

---

## Bidirectional Runtime Interaction

Interaktionen är tvåvägs.

GameBridge kan:

```text
Application
     │
     │ Telemetry / State
     ▼
GameBridge
     │
     │ Context
     ▼
AI
```

men även:

```text
AI
 │
 │ Action / Intent
 ▼
GameBridge
 │
 │ Channel 2
 ▼
Adapter
 │
 ▼
Application
```

Det innebär att AI:n kan få information om målmiljön samtidigt som den kan skicka beslut eller interaktionsdata tillbaka.

---

## Dialogue Guidance Environment

Människans dialog är en egen del av systemet.

Det är inte bara en kommandorad som används för att ge AI:n instruktioner.

GameBridge har en separat kommunikationsväg för människa ↔ AI.

Det är en viktig designprincip: **dialog och applikationsinteraktion är olika typer av signaler och ska kunna hanteras separat.**

---

# 3. De två huvudkanalerna

GameBridge är organiserat kring två huvudsakliga interaktionskanaler.

## Channel 1 — Dialogue

Channel 1 hanterar den mänskliga dialogen.

Den används för:

- användarens textinput,
- AI:ns svar,
- presentation i GUI:t,
- och konversationsrelaterad kommunikation.

I I/O-lagret registreras GUI:ts loggfunktion som mottagare för Channel 1, och text kan därefter skickas mellan användaren och systemets AI-flöde.

---

## Channel 2 — Application Interaction

Channel 2 är den separata vägen mellan GameBridge och den aktiva adaptern.

Den används för två riktningar:

### Läsning

```text
Application
    │
    ▼
Adapter.read_telemetry()
    │
    ▼
Channel 2
    │
    ▼
GameBridge / AI Context
```

### Skrivning

```text
AI Decision
    │
    ▼
GameBridge
    │
    ▼
Channel 2
    │
    ▼
Adapter.execute_interaction()
    │
    ▼
Application
```

I/O-lagret registrerar adapterns input- och outputfunktioner dynamiskt och använder dem som gräns mellan GameBridge och målmiljön.

---

# 4. Channel Matrix

ChannelMatrix fungerar som en kontrollpunkt för vilka interaktionsvägar som är aktiva.

Systemet kan arbeta i olika lägen:

### Channel 1 aktiv, Channel 2 låst

AI:n arbetar som samtalspartner.

```text
Human ↔ AI
```

Ingen applikationsinteraktion ska genereras.

---

### Channel 1 låst, Channel 2 aktiv

Systemet fokuserar på målmiljön.

```text
AI → GameBridge → Adapter → Application
```

---

### Båda aktiva

Dialog och applikationsinteraktion kan användas parallellt.

Det är här GameBridge når sitt mest kompletta interaktionsläge:

```text
Human
  │
  ├──── Channel 1 ────► AI
  │                       │
  │                       ▼
  └──── Dialogue ◄── GameBridge
                          │
                          ▼
                    Channel 2
                          │
                          ▼
                     Application
```

AI-klienten får olika instruktioner beroende på kanalernas aktuella tillstånd. När Channel 2 är aktiv används dessutom ett striktare JSON-format för att skapa tydligare maskinläsbara interaktionspayloads.

---

# 5. GameBridge Core

Vid uppstart skapas de centrala delarna av plattformen och kopplas samman.

Den aktuella startstrukturen inkluderar bland annat:

- `GameBridgeCore`
- `GameBridgeIOLayer`
- `ChannelMatrix`
- `SessionManager`
- `TelemetryCore`
- `LocalizationCore`
- `VoiceCore`
- `GameBridgeGUI`

Dessa skapas separat och kopplas sedan samman innan GUI:t startas.

Det betyder att systemet inte är uppbyggt som en enda monolitisk klass där GUI, AI, applikationslogik och hårdvaruhantering ligger blandade.

I stället finns flera separerade ansvar.

---

# 6. Telemetri

En adapter kan rapportera aktuell information från målmiljön.

Det sker genom:

```python
read_telemetry() -> dict
```

Telemetrin skickas tillbaka som strukturerad data.

Exempel:

```json
{
  "application": "Target Application",
  "status": "connected",
  "telemetry_data": {},
  "timestamp": 1234567890
}
```

GameBridge använder denna information som runtime-kontext.

Det innebär att AI:n inte nödvändigtvis behöver arbeta utifrån en statisk beskrivning av applikationen. En adapter kan rapportera aktuell status medan systemet körs.

BaseAdapter definierar `read_telemetry()` som en obligatorisk del av adapterkontraktet.

---

# 7. Capabilities

Varje adapter beskriver också vad målmiljön faktiskt kan göra.

Det sker genom:

```python
get_capabilities() -> dict
```

Exempel från den aktuella referensadaptern innehåller information om:

- interaktionstyp,
- vilket I/O-verktyg som används,
- om fönsterfokus krävs,
- vilka handlingar som stöds,
- och vilka begränsningar som finns.

Det gör att GameBridge kan behandla adaptern som en beskrivande modul snarare än som en hårdkodad speciallösning.

AI-lagret kan få tillgång till capability-information tillsammans med aktuell telemetri.

---

# 8. Adapter-systemet

En adapter är GameBridges översättare mellan den generella plattformen och en specifik målmiljö.

Kärnan ska inte behöva känna till hur exempelvis ett visst spel, program eller API fungerar.

Det är adapterns ansvar.

Alla adapters ärver från `BaseAdapter` och implementerar följande kontrakt:

```python
initialize()
boot_or_attach()
get_capabilities()
read_telemetry()
execute_interaction(action_data)
shutdown()
```



---

## initialize()

Initierar adaptern.

Exempel på ansvar:

- läsa lokal konfiguration,
- initiera interna variabler,
- kontrollera lokala sökvägar,
- förbereda anslutningar.

---

## boot_or_attach()

Hanterar målprogrammets livscykel.

Adaptern kan exempelvis:

- kontrollera om programmet redan körs,
- ansluta till en befintlig process,
- starta applikationen,
- eller etablera en extern anslutning.

---

## get_capabilities()

Beskriver vad adaptern kan göra.

Detta gör att kärnan och AI-lagret kan arbeta med en generell struktur i stället för att känna till varje applikations interna detaljer.

---

## read_telemetry()

Läser målmiljöns aktuella tillstånd.

Resultatet returneras som en Python-dictionary.

---

## execute_interaction()

Tar emot en handling från GameBridge och översätter den till faktisk interaktion med målmiljön.

Indata kan vara exempelvis:

- en rå sträng,
- JSON,
- eller en redan parsad dictionary.

BaseAdapter definierar uttryckligen stöd för olika typer av exekveringspayloads.

---

## shutdown()

Frigör resurser och kopplar loss adaptern från målmiljön på ett kontrollerat sätt.

---

# 9. Plugin-struktur

En adapter placeras i en egen plugin-mapp.

En typisk struktur är:

```text
GameBridge/
│
├── plugins/
│   └── example_plugin/
│       ├── main_adapter.py
│       ├── plugin_config.json
│       └── system_prompt.txt
│
├── adapters/
├── core/
├── ai/
├── functions/
├── interface/
├── config/
└── main/
```

Referensadaptern visar den grundläggande modellen där en konkret adapter ärver från `BaseAdapter`, använder `PathCore` för projektets sökvägar och laddar sin lokala konfiguration från plugin-mappen.

---

# 10. Adapter-specifika AI-prompter

En plugin kan innehålla en egen `system_prompt.txt`.

AI-klienten laddar prompten dynamiskt från den aktiva pluginens katalog.

Det betyder att olika integrationsmiljöer kan definiera olika AI-beteenden utan att GameBridges generella AI-klient behöver byggas om.

Det ger ungefär följande modell:

```text
GameBridge Core
       │
       ▼
Active Plugin
       │
       ├── Adapter Logic
       ├── Configuration
       └── System Prompt
```

Adaptern beskriver alltså inte bara *hur* applikationen nås.

Pluginen kan också bidra med kontext för *hur AI:n ska förstå den specifika miljön*.

---

# 11. AI-lagret

Den aktuella implementationen innehåller ett lokalt AI-flöde via Ollama.

AI-klienten bygger systemkontexten från bland annat:

- adapter-specifik systemprompt,
- Channel 1 / Channel 2-status,
- capabilities,
- och aktuell telemetri.

När Channel 2 används sänks temperaturinställningen och JSON-format aktiveras för att skapa mer deterministiska interaktionspayloads.

Det viktiga arkitektoniskt är att AI-lagret arbetar med den information som GameBridge och adaptern exponerar.

Applikationsspecifik automation ligger inte direkt i AI-klienten.

---

# 12. Internetlagret

Internetåtkomst är separerad från den vanliga adapterinteraktionen.

Den aktuella strukturen använder:

```text
Cognitive Router
       │
       ▼
InternetTransport
       │
       ▼
Provider
       │
       ▼
External Internet Service
```

`InternetTransport` fungerar som ett stabilt mellanlager mellan routern och en specifik provider.

Provider-specifik logik hålls separat, och rå providerdata skickas inte direkt till Channel 1. I stället omvandlas resultatet tillbaka till GameBridges etablerade responsstruktur.

Det innebär att internetaccess inte är samma sak som själva adapterkontraktet.

Det är ett separat transport- och providerlager.

---

# 13. GUI och mänsklig kontroll

GameBridge har ett grafiskt kontrollgränssnitt som fungerar som användarens kontrollpunkt.

Den aktuella lokaliseringen visar bland annat stöd för:

- AI aktiv/inaktiv,
- Internet AI,
- adapteranslutning,
- Channel 1 textchatt,
- röstläge,
- telemetriläsning,
- och skrivning till adapter via Channel 2.

Detta är viktigt för projektets grundidé.

Människan sitter inte utanför systemet medan en agent arbetar i bakgrunden.

Människan har ett eget gränssnitt till samma integrationsmiljö.

---

# 14. Referensadapter

Den aktuella kodbasen innehåller en Notepad++-adapter som referensimplementation.

Den demonstrerar:

- lokal plugin-konfiguration,
- kontroll av om målprocessen körs,
- möjlighet att starta målprogrammet,
- capability-rapportering,
- telemetri,
- JSON-avkodning,
- och fysisk GUI-interaktion via adapterlagret. 
Referensadaptern är därför framför allt ett exempel på hur GameBridge-kontraktet kan användas.

---

# 15. Arkitekturell princip

GameBridge bygger på en enkel separation:

```text
GameBridge Core
      │
      │ General routing
      │
      ▼
Adapter Contract
      │
      │ Target-specific translation
      │
      ▼
Target Application
```

Applikationsspecifik logik ska ligga i adaptern.

AI-specifik kommunikation ska ligga i AI-lagret.

Presentation ska ligga i GUI-lagret.

Extern internetaccess ska ligga bakom ett transport-/providerlager.

Det gör att varje del kan förändras utan att nödvändigtvis kräva att hela systemet skrivs om.

---

# 16. Vad GameBridge är

GameBridge är:

- ett integrationslager,
- ett runtime-system,
- ett adapterbaserat extensionsystem,
- en miljö för mänsklig dialog och AI-interaktion,
- och en struktur för tvåvägsinteraktion med externa applikationer.

Det är byggt för att låta en människa och en AI arbeta genom samma applikationsmiljö, med tydliga gränser mellan dialog och faktisk runtime-interaktion.

---

# 17. Vad GameBridge inte försöker vara

GameBridge är inte nödvändigtvis:

- en specifik AI-modell,
- ett spel,
- en chatbot med hårdkodade verktyg,
- en universell desktop-agent som försöker ersätta användaren,
- eller en enda integrationslösning för ett specifikt program.

Det är infrastrukturen mellan dessa delar.

---

# 18. Nästa steg

Systemets adaptermodell gör det möjligt att utöka GameBridge med nya integrationsmiljöer.

Exempel på möjliga riktningar är:

- speladapters,
- utvecklingsverktyg,
- utbildningsapplikationer,
- lokala AI-system,
- externa tjänster,
- och andra miljöer där en människa och en AI behöver dela samma applikationskontext.

Den konkreta utvecklingen av varje integration sker i adaptern.

Kärnan ska i möjligaste mån förbli generell.

---

## Sammanfattning

G.A.M.E. B.R.I.D.G.E. står för:

> **Generalized Asynchronous Modular Extension — Bidirectional Runtime Interaction Dialogue Guidance Environment**

Det är ett modulärt integrationslager där:

```text
Human
   ↕
Dialogue
   ↕
GameBridge
   ↕
AI
   ↕
Runtime Interaction
   ↕
Adapter
   ↕
Application
```

är delar av samma övergripande interaktion.

Kärnan tillhandahåller strukturen.

Adaptern känner målmiljön.

AI:n arbetar med den tillgängliga kontexten.

Och människan förblir en aktiv deltagare i systemet.