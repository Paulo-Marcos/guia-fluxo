"""D-186: o refresh de 5 s do painel nao pode devolver a rolagem ao inicio.

Roda o JS da pagina no Node com um DOM minimo: elementos recem-criados nascem
com scrollLeft 0, como no navegador. Sem Node, o teste e pulado.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from conftest_paths import ensure_core_importable

ensure_core_importable()

from _dashboard_page import PAGE_HTML  # noqa: E402

DOM_STUB = r"""
class Node0 { constructor() { this.children = []; this.parent = null; } }
class Text0 extends Node0 { constructor(t) { super(); this.text = String(t); } get textContent() { return this.text; } }
class El extends Node0 {
  constructor(tag) { super(); this.tagName = tag; this.className = ""; this.dataset = {}; this.style = {};
    this.scrollLeft = 0; this.scrollTop = 0; this.hidden = false; this.attrs = {}; }
  setAttribute(k, v) { this.attrs[k] = v; }
  click() { if (this.onclick) this.onclick(); }
  append(...ns) { for (let n of ns) { if (!(n instanceof Node0)) n = new Text0(n); n.parent = this; this.children.push(n); } }
  replaceChildren(...ns) { this.children = []; this.append(...ns); }
  get firstChild() { return this.children[0] || null; }
  get textContent() { return this.children.map(c => c.textContent).join(""); }
  set textContent(v) { this.children = []; this.append(new Text0(v)); }
  querySelectorAll(sel) { const out = []; const walk = n => { for (const c of n.children) { if (c instanceof El) { if (matches(c, sel)) out.push(c); walk(c); } } }; walk(this); return out; }
  querySelector(sel) { return this.querySelectorAll(sel)[0] || null; }
}
function simple(n, part) {
  if (part.startsWith(".")) return n.className.split(/\s+/).includes(part.slice(1));
  const a = part.match(/^\[data-([a-z-]+)\]$/); if (a) return a[1].replace(/-(.)/g, (_, c) => c.toUpperCase()) in n.dataset;
  return n.tagName === part;
}
function matches(n, sel) {
  const parts = sel.trim().split(/\s+/); if (!simple(n, parts.pop())) return false;
  let p = n.parent; while (parts.length && p) { if (p instanceof El && simple(p, parts[parts.length - 1])) parts.pop(); p = p.parent; }
  return !parts.length;
}
const ids = {}; for (const id of ["projects", "main", "dot", "stamp", "version", "shade", "drawer"]) ids[id] = new El("div");
const root = new El("body"); root.append(ids.projects, ids.main, ids.drawer);
globalThis.document = { getElementById: id => ids[id], createElement: t => new El(t), createTextNode: t => new Text0(t),
  querySelectorAll: s => root.querySelectorAll(s), querySelector: s => root.querySelector(s), addEventListener() {} };
globalThis.window = { scrollX: 0, scrollY: 0, scrollTo(x, y) { this.scrollX = x; this.scrollY = y; } };
globalThis.localStorage = { getItem() { return null; }, setItem() {} };
globalThis.setInterval = () => 0;
let snapshot = null;
globalThis.fetch = async () => ({ ok: true, json: async () => JSON.parse(JSON.stringify(snapshot)) });
"""

PROBE = r"""
(async () => {
  snapshot = SNAPSHOT;
  await refresh();
  const board = () => document.querySelector(".board");
  const line = () => document.querySelector(".queue");
  board().scrollLeft = 400; line().scrollLeft = 120;
  await refresh();
  console.log(JSON.stringify({ board: board().scrollLeft, queue: line().scrollLeft }));
})();
"""


DETAIL_PROBE = r"""
(async () => {
  snapshot = SNAPSHOT;
  await refresh();
  select("C:\p");
  document.querySelector(".card").click();
  const drawer = document.getElementById("drawer");
  const opened = !drawer.hidden && drawer.textContent.includes("Por que existe") && drawer.textContent.includes("Sem plano registrado");
  drawer.scrollTop = 90;
  await refresh();
  console.log(JSON.stringify({ opened, still: !drawer.hidden, scroll: drawer.scrollTop,
    chip: document.querySelector(".card").textContent.includes("sem plano"),
    version: document.getElementById("version").textContent }));
})();
"""


def _snapshot() -> dict:
    detail = {"context": "Por que existe", "plan": [], "missingPlan": True, "files": [], "summary": [], "validations": [],
              "pending": [], "requests": [], "chat": None, "steps": [{"step": "Criada", "at": "2026-10-20"}]}
    cards = [{"id": f"D-{i}", "marker": "🐛", "title": "t", "status": "Em desenvolvimento", "updatedAt": None, "detail": detail}
             for i in range(3)]
    stages = [{"label": f"Etapa {i}", "cards": cards if i == 0 else []} for i in range(8)]
    item = {"id": "D-1", "marker": "🐛", "title": "t", "position": 1, "state": "queued", "audited": True, "approved": True}
    return {"guia": {"version": "9.9.9", "engine": "x"}, "projects": [{
        "name": "p", "path": "C:\\p", "mode": "pr", "active": 3, "current": None, "stages": stages,
        "doneTotal": 0, "recentDone": [],
        "queue": {"items": [item, dict(item, id="D-2", position=2)], "history": [], "executor": None, "head": item},
    }]}


@unittest.skipUnless(shutil.which("node"), "node ausente")
class DashboardScrollTest(unittest.TestCase):
    def test_refresh_keeps_horizontal_scroll_of_board_and_queue(self) -> None:
        script = re.search(r"<script>(.*?)</script>", PAGE_HTML, re.S).group(1)
        source = DOM_STUB + script + PROBE.replace("SNAPSHOT", json.dumps(_snapshot()))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "probe.js"
            path.write_text(source, encoding="utf-8")
            out = subprocess.run(["node", str(path)], capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertEqual(out.returncode, 0, out.stderr)
        got = json.loads(out.stdout.strip().splitlines()[-1])
        self.assertEqual(got, {"board": 400, "queue": 120})

    def test_card_opens_the_detail_and_it_survives_the_refresh(self) -> None:
        """D-192: o cartao abre o detalhe; o refresh de 5 s o mantem aberto e na mesma rolagem."""
        script = re.search(r"<script>(.*?)</script>", PAGE_HTML, re.S).group(1)
        source = DOM_STUB + script + DETAIL_PROBE.replace("SNAPSHOT", json.dumps(_snapshot()))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "probe.js"
            path.write_text(source, encoding="utf-8")
            out = subprocess.run(["node", str(path)], capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertEqual(out.returncode, 0, out.stderr)
        got = json.loads(out.stdout.strip().splitlines()[-1])
        self.assertEqual(got, {"opened": True, "still": True, "scroll": 90, "chip": True, "version": "v9.9.9"})


if __name__ == "__main__":
    unittest.main()
