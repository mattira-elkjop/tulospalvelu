# Lagets poängliga: överlämning

Intern poängliga för ett juniorhockeylag (MIF, U13 Valkoinen lohko 3b, säsong 2026–2027). Användaren är lagledare/förälder. Han vill att det ska gå snabbt att mata in statistik efter (eller under) en match på telefonen och att skärmbilder av listorna ska gå att dela i lagets WhatsApp-grupp. Användaren skriver på svenska och vill ha appens texter på svenska.

## Status i korthet

Tre versioner har byggts i den här ordningen. **Den aktuella är filappen (`src/filapp`).** De andra två finns kvar som referens.

| Version | Fil | Lagring | Status |
|---|---|---|---|
| 1. Excel | `src/excel/build.py` → `.xlsx` | I filen | Klar, men har inte stöd för matcher eller +/- |
| 2. Molnapp | `src/molnapp/index.html` | claude.ai artifact-databas (`claude.use("db")`) | Publicerad, men har inte stöd för matcher eller +/- |
| 3. **Filapp** | `src/filapp/Lagets_poangliga.html` | `localStorage` + CSV-export/import | **Aktuell, v2 med matcher och +/-** |

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
- Ingen egen infrastruktur eller inloggning.

## Filappen (aktuell), `src/filapp`

- `app.js` är källan till all logik. `Lagets_poangliga.html` är byggd genom att CSS:en (från tidigare HTML-versioner) och `app.js` klistrats in i en enda fil. **Redigera gärna HTML-filen direkt framöver.** Det finns inget byggsteg kvar som behöver köras. Det enda kravet är att resultatet är en självständig fil utan externa beroenden utöver Google Fonts (Barlow / Barlow Condensed, med reservtypsnitt).
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
src/filapp/Lagets_poangliga.html  AKTUELL app (en fil)
src/filapp/app.js                 JS-källan som ingår i HTML-filen
src/filapp/t.py                   Playwright-test
src/molnapp/index.html, mock.js   molnversionen + db-mock
src/excel/build.py, check.py, Intern_poangliga_MIF_U13.xlsx
data/MIF_U13_databas.csv          startdata v2 (lag + spelare, inga matcher)
data/gammalt_format_v1_exempel.csv  v1-exempel för importtest
```
`t.py` har absoluta sökvägar från den ursprungliga sandlådan (`/home/claude/...`). Justera dem innan körning.
