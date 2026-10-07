import json
from datetime import datetime

# 1. Read the results from the attack run
with open("results.json", "r", encoding="utf-8") as f:
    results = json.load(f)

# 2. Info shown at the top of the report
meta = {
    "target": "Bank assistant chatbot",
    "model": "llama3.2:3b",
    "generated": datetime.now().strftime("%d %b %Y, %H:%M"),
}

# 3. The webpage design (HTML + CSS + JavaScript)
TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>LLM Red-Team Report</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
  :root { --bg:#0a0e17; --panel:#111827; --panel2:#0f172a; --border:#1f2937; --text:#e5e7eb;
          --muted:#94a3b8; --cyan:#22d3ee; --red:#f43f5e; --amber:#f59e0b; --green:#10b981; }
  * { box-sizing:border-box; }
  body { margin:0; background:radial-gradient(circle at top left,#0f1b2d 0,var(--bg) 45%);
         color:var(--text); font-family:Inter,"Segoe UI",Arial,sans-serif; min-height:100vh; }
  .wrap { max-width:1200px; margin:0 auto; padding:32px 24px 60px; }
  header { display:flex; justify-content:space-between; align-items:flex-start; gap:16px; flex-wrap:wrap; margin-bottom:28px; }
  .eyebrow { font-family:"JetBrains Mono",Consolas,monospace; color:var(--cyan); font-size:12px; letter-spacing:.15em; text-transform:uppercase; }
  h1 { margin:6px 0 4px; font-size:32px; }
  .meta { color:var(--muted); font-size:14px; }
  .badge { padding:10px 18px; border-radius:999px; font-weight:700; font-size:14px; border:1px solid; }
  .kpis { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:16px; margin-bottom:16px; }
  .card { background:var(--panel); border:1px solid var(--border); border-radius:14px; padding:18px; }
  .kpi-label { color:var(--muted); font-size:12px; text-transform:uppercase; letter-spacing:.08em; }
  .kpi-value { font-size:30px; font-weight:700; margin-top:6px; }
  .kpi-sub { color:var(--muted); font-size:12px; margin-top:4px; }
  .grid2 { display:grid; grid-template-columns:repeat(auto-fit,minmax(340px,1fr)); gap:16px; margin-bottom:16px; }
  .card h2 { font-size:15px; margin:0 0 14px; font-weight:600; }
  .chart { position:relative; height:280px; }
  .chart.tall { height:420px; }
  .heat { display:grid; gap:6px; }
  .heat-row { display:grid; grid-template-columns:minmax(140px,240px) 1fr; align-items:center; gap:10px; font-size:13px; }
  .cells { display:flex; gap:6px; }
  .cell { width:28px; height:28px; border-radius:6px; }
  .legend { color:var(--muted); font-size:12px; margin-top:10px; }
  .finding { border-left:3px solid var(--red); padding:10px 14px; background:var(--panel2); border-radius:8px; margin-bottom:10px; }
  .finding .name { font-weight:600; }
  .finding .ans { font-family:"JetBrains Mono",Consolas,monospace; font-size:12px; color:var(--muted); white-space:pre-wrap; margin-top:6px; }
  .toolbar { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:12px; }
  .toolbar button { background:var(--panel2); color:var(--text); border:1px solid var(--border); padding:7px 14px; border-radius:8px; cursor:pointer; font:inherit; font-size:13px; }
  .toolbar button.active { border-color:var(--cyan); color:var(--cyan); }
  .toolbar input { flex:1; min-width:180px; background:var(--panel2); border:1px solid var(--border); color:var(--text); padding:7px 12px; border-radius:8px; font:inherit; font-size:13px; }
  .table-wrap { overflow-x:auto; }
  table { width:100%; border-collapse:collapse; font-size:13px; }
  th { text-align:left; color:var(--muted); font-weight:500; padding:10px; border-bottom:1px solid var(--border); text-transform:uppercase; font-size:11px; letter-spacing:.08em; }
  td { padding:10px; border-bottom:1px solid var(--border); vertical-align:top; }
  .pill { display:inline-block; padding:3px 10px; border-radius:999px; font-size:11px; font-weight:600; }
  .ans-cell { font-family:"JetBrains Mono",Consolas,monospace; font-size:12px; color:var(--muted); white-space:pre-wrap; max-width:460px; max-height:60px; overflow:hidden; cursor:pointer; }
  .ans-cell.open { max-height:none; }
  footer { color:var(--muted); font-size:12px; margin-top:30px; text-align:center; }
</style>
</head>
<body>
<div class="wrap">

  <header>
    <div>
      <div class="eyebrow">LLM Red-Team Assessment</div>
      <h1>Security Report</h1>
      <div class="meta" id="meta"></div>
    </div>
    <div class="badge" id="badge"></div>
  </header>

  <section class="kpis">
    <div class="card"><div class="kpi-label">Attack success rate</div><div class="kpi-value" id="k-asr"></div><div class="kpi-sub">of all attempts leaked</div></div>
    <div class="card"><div class="kpi-label">Total attempts</div><div class="kpi-value" id="k-tries"></div><div class="kpi-sub" id="k-tries-sub"></div></div>
    <div class="card"><div class="kpi-label">Leaks found</div><div class="kpi-value" id="k-leaks" style="color:var(--red)"></div><div class="kpi-sub">secret exposed</div></div>
    <div class="card"><div class="kpi-label">Blocked</div><div class="kpi-value" id="k-safe" style="color:var(--green)"></div><div class="kpi-sub">attacks resisted</div></div>
    <div class="card"><div class="kpi-label">Most vulnerable</div><div class="kpi-value" id="k-worst" style="font-size:20px"></div><div class="kpi-sub" id="k-worst-sub"></div></div>
  </section>

  <section class="grid2">
    <div class="card"><h2>Leaked vs blocked</h2><div class="chart"><canvas id="donut"></canvas></div></div>
    <div class="card"><h2>Success rate by category</h2><div class="chart"><canvas id="catChart"></canvas></div></div>
  </section>

  <section class="grid2">
    <div class="card"><h2>Success rate by attack</h2><div class="chart tall"><canvas id="atkChart"></canvas></div></div>
    <div class="card"><h2>How the secret leaked</h2><div class="chart tall"><canvas id="typeChart"></canvas></div></div>
  </section>

  <section class="card" style="margin-bottom:16px">
    <h2>Attempt heatmap</h2>
    <div class="heat" id="heat"></div>
    <div class="legend">Each square = one attempt. Red = leaked, green = blocked. Hover for details.</div>
  </section>

  <section class="card" style="margin-bottom:16px">
    <h2>Top findings</h2>
    <div id="findings"></div>
  </section>

  <section class="card">
    <h2>All attempts</h2>
    <div class="toolbar">
      <button data-f="all" class="active">All</button>
      <button data-f="leaked">Leaked</button>
      <button data-f="safe">Blocked</button>
      <input id="search" placeholder="Search attacks, categories or answers...">
    </div>
    <div class="table-wrap">
      <table>
        <thead><tr><th>Category</th><th>Attack</th><th>Try</th><th>Result</th><th>Model answer (click to expand)</th></tr></thead>
        <tbody id="rows"></tbody>
      </table>
    </div>
  </section>

  <footer>Mapped to OWASP Top 10 for LLM Applications: LLM01 Prompt Injection &middot; LLM07 System Prompt Leakage</footer>
</div>

<script>
const results = __RESULTS__;
const meta = __META__;

function risk(rate) {
  if (rate >= 50) return { label: "HIGH", color: "#f43f5e" };
  if (rate >= 20) return { label: "MEDIUM", color: "#f59e0b" };
  return { label: "LOW", color: "#10b981" };
}

function groupBy(key) {
  const groups = {};
  results.forEach(r => {
    const k = r[key];
    if (!groups[k]) groups[k] = { tries: 0, leaks: 0, category: r.category };
    groups[k].tries++;
    if (r.leak_type) groups[k].leaks++;
  });
  return Object.entries(groups)
    .map(([name, g]) => ({ name, category: g.category, tries: g.tries, leaks: g.leaks, rate: g.leaks / g.tries * 100 }))
    .sort((a, b) => b.rate - a.rate);
}

const total = results.length;
const leaks = results.filter(r => r.leak_type).length;
const asr = total ? leaks / total * 100 : 0;
const cats = groupBy("category");
const atks = groupBy("name");
const overall = risk(asr);

// Header + KPI cards
document.getElementById("meta").textContent = `Target: ${meta.target} · Model: ${meta.model} · Generated: ${meta.generated}`;
const badge = document.getElementById("badge");
badge.textContent = `Overall risk: ${overall.label}`;
badge.style.color = overall.color;
badge.style.borderColor = overall.color;
document.getElementById("k-asr").textContent = asr.toFixed(0) + "%";
document.getElementById("k-asr").style.color = overall.color;
document.getElementById("k-tries").textContent = total;
document.getElementById("k-tries-sub").textContent = `${atks.length} attacks, ${cats.length} categories`;
document.getElementById("k-leaks").textContent = leaks;
document.getElementById("k-safe").textContent = total - leaks;
document.getElementById("k-worst").textContent = cats[0] ? cats[0].name : "-";
document.getElementById("k-worst-sub").textContent = cats[0] ? `${cats[0].rate.toFixed(0)}% success rate` : "";

// Charts
if (window.Chart) {
  Chart.defaults.color = "#94a3b8";
  Chart.defaults.font.family = "Inter, Segoe UI, Arial, sans-serif";
  Chart.defaults.borderColor = "#1f2937";

  new Chart(document.getElementById("donut"), {
    type: "doughnut",
    data: { labels: ["Leaked", "Blocked"], datasets: [{ data: [leaks, total - leaks], backgroundColor: ["#f43f5e", "#10b981"], borderWidth: 0 }] },
    options: { maintainAspectRatio: false, cutout: "70%", plugins: { legend: { position: "bottom" } } }
  });

  const barOptions = {
    indexAxis: "y", maintainAspectRatio: false,
    scales: { x: { min: 0, max: 100, ticks: { callback: v => v + "%" } } },
    plugins: { legend: { display: false }, tooltip: { callbacks: { label: c => c.raw.toFixed(0) + "% success rate" } } }
  };

  new Chart(document.getElementById("catChart"), {
    type: "bar",
    data: { labels: cats.map(c => c.name), datasets: [{ data: cats.map(c => c.rate), backgroundColor: cats.map(c => risk(c.rate).color), borderRadius: 6 }] },
    options: barOptions
  });

  new Chart(document.getElementById("atkChart"), {
    type: "bar",
    data: { labels: atks.map(a => a.name), datasets: [{ data: atks.map(a => a.rate), backgroundColor: atks.map(a => risk(a.rate).color), borderRadius: 6 }] },
    options: barOptions
  });

  const typeCounts = {};
  results.filter(r => r.leak_type).forEach(r => { typeCounts[r.leak_type] = (typeCounts[r.leak_type] || 0) + 1; });
  new Chart(document.getElementById("typeChart"), {
    type: "doughnut",
    data: { labels: Object.keys(typeCounts), datasets: [{ data: Object.values(typeCounts), backgroundColor: ["#f43f5e", "#f59e0b", "#a78bfa", "#22d3ee"], borderWidth: 0 }] },
    options: { maintainAspectRatio: false, cutout: "60%", plugins: { legend: { position: "bottom" } } }
  });
}

// Heatmap
const heat = document.getElementById("heat");
atks.forEach(a => {
  const row = document.createElement("div");
  row.className = "heat-row";
  const label = document.createElement("div");
  label.textContent = a.name;
  const cells = document.createElement("div");
  cells.className = "cells";
  results.filter(r => r.name === a.name).forEach(r => {
    const cell = document.createElement("div");
    cell.className = "cell";
    cell.style.background = r.leak_type ? "#f43f5e" : "rgba(16,185,129,.35)";
    cell.title = `${r.name} - try ${r.try}: ${r.leak_type ? "LEAKED (" + r.leak_type + ")" : "blocked"}`;
    cells.appendChild(cell);
  });
  row.appendChild(label);
  row.appendChild(cells);
  heat.appendChild(row);
});

// Top findings
const findings = document.getElementById("findings");
const topAttacks = atks.filter(a => a.rate > 0).slice(0, 3);
if (topAttacks.length === 0) findings.textContent = "No leaks found.";
topAttacks.forEach(a => {
  const example = results.find(r => r.name === a.name && r.leak_type);
  const box = document.createElement("div");
  box.className = "finding";
  const name = document.createElement("div");
  name.className = "name";
  name.textContent = `${a.name} (${a.category}) - ${a.rate.toFixed(0)}% success rate`;
  const ans = document.createElement("div");
  ans.className = "ans";
  ans.textContent = example.answer.length > 300 ? example.answer.slice(0, 300) + "..." : example.answer;
  box.appendChild(name);
  box.appendChild(ans);
  findings.appendChild(box);
});

// Table with filter + search
let filter = "all";
function cell(text) { const td = document.createElement("td"); td.textContent = text; return td; }

function renderTable() {
  const q = document.getElementById("search").value.toLowerCase();
  const tbody = document.getElementById("rows");
  tbody.innerHTML = "";
  results
    .filter(r => filter === "all" || (filter === "leaked" && r.leak_type) || (filter === "safe" && !r.leak_type))
    .filter(r => (r.name + " " + r.category + " " + r.answer).toLowerCase().includes(q))
    .forEach(r => {
      const tr = document.createElement("tr");
      tr.appendChild(cell(r.category));
      tr.appendChild(cell(r.name));
      tr.appendChild(cell(r.try));
      const res = document.createElement("td");
      const pill = document.createElement("span");
      pill.className = "pill";
      pill.textContent = r.leak_type ? "LEAKED · " + r.leak_type : "BLOCKED";
      pill.style.background = r.leak_type ? "rgba(244,63,94,.15)" : "rgba(16,185,129,.15)";
      pill.style.color = r.leak_type ? "#f43f5e" : "#10b981";
      res.appendChild(pill);
      tr.appendChild(res);
      const ans = cell(r.answer);
      ans.className = "ans-cell";
      ans.onclick = () => ans.classList.toggle("open");
      tr.appendChild(ans);
      tbody.appendChild(tr);
    });
}

document.querySelectorAll(".toolbar button").forEach(b => {
  b.onclick = () => {
    document.querySelectorAll(".toolbar button").forEach(x => x.classList.remove("active"));
    b.classList.add("active");
    filter = b.dataset.f;
    renderTable();
  };
});
document.getElementById("search").oninput = renderTable;
renderTable();
</script>
</body>
</html>"""


# 4. Put the data into the page and save it
def to_js(data):
    return json.dumps(data).replace("</", "<\\/")


page = TEMPLATE.replace("__RESULTS__", to_js(results)).replace("__META__", to_js(meta))

with open("report.html", "w", encoding="utf-8") as f:
    f.write(page)

print("Dashboard saved to report.html")