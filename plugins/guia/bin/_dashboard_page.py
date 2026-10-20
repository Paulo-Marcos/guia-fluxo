"""Pagina do painel local (D-175): HTML, CSS e JS num arquivo so, sem CDN.

Fica num modulo Python (e nao num .html solto) porque o build copia
`core/src/*.py` para `plugins/guia/bin/` - assim a pagina viaja com o motor.
Todo texto vindo do estado entra por `textContent`, nunca por innerHTML.
O servidor troca `TOKEN_PLACEHOLDER` pelo token da sessao do painel (D-187),
que os botoes da fila mandam no cabecalho `X-Guia-Token`.
"""

from __future__ import annotations

TOKEN_PLACEHOLDER = "__GUIA_DASHBOARD_TOKEN__"

PAGE_HTML = r"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="guia-token" content="__GUIA_DASHBOARD_TOKEN__">
<title>Guia Fluxo · Painel</title>
<style>
:root {
  --bg: #f6f7f9; --panel: #ffffff; --ink: #1d2330; --muted: #677085; --line: #e2e5eb;
  --accent: #3b5bdb; --accent-soft: #e8edff; --ok: #2f9e44; --ok-soft: #e6f6ea;
  --warn: #c77700; --warn-soft: #fff4e0; --bad: #c92a2a; --bad-soft: #ffe8e8;
  --chip: #eef0f4; --shadow: 0 1px 2px rgba(20,25,40,.06), 0 2px 8px rgba(20,25,40,.04);
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #12151c; --panel: #1a1e27; --ink: #e6e9f0; --muted: #98a1b3; --line: #2a303c;
    --accent: #7c96ff; --accent-soft: #232b48; --ok: #63c27a; --ok-soft: #1c2f22;
    --warn: #f0a83a; --warn-soft: #34291a; --bad: #ff7b7b; --bad-soft: #3a1f22;
    --chip: #242a35; --shadow: none;
  }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink); font: 14px/1.45 "Segoe UI", system-ui, -apple-system, sans-serif; }
