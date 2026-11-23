// Tester för appens logik. Kör: node --test test/
// Appens kod (src/filapp/app.js) körs i en sandlåda med en minimal DOM och en fejkad tulospalvelu.
// All testdata är påhittad. Lägg aldrig in riktiga spelarnamn här.
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const SRC = fs.readFileSync(path.join(__dirname, "..", "src", "filapp", "app.js"), "utf8");
const EXPOSE = `
;globalThis.API={S,cur,sync,tpSync,resolveConflict,computeStats,leaderboard,score,toCSV,parseImport,
 saveEvent,openEditor,fMatches,filterLabel,locked,T,render,viewLista,viewMatches,viewMatch,setMid,
 views,seriesRankOf,shareText,
 get D(){return D},set D(v){D=v},setSid:v=>{sid=v},setLang:v=>{LANG=v},getPlayers:()=>players};`;

const TID = 100, OPP = 200;
const tpSeason = { season: 2027, ssid: 1, tid: TID, serieId: 9 };
const P = (id, first, last, nr, role = "KP") => ({ PlayerID: id, PersonID: id, FirstName: first, LastName: last, JerseyNr: nr, RoleAbbrv: role });
const ROSTER = [P(1, "Testi", "ALFA", 5), P(2, "Testi", "BETA", 11), P(3, "Testi", "GAMMA", 90, "MV"), P(4, "Testi", "DELTA", 7)];
const game = (id, date, o = {}) => ({ GameID: id, GameDate: date, GameTime: "12:00:00", HomeTeam: TID, AwayTeam: OPP, HomeTeamAbbrv: "Hem", AwayTeamAbbrv: "Borta", HomeGoals: 0, AwayGoals: 0, GameStatus: 2, DeniedResults: 0, GameEffTime: 2700, ...o });
const goal = (key, team, period, t, h, a, scorer, o = {}) => ({ Type: "Goal", Key: key, TeamId: team, Period: period, GameTime: t, HomeTeamGoals: h, AwayTeamGoals: a, ScorerJersey: scorer, ScorerName: "", FirstAssistJersey: 0, FirstAssistName: " ", SecondAssistJersey: 0, SecondAssistName: " ", GoalType: "", GoalSpecialTypeEN: "", Plus: "", Minus: "", ...o });
const pen = (team, t, jersey, min) => ({ Type: "Penalty", TeamId: team, Period: 1, GameTime: t, Jersey: jersey, Name: "", PenaltyMinutesNumber: min, PenaltyReasonsFI: "Koukkaus" });

/* Standardserie: två spelade matcher, en kommande */
function baseData() {
  const games = [
    game(1001, "10.10.2026", { HomeGoals: 2, AwayGoals: 1 }),
    game(1002, "17.10.2026", { HomeGoals: 1, AwayGoals: 1 }),
    game(1003, "01.01.2099", { GameStatus: 0 }),
  ];
  const reports = {
    1001: [goal("Goal_1", TID, 1, 100, 1, 0, 5, { FirstAssistJersey: 11 }), goal("Goal_2", OPP, 2, 1500, 1, 1, 33), goal("Goal_3", TID, 3, 2500, 2, 1, 7), pen(TID, 300, 11, 2)],
    // Matchen 1002: #11 bär #12, missat straffslag (ställningen ändras inte) och ett lagstraff (tröja 0)
    1002: [goal("Goal_4", TID, 1, 200, 1, 0, 12), goal("Goal_5", OPP, 2, 1400, 1, 0, 9, { GoalType: "RL0", GoalSpecialTypeEN: "Penalty shot - no goal" }), goal("Goal_6", OPP, 3, 2600, 1, 1, 9), pen(TID, 900, 0, 2)],
  };
  const rosters = {
    1001: [ROSTER[0], ROSTER[1], ROSTER[2], ROSTER[3]],
    1002: [ROSTER[0], { ...ROSTER[1], JerseyNr: 12 }, ROSTER[2]],
  };
  return { games, reports, rosters };
}

