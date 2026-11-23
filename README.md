# Lagets poängliga / Joukkueen pistepörssi

Intern poängliga för juniorhockeylag, på svenska och finska. Appen hämtar matcher, mål, assist, utvisningar, deltagare och +/- direkt från [tulospalvelu.leijonat.fi](https://tulospalvelu.leijonat.fi) med en knapp, och visar listor gjorda för att skärmdumpas till lagets WhatsApp-grupp.

**Öppna appen:** https://mattira-elkjop.github.io/tulospalvelu/

- **Seriematcher** hämtas automatiskt och är låsta, så att de alltid stämmer med tulospalvelu. +/- kan fyllas i för hand där serien inte för det.
- **Träningsmatcher och turneringar** läggs till för hand. Listorna kan filtreras på matchtyp och period.
- **Serier utan resultat** (t.ex. U10 Leijonaliiga) hämtas från spelschemat, och ni fyller i slutresultatet själva.
- Datan sparas i webbläsaren och kan exporteras och importeras som CSV.

## Utveckling

```
node proxy/server.js          # appen på http://localhost:8787
python src/filapp/build.py    # bygger HTML-filen och index.html från src/filapp/app.js
node --test test/             # tester
```

Tulospalvelu har inget officiellt API och tillåter inte anrop från andra webbsidor (CORS). Därför går anropen via en liten proxy, [proxy/worker.js](proxy/worker.js), som körs som en gratis Cloudflare Worker. Anropen är odokumenterade och kan sluta fungera om tjänsten ändras.

Datamodell, regler och hur hämtningen fungerar finns i [CLAUDE.md](CLAUDE.md).