header { display: flex; align-items: center; gap: 12px; padding: 12px 20px; border-bottom: 1px solid var(--line); background: var(--panel); position: sticky; top: 0; z-index: 2; }
header h1 { font-size: 16px; margin: 0; font-weight: 600; }
header .sub { color: var(--muted); font-size: 12px; margin-left: auto; display: flex; align-items: center; gap: 8px; }
.dot { width: 8px; height: 8px; border-radius: 50%; background: var(--ok); display: inline-block; }
.dot.off { background: var(--bad); }
.layout { display: grid; grid-template-columns: 260px 1fr; min-height: calc(100vh - 49px); }
nav { border-right: 1px solid var(--line); padding: 12px; background: var(--panel); }
nav h2, main h2 { font-size: 12px; text-transform: uppercase; letter-spacing: .06em; color: var(--muted); margin: 6px 4px 8px; font-weight: 600; }
.proj { display: block; width: 100%; text-align: left; border: 1px solid transparent; background: none; color: inherit; padding: 8px 10px; border-radius: 8px; cursor: pointer; font: inherit; margin-bottom: 2px; }
.proj:hover { background: var(--chip); }
.proj.sel { background: var(--accent-soft); border-color: var(--accent); }
.proj .n { font-weight: 600; display: flex; justify-content: space-between; gap: 8px; }
.proj .m { color: var(--muted); font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.proj .err { color: var(--bad); font-size: 12px; }
.hint { color: var(--muted); font-size: 12px; padding: 8px 4px; }
code { background: var(--chip); padding: 1px 5px; border-radius: 4px; font-size: 12px; }
main { padding: 16px 20px 40px; min-width: 0; }
section { margin-bottom: 22px; }
.title-row { display: flex; align-items: baseline; gap: 10px; flex-wrap: wrap; margin-bottom: 12px; }
.title-row h3 { margin: 0; font-size: 20px; }
.chip { display: inline-flex; align-items: center; gap: 4px; background: var(--chip); color: var(--muted); border-radius: 999px; padding: 1px 8px; font-size: 11px; white-space: nowrap; }
.chip.ok { background: var(--ok-soft); color: var(--ok); }
.chip.warn { background: var(--warn-soft); color: var(--warn); }
.chip.bad { background: var(--bad-soft); color: var(--bad); }
.chip.acc { background: var(--accent-soft); color: var(--accent); }
.banner { padding: 10px 12px; border-radius: 8px; margin-bottom: 10px; background: var(--warn-soft); color: var(--warn); }
.act { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin: 0 4px 10px; }
.btn { font: inherit; font-size: 13px; padding: 5px 12px; border-radius: 6px; border: 1px solid var(--accent); background: var(--accent); color: #fff; cursor: pointer; }
.btn:disabled { opacity: .55; cursor: wait; }
.act .msg { font-size: 12px; color: var(--muted); }
.act .msg.bad { color: var(--bad); }
.queue { display: flex; gap: 10px; overflow-x: auto; padding-bottom: 6px; }
.qi { flex: 0 0 260px; background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 10px 12px; box-shadow: var(--shadow); }
.qi.head { border: 2px solid var(--accent); }
.qi .pos { font-size: 11px; color: var(--muted); display: flex; justify-content: space-between; }
.qi.head .pos b { color: var(--accent); }
.qi .t { font-weight: 600; margin: 4px 0; }
.qi .why { font-size: 12px; color: var(--muted); margin-top: 6px; }
.empty { color: var(--muted); background: var(--panel); border: 1px dashed var(--line); border-radius: 10px; padding: 12px; }
.board { display: grid; grid-auto-flow: column; grid-auto-columns: minmax(230px, 1fr); gap: 12px; overflow-x: auto; padding-bottom: 8px; }
.col { background: var(--chip); border-radius: 10px; padding: 8px; min-height: 80px; }
.col.zero { opacity: .55; }
.col h4 { margin: 2px 4px 8px; font-size: 12px; display: flex; justify-content: space-between; color: var(--muted); text-transform: uppercase; letter-spacing: .04em; }
.card { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 8px 10px; margin-bottom: 8px; box-shadow: var(--shadow); }
.card.cur { border-left: 3px solid var(--accent); }
.card .id { font-size: 12px; color: var(--muted); display: flex; justify-content: space-between; gap: 6px; }
.card .t { margin: 3px 0 6px; }
.card .meta { display: flex; flex-wrap: wrap; gap: 4px; }
.card .chat { font-size: 11px; color: var(--muted); margin-top: 6px; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
table { width: 100%; border-collapse: collapse; background: var(--panel); border-radius: 10px; overflow: hidden; border: 1px solid var(--line); }
th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--line); vertical-align: top; }
th { font-size: 11px; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); font-weight: 600; }
td.num { text-align: center; font-variant-numeric: tabular-nums; }
tr.click { cursor: pointer; }
tr.click:hover td { background: var(--chip); }
.two { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.list { background: var(--panel); border: 1px solid var(--line); border-radius: 10px; }
.list div { padding: 7px 12px; border-bottom: 1px solid var(--line); display: flex; gap: 8px; align-items: baseline; }
.list div:last-child { border-bottom: 0; }
.list .grow { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.card.click, .list .click { cursor: pointer; }
.card.click:hover { border-color: var(--accent); }
.card.click:focus-visible, .list .click:focus-visible { outline: 2px solid var(--accent); outline-offset: 1px; }
.list .click:hover { background: var(--chip); }
.shade { position: fixed; inset: 0; background: rgba(10,14,22,.35); z-index: 3; }
.drawer { position: fixed; top: 0; right: 0; bottom: 0; width: min(560px, 100vw); background: var(--panel); border-left: 1px solid var(--line); z-index: 4; overflow-y: auto; padding: 16px 20px 32px; box-shadow: -4px 0 20px rgba(10,14,22,.15); }
.drawer[hidden], .shade[hidden] { display: none; }
.drawer .top { display: flex; align-items: flex-start; gap: 10px; }
.drawer .top h3 { margin: 0; font-size: 17px; flex: 1; }
.drawer .x { border: 1px solid var(--line); background: var(--chip); color: var(--ink); border-radius: 6px; padding: 2px 9px; cursor: pointer; font: inherit; }
.drawer h5 { font-size: 11px; text-transform: uppercase; letter-spacing: .06em; color: var(--muted); margin: 16px 0 6px; }
.drawer p { margin: 0; white-space: pre-wrap; }
.drawer ol, .drawer ul { margin: 0; padding-left: 20px; }
.drawer li { margin-bottom: 3px; overflow-wrap: anywhere; }
.drawer .banner { margin-top: 12px; }
.drawer .none { color: var(--muted); font-style: italic; }
@media (max-width: 860px) {
  .layout { grid-template-columns: 1fr; }
  nav { border-right: 0; border-bottom: 1px solid var(--line); }
  .two { grid-template-columns: 1fr; }
  main { padding: 16px; }
}
</style>
</head>
<body>
<header>
  <h1>Guia Fluxo · Painel</h1>
  <span id="version" class="chip" title="versão do Guia que serve este painel"></span>
  <div class="sub"><span id="dot" class="dot"></span><span id="stamp">carregando…</span></div>
</header>
<div class="layout">
  <nav><h2>Projetos</h2><div id="projects"></div>
    <div class="hint">Cadastre mais com <code>guia dashboard --scan C:\DEV</code> ou <code>--add &lt;pasta&gt;</code>.</div>
  </nav>
  <main id="main"></main>
</div>
<div id="shade" class="shade" hidden></div>
<aside id="drawer" class="drawer" hidden aria-label="Detalhe da demanda"></aside>
<script>
"use strict";
const ALL = "__all__";
let data = { projects: [] };
let selected = null;
try { selected = localStorage.getItem("guia.dashboard.selected"); } catch (e) {}

function el(tag, cls, text) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text !== undefined && text !== null) n.textContent = String(text);
  return n;
}
function chip(text, tone) { return el("span", "chip" + (tone ? " " + tone : ""), text); }
function prLink(pr) {
  if (!pr || !pr.number) return null;
  if (pr.url && /^https:\/\//.test(pr.url)) { const a = el("a", null, "PR #" + pr.number); a.href = pr.url; a.target = "_blank"; a.rel = "noopener"; return a; }
  return chip("PR #" + pr.number);
}
function select(key) {
  selected = key;
  try { localStorage.setItem("guia.dashboard.selected", key); } catch (e) {}
  render();
}
function since(iso) {
  if (!iso) return "";
  const t = Date.parse(iso); if (isNaN(t)) return iso;
  const m = Math.round((Date.now() - t) / 60000);
  if (m < 1) return "agora"; if (m < 60) return m + " min";
  const h = Math.round(m / 60); if (h < 48) return h + " h";
  return Math.round(h / 24) + " d";
}

function renderNav() {
  const box = document.getElementById("projects");
  box.replaceChildren();
  const all = el("button", "proj" + (selected === ALL ? " sel" : ""));
  const n = el("div", "n"); n.append(el("span", null, "Todos os projetos"), chip(data.projects.length));
  all.append(n, el("div", "m", "visão geral e filas"));
  all.onclick = () => select(ALL);
  box.append(all);
  for (const p of data.projects) {
    const b = el("button", "proj" + (selected === p.path ? " sel" : ""));
    b.title = p.path;
    const row = el("div", "n"); row.append(el("span", null, p.name));
    if (!p.error) row.append(chip(p.active, p.active ? "acc" : ""));
    b.append(row);
    if (p.error) b.append(el("div", "err", p.error));
    else {
      const q = p.queue.items.length;
      const ex = p.queue.executor && p.queue.executor.alive ? " · executor ativo" : "";
      b.append(el("div", "m", (p.current ? "atual " + p.current + " · " : "") + (q ? q + " na fila" : "fila vazia") + ex));
    }
    b.onclick = () => select(p.path);
    box.append(b);
  }
}

function queueItem(it, isHead) {
  const box = el("div", "qi" + (isHead ? " head" : ""));
  const pos = el("div", "pos");
  pos.append(isHead ? el("b", null, "▶ NA PONTA") : el("span", null, "#" + it.position));
  if (it.next && !isHead) pos.firstChild.textContent += " · próximo a integrar";
  const tags = el("span");
  if (it.next && isHead) tags.append(chip("próximo a integrar", "ok"));
  if (it.priority === "hotfix") tags.append(chip("hotfix", "bad"));
  pos.append(tags);
  box.append(pos);
  const t = el("div", "t"); t.textContent = it.marker + " " + it.id + " · " + (it.title || ""); box.append(t);
  const meta = el("div", "meta");
  meta.style.display = "flex"; meta.style.gap = "4px"; meta.style.flexWrap = "wrap";
  if (it.pr) meta.append(chip("PR #" + it.pr));
  meta.append(chip(it.state || "?", it.state === "conflict" ? "bad" : it.state === "integrating" ? "acc" : ""));
  meta.append(chip(it.audited ? "auditado" : "sem auditoria", it.audited ? "ok" : "warn"));
  meta.append(chip(it.approved ? "aprovado" : "sem aprovação", it.approved ? "ok" : "warn"));
  box.append(meta);
  box.append(el("div", "why", it.ready ? "✓ pronto para integrar (queue run)" : "Espera: " + (it.waiting || "?")));
  if (it.enqueuedAt) box.append(el("div", "why", "na fila há " + since(it.enqueuedAt)));
  return box;
}

function executorLine(ex) {
  const box = el("div", "hint");
  box.style.margin = "0 4px 8px";
  if (ex && ex.alive) {
    box.append(chip("● executor ativo", "ok"), document.createTextNode(" pid " + ex.pid + " em " + ex.host + " · batimento há " + ex.heartbeatAgeSeconds + " s — basta enfileirar, ele integra."));
  } else if (ex) {
    box.append(chip("executor parado", "warn"), document.createTextNode(" último batimento há " + since(new Date(Date.now() - (ex.heartbeatAgeSeconds || 0) * 1000).toISOString()) + " (lease vencido)."));
  } else {
    box.append(chip("sem executor", ""), document.createTextNode(" ninguém integrando agora — a fila anda com guia queue run."));
  }
  return box;
}

// D-187: as duas acoes do painel. Clique do dono, com confirmacao; o servidor
// roda o motor no projeto. O ultimo retorno de cada projeto sobrevive ao refresh.
const TOKEN = (document.querySelector('meta[name="guia-token"]') || {}).content || "";
const actionNote = {};
let acting = false;
async function act(kind, p, question) {
  if (acting || !window.confirm(question)) return;
  acting = true;
  actionNote[p.path] = { text: "enviando…", bad: false };
  keepScroll(render);
  try {
    const r = await fetch("/api/action/" + kind, {
      method: "POST", cache: "no-store",
      headers: { "Content-Type": "application/json", "X-Guia-Token": TOKEN },
      body: JSON.stringify({ project: p.path }),
    });
    const body = await r.json().catch(() => ({ message: "HTTP " + r.status }));
    actionNote[p.path] = { text: body.message || ("HTTP " + r.status), bad: !r.ok };
  } catch (e) {
    actionNote[p.path] = { text: "sem conexão com o painel (" + e.message + ")", bad: true };
  }
  acting = false;
  refresh();
}
function actionRow(p) {
  const q = p.queue;
  const row = el("div", "act");
  if (q.paused || q.frozenReason) {
    const b = el("button", "btn", "Retomar fila");
    b.disabled = acting;
    b.onclick = () => act("queue-resume", p, q.frozenReason
      ? "A fila foi congelada (main vermelha). Confirme que a main voltou ao verde e retome a fila de " + p.name + "."
      : "Retomar a fila de " + p.name + "? (equivale a guia queue resume)");
    row.append(b);
  } else if (p.mode === "pr" && !(q.executor && q.executor.alive)) {
    const b = el("button", "btn", "Iniciar executor");
    b.disabled = acting;
    b.title = "guia queue run em segundo plano, neste projeto";
    b.onclick = () => act("queue-run", p, "Iniciar o executor da fila de " + p.name + "? Ele integra os itens aprovados e sai quando a fila esvazia (guia queue run).");
    row.append(b);
  }
  const note = actionNote[p.path];
  if (note) row.append(el("span", "msg" + (note.bad ? " bad" : ""), note.text));
  return row.firstChild ? row : null;
}

function renderQueue(p, host) {
  const s = el("section");
  s.append(el("h2", null, "Fila de integração"));
  const q = p.queue;
  s.append(executorLine(q.executor));
  if (q.paused) s.append(el("div", "banner", "Fila pausada" + (q.pausedReason ? ": " + q.pausedReason : "")));
  if (q.frozenReason) s.append(el("div", "banner", "Fila congelada: " + q.frozenReason));
  const actions = actionRow(p); if (actions) s.append(actions);
  if (!q.items.length) s.append(el("div", "empty", "Ninguém na fila agora."));
  else { const line = el("div", "queue"); line.dataset.scroll = "queue"; q.items.forEach((it, i) => line.append(queueItem(it, i === 0))); s.append(line); }
  host.append(s);
}

function card(c, current) {
  const box = el("div", "card click" + (c.id === current ? " cur" : ""));
  clickable(box, c.id);
  const id = el("div", "id"); id.append(el("span", null, c.marker + " " + c.id + (c.id === current ? " · atual" : "")), el("span", null, since(c.updatedAt)));
  box.append(id, el("div", "t", c.title));
  const meta = el("div", "meta");
  const link = prLink(c.pr); if (link) meta.append(link);
  if (c.audit) meta.append(chip("auditoria: " + c.audit, c.audit === "approved" ? "ok" : "warn"));
  if (c.autonomy) meta.append(chip(c.autonomy));
  if (c.parentId) meta.append(chip("épico " + c.parentId));
  if (c.blockedReason) meta.append(chip(c.blockedReason, "bad"));
  if (c.status === "Aguardando validacao" && c.pending && c.pending.length) meta.append(chip(c.pending[0], "warn"));
  if (c.detail && c.detail.missingPlan) meta.append(chip("sem plano", "warn"));
  box.append(meta);
  if (c.chat) box.append(el("div", "chat", "💬 " + c.chat));
  return box;
}

// D-192: o cartao abre o detalhe da demanda. Somente leitura, como o resto.
let opened = null;  // { path, id } da demanda aberta; sobrevive ao refresh de 5 s
function clickable(node, id) {
  node.tabIndex = 0;
  node.setAttribute("role", "button");
  node.onclick = () => openDetail(selected, id);
  node.onkeydown = e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); openDetail(selected, id); } };
}
function findCard(path, id) {
  const p = data.projects.find(x => x.path === path);
  if (!p || p.error) return null;
  for (const st of p.stages) { const c = st.cards.find(x => x.id === id); if (c) return c; }
  return p.recentDone.find(x => x.id === id) || null;
}
function openDetail(path, id) { opened = { path, id }; drawDetail(); }
function closeDetail() {
  opened = null;
  document.getElementById("drawer").hidden = true;
  document.getElementById("shade").hidden = true;
}
function listBlock(host, title, items, ordered, empty) {
  host.append(el("h5", null, title));
  if (!items || !items.length) { host.append(el("div", "none", empty || "—")); return; }
  const l = el(ordered ? "ol" : "ul");
  items.forEach(i => l.append(el("li", null, i)));
  host.append(l);
}
function drawDetail() {
  const box = document.getElementById("drawer");
  const c = opened && findCard(opened.path, opened.id);
  if (!c) { closeDetail(); return; }
  const keep = box.hidden ? 0 : box.scrollTop;
  const d = c.detail || {};
  box.replaceChildren();
  const top = el("div", "top");
  top.append(el("h3", null, c.marker + " " + c.id + " · " + c.title));
  const x = el("button", "x", "✕"); x.title = "Fechar (Esc)"; x.onclick = closeDetail; top.append(x);
  box.append(top);
  const meta = el("div", "meta"); meta.style.display = "flex"; meta.style.flexWrap = "wrap"; meta.style.gap = "4px"; meta.style.marginTop = "8px";
  meta.append(chip(c.status, "acc"), chip(c.kind || "?"));
  if (c.autonomy) meta.append(chip("autonomia " + c.autonomy));
  if (d.triage && d.triage.model) meta.append(chip("modelo " + d.triage.model + "/" + (d.triage.effort || "?")));
  const link = prLink(c.pr); if (link) meta.append(link);
  if (c.audit) meta.append(chip("auditoria: " + c.audit, c.audit === "approved" ? "ok" : "warn"));
  if (d.branch) meta.append(chip("⎇ " + d.branch));
  box.append(meta);
  if (d.missingPlan) box.append(el("div", "banner", "Sem plano registrado. Grave os passos com guia plan " + c.id + " --step \"...\" para saber o que a demanda vai fazer."));
  box.append(el("h5", null, "Contexto"));
  box.append(d.context ? el("p", null, d.context) : el("div", "none", "Sem contexto."));
  if (d.assessment && d.assessment.length) listBlock(box, "Avaliação", d.assessment, false);
  listBlock(box, "Plano", d.plan, true, "Sem plano.");
  listBlock(box, "Arquivos", d.files, false, "Nenhum arquivo ainda.");
  listBlock(box, "Resumo", d.summary, false);
  listBlock(box, "Validações", d.validations, false, "Nenhuma validação registrada.");
  listBlock(box, "Pendências", d.pending, false, "Nada pendente.");
  if (d.requests && d.requests.length) listBlock(box, "Pedido → Teste", d.requests.map(r => r.request + " → " + r.test), false);
  box.append(el("h5", null, "Chat"));
  box.append(d.chat ? el("p", null, "💬 " + d.chat.title + (d.chat.session ? "  (" + d.chat.session + ")" : "")) : el("div", "none", "Sem chat registrado."));
  if (d.dependsOn && d.dependsOn.length) listBlock(box, "Depende de", d.dependsOn, false);
  listBlock(box, "Etapas", (d.steps || []).map(s => s.at.slice(0, 16).replace("T", " ") + " · " + s.step), false);
  if (d.origin) { box.append(el("h5", null, "Origem")); box.append(el("p", null, d.origin)); }
  box.hidden = false;
  document.getElementById("shade").hidden = false;
  box.scrollTop = keep;
}
document.getElementById("shade").onclick = closeDetail;
document.addEventListener("keydown", e => { if (e.key === "Escape" && opened) closeDetail(); });

