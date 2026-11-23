# Lagets poängliga / Joukkueen pistepörssi

Intern poängliga för juniorhockeylag. Statistiken hämtas från tulospalvelu.leijonat.fi med en knapp. Egna matcher (träning, turnering) och +/- kan läggas till för hand. Listorna är gjorda för att skärmdumpas till lagets WhatsApp-grupp. Användaren är lagledare/förälder, skriver på svenska och vill att appen finns på svenska och finska.

- Live: https://mattira-elkjop.github.io/tulospalvelu/ (GitHub Pages, gren `main`, rotmappen)
- Repo: https://github.com/mattira-elkjop/tulospalvelu (publikt)
- Testlag: MIF, U13 Valkoinen lohko 3b, säsong 2026–2027 (`season=2027, subSerieId=4378, teamId=1368627176, serieId=1787`)

## Regler som inte får brytas

- **Inga spelarnamn i repot**, varken i kod, testdata eller dokumentation (användarens krav, repot är publikt). Truppen hämtas från tulospalvelu. Testdata är påhittad ("Testi Alfa", "Spelare 5"). Exporterade CSV-filer innehåller namn och ignoreras av git.
- Appens texter finns på svenska och finska. Ny text skrivs alltid som `T("svenska","suomi")`.
- Appen ska vara en självständig HTML-fil utan externa beroenden utöver Google Fonts.

## Filer

```
index.html                        kopia av appen för GitHub Pages (byggs av build.py)
src/filapp/app.js                 all logik (redigera här)
src/filapp/Lagets_poangliga.html  HTML + CSS, app.js klistras in av build.py
src/filapp/build.py               python src/filapp/build.py
test/app.test.js                  node --test test/  (kör app.js i en sandlåda mot fejkad tulospalvelu)
proxy/worker.js                   Cloudflare Worker-proxy (driftsatt, se nedan)
proxy/server.js                   lokal server + proxy: node proxy/server.js → http://localhost:8787
```

Arbetsflöde: ändra `app.js` (och CSS i HTML-filen) → `python src/filapp/build.py` → `node --test test/` → commit → push. GitHub Pages uppdateras inom någon minut.

## Appen

Ren JS utan ramverk. `render()` bygger om `#app` via `innerHTML`. Klick hanteras med en delegerad lyssnare på `data-a="<action>"`. Flikar: **Lista**, **Matcher**, **Spelare**, **Data**. Säsongsväljare högst upp, språkväljare SV/FI uppe till höger (sparas i `lp_lang`, standard från webbläsarens språk).

### Datamodell (localStorage `lp_data_v1`)

```js
D = { v:2, last:ISO|null, changes:Number, seasons:[{
  id, lag, serie, sasong, created, pm:Boolean,          // pm = visa/registrera +/-
  tp:{season, ssid, tid, serieId},                       // koppling till tulospalvelu (saknas för manuella lag)
  tpAt, tpNext:[...], tpNores:Boolean, tpSkip:[GameID],  // senast hämtat, nästa matcher, serie utan resultat, bortvalda matcher
  tpTable:{official, lines:[rank], rows:[{id?,name,gp,w,t,l,gf,ga,pts,rank}]},  // serietabell
  tpSeries:[{id,n,t,tid,gp,g,a,u,pm}],                   // hela seriens spelare (bara om tulospalvelu publicerar dem)
  // tp.flags={stats,standings,winPoints}, tp.abbr = lagets förkortning i serien
  players:[{id, nr, name, pos:"UP"|"MV", tpid?, tpName?, hide?}],
  matches:[{id, date, opp, type:"serie"|"tr"|"cup", players:[pid], ts,
            gid?, nores?, res?:[egna,insläppta], xgid?, notGid?:[GameID],
            gk?:[{pid, sv, ga, w:0|1, sec}]}],               // målvakter i matchen (från protokollet)
  goals:[{id, mid, k?, so?, pp?, scorer, a1, a2, ice:[pid], ts}],  // k = händelse-ID ("Goal_9"), so = avgörande straffslag, pp = powerplay
  ga:[{id, mid, k?, so?, pp?, ice:[pid], ts}],
  pens:[{id, mid, pid, min, ts}]
}]}
```