function makeApp(data, opts = {}) {
  const store = new Map(Object.entries(opts.storage || {}));
  const calls = [];
  const el = { innerHTML: "", contains: () => false, insertBefore() {}, scrollIntoView() {} };
  const ctx = {
    console, URL, URLSearchParams, Blob: class {}, File: class {},
    localStorage: { getItem: k => (store.has(k) ? store.get(k) : null), setItem: (k, v) => store.set(k, String(v)), removeItem: k => store.delete(k) },
    navigator: { language: opts.lang || "sv" },
    location: { protocol: "https:", hostname: "example.test", origin: "https://example.test" },
    window: { scrollY: 0, scrollTo() {} },
    document: { querySelector: () => el, addEventListener() {}, activeElement: null, body: { classList: { toggle() {} } }, documentElement: { lang: "" }, title: "", getElementById: () => null, createElement: () => ({}) },
    setTimeout: () => 0, clearTimeout: () => {},
    fetch: async url => {
      const u = new URL(url), p = u.pathname.replace(/^\/+/, ""), q = Object.fromEntries(u.searchParams);
      calls.push(p);
      let body;
      if (p === "helpers/getgames") body = [{ Games: data.games }];
      else if (p === "helpers/getteamserieroster") body = { Players: ROSTER };
      else if (p === "gamereport/getgamereportdata") body = { GamesUpdate: [{ Id: Number(q.gameid) }], GameLogsUpdate: data.reports[q.gameid] || [] };
      else if (p === "game/helpers/getsummary") body = { HomeTeamGameRoster: { Players: data.rosters[q.gameid] || [] }, AwayTeamGameRoster: { Players: [] } };
      else if (p === "serie/helpers/getsubserie") body = data.sub || { playerStatistics: false, showStandings: false, winPoints: 2, serieId: 9 };
      else if (p === "serie/helpers/getstandings" && data.standings) body = data.standings;
      else if (p === "helpers/getplayers" && data.players) body = { Players: data.players };
      else return { ok: false, status: 404, json: async () => ({}) };
      return { ok: true, status: 200, json: async () => JSON.parse(JSON.stringify(body)) };
    },
  };
  vm.createContext(ctx);
  vm.runInContext(SRC + EXPOSE, ctx);
  const A = ctx.API;
  A.cur().tp = { ...tpSeason };
  A.calls = calls;
  A.store = store;
  return A;
}
const plain = x => JSON.parse(JSON.stringify(x));
const byNr = (A, nr) => A.cur().players.filter(p => p.nr === nr);
const stat = (A, nr, ms) => A.computeStats(ms).find(r => r.p.nr === nr);
const matchByGid = (A, gid) => A.cur().matches.find(m => m.gid === gid);

test("hämtning: resultat, missat straffslag, nummerbyte och lagstraff", async () => {
  const A = makeApp(baseData());
  await A.tpSync(false);
  const s = A.cur();
  assert.equal(s.matches.length, 2);
  assert.deepEqual([...A.score(matchByGid(A, 1001))], [2, 1]);
  assert.deepEqual([...A.score(matchByGid(A, 1002))], [1, 1], "missat straffslag räknas inte");
  assert.equal(s.players.length, 4, "#12 i en match blir inte en ny spelare (person-ID)");
  const beta = stat(A, 11);
  assert.equal(beta.gp, 2); assert.equal(beta.g, 1); assert.equal(beta.a, 1); assert.equal(beta.u, 2);
  assert.equal(s.pens.length, 1, "lagstraffet läggs inte på någon spelare");
  assert.equal(s.tpNext.length, 1);
  assert.equal(A.D.changes, 0, "hämtad data räknas inte som osparad");
});

test("hämtade matcher är låsta men +/- kan fyllas i och finns kvar efter ny hämtning", async () => {
  const A = makeApp(baseData());
  await A.tpSync(false);
  const m = matchByGid(A, 1001), s = A.cur();
  assert.equal(A.locked(m), true);
  A.setMid(m.id); A.sync();
  // försök lägga till ett mål i en låst match: ska ignoreras
  A.openEditor("g"); A.S.ev.pick = [byNr(A, 5)[0].id, null, null]; A.saveEvent();
  assert.equal(s.goals.filter(x => x.mid === m.id).length, 2);
  // fyll i På isen för första målet
  s.pm = true;
  const g1 = s.goals.find(x => x.k === "Goal_1");
  A.openEditor("g", g1.id, true); A.S.ev.ice = [byNr(A, 7)[0].id]; A.saveEvent();
  assert.equal(s.goals.find(x => x.k === "Goal_1").ice.length, 3, "målskytt + assist + vald spelare");
  await A.tpSync(true);
  assert.equal(A.cur().goals.find(x => x.k === "Goal_1").ice.length, 3, "+/- finns kvar efter omhämtning");
  assert.equal(stat(A, 7).pm, 1);
});

