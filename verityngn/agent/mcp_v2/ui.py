"""MCP Apps widgets (``ui://splitrisk/*``, MIME ``text/html;profile=mcp-app``).

Each widget is one self-contained HTML document. Widgets make no network
requests (all tool calls go through the host bridge), store nothing in the
browser, and carry the not-legal-advice and Allegation banners in their markup.
"""

from __future__ import annotations

from typing import Any

from verityngn.agent.mcp_v2.contracts import UI_MIME

APPS_PROTOCOL = "2026-01-26"

_CSS = """
:root{--teal:#0f766e;--amber:#b45309;--grey:#6b7280;--bg:#fff;--fg:#111827;--line:#e5e7eb}
@media (prefers-color-scheme:dark){:root{--bg:#111827;--fg:#f9fafb;--line:#374151}}
body{margin:0;font:13px/1.45 system-ui,-apple-system,Segoe UI,sans-serif;background:var(--bg);color:var(--fg)}
.banner{padding:6px 10px;font-size:12px;border-bottom:1px solid var(--line)}
.banner.legal{background:rgba(15,118,110,.08)}
.banner.allegation{background:repeating-linear-gradient(45deg,rgba(180,83,9,.12) 0 6px,transparent 6px 12px)}
main{padding:10px}
.card{border:1px solid var(--line);border-radius:8px;padding:10px;margin-bottom:8px}
.row{display:flex;gap:6px;align-items:center;flex-wrap:wrap}
.tag{font-size:11px;padding:1px 6px;border-radius:999px;border:1px solid var(--line)}
.high{border-color:#b91c1c;color:#b91c1c}.medium{border-color:var(--amber);color:var(--amber)}.low{color:var(--grey)}
.CONTESTED{color:var(--amber)}.SUPPORTED{color:var(--teal)}
.dot{width:10px;height:10px;border-radius:50%;display:inline-block;border:1px solid var(--grey)}
.dot.hit{background:var(--teal);border-color:var(--teal)}.dot.junior_obvious{background:var(--amber);border-color:var(--amber)}
.quote{border-left:3px solid var(--teal);padding:2px 8px;margin:6px 0}
.quote.allegation{border-left-style:dashed;border-left-color:var(--amber)}
table{border-collapse:collapse;width:100%}td,th{border:1px solid var(--line);padding:4px 6px;text-align:left;vertical-align:top}
td.cell{cursor:pointer;text-align:center}button{font:inherit;padding:2px 8px;margin-right:4px;cursor:pointer}
.muted{color:var(--grey)}
"""

_BRIDGE = """
const state = { input: {}, host: null };
const bridge = (() => {
  let nextId = 1; const pending = new Map(); const handlers = {};
  window.addEventListener('message', (ev) => {
    const m = ev.data;
    if (!m || m.jsonrpc !== '2.0') return;
    if (m.id !== undefined && pending.has(m.id) && (m.result !== undefined || m.error !== undefined)) {
      const p = pending.get(m.id); pending.delete(m.id);
      if (m.error) p.reject(m.error); else p.resolve(m.result);
      return;
    }
    if (m.method && handlers[m.method]) handlers[m.method](m.params || {});
  });
  function request(method, params) {
    const id = nextId++;
    window.parent.postMessage({ jsonrpc: '2.0', id, method, params }, '*');
    return new Promise((resolve, reject) => pending.set(id, { resolve, reject }));
  }
  function notify(method, params) { window.parent.postMessage({ jsonrpc: '2.0', method, params }, '*'); }
  function on(method, fn) { handlers[method] = fn; }
  return { request, notify, on };
})();
function el(tag, attrs, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (k === 'onclick') node.addEventListener('click', v); else if (v !== undefined && v !== null) node.setAttribute(k, v);
  }
  for (const c of children.flat()) { if (c === null || c === undefined) continue; node.append(c instanceof Node ? c : document.createTextNode(String(c))); }
  return node;
}
function openLink(url) { if (url) bridge.request('ui/open-link', { url }).catch(() => {}); }
function sourceLink(ev) {
  if (!ev || !ev.url) return '';
  if (ev.url.includes('youtube.com/')) return ev.url;
  return ev.quote ? ev.url + '#:~:text=' + encodeURIComponent(ev.quote.slice(0, 80)) : ev.url;
}
function callTool(name, args) {
  return bridge.request('tools/call', { name, arguments: args }).then((r) => r.structuredContent || {});
}
function showAllegationBanner(has) { document.getElementById('allegation-banner').hidden = !has; }
bridge.on('ui/notifications/tool-input', (p) => { state.input = p.arguments || {}; });
bridge.on('ui/notifications/tool-result', (r) => {
  const main = document.querySelector('main'); main.replaceChildren();
  const sc = r.structuredContent || {};
  if (r.isError) { main.append(el('div', { class: 'card' }, el('strong', {}, sc.code || 'Error'), ' ', sc.message || '', sc.alternative ? el('div', { class: 'muted' }, 'Instead: ' + sc.alternative) : null)); return; }
  render(sc, main);
});
bridge.request('ui/initialize', {
  appInfo: { name: '__NAME__', version: '4.0.0' },
  appCapabilities: { availableDisplayModes: ['inline'] },
  protocolVersion: '__APPS__',
}).then((res) => { state.host = res; bridge.notify('ui/notifications/initialized', {}); }).catch(() => {});
"""

