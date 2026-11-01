const form = document.querySelector('#risk-form');
const results = document.querySelector('#results');
const emptyState = document.querySelector('#empty-state');
const errorMessage = document.querySelector('#error-message');
const submitButton = form.querySelector('button[type="submit"]');
let latestResult = null;

const examples = {
  rail: { name: 'Eastside Rapid Transit Extension', project_type: 'rail', phase: 'planning', capital_cost: 1450, duration_months: 84, delivery_method: 'design_build', design_completion_percent: 15, labor_share_percent: 42, labor_escalation_percent: 5.2, material_escalation_percent: 4.6, estimate_escalation_percent: 3, contingency_percent: 20, regulatory_bodies: 7, approvals_required: 14, approval_complexity: 4, site_uncertainty: 4, stakeholder_complexity: 5 },
  water: { name: 'Regional Water Treatment Upgrade', project_type: 'water', phase: 'preliminary_design', capital_cost: 380, duration_months: 54, delivery_method: 'cmgc', design_completion_percent: 35, labor_share_percent: 36, labor_escalation_percent: 4.4, material_escalation_percent: 4.1, estimate_escalation_percent: 3, contingency_percent: 18, regulatory_bodies: 5, approvals_required: 9, approval_complexity: 4, site_uncertainty: 3, stakeholder_complexity: 2 },
  bridge: { name: 'Grand River Bridge Replacement', project_type: 'bridge', phase: 'final_design', capital_cost: 620, duration_months: 60, delivery_method: 'design_bid_build', design_completion_percent: 72, labor_share_percent: 39, labor_escalation_percent: 4.7, material_escalation_percent: 5.1, estimate_escalation_percent: 3.2, contingency_percent: 12, regulatory_bodies: 6, approvals_required: 11, approval_complexity: 3, site_uncertainty: 4, stakeholder_complexity: 3 }
};

const numericFields = new Set([
  'capital_cost', 'duration_months', 'labor_share_percent', 'labor_escalation_percent',
  'material_escalation_percent', 'estimate_escalation_percent', 'regulatory_bodies',
  'approvals_required', 'approval_complexity', 'design_completion_percent', 'site_uncertainty',
  'stakeholder_complexity', 'contingency_percent'
]);

function readForm() {
  const data = Object.fromEntries(new FormData(form));
  numericFields.forEach((key) => { data[key] = Number(data[key]); });
  return data;
}

function setForm(values) {
  Object.entries(values).forEach(([key, value]) => {
    const input = form.elements.namedItem(key);
    if (input) input.value = value;
  });
  updateRangeOutputs();
}

function updateRangeOutputs() {
  form.querySelectorAll('input[type="range"]').forEach((input) => {
    const output = input.closest('label').querySelector('output');
    if (output) output.textContent = `${input.value}%`;
  });
}

function money(value) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: value >= 100 ? 0 : 1 }).format(value) + 'M';
}

function number(value, digits = 0) {
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: digits }).format(value);
}

function signedPercent(value) {
  return `${value >= 0 ? '+' : ''}${number(value, 1)}%`;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[char]));
}

function rangeRow(name, points, accessor, format, className) {
  const values = ['p10', 'p50', 'p80', 'p90'].map((key) => accessor(points[key]));
  const baseline = name === 'Cost' ? latestResult.baseline.capital_cost : latestResult.baseline.duration_months;
  const minimum = Math.min(baseline * .9, values[0]);
  const maximum = Math.max(values[3] * 1.04, baseline * 1.1);
  const position = (value) => Math.max(0, Math.min(100, (value - minimum) / (maximum - minimum) * 100));
  const left = position(values[0]);
  const width = position(values[3]) - left;
  return `<div class="range-row">
    <span class="range-name">${name}</span>
    <div class="range-track" aria-label="${name} modeled range from ${format(values[0])} to ${format(values[3])}">
      <span class="baseline-marker" style="left:${position(baseline)}%" title="Baseline ${format(baseline)}"></span>
      <span class="range-span ${className}" style="left:${left}%;width:${width}%"></span>
      <span class="range-marker" style="left:${position(values[1])}%"></span>
    </div>
    <span class="range-value">${format(values[0])}–${format(values[3])}</span>
  </div>`;
}