test("officiell +/- från tulospalvelu används och slår på +/-", async () => {
  const d = baseData();
  d.reports[1001][0].Plus = "5 11 7";
  d.reports[1001][1].Minus = "5 90";
  const A = makeApp(d);
  await A.tpSync(false);
  assert.equal(A.cur().pm, true);
  // Goal_1: +1 för 5, 11, 7. Goal_2 (insläppt): −1 för 5 och 90. Goal_3 saknar +/- i protokollet.
  assert.equal(stat(A, 5).pm, 0); assert.equal(stat(A, 7).pm, 1); assert.equal(stat(A, 11).pm, 1); assert.equal(stat(A, 90).pm, -1);
});

test("krock med egen match: välj tulospalvelus, behåll min eller olika matcher", async () => {
  for (const choice of ["tp", "mine", "both"]) {
    const A = makeApp(baseData());
    const s = A.cur();
    s.matches.push({ id: "own", date: "2026-10-10", opp: "Borta", players: [], type: "serie", res: [3, 0] });
    await A.tpSync(false);
    assert.equal(A.S.conflicts.length, 1, choice);
    assert.equal(matchByGid(A, 1001), undefined, "importeras inte förrän användaren valt");
    A.resolveConflict(0, choice);
    const own = A.cur().matches.find(m => m.id === "own");
    if (choice === "tp") { assert.equal(own, undefined); assert.ok(matchByGid(A, 1001)); }
    if (choice === "mine") { assert.ok(own); assert.equal(matchByGid(A, 1001), undefined); assert.ok(A.cur().tpSkip.includes(1001)); }
    if (choice === "both") { assert.ok(own); assert.ok(matchByGid(A, 1001)); }
    await A.tpSync(false);
    assert.equal(A.S.conflicts.length, 0, "ingen ny fråga vid nästa hämtning: " + choice);
  }
});

test("filter: matchtyp och senaste N matcher", async () => {
  const A = makeApp(baseData());
  await A.tpSync(false);
  const s = A.cur(), alfa = byNr(A, 5)[0].id;
  s.matches.push({ id: "tr1", date: "2026-10-20", opp: "Vänner", players: [alfa], type: "tr" });
  s.goals.push({ id: "gt", mid: "tr1", scorer: alfa, a1: null, a2: null, ice: [], ts: 1 });
  A.sync();
  // #5 har ett seriemål (Goal_1) och ett mål i träningsmatchen
  A.S.ftype = "all"; assert.equal(stat(A, 5, A.fMatches()).g, 2);
  A.S.ftype = "serie"; assert.equal(stat(A, 5, A.fMatches()).g, 1, "träningsmatch bortvald");
  A.S.ftype = "tr"; assert.equal(stat(A, 5, A.fMatches()).g, 1);
  A.S.ftype = "all"; A.S.fper = "1";
  assert.equal(A.fMatches()[0].id, "tr1", "senaste matchen");
  assert.match(A.filterLabel(), /senaste 1/);
  assert.match(A.viewLista(), /senaste 1 matcherna/, "filtret syns i rubriken");
  A.S.shot = true;
  assert.doesNotMatch(A.viewLista(), /id="f-type"|id="f-per"|id="topn"/, "filterväljarna syns inte i skärmbildsläget");
});

test("serie utan resultat: matcher från schemat, eget slutresultat", async () => {
  const d = { games: [game(2001, "05.10.2026", { DeniedResults: 1, GameStatus: 0 }), game(2002, "01.01.2099", { DeniedResults: 1, GameStatus: 0 })], reports: {}, rosters: {} };
  const A = makeApp(d);
  await A.tpSync(false);
  const s = A.cur();
  assert.equal(s.matches.length, 1, "bara spelade (passerade) matcher");
  const m = s.matches[0];
  assert.equal(m.nores, true); assert.equal(A.locked(m), false);
  assert.equal(A.score(m), null);
  m.res = [4, 2];
  assert.deepEqual([...A.score(m)], [4, 2]);
  assert.equal(s.tpNores, true);
  assert.ok(!A.calls.includes("gamereport/getgamereportdata"), "inga protokoll hämtas");
  await A.tpSync(false);
  assert.deepEqual([...A.score(s.matches[0])], [4, 2], "resultatet finns kvar efter ny hämtning");
});