_SEV_DOTS = """
const CLASSES = ['own', 'staff', 'docket', 'short', 'spoken'];
function coverageDots(cov) {
  return el('span', { class: 'row', title: 'Coverage: own, staff, docket, short, spoken' },
    CLASSES.map((c) => el('span', { class: 'dot ' + ((cov || {})[c] || { state: 'none' }).state, title: c })));
}
function card(rec) {
  const sev = (rec.severity || {}).level || '';
  const ev = (rec.evidence || []).map((e) => el('div', { class: 'quote' + (e.allegation ? ' allegation' : '') },
    e.allegation ? el('span', { class: 'tag medium' }, 'Allegation') : null, ' ', '\u201c' + (e.quote || '') + '\u201d',
    el('div', { class: 'muted' }, (e.source || '') + ' \u00b7 ' + (e.date || '') + ' ',
      el('button', { onclick: () => openLink(sourceLink(e)) }, 'Open source'),
      el('button', { onclick: () => navigator.clipboard && navigator.clipboard.writeText((e.source || '') + ', ' + (e.date || '') + ': \u201c' + (e.quote || '') + '\u201d ' + (e.url || '')) }, 'Copy citation'))));
  const details = el('details', {}, el('summary', {}, (rec.evidence || []).length + ' evidence'), ev);
  return el('div', { class: 'card' },
    el('div', { class: 'row' }, el('strong', { class: rec.verdict_or_action }, rec.verdict_or_action),
      el('span', { class: 'tag ' + sev }, sev ? 'severity ' + sev : ''), el('span', { class: 'tag' }, rec.claim_kind), coverageDots(rec.coverage)),
    el('div', {}, rec.claim_text),
    rec.target && rec.target.anchor_status && rec.target.anchor_status !== 'exact' ? el('div', { class: 'muted' }, 'Location ' + rec.target.anchor_status) : null,
    rec.illustrative_rewrite ? el('div', { class: 'muted' }, 'Illustrative rewrite for counsel to edit: ' + rec.illustrative_rewrite) : null,
    details);
}
"""