function renderProject(p) {
  const main = document.getElementById("main");
  main.replaceChildren();
  const head = el("div", "title-row");
  head.append(el("h3", null, p.name), chip("modo " + p.mode), el("span", "hint", p.path));
  main.append(head);
  if (p.error) { main.append(el("div", "banner", p.error)); return; }
  renderQueue(p, main);
  const s = el("section"); s.append(el("h2", null, "Demandas por etapa"));
  const board = el("div", "board"); board.dataset.scroll = "board";
  for (const st of p.stages) {
    const col = el("div", "col" + (st.cards.length ? "" : " zero"));
    const h = el("h4"); h.append(el("span", null, st.label), el("span", null, st.cards.length));
    col.append(h);
    st.cards.forEach(c => col.append(card(c, p.current)));
    board.append(col);
  }
  s.append(board); main.append(s);
  const two = el("div", "two");
  const done = el("section"); done.append(el("h2", null, "Concluídas recentes (" + p.doneTotal + " no total)"));
  const dl = el("div", "list");
  if (!p.recentDone.length) dl.append(el("div", "hint", "Nada concluído ainda."));
  p.recentDone.forEach(c => { const r = el("div", "click"); clickable(r, c.id); r.append(el("span", null, c.marker + " " + c.id), el("span", "grow", c.title), chip(c.status, c.status === "Cancelada" ? "" : "ok")); dl.append(r); });
  done.append(dl);
  const hist = el("section"); hist.append(el("h2", null, "Saídas recentes da fila"));
  const hl = el("div", "list");
  if (!p.queue.history.length) hl.append(el("div", "hint", "Sem histórico."));
  p.queue.history.forEach(h => { const r = el("div"); r.append(el("span", null, h.id), el("span", "grow", h.reason || (h.pr ? "PR #" + h.pr : "")), chip(h.state, h.state === "merged" ? "ok" : "warn"), el("span", "hint", since(h.closedAt))); r.title = h.reason || ""; hl.append(r); });
  hist.append(hl);
  two.append(done, hist); main.append(two);
}