test("dölj spelare och koppla loss match", async () => {
  const A = makeApp(baseData());
  await A.tpSync(false);
  const s = A.cur();
  byNr(A, 5)[0].hide = true; A.sync();
  A.S.hide = false;
  assert.equal(A.leaderboard().some(r => r.p.nr === 5), false);
  await A.tpSync(false);
  assert.equal(byNr(A, 5).length, 1, "dold spelare läggs inte till igen");
  const m = matchByGid(A, 1001);
  s.tpSkip.push(m.gid); m.xgid = m.gid; delete m.gid;
  assert.equal(A.locked(m), false);
  await A.tpSync(true);
  assert.equal(s.matches.filter(x => x.xgid === 1001 || x.gid === 1001).length, 1, "bortkopplad match hämtas inte igen");
});

test("CSV export och import behåller koppling, ID:n, typer, resultat och +/-", async () => {
  const A = makeApp(baseData());
  await A.tpSync(false);
  const s = A.cur(), alfa = byNr(A, 5)[0];
  s.pm = true; s.goals.find(x => x.k === "Goal_1").ice = [alfa.id];
  s.matches.push({ id: "tr1", date: "2026-10-20", opp: "Vänner", players: [alfa.id], type: "cup", res: [5, 3] });
  s.tpSkip.push(4242); byNr(A, 7)[0].hide = true; A.sync();
  const before = JSON.stringify(A.computeStats().map(r => [r.p.nr, r.gp, r.g, r.a, r.u, r.pm]));
  const imp = A.parseImport(A.toCSV());
  assert.equal(imp.warnings.length, 0, imp.warnings.join("\n"));
  const n = imp.seasons[0];
  assert.deepEqual({ ...n.tp }, { ...tpSeason });
  assert.deepEqual([...n.tpSkip], [4242]);
  assert.equal(n.players.find(p => p.nr === 5).tpid, 1);
  assert.equal(n.players.find(p => p.nr === 7).hide, true);
  assert.equal(n.goals.filter(x => x.k).length, s.goals.length);
  const cup = n.matches.find(m => m.type === "cup");
  assert.deepEqual([...cup.res], [5, 3]);
  A.D = { v: 2, last: null, changes: 0, seasons: imp.seasons }; A.setSid(n.id); A.sync();
  assert.equal(JSON.stringify(A.computeStats().map(r => [r.p.nr, r.gp, r.g, r.a, r.u, r.pm])), before);
  await A.tpSync(false);
  assert.equal(A.cur().matches.filter(m => m.gid).length, 2, "inga dubbletter efter import");
});

test("finska och svenska", async () => {
  const A = makeApp(baseData(), { lang: "fi-FI" });
  await A.tpSync(false);
  assert.equal(A.T("a", "b"), "b");
  assert.match(A.viewLista(), /Pistepörssi/);
  assert.match(A.viewMatches(), /Hae ottelut/);
  A.setLang("sv");
  assert.match(A.viewLista(), /Poängliga/);
});

test("serietabell uträknad från alla lags matcher (inget extra anrop)", async () => {
  const d = baseData();
  d.games.push(game(3001, "11.10.2026", { HomeTeam: 300, AwayTeam: OPP, HomeTeamAbbrv: "Tredje", AwayTeamAbbrv: "Borta", HomeGoals: 3, AwayGoals: 0 }));
  const A = makeApp(d);
  await A.tpSync(false);
  const s = A.cur();
  assert.equal(s.matches.length, 2, "bara egna matcher importeras");
  assert.equal(A.calls.filter(c => c === "helpers/getgames").length, 1);
  assert.ok(!A.calls.includes("serie/helpers/getstandings") && !A.calls.includes("helpers/getplayers"), "inga serieanrop när tulospalvelu inte visar dem");
  const t = s.tpTable;
  assert.equal(t.official, false);
  // Hem: V + O = 3 p, Tredje: V = 2 p, Borta: O + F + F = 1 p
  assert.deepEqual(plain(t.rows.map(r => [r.rank, r.name, r.gp, r.pts])), [[1, "Hem", 2, 3], [2, "Tredje", 1, 2], [3, "Borta", 3, 1]]);
  assert.deepEqual(plain(A.views().map(v => v[0])), ["lag", "tabell"], "ingen Hela serien-vy utan serielista");
  A.S.view = "tabell";
  const html = A.viewLista();
  assert.match(html, /class="row own"/, "eget lag markerat");
  assert.match(html, /Uträknad från resultaten/);
  A.S.shot = true;
  assert.doesNotMatch(A.viewLista(), /data-a="view"|data-a="shot"/, "inga väljare i skärmbildsläget");
});