Inställningar för gränssnittet ligger i separata `lp_*`-nycklar (tab, stat, top, hide, ftype, fper, view, sown, sid, mid, lang, proxy). `changes` räknar bara egna ändringar (sådant som inte kan hämtas igen). `changed(false)` används för hämtad data.

### Tre sorters matcher

| Sort | Känns igen på | Redigering |
|---|---|---|
| Hämtad med protokoll | `gid`, inte `nores` (`locked(m)`) | Låst. Bara +/- (På isen) kan fyllas i. "Koppla loss" gör den manuell (`xgid`, läggs i `tpSkip`). "Ta bort" lägger den i `tpSkip`. |
| Schemamatch (serie utan resultat, t.ex. U10) | `gid` + `nores` | Datum och motståndare från tulospalvelu. Resultat (`res`), deltagare och händelser fylls i för hand och skrivs aldrig över. |
| Egen match | ingen `gid`, `type` tr eller cup | Fullt redigerbar. |

Resultat: räknas från målen om det finns mål (eller om matchen är låst), annars `res`, annars "–".

### Hämtning (`tpSync`)

- Hämtar `getgames` med `teamid=0` (alla lags matcher i serien i ett anrop, behövs för tabellen), `getsubserie` (flaggor: publicerar serien statistik och tabell, poäng för vinst), truppen (`getteamserieroster`) och nästa matcher. Sedan `tpSeriesData`: officiell tabell (`getstandings`) om `showStandings`, annars uträknad från alla lags resultat. Serielista (`getplayers`, ett anrop) bara om `playerStatistics`. Totalt 3–5 anrop plus två per ny eller nyligen spelad match.
- Färdiga matcher med protokoll (`GameStatus===2`, `DeniedResults` falskt, inte i `tpSkip`): nya matcher, matcher från de senaste 30 dagarna, eller alla vid "Kontrollera hela säsongen". För varje match hämtas protokoll och laguppställning, och `tpImportGame` ersätter händelserna.
- Serier med `DeniedResults` (U10/U11): spelade matcher i schemat läggs in som schemamatcher (`tpScheduleGame`). Tulospalvelu har varken resultat, trupp eller protokoll för dem (kontrollerat för U10 Leijonaliiga: alla matcher står som ej spelade, 0–0, tom tabell). Spelare läggs därför till för hand.
- **Krock:** en ny match från tulospalvelu samma dag som en egen match importeras inte direkt. Användaren väljer på ett kort i Matcher: "Använd tulospalvelus" (egen match tas bort), "Behåll min" (`tpSkip`) eller "Olika matcher" (`notGid`). För schemamatcher: "Samma match, koppla ihop" (egen match får `gid`) eller "Olika matcher". Krockarna ligger i `S.conflicts` (inte sparade). Nästa hämtning frågar igen om användaren inte valt.
- Spelare matchas i ordningen tulospalvelus person-ID (`PersonID`/`PlayerID` → `tpid`), namnet som det står i tulospalvelu (`tpName`), tröjnummer. Nummer kan skilja mellan matcher. Namnändringar i appen påverkar inte matchningen. Spelare som läggs till för hand (utan `tpid`) kan tas bort, medan spelare från tulospalvelu bara kan döljas.
- Mål räknas bara om lagets löpande ställning ökar. Missade straffslag loggas som mål med `GoalType:"RL0"` men ändrar inte ställningen.
- Avgörande straffslag (`GoalType:"VL"`, period 5) sparas med `so:true`: de räknas i matchresultatet men inte som mål, assist eller +/-.
- Mål i powerplay (`GoalType` innehåller "YV") sparas med `pp:true` och räknas inte i +/-, precis som i tulospalvelus statistik (de listar ändå vilka som var på isen).
- +/-: fälten `Plus`/`Minus` (mellanslagsseparerade tröjnummer) används när de finns, och `pm` slås då på. Annars behålls användarens egna På isen per händelse-ID (`k`) vid omhämtning. Officiell +/- vinner över egen.
- Lagstraff (tröja 0) läggs inte på någon spelare.
- Målvakter (`tpGoalies`): räddningar från `GoalkeeperSummary` (GkSaves, Period 0 = totalt). Insläppta, vinst och minuter från tidslinjen `GK_start`/`GK_change`/`GK_out` (målvakten ute)/`GK_in`. Mål i tom kasse och avgörande straffslag belastar ingen målvakt. Vinsten går till målvakten i mål vid det avgörande målet (lagets mål nr motståndarens slutsumma + 1), vid straffläggning till den som stod i mål sist. Minuter räknas till matchens slut (`GameEffTime`, eller sista målet i förlängningen eller straffläggningen). Tulospalvelu räknar inte vinster eller minuter själv (0 i deras lista), så de kan inte verifieras mot den. Låsta matcher utan `gk` hämtas om en gång (migrering).

