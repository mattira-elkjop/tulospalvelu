# Lagets poängliga: överlämning

Intern poängliga för ett juniorhockeylag (MIF, U13 Valkoinen lohko 3b, säsong 2026–2027). Användaren är lagledare/förälder. Han vill att det ska gå snabbt att mata in statistik efter (eller under) en match på telefonen och att skärmbilder av listorna ska gå att dela i lagets WhatsApp-grupp. Användaren skriver på svenska och vill ha appens texter på svenska.

## Status i korthet

Tre versioner har byggts i den här ordningen. **Den aktuella är filappen (`src/filapp`).** De andra två finns kvar som referens.

| Version | Fil | Lagring | Status |
|---|---|---|---|
| 1. Excel | `src/excel/build.py` → `.xlsx` | I filen | Klar, men har inte stöd för matcher eller +/- |
| 2. Molnapp | `src/molnapp/index.html` | claude.ai artifact-databas (`claude.use("db")`) | Publicerad, men har inte stöd för matcher eller +/- |
| 3. **Filapp** | `src/filapp/Lagets_poangliga.html` (+ `index.html`) | `localStorage` + CSV-export/import | **Aktuell, v3: hämtar matcher från tulospalvelu, plus manuell inmatning** |

## Spelarlista (källa)

https://tulospalvelu.leijonat.fi/serierosterlist?season=2027&tid=1368627176&sid=1787&ssid=4378&lang=fi&pdf=1

18 spelare: 15 utespelare (UP) och 3 målvakter (MV). Källan skriver positionerna KP/MV, vilket här blivit UP/MV. Namnen står i ordningen förnamn efternamn.
Namnen lagras inte i repot. Appen hämtar spelarlistan från tulospalvelu (se nedan), och testdata använder platshållare som "Spelare 5".
Säsongen "2026–2027" är antagen, eftersom källan bara säger 2027.

## Krav från användaren (samlade)

- Statistik per spelare: **spelade matcher, mål, assist, poäng (= mål + assist), utvisningsminuter**, och **+/-** som valbart tillägg.
- Ny match: först väljer man vilka spelare som deltog. Det görs genom att trycka på nummer, med namnet i liten text under varje nummer. Därefter matar man in mål, assist, insläppta mål och utvisningar.
- Datum och motståndare per match. Motståndaren är valfri.
- Allt ska gå att redigera i appen i efterhand.
- Listor för poäng, mål, assist, utvisningsminuter och +/- (när det är påslaget) som ser bra ut på telefon och fungerar för skärmbilder.
- Appen ska gå att återanvända för andra lag och säsonger.
- Den ska gå att skicka som **en fil via WhatsApp** till en kompis som använder den på sin telefon. Datan sparas lokalt på telefonen och kan exporteras och importeras som CSV.
- Ingen egen infrastruktur eller inloggning. **Undantag (v3):** hämtningen från tulospalvelu kräver en liten proxy, se nedan.
- **(v3)** Statistiken ska hämtas automatiskt från tulospalvelu.leijonat.fi med en knapp efter matchen, i stället för att knappas in.

## Filappen (aktuell), `src/filapp`

- `app.js` är källan till all logik. **Redigera `app.js` och kör `python src/filapp/build.py`**, som klistrar in JS:en i `Lagets_poangliga.html` (CSS:en ligger i HTML-filen) och kopierar resultatet till `index.html` i reporoten (för GitHub Pages). Det enda kravet är att resultatet är en självständig fil utan externa beroenden utöver Google Fonts (Barlow / Barlow Condensed, med reservtypsnitt).
- Ren JS utan ramverk. `render()` bygger om `#app` via `innerHTML`. Klick hanteras med en delegerad lyssnare på `data-a="<action>"`.
- Flikar: **Lista**, **Matcher**, **Spelare**, **Data**. En säsongsväljare finns högst upp (ark för att byta, skapa, redigera och ta bort säsong).

### Datamodell (localStorage-nyckel `lp_data_v1`, `v:2`)

