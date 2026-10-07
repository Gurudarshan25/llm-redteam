import json
import os
from datetime import datetime


# ---------- 1. Read every results file (missing files are skipped) ----------
def read(path):
    if not os.path.exists(path):
        print(f"Note: {path} not found, that section will be empty")
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def clean_attacks(rows, suite):
    out = []
    for r in rows or []:
        answer = r.get("answer") or "\n\n--- next message ---\n\n".join(r.get("answers", []))
        out.append({
            "suite": r.get("suite", suite),
            "defense": r["defense"],
            "category": r["category"],
            "name": r["name"],
            "try": r["try"],
            "answer": answer,
            "leak_type": r["leak_type"],
        })
    return out


balanced = read("results_balanced.json") or {"attacks": [], "benign": []}

attacks = (
    clean_attacks(read("results_defenses.json"), "Basic")
    + clean_attacks(read("results_advanced.json"), "Advanced")
    + clean_attacks(balanced["attacks"], "Basic")
)

benign = [
    {"defense": r["defense"], "question": r["question"], "outcome": r["outcome"]}
    for r in (read("results_benign.json") or []) + balanced["benign"]
]

indirect = [
    {"level": r["level"], "type": r["type"], "name": r["name"], "try": r["try"],
     "outcome": r["outcome"], "success": r["success"], "answer": r["answer"]}
    for r in (read("results_indirect.json") or [])
]

# Judge: only the summary numbers are needed on the page
judge = None
judged_rows = [r for r in (read("results_judged.json") or []) if r.get("judge_leaked") is not None]
if judged_rows:
    levels = ["1. no defense", "2. hardened prompt", "3. full defense", "4. balanced defense"]
    judge = {
        "total": len(judged_rows),
        "both_leak": sum(1 for r in judged_rows if r["leak_type"] and r["judge_leaked"]),
        "both_safe": sum(1 for r in judged_rows if not r["leak_type"] and not r["judge_leaked"]),
        "only_detector": sum(1 for r in judged_rows if r["leak_type"] and not r["judge_leaked"]),
        "only_judge": sum(1 for r in judged_rows if not r["leak_type"] and r["judge_leaked"]),
        "levels": [],
    }
    for level in levels:
        rows = [r for r in judged_rows if r["defense"] == level]
        if rows:
            judge["levels"].append({
                "level": level,
                "detector": sum(1 for r in rows if r["leak_type"]) / len(rows) * 100,
                "judge": sum(1 for r in rows if r["judge_leaked"]) / len(rows) * 100,
            })

meta = {
    "target": "Bank assistant chatbot",
    "model": "llama3.2:3b",
    "judge_model": "qwen2.5:3b",
    "generated": datetime.now().strftime("%d %B %Y, %H:%M"),
}


