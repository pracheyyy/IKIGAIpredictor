/* ═══════════════════════════════════════════════════════════
   IKIGAI — predict.js
   Dashboard: auth gate, habit form submit, result rendering,
              history display
   ═══════════════════════════════════════════════════════════ */

const HISTORY_KEY = 'ikigai_history';

/* ── INIT ───────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  const user = getDashboardUser();

  if (!user) {
    /* Not logged in — show gate, hide main */
    document.getElementById('auth-gate').style.display = 'flex';
    document.getElementById('dash-main').style.display = 'none';
    return;
  }

  /* Logged in — show dashboard */
  document.getElementById('auth-gate').style.display = 'none';
  document.getElementById('dash-main').style.display  = 'block';

  /* Set name in nav + welcome */
  const firstName = user.name.split(' ')[0];
  const navName   = document.getElementById('nav-user-name');
  const welcomeN  = document.getElementById('welcome-name');
  if (navName)  navName.textContent  = user.name;
  if (welcomeN) welcomeN.textContent = firstName;

  /* Load history */
  loadHistory(user);
});

/* ── HABIT SUBMIT ────────────────────────────────────────── */
async function submitHabits() {
  const user = getDashboardUser();

  /* Read inputs */
  const sleep    = parseFloat(document.getElementById('h-sleep')?.value);
  const study    = parseFloat(document.getElementById('h-study')?.value);
  const extra    = parseFloat(document.getElementById('h-extra')?.value);
  const social   = parseFloat(document.getElementById('h-social')?.value);
  const physical = parseFloat(document.getElementById('h-physical')?.value);
  const gpaRaw   = document.getElementById('h-gpa')?.value;
  const gpa      = gpaRaw ? parseFloat(gpaRaw) : 3.0;

  /* Validate */
  const errEl = document.getElementById('form-err');
  if ([sleep, study, extra, social, physical].some(isNaN)) {
    if (errEl) { errEl.textContent = 'Please fill in all required fields.'; errEl.style.display = 'block'; }
    return;
  }
  if (errEl) { errEl.textContent = ''; errEl.style.display = 'none'; }

  /* Loading state */
  const submitBtn  = document.getElementById('submit-btn');
  const submitText = document.getElementById('submit-text');
  const submitSpin = document.getElementById('submit-spin');
  if (submitBtn)  submitBtn.disabled  = true;
  if (submitText) submitText.style.display = 'none';
  if (submitSpin) submitSpin.style.display = 'inline';

  try {
    const res = await fetch('/api/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sleep, study,
        extracurricular: extra,
        social, physical, gpa,
        user_id: user?.id,
      }),
    });

    const data = await res.json();
    if (!res.ok) {
      if (errEl) { errEl.textContent = data.error || 'Prediction failed.'; errEl.style.display = 'block'; }
      return;
    }

    renderResults(data);
    saveLocalHistory(user?.id, data);
    loadHistory(user);

    /* Scroll to results */
    setTimeout(() => {
      document.getElementById('results-section')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 200);

  } catch (e) {
    if (errEl) { errEl.textContent = 'Network error. Is the Flask server running on port 5000?'; errEl.style.display = 'block'; }
  } finally {
    if (submitBtn)  submitBtn.disabled  = false;
    if (submitText) submitText.style.display = 'inline';
    if (submitSpin) submitSpin.style.display = 'none';
  }
}

/* ── RENDER RESULTS ─────────────────────────────────────── */
function renderResults(data) {
  const section = document.getElementById('results-section');
  if (section) section.style.display = 'block';

  const { layer1_scores, layer2, layer3, ikigai, gpa_prediction, recommendations } = data;

  /* ── Override banner ── */
  const banner = document.getElementById('override-banner');
  const oText  = document.getElementById('override-text');
  if (layer3.override_applied && banner && oText) {
    oText.textContent = layer3.override_reason;
    banner.style.display = 'flex';
  } else if (banner) {
    banner.style.display = 'none';
  }

  /* ── Score cards ── */
  const stressLevel = layer3.final_stress_level;
  const levelEl = document.getElementById('r-stress-level');
  if (levelEl) {
    levelEl.textContent = stressLevel;
    levelEl.className   = 'sc-val serif level-' + stressLevel.toLowerCase();
  }
  setText('r-stress-score', `Score: ${layer2.stress_score}/100`);
  setText('r-ikigai',       ikigai.ikigai_score.toFixed(1));
  setText('r-productivity', layer2.productivity.toFixed(1));
  setText('r-gpa',          gpa_prediction.toFixed(2));

  /* ── Layer 1 score bars ── */
  const layer1Items = [
    { name: 'Sleep',           val: layer1_scores.sleep_score    },
    { name: 'Study',           val: layer1_scores.study_score    },
    { name: 'Physical',        val: layer1_scores.physical_score },
    { name: 'Social',          val: layer1_scores.social_score   },
    { name: 'Extracurricular', val: layer1_scores.extra_score    },
  ];
  const l1Container = document.getElementById('layer1-bars');
  if (l1Container) {
    l1Container.innerHTML = layer1Items.map(item => `
      <div class="score-bar-row">
        <div class="sb-header">
          <span class="sb-name">${item.name}</span>
          <span class="sb-val">${item.val.toFixed(1)}</span>
        </div>
        <div class="sb-track">
          <div class="sb-fill" style="width:${item.val}%"></div>
        </div>
      </div>
    `).join('');
  }

  /* ── ML confidence bars ── */
  const mlBars   = document.getElementById('ml-bars');
  const mlMeta   = document.getElementById('ml-meta');
  const probs    = layer3.class_probabilities;
  const classMap = { Low: 'low-fill', Medium: 'medium-fill', High: 'high-fill' };

  if (mlBars) {
    mlBars.innerHTML = Object.entries(probs)
      .sort((a, b) => b[1] - a[1])
      .map(([cls, pct]) => `
        <div class="ml-bar-row">
          <div class="ml-bar-label"><span>${cls} Stress</span><span>${pct}%</span></div>
          <div class="ml-bar-track">
            <div class="ml-bar-fill ${classMap[cls] || ''}" style="width:${pct}%"></div>
          </div>
        </div>
      `).join('');
  }
  if (mlMeta) {
    const overrideNote = layer3.override_applied
      ? `<strong>Rule override applied:</strong> ${layer3.override_reason}`
      : `ML prediction confirmed (no override needed).`;
    mlMeta.innerHTML = `
      ML model predicted: <strong>${layer3.ml_stress_level}</strong>
      (${layer3.ml_confidence}% confidence) &nbsp;·&nbsp;
      Final: <strong>${layer3.final_stress_level}</strong><br>
      <span style="opacity:.7;font-size:.75rem">${overrideNote}</span>
    `;
  }

  /* ── Charts ── */
  renderRadarChart(layer1_scores);
  renderPillarChart(ikigai);

  /* ── Recommendations ── */
  const recList = document.getElementById('rec-list');
  if (recList && recommendations?.length) {
    recList.innerHTML = recommendations.map(r => `
      <div class="rec-card priority-${r.priority}">
        <div class="rec-icon">${r.icon}</div>
        <div class="rec-body">
          <div><span class="rec-badge ${r.priority}">${r.priority}</span></div>
          <div class="rec-title serif">${r.title}</div>
          <div class="rec-text">${r.body}</div>
        </div>
      </div>
    `).join('');
  } else if (recList) {
    recList.innerHTML = '<p style="color:var(--muted);font-size:.88rem">No specific recommendations at this time. Your balance looks good!</p>';
  }
}

