// Lokal server för utveckling och test: serverar appen på http://localhost:8787
// och skickar /api/... vidare till tulospalvelu.leijonat.fi. Inga beroenden.
// Kör: node proxy/server.js
const http = require("http");
const fs = require("fs");
const path = require("path");

const PORT = process.env.PORT || 8787;
const UPSTREAM = "https://tulospalvelu.leijonat.fi/";
const APP = path.join(__dirname, "..", "src", "filapp", "Lagets_poangliga.html");
const CACHE_MS = 60 * 1000;
const ALLOWED = new Set([
  "helpers/getlevels",
  "helpers/getdistricts",
  "serie/helpers/getsubseries",
  "serie/helpers/getsubserie",
  "helpers/getgames",
  "helpers/getteamserieroster",
  "gamereport/getgamereportdata",
  "game/helpers/getsummary",
  "helpers/getplayers",
  "serie/helpers/getstandings",
]);
const cache = new Map();

async function proxy(apiPath, search, res) {
  if (!ALLOWED.has(apiPath)) {
    res.writeHead(404, { "content-type": "application/json" });
    return res.end(JSON.stringify({ error: "not allowed" }));
  }
  const url = UPSTREAM + apiPath + search;
  const hit = cache.get(url);
  if (hit && Date.now() - hit.t < CACHE_MS) {
    res.writeHead(200, { "content-type": "application/json; charset=utf-8" });
    return res.end(hit.body);
  }
  try {
    const r = await fetch(url, { headers: { accept: "application/json", "user-agent": "lagets-poangliga-proxy" } });
    const body = await r.text();
    if (r.ok) cache.set(url, { t: Date.now(), body });
    res.writeHead(r.status, { "content-type": "application/json; charset=utf-8" });
    res.end(body);
  } catch (e) {
    res.writeHead(502, { "content-type": "application/json" });
    res.end(JSON.stringify({ error: String(e) }));
  }
}

http
  .createServer((req, res) => {
    const u = new URL(req.url, "http://localhost");
    if (u.pathname.startsWith("/api/")) return proxy(u.pathname.slice(5), u.search, res);
    if (u.pathname !== "/") {
      res.writeHead(404);
      return res.end();
    }
    fs.readFile(APP, (err, data) => {
      if (err) {
        res.writeHead(500);
        return res.end(String(err));
      }
      res.writeHead(200, { "content-type": "text/html; charset=utf-8", "cache-control": "no-store" });
      res.end(data);
    });
  })
  .listen(PORT, () => console.log(`Appen körs på http://localhost:${PORT}`));
