const byId = (id) => document.getElementById(id);

const playerList = byId('player-list');
const valuationResult = byId('valuation-result');
const similarResult = byId('similar-result');

const eur = (v) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(v ?? 0);

function statusBadge(status) {
  const st = (status || '').toLowerCase();
  let cls = 'warn';
  if (st.includes('undervalued')) cls = 'ok';
  if (st.includes('overvalued')) cls = 'bad';
  return `<span class="badge ${cls}">${status}</span>`;
}

async function fetchJson(url) {
  const res = await fetch(url);
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Request failed');
  return data;
}

async function loadPlayers(q = '') {
  const data = await fetchJson(`/api/players?q=${encodeURIComponent(q)}`);
  playerList.innerHTML = data.players.map((name) => `<option value="${name}"></option>`).join('');
}

async function onPredict() {
  const player = byId('valuation-player').value.trim();
  if (!player) return;
  valuationResult.innerHTML = '<p class="small">Predicting...</p>';
  try {
    const result = await fetchJson(`/api/predict?player_name=${encodeURIComponent(player)}`);
    valuationResult.innerHTML = `
      <div class="kv">
        <div><p class="small">Player</p><strong>${result.player_name}</strong></div>
        <div><p class="small">Position / Age</p><strong>${result.position} / ${result.age ?? '-'} </strong></div>
        <div><p class="small">Predicted Value</p><strong>${eur(result.predicted_value_eur)}</strong></div>
        <div><p class="small">Actual Market Value</p><strong>${eur(result.actual_market_value_eur)}</strong></div>
      </div>
      <p class="small" style="margin-top:10px">${statusBadge(result.market_status)}</p>
    `;
  } catch (err) {
    valuationResult.innerHTML = `<p class="error">${err.message}</p>`;
  }
}

async function onSimilar() {
  const player = byId('similar-player').value.trim();
  if (!player) return;
  const maxPrice = byId('max-price').value.trim();
  const maxAge = byId('max-age').value.trim();
  const topK = byId('top-k').value.trim() || '5';

  const params = new URLSearchParams({ player_name: player, top_k: topK });
  if (maxPrice) params.set('max_price', maxPrice);
  if (maxAge) params.set('max_age', maxAge);

  similarResult.innerHTML = '<p class="small">Searching similar players...</p>';
  try {
    const result = await fetchJson(`/api/similar?${params.toString()}`);
    if (!result.results?.length) {
      similarResult.innerHTML = `<p class="small">No results found for current filters.</p>`;
      return;
    }
    const rows = result.results.map((r) => `
      <tr>
        <td>${r.name}</td>
        <td>${r.position}</td>
        <td>${r.age ?? '-'}</td>
        <td>${r.club ?? '-'}</td>
        <td>${eur(r.market_value_eur)}</td>
        <td>${r.similarity_score}</td>
      </tr>
    `).join('');

    similarResult.innerHTML = `
      <table class="table">
        <thead>
          <tr><th>Name</th><th>Pos</th><th>Age</th><th>Club</th><th>Value</th><th>Score</th></tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    `;
  } catch (err) {
    similarResult.innerHTML = `<p class="error">${err.message}</p>`;
  }
}

byId('predict-btn').addEventListener('click', onPredict);
byId('similar-btn').addEventListener('click', onSimilar);
byId('valuation-player').addEventListener('input', (e) => loadPlayers(e.target.value));
byId('similar-player').addEventListener('input', (e) => loadPlayers(e.target.value));

loadPlayers().catch(() => {});