function renderAll() {
  const main = document.getElementById("main");
  main.replaceChildren();
  const head = el("div", "title-row"); head.append(el("h3", null, "Todos os projetos")); main.append(head);
  if (!data.projects.length) { main.append(el("div", "empty", "Nenhum projeto cadastrado. Rode guia dashboard dentro de um projeto ou use --scan <pasta>.")); return; }
  const s = el("section"); s.append(el("h2", null, "Quem está na ponta de cada fila"));
  const heads = data.projects.filter(p => !p.error && p.queue.head);
  if (!heads.length) s.append(el("div", "empty", "Todas as filas estão vazias."));
  else { const line = el("div", "queue"); line.dataset.scroll = "heads"; heads.forEach(p => { const b = queueItem(p.queue.head, true); b.querySelector(".pos b").textContent = "▶ " + p.name + " · " + p.queue.items.length + " na fila"; line.append(b); }); s.append(line); }
  main.append(s);
  const t = el("section"); t.append(el("h2", null, "Demandas por etapa"));
  const table = el("table");
  const keys = data.projects.find(p => !p.error);
  const tr = el("tr"); tr.append(el("th", null, "Projeto"));
  if (keys) keys.stages.forEach(st => tr.append(el("th", null, st.label)));
  tr.append(el("th", null, "Fila"));
  table.append(tr);
  for (const p of data.projects) {
    const r = el("tr", "click"); r.onclick = () => select(p.path);
    r.append(el("td", null, p.name));
    if (p.error) { const td = el("td", null, p.error); td.colSpan = 99; r.append(td); }
    else { p.stages.forEach(st => r.append(el("td", "num", st.cards.length || "·"))); r.append(el("td", "num", p.queue.items.length || "·")); }
    table.append(r);
  }
  t.append(table); main.append(t);
}