function renderResult(result) {
  latestResult = result;
  emptyState.hidden = true;
  errorMessage.hidden = true;
  results.hidden = false;

  document.querySelector('#result-name').textContent = result.project.name;
  document.querySelector('#result-meta').textContent = `${result.project.project_type_label} · ${result.project.phase.replaceAll('_', ' ')} · ${number(result.project.simulations)} scenarios`;
  document.querySelector('#cost-p80').textContent = money(result.cost.p80.amount);
  document.querySelector('#cost-variance').textContent = signedPercent(result.cost.p80.variance_percent);
  document.querySelector('#cost-range').textContent = `P50 ${money(result.cost.p50.amount)} · P90 ${money(result.cost.p90.amount)}`;
  document.querySelector('#time-p80').textContent = `${number(result.schedule.p80.months, 1)} mo`;
  document.querySelector('#time-variance').textContent = signedPercent(result.schedule.p80.variance_percent);
  document.querySelector('#time-range').textContent = `P50 ${number(result.schedule.p50.months, 1)} · P90 ${number(result.schedule.p90.months, 1)} months`;
  document.querySelector('#budget-probability').textContent = `${number(result.probability_exceeding_funded_budget_percent, 1)}%`;
  document.querySelector('#budget-label').textContent = result.probability_exceeding_funded_budget_percent > 50 ? 'Elevated' : result.probability_exceeding_funded_budget_percent > 25 ? 'Watch' : 'Contained';
  document.querySelector('#budget-value').textContent = `Funded budget ${money(result.baseline.funded_budget_with_contingency)}`;
  document.querySelector('#confidence-score').textContent = `${result.confidence.score}/100`;
  document.querySelector('#confidence-label').textContent = result.confidence.label;

  document.querySelector('#range-visuals').innerHTML =
    rangeRow('Cost', result.cost, (point) => point.amount, money, 'cost') +
    rangeRow('Schedule', result.schedule, (point) => point.months, (v) => `${number(v, 1)} mo`, 'time');

  const maxDriver = Math.max(...result.drivers.map((driver) => Math.abs(driver.expected_cost_effect_percent)), 1);
  document.querySelector('#driver-list').innerHTML = result.drivers.slice(0, 5).map((driver) => `
    <div class="driver-row">
      <span>${escapeHtml(driver.name)}</span>
      <div class="driver-track"><div class="driver-fill" style="width:${Math.abs(driver.expected_cost_effect_percent) / maxDriver * 100}%"></div></div>
      <span>${signedPercent(driver.expected_cost_effect_percent)}</span>
    </div>`).join('');

  const top = result.drivers[0];
  document.querySelector('#interpretation').innerHTML = `<strong>Planning readout.</strong> ${escapeHtml(top.name)} is the largest modeled cost driver. A P80 funding position is ${money(result.cost.p80.amount)}, while a P80 delivery allowance is ${number(result.schedule.p80.months, 1)} months. Re-run after each design or approval milestone; the range should narrow as uncertainty is retired.`;
  results.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

async function analyze(event) {
  if (event) event.preventDefault();
  if (!form.reportValidity()) return;
  submitButton.disabled = true;
  submitButton.querySelector('span').textContent = 'Running scenarios…';
  errorMessage.hidden = true;
  try {
    const response = await fetch('/api/estimate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(readForm()) });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || 'Analysis failed.');
    renderResult(payload);
  } catch (error) {
    errorMessage.textContent = error.message;
    errorMessage.hidden = false;
  } finally {
    submitButton.disabled = false;
    submitButton.querySelector('span').textContent = 'Run risk analysis';
  }
}

function download(filename, content, type) {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const anchor = document.createElement('a');
  anchor.href = url; anchor.download = filename; anchor.click();
  URL.revokeObjectURL(url);
}

function getPortfolio() {
  try { return JSON.parse(localStorage.getItem('public_infrastructure_budget_multiplier_portfolio') || '[]'); }
  catch { return []; }
}

function renderPortfolio() {
  const portfolio = getPortfolio();
  const body = document.querySelector('#portfolio-body');
  const exportButton = document.querySelector('#portfolio-export');
  exportButton.hidden = portfolio.length === 0;
  if (!portfolio.length) {
    body.innerHTML = '<tr class="portfolio-empty"><td colspan="7">No saved projects yet. Run an analysis and select “Portfolio.”</td></tr>';
    return;
  }
  body.innerHTML = portfolio.map((item, index) => `<tr>
    <td><strong>${escapeHtml(item.project.name)}</strong></td>
    <td>${escapeHtml(item.project.project_type_label)}<br>${escapeHtml(item.project.phase.replaceAll('_', ' '))}</td>
    <td>${money(item.baseline.capital_cost)}</td>
    <td>${money(item.cost.p80.amount)} <small>(${signedPercent(item.cost.p80.variance_percent)})</small></td>
    <td>${number(item.schedule.p80.months, 1)} mo</td>
    <td><span class="risk-pill">${number(item.probability_exceeding_funded_budget_percent, 1)}%</span></td>
    <td><button class="remove-row" data-index="${index}" aria-label="Remove ${escapeHtml(item.project.name)}">×</button></td>
  </tr>`).join('');
}

form.addEventListener('submit', analyze);
form.addEventListener('input', updateRangeOutputs);
document.querySelector('#sample-select').addEventListener('change', (event) => {
  if (examples[event.target.value]) setForm(examples[event.target.value]);
});
document.querySelector('#export-button').addEventListener('click', () => {
  if (latestResult) download(`${latestResult.project.name.toLowerCase().replace(/[^a-z0-9]+/g, '-')}-risk.json`, JSON.stringify(latestResult, null, 2), 'application/json');
});
document.querySelector('#save-button').addEventListener('click', () => {
  if (!latestResult) return;
  const portfolio = getPortfolio().filter((item) => item.project.name !== latestResult.project.name);
  portfolio.unshift(latestResult);
  localStorage.setItem('public_infrastructure_budget_multiplier_portfolio', JSON.stringify(portfolio.slice(0, 25)));
  renderPortfolio();
  document.querySelector('#save-button').textContent = '✓ Saved';
  setTimeout(() => { document.querySelector('#save-button').textContent = '＋ Portfolio'; }, 1400);
});
document.querySelector('#portfolio-body').addEventListener('click', (event) => {
  const button = event.target.closest('.remove-row');
  if (!button) return;
  const portfolio = getPortfolio();
  portfolio.splice(Number(button.dataset.index), 1);
  localStorage.setItem('public_infrastructure_budget_multiplier_portfolio', JSON.stringify(portfolio));
  renderPortfolio();
});
document.querySelector('#portfolio-export').addEventListener('click', () => {
  const rows = [['Project', 'Type', 'Phase', 'Baseline cost (millions)', 'P80 cost (millions)', 'P80 months', 'Budget exceedance probability']];
  getPortfolio().forEach((item) => rows.push([item.project.name, item.project.project_type_label, item.project.phase, item.baseline.capital_cost, item.cost.p80.amount, item.schedule.p80.months, item.probability_exceeding_funded_budget_percent]));
  const csv = rows.map((row) => row.map((cell) => `"${String(cell).replaceAll('"', '""')}"`).join(',')).join('\n');
  download('infrastructure-risk-portfolio.csv', csv, 'text/csv');
});

updateRangeOutputs();
renderPortfolio();