# ---------- 2. The page design ----------
TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Red-teaming a bank chatbot</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans+Condensed:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
  :root {
    --ink: #0E1726;
    --surface: #141F35;
    --raise: #1A2742;
    --line: #26324D;
    --text: #E8ECF4;
    --muted: #97A3BA;
    --red: #FF5A5F;
    --amber: #F2B33D;
    --green: #3CCB8C;
    --accent: #8EA2FF;
    --sans: "IBM Plex Sans", "Segoe UI", Arial, sans-serif;
    --cond: "IBM Plex Sans Condensed", "Arial Narrow", "Segoe UI", sans-serif;
    --mono: "IBM Plex Mono", Consolas, "Courier New", monospace;
  }
  * { box-sizing: border-box; }
  html { scroll-behavior: smooth; scroll-padding-top: 70px; }
  body { margin: 0; background: var(--ink); color: var(--text); font-family: var(--sans); font-size: 15px; line-height: 1.55; }
  a { color: var(--accent); }
  :focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; border-radius: 4px; }

  /* top navigation */
  nav { position: sticky; top: 0; z-index: 10; background: rgba(14, 23, 38, .92); backdrop-filter: blur(8px); border-bottom: 1px solid var(--line); }
  nav .in { max-width: 1160px; margin: 0 auto; padding: 0 24px; display: flex; gap: 4px; overflow-x: auto; }
  nav a { color: var(--muted); text-decoration: none; padding: 14px 10px; white-space: nowrap; font-size: 14px; border-bottom: 2px solid transparent; }
  nav a:hover { color: var(--text); border-bottom-color: var(--accent); }

  main { max-width: 1160px; margin: 0 auto; padding: 0 24px 80px; }

  /* masthead */
  .mast { padding: 56px 0 40px; border-bottom: 1px solid var(--line); }
  .mast h1 { font-family: var(--cond); font-weight: 700; font-size: clamp(38px, 6vw, 64px); line-height: 1.02; letter-spacing: -.01em; margin: 0 0 18px; max-width: 14ch; }
  .lede { font-size: 18px; color: var(--muted); max-width: 62ch; margin: 0 0 28px; }
  .lede strong { color: var(--text); font-weight: 600; }
  .facts { display: flex; flex-wrap: wrap; gap: 12px 40px; margin: 0; }
  .facts div { min-width: 120px; }
  .facts dt { color: var(--muted); font-size: 13px; }
  .facts dd { margin: 2px 0 0; font-weight: 500; }

  section { padding: 48px 0 8px; }
  h2 { font-family: var(--cond); font-weight: 600; font-size: 30px; line-height: 1.15; margin: 0 0 6px; }
  .note { color: var(--muted); margin: 0 0 22px; max-width: 70ch; }
  h3 { font-size: 16px; margin: 0 0 4px; font-weight: 600; }

  /* the ladder: the one memorable element */
  .ladder { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(4, 1fr); gap: 0; border: 1px solid var(--line); border-radius: 12px; overflow: hidden; }
  .ladder li { padding: 22px 20px 20px; background: var(--surface); border-right: 1px solid var(--line); display: flex; flex-direction: column; }
  .ladder li:last-child { border-right: 0; }
  .ladder li.best { background: linear-gradient(180deg, rgba(60, 203, 140, .10), var(--surface) 70%); box-shadow: inset 0 3px 0 var(--green); }
  .ladder .lvl { font-family: var(--cond); font-size: 15px; color: var(--muted); }
  .ladder h3 { font-family: var(--cond); font-size: 22px; font-weight: 600; margin: 2px 0 6px; }
  .ladder .desc { color: var(--muted); font-size: 13.5px; margin: 0 0 18px; min-height: 42px; }
  .meter { margin-bottom: 14px; }
  .meter .row { display: flex; justify-content: space-between; align-items: baseline; font-size: 13px; color: var(--muted); }
  .meter .val { font-family: var(--cond); font-size: 26px; font-weight: 700; line-height: 1; }
  .meter .track { height: 8px; background: var(--raise); border-radius: 4px; margin-top: 6px; overflow: hidden; }
  .meter .fill { height: 100%; border-radius: 4px; width: 0; transition: width .9s cubic-bezier(.2, .7, .2, 1); }
  .verdict { margin-top: auto; padding-top: 8px; font-weight: 600; font-size: 14px; }
  .verdict::before { content: ""; display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: currentColor; margin-right: 8px; vertical-align: 1px; }
  .headline { margin: 26px 0 0; font-size: 17px; color: var(--muted); }
  .headline b { color: var(--text); }

  /* panels, charts, tables */
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 16px; margin-bottom: 16px; }
  .panel { background: var(--surface); border: 1px solid var(--line); border-radius: 10px; padding: 20px; }
  .panel .note { margin-bottom: 14px; font-size: 13.5px; }
  .chart { position: relative; height: 280px; }
  .chart.tall { height: 360px; }
  .scroll { overflow-x: auto; }
  table { width: 100%; border-collapse: collapse; font-size: 14px; }
  th { text-align: left; color: var(--muted); font-weight: 500; font-size: 13px; padding: 10px 12px; border-bottom: 1px solid var(--line); }
  td { padding: 10px 12px; border-bottom: 1px solid var(--line); vertical-align: top; }
  tr:last-child td { border-bottom: 0; }
  .num { text-align: center; }
  .big td.num { font-family: var(--cond); font-size: 20px; font-weight: 700; vertical-align: middle; }
  .big td { vertical-align: middle; }
  tr.best td { background: rgba(60, 203, 140, .07); }
  .cell { text-align: center; font-weight: 600; border-radius: 6px; white-space: nowrap; }
  .grid-gap td { border-bottom: 0; padding: 3px; }
  .grid-gap td:first-child { padding-right: 14px; }
  .suite { font-size: 12px; color: var(--muted); margin-left: 6px; }
  details { margin-top: 16px; }
  summary { cursor: pointer; color: var(--accent); font-weight: 500; padding: 6px 0; }
  details[open] summary { margin-bottom: 12px; }

  .flow { display: flex; gap: 0; flex-wrap: wrap; border: 1px solid var(--line); border-radius: 10px; overflow: hidden; }
  .flow .step { flex: 1 1 140px; padding: 16px; background: var(--surface); border-right: 1px solid var(--line); }
  .flow .step:last-child { border-right: 0; }
  .flow .step.guard { background: var(--raise); }
  .flow .t { font-weight: 600; }
  .flow .s { color: var(--muted); font-size: 13px; }
  .flow .n { font-family: var(--cond); font-size: 24px; font-weight: 700; margin-top: 6px; }

  .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 16px; margin-bottom: 16px; }
  .stat .v { font-family: var(--cond); font-size: 34px; font-weight: 700; line-height: 1.1; }
  .stat .l { color: var(--muted); font-size: 13.5px; }

  .finding { border-left: 3px solid var(--red); background: var(--surface); border-radius: 0 8px 8px 0; padding: 14px 16px; margin-bottom: 12px; }
  .finding .ans { font-family: var(--mono); font-size: 12.5px; color: var(--muted); white-space: pre-wrap; margin-top: 8px; }
  .lessons { padding-left: 20px; max-width: 80ch; }
  .lessons li { margin-bottom: 8px; }

  .tools { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px; }
  .tools select, .tools input { background: var(--raise); border: 1px solid var(--line); color: var(--text); padding: 8px 12px; border-radius: 8px; font: inherit; font-size: 14px; }
  .tools input { flex: 1; min-width: 200px; }
  .pill { display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; white-space: nowrap; }
  .answer { font-family: var(--mono); font-size: 12px; color: var(--muted); white-space: pre-wrap; max-width: 460px; max-height: 58px; overflow: hidden; cursor: pointer; }
  .answer.open { max-height: none; }
  .count { color: var(--muted); font-size: 13px; margin: 0 0 8px; }

  footer { border-top: 1px solid var(--line); margin-top: 56px; padding-top: 20px; color: var(--muted); font-size: 13px; }

  @media (max-width: 900px) {
    .ladder { grid-template-columns: repeat(2, 1fr); }
    .ladder li:nth-child(2) { border-right: 0; }
    .ladder li:nth-child(-n+2) { border-bottom: 1px solid var(--line); }
  }
  @media (max-width: 560px) {
    .ladder { grid-template-columns: 1fr; }
    .ladder li { border-right: 0; border-bottom: 1px solid var(--line); }
    .grid { grid-template-columns: 1fr; }
  }
  @media (prefers-reduced-motion: reduce) {
    html { scroll-behavior: auto; }
    .meter .fill { transition: none; }
  }