```js
D = { v:2, last:ISO|null, changes:Number, seasons:[{
  id, lag, serie, sasong, created, pm:Boolean,          // pm = +/- påslaget
  players:[{id, nr, name, pos:"UP"|"MV"}],
  matches:[{id, date:"YYYY-MM-DD", opp, players:[playerId], ts, auto?:true}],
  goals:[{id, mid, scorer, a1, a2, ice:[playerId], ts}], // egna mål
  ga:[{id, mid, ice:[playerId], ts}],                     // insläppta mål
  pens:[{id, mid, pid, min, ts}]
}]}
```
- `changes` räknar ändringar sedan senaste export och visas som en påminnelse i sidhuvudet.
- Inställningar för gränssnittet ligger i separata `lp_*`-nycklar (tab, stat, top, hide, sid, mid).
- `migrateSeason()` gör om data i v1-format (mål och utvisningar med `date`/`opp` men utan `mid`) till matcher, grupperade på datum och motståndare. Deltagarna gissas då utifrån vilka som har statistik, och matchen markeras `auto:true`, vilket visar en varning i appen. Funktionen ser också till att alla som har statistik i en match finns med bland matchens deltagare.

### Statistikregler

- Spelade matcher = antal matcher där spelaren finns i `match.players`.
- +/- räknas bara när `season.pm` är sant: +1 för varje spelare i `goal.ice`, −1 för varje spelare i `ga.ice`. När ett mål sparas med +/- påslaget läggs målskytt och assist automatiskt in i `ice`.
- Sortering och tiebreak: poäng → mål → färre matcher; mål → poäng → färre matcher; assist → poäng → färre matcher; utvisningsminuter → fler matcher; +/- → fler matcher. Lika värde på den statistik som sorteras på ger delad placering, så att två spelare med samma poäng båda får till exempel plats 2 och nästa spelare plats 4.
- "Dölj nollor" döljer spelare som har 0 i den valda statistiken. För +/- döljs i stället spelare utan spelade matcher.

### CSV-format v2 (semikolon, UTF-8 med BOM, öppnas i Excel)

Kolumner: `typ;lag;serie;sasong;match;datum;motstandare;nr;namn;pos;assist1_nr;assist2_nr;minuter;spelare_nr`

Radtyperna (`typ`) är `installning`, `spelare`, `match`, `mal`, `slappt` och `utvisning`. Vad varje typ använder:
- `installning`: `namn`=plusminus, `nr`=0/1.
- `spelare`: `nr`, `namn`, `pos`.
- `match`: `match` (nyckel, till exempel m1), `datum`, `motstandare`, `spelare_nr` (deltagare).
- `mal`: `match`, `nr` (målskytt), `assist1_nr`, `assist2_nr`, `spelare_nr` (på isen).
- `slappt`: `match`, `spelare_nr` (på isen).
- `utvisning`: `match`, `nr`, `minuter`.

Fältet `spelare_nr` är en mellanslagsseparerad lista med spelarnummer (inte komman, eftersom komma är decimaltecken i finsk Excel). Säsongen identifieras av kombinationen lag + serie + säsong.

Importen klarar också v1-filer (utan kolumnen `match`), komma- och tab-separerade filer samt datum i formatet `d.m.yyyy`. Rader med fel hoppas över, och varningarna visas för användaren.

### Begränsningar i sandlådan som påverkat designen

Appen har byggts för att också fungera som claude.ai-artifact. Där är `alert`/`confirm` blockerade, så borttagning bekräftas genom att man trycker två gånger ("Säker?"). Nedladdning och Web Share har reservlösningar: om de inte fungerar visas CSV-texten för manuell kopiering. Som fristående fil på en telefon fungerar nedladdning och delning normalt.

### Testat

Testerna (`t.py`, Playwright, Chromium 390×844) täcker:
- ny match med deltagare, mål med +/-, insläppt mål med "Samma som förra", utvisning och redigering av en målskytt
- "Samma som förra matchen" och att spelare med statistik behålls när de tas bort ur laguppställningen
- att datan finns kvar efter omladdning
- att export och import ger identisk statistik
- import av en v1-CSV och migrering av v1-data i localStorage

Inga JS-fel uppstod i testerna. **Appen har inte testats på riktiga telefoner.**

### Öppna frågor och risker