function render() {
  if (selected !== ALL && !data.projects.some(p => p.path === selected)) selected = data.projects.length === 1 ? data.projects[0].path : ALL;
  renderNav();
  if (selected === ALL) renderAll(); else renderProject(data.projects.find(p => p.path === selected));
}

// D-186: o refresh redesenha tudo; sem isto a pagina e os quadros com
// rolagem horizontal voltariam ao inicio a cada 5 s.
function keepScroll(draw) {
  const page = [window.scrollX, window.scrollY];
  const inner = {};
  document.querySelectorAll("[data-scroll]").forEach(n => { inner[n.dataset.scroll] = [n.scrollLeft, n.scrollTop]; });
  draw();
  document.querySelectorAll("[data-scroll]").forEach(n => { const v = inner[n.dataset.scroll]; if (v) { n.scrollLeft = v[0]; n.scrollTop = v[1]; } });
  window.scrollTo(page[0], page[1]);
}

async function refresh() {
  try {
    const r = await fetch("/api/snapshot", { cache: "no-store" });
    if (!r.ok) throw new Error("HTTP " + r.status);
    data = await r.json();
    document.getElementById("dot").className = "dot";
    document.getElementById("stamp").textContent = "atualizado " + new Date().toLocaleTimeString("pt-BR") + " · a cada 5 s";
    keepScroll(render);
    const v = data.guia && data.guia.version;
    const vEl = document.getElementById("version");
    vEl.textContent = v ? "v" + v : "versão ?";
    if (data.guia && data.guia.engine) vEl.title = "versão do Guia que serve este painel · " + data.guia.engine;
    if (opened) drawDetail();
  } catch (e) {
    document.getElementById("dot").className = "dot off";
    document.getElementById("stamp").textContent = "sem conexão com o motor (" + e.message + ")";
  }
}
refresh();
setInterval(refresh, 5000);
</script>
</body>
</html>
"""

__all__ = ["PAGE_HTML"]