### Vyer i Lista

**Utespelare** (egen statistik, målvakter (`pos:"MV"`) visas inte här), **Målvakter** (matcher i mål, vinster, minuter, räddningar, insläppta, räddnings%, med samma filter för matchtyp och period), **Hela serien** (bara om serien publicerar spelarstatistik, t.ex. U20: alla spelare i serien, vårt lag markerat, valet "Bara vårt lag") och **Tabell** (officiell eller uträknad, eget lag markerat, slutspelsstreck från `StandingLines`). I Laget visas varje spelares placering i serien ("Serien 43/582") när serielistan finns och inget periodfilter eller träningsfilter är valt. För U13 finns ingen serielista (förbundet publicerar den inte), och vi hämtar avsiktligt inte alla lags matcher för att räkna fram den, eftersom det skulle bli hundratals anrop. Där finns bara tabellen.

### Filter i Lista

Matchtyp (Alla/Serie/Träning/Turnering, visas bara om säsongen har flera typer) och period (Hela säsongen/Senaste 5/Senaste 10 spelade matcher). Aktiva filter syns i rubriken så att de följer med på skärmbilden. Skärmbildsläget visar bara rubrik och tabell. Utvärderat och avstått: hemma/borta, motståndare och position (för lite nytta i juniorlag, och fler val gör listan svårare att läsa).

### Statistikregler

- Spelade matcher = antal (filtrerade) matcher där spelaren finns i `match.players`.
- +/- räknas bara när `season.pm` är sant: +1 för varje spelare i `goal.ice`, −1 för varje spelare i `ga.ice`.
- Sortering: poäng → mål → färre matcher; mål → poäng → färre matcher; assist → poäng → färre matcher; utvisningsminuter → fler matcher; +/- → fler matcher. Lika värde ger delad placering.
- Dolda spelare syns inte i listorna, men deras statistik finns kvar.

### CSV (semikolon, UTF-8 med BOM)

Kolumner: `typ;lag;serie;sasong;match;datum;motstandare;nr;namn;pos;assist1_nr;assist2_nr;minuter;spelare_nr;tp_id;matchtyp;resultat;dold`

- `installning`: `namn`=plusminus (nr 0/1), tp_season/tp_serieid/tp_lagid/tp_serie (nr), tp_bortvalda (GameID:n i `spelare_nr`).
- `spelare`: nr, namn, pos, `tp_id`=person-ID, `dold`=1.
- `match`: match (nyckel m1, m2 …), datum, motstandare, spelare_nr, `tp_id`=GameID, `matchtyp` serie/serie0/tr/cup (serie0 = schemamatch), `resultat` t.ex. 5-3.
- `mal`: match, nr, assist1_nr, assist2_nr, spelare_nr (på isen), `tp_id`=händelse-ID, `pos`=VL (avgörande straffslag) eller YV (powerplay). `slappt`: match, spelare_nr, tp_id, pos. `utvisning`: match, nr, minuter.
- `malvakt`: match, nr, `resultat`=räddningar-insläppta (t.ex. 23-1), `minuter`=minuter i mål (decimaler), `pos`=V vid vinst.
- `spelare_nr` är mellanslagsseparerade nummer (komma är decimaltecken i finsk Excel). Det gamla v1-formatet stöds inte längre.

