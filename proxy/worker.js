// Cloudflare Worker: proxy till tulospalvelu.leijonat.fi med CORS-headers.
// Tjänsten skickar inga CORS-headers, så appen i webbläsaren kan inte anropa den direkt.
//
// Installation (gratis):
//   1. Skapa ett konto på https://dash.cloudflare.com och välj Workers & Pages → Create → Worker.
//   2. Klistra in den här filen, tryck Deploy.
//   3. Kopiera adressen (t.ex. https://poangliga-proxy.<namn>.workers.dev/) och klistra in den
//      i appen under Data → Anslutning, eller i TP_DEFAULT_PROXY i src/filapp/app.js.

const UPSTREAM = "https://tulospalvelu.leijonat.fi/";

// Bara de här interna JSON-endpointsen släpps igenom.
const ALLOWED = new Set([
  "helpers/getlevels",
  "helpers/getdistricts",
  "serie/helpers/getsubseries",
  "serie/helpers/getsubserie",
  "helpers/getgames",
  "helpers/getteamserieroster",
  "gamereport/getgamereportdata",
  "game/helpers/getsummary",
]);

const CORS = {
  "access-control-allow-origin": "*",
  "access-control-allow-methods": "GET, OPTIONS",
  "access-control-allow-headers": "accept",
};

export default {
  async fetch(request, env, ctx) {
    if (request.method === "OPTIONS") return new Response(null, { headers: CORS });
    const url = new URL(request.url);
    const path = url.pathname.replace(/^\/+/, "").replace(/^api\//, "");
    if (request.method !== "GET" || !ALLOWED.has(path)) {
      return new Response(JSON.stringify({ error: "not allowed" }), {
        status: 404,
        headers: { ...CORS, "content-type": "application/json" },
      });
    }
    const target = UPSTREAM + path + url.search;
    const cache = caches.default;
    const key = new Request(target);
    let res = await cache.match(key);
    if (!res) {
      const upstream = await fetch(target, {
        headers: { accept: "application/json", "user-agent": "lagets-poangliga-proxy" },
      });
      res = new Response(upstream.body, upstream);
      res.headers.set("cache-control", "public, max-age=60");
      if (upstream.ok) ctx.waitUntil(cache.put(key, res.clone()));
    }
    res = new Response(res.body, res);
    for (const [k, v] of Object.entries(CORS)) res.headers.set(k, v);
    return res;
  },
};