</style>
</head>
<body>

<nav aria-label="Sections"><div class="in">
  <a href="#overview">Overview</a>
  <a href="#scorecard">Scorecard</a>
  <a href="#direct">Direct attacks</a>
  <a href="#customers">Normal customers</a>
  <a href="#indirect">Indirect injection</a>
  <a href="#judge">Judge check</a>
  <a href="#evidence">Evidence</a>
  <a href="#attempts">All attempts</a>
</div></nav>

<main>
  <header class="mast">
    <h1>Red-teaming a bank chatbot</h1>
    <p class="lede" id="lede"></p>
    <dl class="facts" id="facts"></dl>
  </header>

  <section id="overview">
    <h2>How the defenses compare</h2>
    <p class="note">Each level changes or adds a layer of protection. A good defense keeps both bars short: few attackers get through, and few real customers get blocked. Attack numbers show the worse of the basic and advanced attack sets.</p>
    <ol class="ladder" id="ladder"></ol>
    <p class="headline" id="headline"></p>
  </section>

  <section id="scorecard">
    <h2>Scorecard</h2>
    <p class="note">Attack success rate for basic and advanced attacks, and the share of normal customer questions that were wrongly blocked. Lower is better everywhere.</p>
    <div class="panel scroll"><table class="big" id="score"></table></div>
  </section>

  <section id="direct">
    <h2>Direct attacks</h2>
    <p class="note">The attacker types the trick straight into the chat. 14 basic attacks in 8 categories, and 10 advanced attacks including multi-turn conversations, encoding and filter evasion.</p>
    <div class="grid">
      <div class="panel"><h3>Basic vs advanced attacks</h3><p class="note">Attack success rate per defense level</p><div class="chart"><canvas id="levelChart" aria-label="Attack success rate per defense level"></canvas></div></div>
      <div class="panel"><h3>What works on an unprotected bot</h3><p class="note">Success rate by attack category, no defense</p><div class="chart"><canvas id="catChart" aria-label="Success rate by category"></canvas></div></div>
    </div>
    <div class="grid">
      <div class="panel"><h3>Advanced attacks vs the strict prompt</h3><p class="note">Which smart attacks broke the prompt-only defense</p><div class="chart tall"><canvas id="advChart" aria-label="Advanced attacks against the hardened prompt"></canvas></div></div>
      <div class="panel"><h3>How the secret leaked</h3><p class="note">Every successful leak, by the form it took</p><div class="chart tall"><canvas id="typeChart" aria-label="Leak types"></canvas></div></div>
    </div>
    <div class="panel">
      <h3>The balanced defense, layer by layer</h3>
      <p class="note">Where each attack attempt against the final defense was stopped</p>
      <div class="flow" id="flow"></div>
    </div>
    <details>
      <summary>Show every attack against every defense level</summary>
      <div class="panel scroll"><table class="grid-gap" id="matrix"></table></div>
    </details>
  </section>

  <section id="customers">
    <h2>Normal customers</h2>
    <p class="note">16 innocent questions, 9 of them using words like "code", "translate" or "secret". This measures how often security gets in the way of real users.</p>
    <div class="grid">
      <div class="panel"><h3>Why customers were blocked</h3><p class="note">Number of questions wrongly blocked, by cause</p><div class="chart"><canvas id="fpChart" aria-label="False positives by cause"></canvas></div></div>
      <div class="panel scroll"><h3>Every question, every level</h3><p class="note">Green means the customer was helped. Hover a red cell to see why it was blocked.</p><table class="grid-gap" id="benignMatrix"></table></div>
    </div>
  </section>

  <section id="indirect">
    <h2>Indirect prompt injection</h2>
    <p class="note">Here the attacker never talks to the bot. The instructions are hidden inside an email, invoice or letter that an employee asks the bot to summarize or translate. Goals: leak the secret, pass on a fake IBAN, or push a phishing link.</p>
    <div class="grid">
      <div class="panel"><h3>Injection success vs blocked documents</h3><p class="note">Lower is better for both</p><div class="chart"><canvas id="indChart" aria-label="Indirect injection results"></canvas></div></div>
      <div class="panel scroll"><h3>Every document, every level</h3><p class="note">Out of the number of tries per document</p><table class="grid-gap" id="indMatrix"></table></div>
    </div>
  </section>

  <section id="judge">
    <h2>Judge check</h2>
    <p class="note" id="judgeNote"></p>
    <div class="stats" id="judgeStats"></div>
    <div class="panel scroll"><table id="judgeTable"></table></div>
  </section>

  <section id="evidence">
    <h2>What I learned</h2>
    <ul class="lessons" id="lessons"></ul>
    <h3 style="margin-top:28px">Evidence from the logs</h3>
    <p class="note">Real answers where the secret leaked, starting with the strongest defense that was broken</p>
    <div id="evidenceList"></div>
  </section>

  <section id="attempts">
    <h2>All attack attempts</h2>
    <p class="note">Every direct attack attempt with the model's full answer. Click an answer to expand it.</p>
    <div class="tools">
      <select id="fSuite" aria-label="Filter by suite"><option value="">All attacks</option><option value="Basic">Basic</option><option value="Advanced">Advanced</option></select>
      <select id="fDef" aria-label="Filter by defense level"></select>
      <select id="fRes" aria-label="Filter by result">
        <option value="">All results</option>
        <option value="leaked">Leaked</option>
        <option value="filter">Blocked by a filter</option>
        <option value="safe">Refused by the model</option>
      </select>
      <input id="search" type="search" placeholder="Search attacks, categories or answers" aria-label="Search">
    </div>
    <p class="count" id="count"></p>
    <div class="panel scroll">
      <table>
        <thead><tr><th>Attack</th><th>Defense</th><th>Try</th><th>Result</th><th>Model answer</th></tr></thead>
        <tbody id="rows"></tbody>
      </table>
    </div>
  </section>

  <footer>
    Mapped to the OWASP Top 10 for LLM Applications: LLM01 Prompt Injection and LLM07 System Prompt Leakage.
    Generated by make_dashboard.py from the raw results files.
  </footer>