## tulospalvelu.leijonat.fi

Inget officiellt API, men öppna interna JSON-endpoints (GET, `accept: application/json`, ingen nyckel, kan ändras utan förvarning, HTTP 429 vid för många anrop). Säsong `2027` = 2026–2027.

| Syfte | Endpoint | Parametrar |
|---|---|---|
| Nivåer | `helpers/getlevels` | `season` |
| Distrikt | `helpers/getdistricts` | `season, levelId` |
| Serier | `serie/helpers/getsubseries` | `season, levelid, districtid` |
| Seriens lag + serieId | `serie/helpers/getsubserie` | `season, subSerieId, teamid=0` |
| Trupp | `helpers/getteamserieroster` | `season, teamid, serieId, lang` |
| Matcher | `helpers/getgames` | `season, subSerieId, teamid, districtid=0, gamedays=3, dog=, levelid=-1, dwl=0` |
| Protokoll | `gamereport/getgamereportdata` | `gameid, season` |
| Laguppställning per match | `game/helpers/getsummary` | `gameid, season, subSerieId, gamelength` |
| Seriens spelarstatistik | `helpers/getplayers` | `season, subSerieId, type=0, teamid=0, nop=9999` (tom om serien inte publicerar) |
| Officiell tabell | `serie/helpers/getstandings` | `season, subSerieId` (poäng 0 om serien inte visar tabell) |

**CORS:** tjänsten skickar inga CORS-headers. Därför går alla anrop via `proxy/worker.js`, **driftsatt på https://tulospalvelu-proxy.matti-rantakangas.workers.dev/** (konstanten `TP_DEFAULT_PROXY`). Workern släpper bara igenom endpointsen ovan. Den uppdateras inte automatiskt från repot: ändras `worker.js` måste den klistras in och driftsättas igen i Cloudflare-panelen. Användaren kan ange en annan proxy under Data → Anslutning (`lp_proxy`).

## Verifierat (2026-11-23)

- MIF U13: 14 matcher, 55–88. Spelade matcher, mål, assist och utvisningsminuter per spelare stämmer exakt mot tulospalvelus egna summeringar.
- SV och FI, filter, skärmbildsläge, egen träningsmatch med resultat och U10 Leijonaliiga (schemamatcher, eget resultat och egna spelare som finns kvar efter ny hämtning) testade i webbläsaren mot riktig data. Inga JS-fel.
- `node --test test/`: 14 tester (målvakter, hämtning, låsning och +/- som finns kvar, officiell +/-, krockval, filter och skärmbildsläge, serie utan resultat, dölja och koppla loss, CSV, språk, uträknad tabell, officiell tabell och serielista, straffläggning, powerplay och +/-).
- U20 SM-serien (Ässät): matcher, mål, assist, utvisningsminuter och +/- för alla 35 spelare stämmer exakt mot tulospalvelus serielista. Målvakter: matcher i mål, räddningar och insläppta stämmer exakt för alla tre mot `getgoalkeepers`. Målvaktsvinster = lagets vinster (U20 7, U13 4). Minuter per match: U13 45, U20 58–65 (målvakt ute i slutet, förlängning). MIF U13: den uträknade tabellen stämmer med matchsiffrorna.
- **Inte testat på riktiga telefoner.**

## Idéer som inte är gjorda

- PWA (manifest + service worker) så att appen kan installeras och fungerar offline.
- Exportera listan som bild direkt.
- Statistik per match och form (vinst/förlust) i Lista.
- Synk mellan flera telefoner (idag: en person matar in egna data och delar CSV).
