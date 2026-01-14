async function loadLatest() {
  const res = await fetch("./data/latest.json", { cache: "no-store" });
  return res.json();
}

function card(result) {
  const status = result.ok ? "OK" : "DOWN";
  const cls = result.ok ? "ok" : "bad";
  const code = result.status_code ?? "—";
  const err = result.error ? `<div class="muted">Error: ${result.error}</div>` : "";

  return `
    <div class="card">
      <div><strong><a href="${result.url}" target="_blank" rel="noreferrer">${result.name}</a></strong></div>
      <div class="${cls}">${status}</div>
      <div class="muted">HTTP: ${code}</div>
      <div class="muted">Latency: ${result.latency_ms} ms</div>
      <div class="muted">Checked: ${new Date(result.timestamp).toLocaleString()}</div>
      ${err}
    </div>
  `;
}

(async () => {
  const latest = await loadLatest();
  const container = document.getElementById("status");
  container.innerHTML = latest.results.map(card).join("");
})();