</main>

<script>
(() => {
  const attacks = __ATTACKS__;
  const benign = __BENIGN__;
  const indirect = __INDIRECT__;
  const judge = __JUDGE__;
  const meta = __META__;

  const LEVELS = ["1. no defense", "2. hardened prompt", "3. full defense", "4. balanced defense"];
  const NAME = {
    "1. no defense": "No defense",
    "2. hardened prompt": "Strict prompt",
    "3. full defense": "Keyword filter",
    "4. balanced defense": "Balanced defense",
  };
  const DESC = {
    "1. no defense": "One line in the system prompt: never reveal the code.",
    "2. hardened prompt": "Five strict security rules in the system prompt.",
    "3. full defense": "Strict prompt plus a keyword input filter and an output filter.",
    "4. balanced defense": "Helpful prompt, pattern-based input filter, stronger output filter.",
  };
  const BEST = "4. balanced defense";
  const IND_LEVELS = ["1. no defense", "2. balanced defense", "3. balanced + spotlighting"];
  const IND_NAME = {
    "1. no defense": "No defense",
    "2. balanced defense": "Balanced defense",
    "3. balanced + spotlighting": "Balanced + spotlighting",
  };
  const C = { red: "#FF5A5F", amber: "#F2B33D", green: "#3CCB8C", accent: "#8EA2FF", muted: "#97A3BA", faint: "#4A5875" };

  // ---------- helpers ----------
  const $ = id => document.getElementById(id);
  function el(tag, text, cls) {
    const e = document.createElement(tag);
    if (text !== undefined && text !== null) e.textContent = text;
    if (cls) e.className = cls;
    return e;
  }
  function rate(part, total) { return total ? part / total * 100 : null; }
  function pct(v) { return v === null || v === undefined ? "–" : Math.round(v) + "%"; }
  function stats(rows) {
    const leaks = rows.filter(r => r.leak_type).length;
    return { tries: rows.length, leaks, rate: rate(leaks, rows.length) };
  }
  function pick(suite, level) {
    return attacks.filter(r => (!suite || r.suite === suite) && (!level || r.defense === level));
  }
  function fp(level) {
    const rows = benign.filter(r => r.defense === level);
    const blocked = rows.filter(r => r.outcome !== "answered").length;
    return { tries: rows.length, blocked, rate: rate(blocked, rows.length) };
  }
  function color(v) {
    if (v === null || v === undefined) return C.faint;
    if (v >= 50) return C.red;
    if (v > 0) return C.amber;
    return C.green;
  }
  function verdict(asr, fpr) {
    if (asr !== null && asr >= 20 && fpr !== null && fpr >= 20) return ["Insecure and too strict", C.red];
    if (asr !== null && asr >= 20) return ["Insecure", C.red];
    if (fpr !== null && fpr >= 20) return ["Too strict to use", C.amber];
    if (asr !== null && asr > 5) return ["Needs work", C.amber];
    return ["Secure and usable", C.green];
  }
  function outcome(r) {
    if (r.leak_type) return "leaked";
    if (r.answer.includes("[BLOCKED")) return "filter";
    return "safe";
  }
  function worst(level) {
    const rates = ["Basic", "Advanced"].map(su => stats(pick(su, level)).rate).filter(v => v !== null);
    return rates.length ? Math.max(...rates) : null;
  }
  function groupRates(rows, key) {
    const g = {};
    rows.forEach(r => { (g[r[key]] = g[r[key]] || []).push(r); });
    return Object.entries(g).map(([k, v]) => ({ key: k, ...stats(v) })).sort((a, b) => b.rate - a.rate);
  }
  function tint(v, good) {
    if (v === null) return "transparent";
    if (good) return v === 0 ? "rgba(60,203,140,.16)" : `rgba(255,90,95,${0.18 + v / 100 * 0.55})`;
    return v === 0 ? "rgba(60,203,140,.16)" : `rgba(242,179,61,${0.18 + v / 100 * 0.5})`;
  }

  const baseline = stats(pick("Basic", "1. no defense"));
  const bestAll = stats(pick(null, BEST));
  const bestFp = fp(BEST);
  const docCount = new Set(indirect.filter(r => r.type === "attack").map(r => r.name)).size;
  const attackCount = new Set(attacks.map(r => r.suite + r.name)).size;

  // ---------- masthead ----------
  const lede = $("lede");
  lede.append(
    "I attacked a ", el("strong", meta.model), " bank assistant with ", el("strong", attackCount + " prompt-injection attacks"),
    docCount ? " and " : "", docCount ? el("strong", docCount + " poisoned documents") : "",
    ", then built defenses until it stopped leaking its secret without getting in the way of real customers."
  );
  [["Target", meta.target], ["Target model", meta.model], ["Judge model", meta.judge_model], ["Generated", meta.generated]].forEach(([k, v]) => {
    const d = el("div");
    d.append(el("dt", k), el("dd", v));
    $("facts").appendChild(d);
  });

  // ---------- ladder ----------
  const fills = [];
  LEVELS.forEach((l, i) => {
    const s = { rate: worst(l) };
    const f = fp(l);
    const li = el("li", null, l === BEST ? "best" : "");
    li.append(el("span", "Level " + (i + 1), "lvl"), el("h3", NAME[l]), el("p", DESC[l], "desc"));
    [["Attacks that got through", s.rate], ["Customers wrongly blocked", f.rate]].forEach(([label, v]) => {
      const m = el("div", null, "meter");
      const row = el("div", null, "row");
      const val = el("span", pct(v), "val");
      val.style.color = color(v);
      row.append(el("span", label), val);
      const track = el("div", null, "track");
      const fill = el("div", null, "fill");
      fill.style.background = color(v);
      track.appendChild(fill);
      fills.push([fill, v === null ? 0 : Math.max(v, v > 0 ? 3 : 0)]);
      m.append(row, track);
      li.appendChild(m);
    });
    const [vt, vc] = verdict(s.rate, f.rate);
    const v = el("div", vt, "verdict");
    v.style.color = vc;
    li.appendChild(v);
    $("ladder").appendChild(li);
  });
  requestAnimationFrame(() => setTimeout(() => fills.forEach(([f, w]) => { f.style.width = w + "%"; }), 120));

  const hl = $("headline");
  hl.append("Attack success went from ", el("b", pct(baseline.rate)), " with no defense to ", el("b", pct(bestAll.rate)),
    " with the balanced defense, while ", el("b", pct(bestFp.rate)), " of normal customers were blocked.");

  // ---------- scorecard ----------
  const score = $("score");
  const head = el("tr");
  [["Defense level", ""], ["Basic attacks", "num"], ["Advanced attacks", "num"], ["Customers blocked", "num"], ["Verdict", ""]]
    .forEach(([h, c]) => head.appendChild(el("th", h, c)));
  score.appendChild(head);
  LEVELS.forEach(l => {
    const tr = el("tr", null, l === BEST ? "best" : "");
    tr.appendChild(el("td", NAME[l]));
    [stats(pick("Basic", l)).rate, stats(pick("Advanced", l)).rate, fp(l).rate].forEach(v => {
      const td = el("td", pct(v), "num");
      td.style.color = color(v);
      tr.appendChild(td);
    });
    const [vt, vc] = verdict(worst(l), fp(l).rate);
    const td = el("td");
    const p = el("span", vt, "pill");
    p.style.color = vc;
    p.style.background = vc + "22";
    td.appendChild(p);
    tr.appendChild(td);
    score.appendChild(tr);
  });

  // ---------- pipeline ----------
  const bestRows = pick(null, BEST);
  const inBlocked = bestRows.filter(r => r.answer.includes("[BLOCKED by input filter]")).length;
  const outBlocked = bestRows.filter(r => r.answer.includes("[BLOCKED by output filter]")).length;
  const refused = bestRows.filter(r => outcome(r) === "safe").length;
  [
    ["Attack attempts", "sent to the bot", bestRows.length, false],
    ["Input filter", "blocked before the model", inBlocked, true],
    ["System prompt", "refused by the model", refused, true],
    ["Output filter", "blocked before the user", outBlocked, true],
    ["Leaks", "reached the user", bestAll.leaks, false],
  ].forEach(([t, s, n, guard]) => {
    const box = el("div", null, "step" + (guard ? " guard" : ""));
    const num = el("div", String(n), "n");
    if (t === "Leaks") num.style.color = n ? C.red : C.green;
    box.append(el("div", t, "t"), el("div", s, "s"), num);
    $("flow").appendChild(box);
  });

  // ---------- charts ----------
  if (window.Chart) {
    Chart.defaults.color = C.muted;
    Chart.defaults.font.family = '"IBM Plex Sans", "Segoe UI", Arial, sans-serif';
    Chart.defaults.borderColor = "#26324D";
    const pctAxis = { min: 0, max: 100, ticks: { callback: v => v + "%" } };
    const legend = { position: "bottom", labels: { boxWidth: 12, boxHeight: 12 } };
    const tip = { callbacks: { label: c => `${c.dataset.label ? c.dataset.label + ": " : ""}${Math.round(c.raw)}%` } };
    const labels = LEVELS.map(l => NAME[l]);

    new Chart($("levelChart"), {
      type: "bar",
      data: {
        labels,
        datasets: [
          { label: "Basic attacks", data: LEVELS.map(l => stats(pick("Basic", l)).rate), backgroundColor: C.accent, borderRadius: 4 },
          { label: "Advanced attacks", data: LEVELS.map(l => stats(pick("Advanced", l)).rate), backgroundColor: C.red, borderRadius: 4 },
        ],
      },
      options: { maintainAspectRatio: false, scales: { y: pctAxis, x: { grid: { display: false } } }, plugins: { legend, tooltip: tip } },
    });

    const hbar = { indexAxis: "y", maintainAspectRatio: false, scales: { x: pctAxis, y: { grid: { display: false } } }, plugins: { legend: { display: false }, tooltip: tip } };

    const cats = groupRates(pick("Basic", "1. no defense"), "category");
    new Chart($("catChart"), {
      type: "bar",
      data: { labels: cats.map(c => c.key), datasets: [{ data: cats.map(c => c.rate), backgroundColor: cats.map(c => color(c.rate)), borderRadius: 4 }] },
      options: hbar,
    });

    const adv = groupRates(pick("Advanced", "2. hardened prompt"), "name");
    new Chart($("advChart"), {
      type: "bar",
      data: { labels: adv.map(a => a.key), datasets: [{ data: adv.map(a => a.rate), backgroundColor: adv.map(a => color(a.rate)), borderRadius: 4 }] },
      options: hbar,
    });

    const types = {};
    attacks.filter(r => r.leak_type).forEach(r => { types[r.leak_type] = (types[r.leak_type] || 0) + 1; });
    new Chart($("typeChart"), {
      type: "doughnut",
      data: { labels: Object.keys(types), datasets: [{ data: Object.values(types), backgroundColor: [C.red, C.amber, C.accent, "#5FD4E8", "#C792EA", "#F78C6C"], borderWidth: 0 }] },
      options: { maintainAspectRatio: false, cutout: "62%", plugins: { legend } },
    });

    const reasons = [["blocked by input filter", C.accent], ["blocked by output filter", "#C792EA"], ["refused by model", C.amber]];
    new Chart($("fpChart"), {
      type: "bar",
      data: {
        labels,
        datasets: reasons.map(([reason, col]) => ({
          label: reason[0].toUpperCase() + reason.slice(1),
          data: LEVELS.map(l => benign.filter(r => r.defense === l && r.outcome === reason).length),
          backgroundColor: col,
          borderRadius: 3,
        })),
      },
      options: {
        maintainAspectRatio: false,
        scales: { x: { stacked: true, grid: { display: false } }, y: { stacked: true, beginAtZero: true, ticks: { precision: 0 } } },
        plugins: { legend },
      },
    });

    if (indirect.length) {
      new Chart($("indChart"), {
        type: "bar",
        data: {
          labels: IND_LEVELS.map(l => IND_NAME[l]),
          datasets: [
            { label: "Injection success", data: IND_LEVELS.map(l => { const a = indirect.filter(r => r.level === l && r.type === "attack"); return rate(a.filter(r => r.success).length, a.length); }), backgroundColor: C.red, borderRadius: 4 },
            { label: "Normal documents blocked", data: IND_LEVELS.map(l => { const b = indirect.filter(r => r.level === l && r.type === "benign"); return rate(b.filter(r => r.outcome !== "helped").length, b.length); }), backgroundColor: C.amber, borderRadius: 4 },
          ],
        },
        options: { maintainAspectRatio: false, scales: { y: pctAxis, x: { grid: { display: false } } }, plugins: { legend, tooltip: tip } },
      });
    }
  } else {
    document.querySelectorAll("canvas").forEach(c => {
      c.replaceWith(el("p", "Charts need an internet connection to load. Reopen this page while online.", "note"));
    });
  }

  // ---------- attack x defense matrix ----------
  function header(first, names) {
    const tr = el("tr");
    tr.appendChild(el("th", first));
    names.forEach(n => tr.appendChild(el("th", n, "num")));
    return tr;
  }
  const matrix = $("matrix");
  matrix.appendChild(header("Attack", LEVELS.map(l => NAME[l])));
  [...new Set(attacks.map(r => r.suite + "|" + r.name))].forEach(k => {
    const [suite, name] = k.split("|");
    const tr = el("tr");
    const label = el("td", name);
    label.appendChild(el("span", suite.toLowerCase(), "suite"));
    tr.appendChild(label);
    LEVELS.forEach(l => {
      const s = stats(attacks.filter(r => r.suite === suite && r.name === name && r.defense === l));
      const td = el("td", s.rate === null ? "not tested" : pct(s.rate), "cell");
      if (s.rate === null) td.style.color = C.faint;
      td.style.background = tint(s.rate, true);
      tr.appendChild(td);
    });
    matrix.appendChild(tr);
  });

  // ---------- customer matrix ----------
  const bm = $("benignMatrix");
  bm.appendChild(header("Question", LEVELS.map(l => NAME[l])));
  [...new Set(benign.map(r => r.question))].forEach(q => {
    const tr = el("tr");
    tr.appendChild(el("td", q));
    LEVELS.forEach(l => {
      const r = benign.find(x => x.question === q && x.defense === l);
      const td = el("td", "", "cell");
      if (!r) { td.textContent = "–"; td.style.color = C.faint; }
      else if (r.outcome === "answered") { td.textContent = "helped"; td.style.color = C.green; td.style.background = "rgba(60,203,140,.14)"; }
      else { td.textContent = "blocked"; td.style.color = C.red; td.style.background = "rgba(255,90,95,.16)"; td.title = r.outcome; }
      tr.appendChild(td);
    });
    bm.appendChild(tr);
  });

  // ---------- indirect matrix ----------
  const im = $("indMatrix");
  if (!indirect.length) {
    im.replaceWith(el("p", "No indirect injection results found. Run run_indirect.py first.", "note"));
  } else {
    im.appendChild(header("Document", IND_LEVELS.map(l => IND_NAME[l])));
    const docs = [...new Set(indirect.map(r => r.type + "|" + r.name))].sort((a, b) => a.localeCompare(b));
    docs.forEach(k => {
      const [type, name] = k.split("|");
      const tr = el("tr");
      const label = el("td", name);
      label.appendChild(el("span", type === "attack" ? "poisoned" : "normal", "suite"));
      tr.appendChild(label);
      IND_LEVELS.forEach(l => {
        const rows = indirect.filter(r => r.level === l && r.name === name);
        const td = el("td", "", "cell");
        if (!rows.length) { td.textContent = "–"; td.style.color = C.faint; }
        else if (type === "attack") {
          const bad = rows.filter(r => r.success).length;
          td.textContent = bad ? `hijacked ${bad}/${rows.length}` : "stopped";
          td.style.color = bad ? C.red : C.green;
          td.style.background = tint(rate(bad, rows.length), true);
          td.title = rows.map(r => r.outcome).join("\n");
        } else {
          const bad = rows.filter(r => r.outcome !== "helped").length;
          td.textContent = bad ? `blocked ${bad}/${rows.length}` : "helped";
          td.style.color = bad ? C.amber : C.green;
          td.style.background = tint(rate(bad, rows.length), false);
          td.title = rows.map(r => r.outcome).join("\n");
        }
        tr.appendChild(td);
      });
      im.appendChild(tr);
    });
  }

  // ---------- judge check ----------
  if (!judge) {
    $("judgeNote").textContent = "No judge results found. Run judge.py to fill this section.";
    $("judgeTable").remove();
  } else {
    $("judgeNote").textContent = `A second model (${meta.judge_model}) re-read ${judge.total} saved answers and decided independently whether the secret leaked. Any leak it claimed had to be backed by words quoted from the answer. Every disagreement was checked by hand.`;
    const agree = rate(judge.both_leak + judge.both_safe, judge.total);
    [
      [pct(agree), "agreement between detector and judge", null],
      [judge.both_leak, "leaks both methods found", C.red],
      [judge.only_judge, "extra leaks only the judge claimed", judge.only_judge ? C.amber : C.green],
      [judge.only_detector, "leaks only the detector found", judge.only_detector ? C.amber : C.green],
    ].forEach(([v, l, col]) => {
      const s = el("div", null, "panel stat");
      const val = el("div", String(v), "v");
      if (col) val.style.color = col;
      s.append(val, el("div", l, "l"));
      $("judgeStats").appendChild(s);
    });
    const jt = $("judgeTable");
    const h = el("tr");
    ["Defense level", "Detector says leaked", "Judge says leaked"].forEach((t, i) => h.appendChild(el("th", t, i ? "num" : "")));
    jt.appendChild(h);
    judge.levels.forEach(r => {
      const tr = el("tr");
      tr.appendChild(el("td", NAME[r.level] || r.level));
      [r.detector, r.judge].forEach(v => { const td = el("td", pct(v), "num"); td.style.color = color(v); tr.appendChild(td); });
      jt.appendChild(tr);
    });
  }

  // ---------- lessons + evidence ----------
  const hb = stats(pick("Basic", "2. hardened prompt"));
  const ha = stats(pick("Advanced", "2. hardened prompt"));
  const full = stats(pick(null, "3. full defense"));
  const topCat = groupRates(pick("Basic", "1. no defense"), "category")[0];
  const indRate = l => { const a = indirect.filter(r => r.level === l && r.type === "attack"); return rate(a.filter(r => r.success).length, a.length); };
  const lessons = [
    `Indirect requests are the dangerous ones. With no defense, ${topCat ? topCat.key + " attacks worked " + pct(topCat.rate) + " of the time" : "creative requests worked best"}, while simply asking for the code never did.`,
    `A strict prompt is not enough on its own. It stopped basic attacks (${pct(hb.rate)}) but advanced attacks still got through ${pct(ha.rate)} of the time, and it refused ${pct(fp("2. hardened prompt").rate)} of normal customers.`,
    `Blocking words is the wrong approach. A keyword filter reached ${pct(full.rate)} attack success but blocked ${pct(fp("3. full defense").rate)} of customers. Matching attack patterns instead brought both numbers down to ${pct(bestAll.rate)} and ${pct(bestFp.rate)}.`,
  ];
  if (indirect.length) {
    lessons.push(`Defenses for direct attacks do not cover documents. Hidden instructions in emails and invoices worked ${pct(indRate("1. no defense"))} of the time with no defense and ${pct(indRate("2. balanced defense"))} with the balanced defense. Spotlighting and sanitizing documents brought it to ${pct(indRate("3. balanced + spotlighting"))}.`);
  }
  lessons.push("An AI judge needs checking too. My first judge called harmless refusals leaks, and the stricter version missed real ones. I ended up using rules and judge together, with manual review of every disagreement.");
  lessons.push(`Limits: ${attackCount} direct attacks${docCount ? " and " + docCount + " documents" : ""} against one small model, two to three tries each. 0% means these attacks failed in these runs, not that the bot is unbreakable.`);
  lessons.forEach(t => $("lessons").appendChild(el("li", t)));

  const seen = new Set();
  const ev = attacks.filter(r => r.leak_type)
    .sort((a, b) => LEVELS.indexOf(b.defense) - LEVELS.indexOf(a.defense))
    .filter(r => { const k = r.suite + r.name; if (seen.has(k)) return false; seen.add(k); return true; })
    .slice(0, 3);
  if (!ev.length) $("evidenceList").appendChild(el("p", "No leaks were recorded.", "note"));
  ev.forEach(r => {
    const box = el("div", null, "finding");
    box.append(
      el("h3", `${r.name}, against ${NAME[r.defense].toLowerCase()}`),
      el("div", `Leaked as: ${r.leak_type}`, "note"),
      el("div", r.answer.length > 320 ? r.answer.slice(0, 320) + "..." : r.answer, "ans"),
    );
    $("evidenceList").appendChild(box);
  });

  // ---------- attempts table ----------
  const fDef = $("fDef");
  fDef.appendChild(Object.assign(document.createElement("option"), { value: "", textContent: "All defense levels" }));
  LEVELS.forEach(l => fDef.appendChild(Object.assign(document.createElement("option"), { value: l, textContent: NAME[l] })));
  const PILL = {
    leaked: ["Leaked", "rgba(255,90,95,.16)", C.red],
    filter: ["Blocked by filter", "rgba(142,162,255,.16)", C.accent],
    safe: ["Refused", "rgba(60,203,140,.16)", C.green],
  };

  function render() {
    const suite = $("fSuite").value, def = fDef.value, res = $("fRes").value, q = $("search").value.toLowerCase();
    const tbody = $("rows");
    tbody.innerHTML = "";
    const rows = attacks
      .filter(r => (!suite || r.suite === suite) && (!def || r.defense === def) && (!res || outcome(r) === res))
      .filter(r => (r.name + " " + r.category + " " + r.answer).toLowerCase().includes(q));
    $("count").textContent = `Showing ${rows.length} of ${attacks.length} attempts`;
    rows.forEach(r => {
      const tr = el("tr");
      const name = el("td", r.name);
      name.appendChild(el("span", r.category, "suite"));
      tr.appendChild(name);
      tr.appendChild(el("td", NAME[r.defense]));
      tr.appendChild(el("td", String(r.try), "num"));
      const [txt, bg, col] = PILL[outcome(r)];
      const cell = el("td");
      const p = el("span", r.leak_type ? `${txt}: ${r.leak_type}` : txt, "pill");
      p.style.background = bg;
      p.style.color = col;
      cell.appendChild(p);
      tr.appendChild(cell);
      const ans = el("td", r.answer, "answer");
      ans.tabIndex = 0;
      ans.title = "Click to expand";
      const toggle = () => ans.classList.toggle("open");
      ans.onclick = toggle;
      ans.onkeydown = e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggle(); } };
      tr.appendChild(ans);
      tbody.appendChild(tr);
    });
  }
  ["fSuite", "fRes"].forEach(id => { $(id).onchange = render; });
  fDef.onchange = render;
  $("search").oninput = render;
  render();
})();
</script>
</body>
</html>"""


# ---------- 3. Put the data into the page and save it ----------
def to_js(value):
    return json.dumps(value).replace("</", "<\\/")


page = (TEMPLATE
        .replace("__ATTACKS__", to_js(attacks))
        .replace("__BENIGN__", to_js(benign))
        .replace("__INDIRECT__", to_js(indirect))
        .replace("__JUDGE__", to_js(judge))
        .replace("__META__", to_js(meta)))

with open("dashboard.html", "w", encoding="utf-8") as f:
    f.write(page)

print(f"Dashboard saved to dashboard.html "
      f"({len(attacks)} attack attempts, {len(benign)} customer questions, {len(indirect)} document tests)")