test("serie med statistik: officiell tabell, hela serien och egna spelares placering", async () => {
  const d = baseData();
  d.sub = { playerStatistics: true, showStandings: true, winPoints: 3, serieId: 9 };
  d.standings = { StandingLines: ["1"], Teams: [
    { TeamAbbrv: "Borta", Games: 2, Wins: 1, OtWins: 1, Ties: 0, OtLooses: 0, Looses: 0, GoalsFor: 5, GoalsAgainst: 2, Points: 5, Ranking: 1 },
    { TeamAbbrv: "Hem", Games: 2, Wins: 1, OtWins: 0, Ties: 0, OtLooses: 1, Looses: 0, GoalsFor: 3, GoalsAgainst: 2, Points: 4, Ranking: 2 }] };
  const sp = (id, last, team, tid, gp, g, a) => ({ PlayerID: id, FirstName: "Testi", LastName: last, TeamAbbrv: team, TeamID: tid, PlayerGames: gp, PlayerGoals: g, PlayerAssists: a, PlayerPoints: g + a, PlayerPenaltyMin: 0, PlayerPlusMinus: 0 });
  d.players = [sp(501, "MUU", "Borta", OPP, 2, 4, 2), sp(1, "ALFA", "Hem", TID, 2, 1, 1), sp(502, "TOINEN", "Borta", OPP, 2, 0, 2), sp(4, "DELTA", "Hem", TID, 1, 1, 0)];
  const A = makeApp(d);
  await A.tpSync(false);
  const s = A.cur();
  assert.equal(s.tpTable.official, true);
  assert.deepEqual(plain(s.tpTable.rows.map(r => [r.rank, r.name, r.w, r.l, r.pts])), [[1, "Borta", 2, 0, 5], [2, "Hem", 1, 1, 4]]);
  assert.deepEqual(plain(A.views().map(v => v[0])), ["lag", "serie", "tabell"]);
  // Egen lista: #5 (tpid 1) har 2 p och är 2:a av 4 i serien
  assert.deepEqual({ ...A.seriesRankOf(1, "pts") }, { rank: 2, of: 4 });
  assert.match(A.viewLista(), /Serien 2\/4/);
  A.S.view = "serie";
  let html = A.viewLista();
  assert.equal((html.match(/class="row own"/g) || []).length, 2, "egna spelare markerade i serielistan");
  assert.match(html, /Hela serien/);
  A.S.sown = true;
  html = A.viewLista();
  assert.doesNotMatch(html, /Muu/, "Bara vårt lag döljer andra lag");
  assert.match(A.shareText(), /Hela serien/);
  A.S.shot = true;
  assert.doesNotMatch(A.viewLista(), /id="sown"|id="topn"|data-a="view"/);
});

test("avgörande straffslag (VL) räknas i resultatet men inte i spelarstatistiken", async () => {
  const d = baseData();
  d.games[1].HomeGoals = 2; // 1002 avgörs på straffar: 2–1
  d.reports[1002].push(goal("Goal_9", TID, 5, 3900, 2, 1, 7, { GoalType: "VL" }));
  const A = makeApp(d);
  await A.tpSync(false);
  assert.deepEqual([...A.score(matchByGid(A, 1002))], [2, 1]);
  assert.equal(stat(A, 7).g, 1, "#7 får bara sitt vanliga mål i 1001");
  const imp = A.parseImport(A.toCSV());
  assert.equal(imp.seasons[0].goals.filter(x => x.so).length, 1, "flaggan följer med i CSV");
});

test("mål i powerplay (YV) räknas inte i +/-", async () => {
  const d = baseData();
  d.reports[1001][0].Plus = "5 11 7"; d.reports[1001][0].GoalType = "YV";
  d.reports[1001][2].Plus = "7 4";
  const A = makeApp(d);
  await A.tpSync(false);
  assert.equal(stat(A, 5).pm, 0, "bara YV-mål för #5");
  assert.equal(stat(A, 7).pm, 1, "#7: YV-målet räknas inte, Goal_3 räknas");
  const imp = A.parseImport(A.toCSV());
  assert.equal(imp.seasons[0].goals.filter(x => x.pp).length, 1);
});
