# Lagets poängliga

Intern poängliga för ett juniorhockeylag. Appen hämtar matcher, mål, assist, utvisningar och deltagare direkt från [tulospalvelu.leijonat.fi](https://tulospalvelu.leijonat.fi) med en knapp, och visar listor för poäng, mål, assist, utvisningsminuter och +/- som är gjorda för att skärmdumpas till lagets WhatsApp-grupp. Matcher kan också läggas in och ändras för hand.

Allt ligger i en enda HTML-fil. Datan sparas i webbläsaren (localStorage) och kan exporteras och importeras som CSV.

## Kom igång lokalt

```
node proxy/server.js
```

Öppna sedan http://localhost:8787. Inga beroenden behövs, bara Node 18 eller nyare.

## Varför en proxy?

tulospalvelu.leijonat.fi har inget officiellt API. Appen använder samma öppna JSON-anrop som webbsidan, men tjänsten tillåter inte anrop från andra webbsidor (CORS). Därför går anropen via en liten proxy:

- **Lokalt:** `proxy/server.js` (se ovan).
- **På telefonen:** lägg ut `proxy/worker.js` som en gratis [Cloudflare Worker](https://dash.cloudflare.com) (Workers & Pages → Create → Worker → klistra in → Deploy). Klistra in Worker-adressen i appen under **Data → Anslutning**, eller i `TP_DEFAULT_PROXY` i `src/filapp/app.js` så att alla får den automatiskt. Appen använder redan en driftsatt Worker som standard, så ingen inställning behövs.

Anropen är odokumenterade och kan sluta fungera om tjänsten ändras.

## Ändra i appen

Logiken finns i `src/filapp/app.js`. Kör efter ändringar:

```
python src/filapp/build.py
```

Det bygger `src/filapp/Lagets_poangliga.html` (filen som delas) och `index.html` (för GitHub Pages).

Mer om datamodell, CSV-format och hur hämtningen fungerar finns i [CLAUDE.md](CLAUDE.md).
