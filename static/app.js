const $ = (id) => document.getElementById(id);
const fmt = (value, suffix = '') => value == null ? '—' : `${value}${suffix}`;

function render(data) {
  const { latest, analysis, history, threshold } = data;
  $('moisture').textContent = fmt(latest.soil_moisture, '%');
  $('temperature').textContent = fmt(latest.temperature, '°C');
  $('humidity').textContent = fmt(latest.humidity, '%');
  $('age').textContent = `${analysis.age_minutes} min`;
  $('threshold').textContent = `${threshold}%`;
  $('decision').textContent = analysis.decision;
  $('explanation').textContent = analysis.explanation;
  $('trust').textContent = `${analysis.trust_score}/100`;
  $('meter').style.width = `${analysis.trust_score}%`;
  $('meter').style.background = analysis.trust_score >= 70 ? 'var(--lime)' : 'var(--orange)';
  $('alerts').textContent = analysis.issues.length ? analysis.issues.join(' · ') : 'All latest data-quality checks passed.';
  $('alerts').classList.toggle('has-alert', analysis.issues.length > 0);
  $('factors').innerHTML = Object.entries(analysis.components).map(([key, value]) => `<div><span>${key}</span><b>${Math.round(value * 100)}%</b><i><em style="width:${value * 100}%"></em></i></div>`).join('');
  drawChart(history, threshold);
}

function drawChart(history, threshold) {
  const values = history.map(item => item.soil_moisture).filter(v => v != null);
  const max = Math.max(70, ...values, threshold + 12), min = Math.min(0, ...values, threshold - 12);
  const points = history.map((item, index) => {
    if (item.soil_moisture == null) return '';
    const x = history.length === 1 ? 50 : (index / (history.length - 1)) * 100;
    const y = 92 - ((item.soil_moisture - min) / (max - min)) * 78;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).filter(Boolean).join(' ');
  const thresholdY = 92 - ((threshold - min) / (max - min)) * 78;
  $('chart').innerHTML = `<svg viewBox="0 0 100 100" preserveAspectRatio="none" aria-label="Soil moisture chart"><line x1="0" y1="${thresholdY}" x2="100" y2="${thresholdY}" class="threshold"/><polyline points="${points}" class="line"/></svg><span class="chart-label">${threshold}% threshold</span>`;
}

async function load(url = '/api/dashboard', options) {
  const response = await fetch(url, options);
  if (!response.ok) throw new Error('Could not update dashboard');
  render(await response.json());
}
document.querySelectorAll('[data-scenario]').forEach(button => button.addEventListener('click', async () => {
  button.disabled = true;
  try { await load('/api/simulate', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({scenario: button.dataset.scenario}) }); }
  catch (error) { $('alerts').textContent = error.message; }
  finally { button.disabled = false; }
}));
load();