/* ── RESET FORM ─────────────────────────────────────────── */
function resetForm() {
  const resultsSection = document.getElementById('results-section');
  if (resultsSection) resultsSection.style.display = 'none';
  /* Clear inputs */
  ['h-sleep','h-study','h-extra','h-social','h-physical','h-gpa'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = '';
  });
  document.getElementById('form-section')?.scrollIntoView({ behavior: 'smooth' });
}

/* ── LOCAL HISTORY ──────────────────────────────────────── */
function getLocalHistory(uid) {
  try { return JSON.parse(localStorage.getItem(HISTORY_KEY + '_' + uid)) || []; }
  catch { return []; }
}

function saveLocalHistory(uid, entry) {
  if (!uid) return;
  const history = getLocalHistory(uid);
  history.push({ ...entry, date: new Date().toLocaleDateString('en-IN') });
  localStorage.setItem(HISTORY_KEY + '_' + uid, JSON.stringify(history));
}

function loadHistory(user) {
  if (!user) return;
  const history   = getLocalHistory(user.id);
  const container = document.getElementById('history-list');
  const trendWrap = document.getElementById('trend-wrap');
  const sub       = document.getElementById('history-sub');

  /* Update summary chips */
  setText('chip-entries', history.length);
  setText('chip-streak',  Math.min(history.length, 7));
  if (history.length > 0) {
    const avgIk = (history.reduce((s, e) => s + (e.ikigai?.ikigai_score || 0), 0) / history.length).toFixed(1);
    setText('chip-avg', avgIk);
  }

  if (!container) return;

  if (!history.length) {
    container.innerHTML = '<p class="history-empty">No entries yet. Log your first day above!</p>';
    if (trendWrap) trendWrap.style.display = 'none';
    if (sub) sub.textContent = 'Your logged entries will appear here.';
    return;
  }

  if (sub) sub.textContent = `${history.length} entr${history.length === 1 ? 'y' : 'ies'} logged`;

  container.innerHTML = `
    <div class="history-entry" style="font-size:.7rem;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);font-weight:500">
      <span>Date</span>
      <span style="text-align:center">Stress</span>
      <span style="text-align:center">Ikigai</span>
      <span style="text-align:center">Productivity</span>
      <span style="text-align:center">GPA Est.</span>
    </div>
    ${history.slice().reverse().map(e => `
      <div class="history-entry">
        <span class="he-date">${e.date || '—'}</span>
        <div>
          <span class="he-val level-${(e.layer3?.final_stress_level || '').toLowerCase()}">${e.layer3?.final_stress_level || '—'}</span>
          <span class="he-label">stress</span>
        </div>
        <div>
          <span class="he-val">${(e.ikigai?.ikigai_score || 0).toFixed(1)}</span>
          <span class="he-label">/100</span>
        </div>
        <div>
          <span class="he-val">${(e.layer2?.productivity || 0).toFixed(1)}</span>
          <span class="he-label">/100</span>
        </div>
        <div>
          <span class="he-val">${e.gpa_prediction?.toFixed(2) || '—'}</span>
          <span class="he-label">/4.0</span>
        </div>
      </div>
    `).join('')}
  `;

  /* Show trend if >= 2 entries */
  if (history.length >= 2 && trendWrap) {
    trendWrap.style.display = 'block';
    renderTrendChart(history);
  }
}

/* ── UTIL ───────────────────────────────────────────────── */
function setText(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}