- **iPhone:** att öppna en HTML-fil från WhatsApp körs ofta inte i Safari. Android bör fungera (spara filen och öppna i Chrome). Ett möjligt alternativ är att hosta filen på en statisk adress, till exempel GitHub Pages eller Netlify Drop, och lägga den på hemskärmen som PWA.
- **localStorage:** kan raderas om användaren rensar webbläsardata. Varje ny fil-URL eller sökväg kan ge en egen lagringsplats, så om filen öppnas från ett nytt ställe är datan tom och måste importeras från CSV.
- **Två telefoner:** ingen synk. Arbetsflödet är att en person matar in och delar CSV-filen.
- **Gamla data:** matcher som skapats av migreringen behöver att deltagarna kontrolleras manuellt (de är märkta "kontrollera").

### Idéer som inte är gjorda

- Hosting som PWA (manifest + service worker), så att datan blir mer stabil och appen kan installeras på iPhone.
- Uppdatera molnappen (version 2) till samma datamodell, om användaren vill ha delad realtidsdata i stället för fil.
- Visa matchresultatet (vinst/förlust) och statistik per match i Lista. Visa poäng per match.
- Exportera listan som en bild direkt, så att man slipper ta skärmbild.

## Hämtning från tulospalvelu (v3)

tulospalvelu.leijonat.fi har inget officiellt API, men webbsidorna hämtar data från öppna interna JSON-endpoints (GET, `accept: application/json`, ingen nyckel). De är inte dokumenterade och kan ändras utan förvarning. Säsong `2027` = 2026–2027.

| Syfte | Endpoint | Parametrar |
|---|---|---|
| Nivåer | `helpers/getlevels` | `season` |
| Distrikt | `helpers/getdistricts` | `season, levelId` |
| Serier (lohkon) | `serie/helpers/getsubseries` | `season, levelid, districtid` |
| Seriens lag + `serieId` | `serie/helpers/getsubserie` | `season, subSerieId, teamid=0` |
| Lagets säsongstrupp | `helpers/getteamserieroster` | `season, teamid, serieId, lang` |
| Alla matcher (resultat, status) | `helpers/getgames` | `season, subSerieId, teamid, districtid=0, gamedays=3, dog=, levelid=-1, dwl=0` |
| Matchprotokoll (händelser) | `gamereport/getgamereportdata` | `gameid, season` |
| Laguppställning per match | `game/helpers/getsummary` | `gameid, season, subSerieId, gamelength` |

MIF U13: `season=2027, subSerieId=4378, teamId=1368627176, serieId=1787`.

**CORS:** tjänsten skickar inga CORS-headers, så webbläsaren blockerar direkta anrop (även från en lokal fil). Publika CORS-proxyer (corsproxy.io m.fl.) kräver numera nyckel eller fungerar inte. Därför:
- `proxy/worker.js`: Cloudflare Worker (gratis), släpper bara igenom endpointsen ovan och lägger till CORS. Adressen klistras in i appen under Data → Anslutning (sparas i `lp_proxy`) eller i konstanten `TP_DEFAULT_PROXY` i `app.js`.
- `proxy/server.js`: lokal Node-server utan beroenden, serverar appen på http://localhost:8787 och proxar `/api/...`. Används för utveckling och test.
- `tpBase()` väljer i ordningen: inställd proxy → `TP_DEFAULT_PROXY` → `<origin>/api/` (om sidan körs över http) → direkt (fungerar inte p.g.a. CORS, ger ett felmeddelande som pekar på Data → Anslutning).

**Datamodell (tillägg):** `season.tp = {season, ssid, tid, serieId}` (kopplingen), `season.tpAt` (senast hämtat), `season.tpNext` (nästa 3 matcher), `match.gid` (tulospalvelus GameID). CSV: ny sista kolumn `tp_id` på `match`-rader och `installning`-rader `tp_season`, `tp_serieid`, `tp_lagid`, `tp_serie`. Äldre filer utan dessa går fortfarande att importera.