_WIDGETS: dict[str, dict[str, Any]] = {
    "assessment": {
        "title": "SplitRisk assessment",
        "description": "Risk cards with severity, coverage dots and anchored evidence.",
        "permissions": {"clipboardWrite": {}},
        "js": _SEV_DOTS + """
function render(sc, main) {
  const recs = sc.records || [];
  showAllegationBanner(recs.some((r) => r.allegation));
  if (sc.status === 'running') { main.append(el('div', { class: 'card' }, 'Running. Report ' + sc.report_id)); return; }
  if (!recs.length) main.append(el('div', { class: 'muted' }, 'No findings in this selection.'));
  recs.forEach((r) => main.append(card(r)));
}
""",
    },
    "coverage": {
        "title": "SplitRisk coverage",
        "description": "Five-column coverage grid (own, staff, docket, short, spoken) with severity per row.",
        "js": _SEV_DOTS + """
function render(sc, main) {
  const cov = sc.coverage || sc;
  if (sc.status === 'running') { main.append(el('div', { class: 'card' }, 'Running. Report ' + sc.report_id)); return; }
  const rows = cov.rows || [];
  showAllegationBanner(rows.some((r) => Object.values(r.cells || {}).some((c) => c.allegation)));
  const detail = el('div', { class: 'card', hidden: '' });
  const table = el('table', {}, el('tr', {}, el('th', {}, 'Risk'), el('th', {}, 'Severity'), CLASSES.map((c) => el('th', {}, c))));
  rows.forEach((row) => table.append(el('tr', {}, el('td', {}, row.heading), el('td', {}, row.severity.level),
    CLASSES.map((c) => { const cell = row.cells[c] || { state: 'none' };
      return el('td', { class: 'cell', onclick: () => showCell(cell, detail) }, cell.state === 'none' ? '\u2014' : (cell.date || '\u25cf')); }))));
  main.append(table, detail);
  const unc = cov.uncovered_spoken || [];
  if (unc.length) main.append(el('div', { class: 'card' }, unc.length + ' spoken claims not covered by the written risk factors.'));
}
function showCell(cell, detail) {
  detail.hidden = false; detail.replaceChildren(cell.state === 'none' ? 'No dated quote in this source class.' : '\u201c' + (cell.quote || '') + '\u201d');
  if (cell.record_id) callTool('get_record', { record_id: cell.record_id }).then((rec) => { detail.replaceChildren(card(rec)); }).catch(() => {});
}
""",
    },
    "results": {
        "title": "SplitRisk results",
        "description": "Dated result list with Allegation badges and provider attribution.",
        "js": """
function render(sc, main) {
  const items = sc.articles || sc.videos || [];
  const isVideo = !!sc.videos;
  showAllegationBanner(items.some((a) => a.allegation));
  if (sc.window) main.append(el('div', { class: 'muted' }, 'Window ' + sc.window.from + ' to ' + sc.window.to));
  const picked = new Set();
  items.forEach((a) => {
    const id = isVideo ? a.video_id : (a.url || a.uri);
    main.append(el('div', { class: 'card row' },
      el('input', { type: 'checkbox', onclick: (e) => e.target.checked ? picked.add(id) : picked.delete(id) }),
      a.allegation ? el('span', { class: 'tag medium' }, 'Allegation') : null,
      el('span', {}, (a.published_at || a.date || '').slice(0, 10)), el('strong', {}, a.headline || a.title || a.video_id),
      el('span', { class: 'muted' }, a.source || '')));
  });
  const verb = isVideo ? 'Analyze' : 'Assess';
  main.append(el('button', { onclick: () => picked.size && bridge.request('ui/message', { role: 'user', content: { type: 'text',
    text: isVideo ? 'Run analyze_video on: ' + [...picked].join(', ') : 'Register and assess these articles: ' + [...picked].join(' ') } }).catch(() => {}) }, verb + ' selected'));
  if (sc.attribution) main.append(el('div', { class: 'muted' }, sc.attribution));
}
""",
    },
    "video": {
        "title": "SplitRisk video",
        "description": "Task progress, then spoken claims with timestamps and an embedded player (video_id only).",
        "frame_domains": ["https://www.youtube-nocookie.com"],
        "js": _SEV_DOTS + """
function render(sc, main) {
  if (sc.status === 'running') { main.append(el('div', { class: 'card' }, 'Analyzing. Report ' + sc.report_id + '; results appear when the task completes.')); return; }
  const recs = sc.records || [];
  const vid = (state.input.video_id || ((recs[0] || {}).evidence || [{}])[0].source_id || '').split('+')[0];
  const player = el('iframe', { width: '100%', height: '220', title: 'Video', allow: 'encrypted-media', src: vid ? 'https://www.youtube-nocookie.com/embed/' + vid : 'about:blank' });
  main.append(player);
  recs.forEach((r) => {
    const t = parseInt((((r.evidence || [])[0] || {}).source_id || '').split('t=')[1] || '0', 10);
    const c = card(r);
    c.prepend(el('button', { onclick: () => { player.src = 'https://www.youtube-nocookie.com/embed/' + vid + '?start=' + t + '&autoplay=1'; } }, Math.floor(t / 60) + ':' + String(t % 60).padStart(2, '0')));
    main.append(c);
  });
}
""",
    },
    "workpaper": {
        "title": "SplitRisk workpaper",
        "description": "General counsel workpaper: accept, edit or reject; Judgment column only when switched on.",
        "js": """
function render(sc, main) {
  const recs = sc.records || [];
  const gc = sc.viewer_role === 'gc';
  const judgment = gc && sc.judgment_enabled;
  showAllegationBanner(recs.some((r) => r.allegation));
  main.append(el('div', { class: 'muted' }, 'Report ' + sc.report_id + ' \u00b7 ' + sc.status + (gc ? '' : ' \u00b7 read-only: decisions are for general counsel')));
  const head = el('tr', {}, el('th', {}, 'Finding'), el('th', {}, 'Action'), el('th', {}, 'Severity'), el('th', {}, 'Review'), judgment ? el('th', {}, 'Judgment (reviewer judgment, not computed)') : null, el('th', {}, ''));
  const table = el('table', {}, head);
  recs.forEach((r) => {
    const v = (r.review || {}).version;
    const act = (action, extra) => callTool('record_review_action', Object.assign({ record_id: r.claim_id, action, expected_version: v }, extra || {}))
      .then((rec) => { r.review = rec.review; r.judgment = rec.judgment; main.replaceChildren(); render(sc, main); }).catch(() => {});
    const buttons = gc ? [el('button', { onclick: () => act('accept') }, 'Accept'),
      el('button', { onclick: () => { const t = prompt('Illustrative rewrite for counsel to edit', r.illustrative_rewrite || ''); if (t !== null) act('edit', { illustrative_rewrite: t }); } }, 'Edit'),
      el('button', { onclick: () => act('reject') }, 'Reject')]
      : [el('button', { onclick: () => { const n = prompt('Note for general counsel'); if (n) act('propose', { note: n }); } }, 'Propose')];
    const jcell = judgment ? el('td', {}, el('select', { onchange: (e) => e.target.value ? act('set_judgment', { judgment_likelihood: e.target.value }) : act('clear_judgment') },
      ['', 'remote', 'possible', 'likely'].map((o) => { const opt = el('option', { value: o }, o || '\u2014'); if ((r.judgment || {}).likelihood === o) opt.selected = true; return opt; }))) : null;
    table.append(el('tr', {}, el('td', {}, r.claim_text), el('td', {}, r.verdict_or_action), el('td', {}, ((r.severity || {}).level || '') + ' (' + ((r.severity || {}).basis || '') + ')'),
      el('td', {}, (r.review || {}).state || ''), jcell, el('td', {}, buttons)));
  });
  main.append(table);
}
""",
    },
}