**Hämtning (`tpSync`):** `getgames` → färdiga matcher (`GameStatus===2`, `DeniedResults` falskt) som inte redan har en match med samma `gid` (alla vid "Hämta om alla matcher"). För varje match hämtas protokoll och laguppställning parallellt, och `tpImportGame` ersätter matchens händelser:
- Deltagare = lagets spelare i `getsummary`. Spelare matchas först på exakt namn (nummer kan skilja mellan matcher, t.ex. en spelare som är #11 i truppen men bar #12 i en match), sedan på nummer, annars läggs de till. Namn görs om från `VERSALER` till `Versaler`.
- Mål (`Type:"Goal"`) räknas bara om lagets löpande ställning ökar. Missade straffslag loggas som mål med `GoalType:"RL0"` men ändrar inte ställningen.
- Eget mål → `goals` (målskytt, assist via tröjnummer, `ice` från fältet `Plus`). Motståndarmål → `ga` (`ice` från `Minus`). `Plus`/`Minus` är mellanslagsseparerade tröjnummer och finns bara i serier som för +/- (inte U13). Finns de slås `season.pm` på automatiskt.
- Utvisningar → `pens`. Lagstraff (tröja 0, t.ex. för många spelare på isen) räknas inte på någon spelare.
- Manuellt inlagda matcher rörs aldrig. Om en manuell match har samma datum som en hämtad visas "Möjlig dubblett".
- U10/U11 (t.ex. Leijonaliiga) har `DeniedResults=1`, så där finns inga resultat att hämta.

**Verifierat (2026-11-23):** MIF U13: 14 matcher, 55–88 i mål, och spelade matcher, mål, assist och utvisningsminuter per spelare stämmer exakt mot tulospalvelus egna summeringar (`getsummary`). En andra hämtning hittar inga nya matcher, CSV-export/import behåller koppling och `gid` med identisk statistik, och "Nytt lag från tulospalvelu" fungerar (testat med Diskos Punainen, 14 matcher). Inga JS-fel. `t.py` är inte uppdaterad eller körd för v3.

## Molnappen (version 2), `src/molnapp`

- Publicerad som claude.ai-artifact med slug `9f7b4c11-f442-4ba0-9765-33d239a40fa4` (https://claude.ai/artifact/LhDqcdrtrwCuhx5vwB7YMq). Den är privat för ägaren och delas via claude.ai, där delning med rollen Contributor krävs för att andra ska kunna skriva.
- Deklarerade capabilities är `{db:{}, user:{}}`. Data ligger i sökvägarna `seasons/{sid}`, `seasons/{sid}/players`, `/goals` och `/pens`. MIF och de 18 spelarna är inlagda under `seasons/s1`.
- Den gamla modellen saknar matcher, deltagare och +/-. `mock.js` är en fejkad `claude.use("db")` som används för lokala tester.

## Excel (version 1), `src/excel`

- `build.py` (openpyxl) skapar fyra flikar: Spelare, Matcher (en rad per mål med datum, motståndare, målskytt och assist 1/2, plus en tabell för utvisningar), Telefonvy och Datorvy.
- Listorna sorteras med formler, utan VBA och utan Excel 365-funktioner som SORT och FILTER. Detta görs med dolda sorteringsnycklar `värde*1e7 + sekundärt*1e4 + (100-rad)` plus `LARGE`/`MATCH`.
- `check.py` verifierar sorteringen mot en beräkning i Python. Omräkning görs i LibreOffice med `recalc.py` från xlsx-skillen.
- Excel-versionen saknar spelade matcher och +/-. Den är troligen inte värd att vidareutveckla.

## Filer i det här paketet

```
CLAUDE.md                         denna fil
index.html                        kopia av appen för GitHub Pages (byggs av build.py)
src/filapp/Lagets_poangliga.html  AKTUELL app (en fil)
src/filapp/app.js                 JS-källan som ingår i HTML-filen
src/filapp/build.py               klistrar in app.js i HTML-filen och skriver index.html
proxy/worker.js                   Cloudflare Worker-proxy till tulospalvelu
proxy/server.js                   lokal server + proxy (node proxy/server.js)
src/filapp/t.py                   Playwright-test
src/molnapp/index.html, mock.js   molnversionen + db-mock
src/excel/build.py, check.py, Intern_poangliga_MIF_U13.xlsx
data/MIF_U13_databas.csv          startdata v2 (lag + spelare, inga matcher)
data/gammalt_format_v1_exempel.csv  v1-exempel för importtest
```
`t.py` har absoluta sökvägar från den ursprungliga sandlådan (`/home/claude/...`). Justera dem innan körning.