WIDGET_NAMES = list(_WIDGETS)


def uri(name: str) -> str:
    return f"ui://splitrisk/{name}"


def html(name: str) -> str:
    w = _WIDGETS[name]
    script = _BRIDGE.replace("__NAME__", f"splitrisk-{name}").replace("__APPS__", APPS_PROTOCOL) + w["js"]
    return (
        "<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
        f"<title>{w['title']}</title>\n<style>{_CSS}</style>\n</head>\n<body>\n"
        "<div class=\"banner legal\" id=\"legal-banner\">Not legal advice. Illustrative rewrites are for counsel to edit; "
        "no final disclosure is drafted. Verdicts are Supported, Contested or Unresolved and cover source-backed facts only; "
        "likelihood is never computed.</div>\n"
        "<div class=\"banner allegation\" id=\"allegation-banner\" hidden>Allegation: short-seller material is shown "
        "internally, with a publisher-conflict caveat. It is not a finding.</div>\n"
        "<main><div class=\"muted\">Waiting for results\u2026</div></main>\n"
        f"<script>{script}</script>\n</body>\n</html>\n"
    )


def resource_meta(name: str) -> dict[str, Any]:
    w = _WIDGETS[name]
    ui: dict[str, Any] = {"csp": {"connectDomains": [], "resourceDomains": []}, "prefersBorder": True}
    if w.get("frame_domains"):
        ui["csp"]["frameDomains"] = list(w["frame_domains"])
    if w.get("permissions"):
        ui["permissions"] = dict(w["permissions"])
    return {"ui": ui}


def resource_listing(name: str) -> dict[str, Any]:
    w = _WIDGETS[name]
    return {"uri": uri(name), "name": f"splitrisk_{name}", "title": w["title"], "description": w["description"], "mimeType": UI_MIME}


def read(name: str) -> dict[str, Any]:
    return {"uri": uri(name), "mimeType": UI_MIME, "text": html(name), "_meta": resource_meta(name)}
