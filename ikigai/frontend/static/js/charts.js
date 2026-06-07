/* ═══════════════════════════════════════════════════════════
   IKIGAI — charts.js
   Chart.js wrappers for radar, pillar bar, and trend line
   ═══════════════════════════════════════════════════════════ */

/* Paper-ink palette matching the Ikigai book theme */
const PALETTE = {
  ink:     '#1a1714',
  red:     '#b03a2e',
  muted:   '#8c8070',
  paper:   '#f5f0e8',
  paper2:  '#ede6d8',
  border:  'rgba(26,23,20,0.12)',
  pillars: ['#b03a2e', '#5b6f82', '#8c8070', '#3d6e4e'],
};

/* shared Chart.js defaults */
Chart.defaults.font.family = "'DM Sans', sans-serif";
Chart.defaults.font.size   = 11;
Chart.defaults.color       = PALETTE.muted;

let radarChartInst  = null;
let pillarChartInst = null;
let trendChartInst  = null;

/* ── RADAR: Layer 1 normalized scores ──────────────────── */
function renderRadarChart(scores) {
  const ctx = document.getElementById('radarChart');
  if (!ctx) return;

  if (radarChartInst) radarChartInst.destroy();

  radarChartInst = new Chart(ctx, {
    type: 'radar',
    data: {
      labels: ['Sleep', 'Study', 'Physical', 'Social', 'Extracurricular'],
      datasets: [{
        label: 'Your Scores',
        data: [
          scores.sleep_score,
          scores.study_score,
          scores.physical_score,
          scores.social_score,
          scores.extra_score,
        ],
        backgroundColor: 'rgba(176,58,46,0.12)',
        borderColor:     PALETTE.red,
        borderWidth:     1.5,
        pointBackgroundColor: PALETTE.red,
        pointBorderColor:     PALETTE.paper,
        pointRadius:          4,
        pointHoverRadius:     6,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        r: {
          min: 0, max: 100,
          ticks: {
            stepSize: 25, display: true,
            font: { size: 9 }, color: PALETTE.muted,
            backdropColor: 'transparent',
          },
          grid:        { color: PALETTE.border },
          angleLines:  { color: PALETTE.border },
          pointLabels: { font: { size: 11 }, color: PALETTE.ink },
        }
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => ` ${ctx.parsed.r.toFixed(1)} / 100`
          }
        }
      }
    }
  });
}

/* ── BAR: Ikigai Pillars ────────────────────────────────── */
function renderPillarChart(ikigai) {
  const ctx = document.getElementById('pillarChart');
  if (!ctx) return;

  if (pillarChartInst) pillarChartInst.destroy();

  pillarChartInst = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Love', 'Good At', 'Need', 'Value'],
      datasets: [{
        label: 'Pillar Score',
        data: [ikigai.love, ikigai.good_at, ikigai.need, ikigai.value],
        backgroundColor: PALETTE.pillars.map(c => c + '22'),
        borderColor:     PALETTE.pillars,
        borderWidth:     1.5,
        borderRadius:    0,
        barThickness:    36,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: 'y',
      scales: {
        x: {
          min: 0, max: 100,
          grid: { color: PALETTE.border },
          ticks: { font: { size: 10 }, callback: v => v },
        },
        y: {
          grid: { display: false },
          ticks: { font: { size: 11 }, color: PALETTE.ink },
        }
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => ` ${ctx.parsed.x.toFixed(1)} / 100`
          }
        }
      }
    }
  });
}

/* ── LINE: Ikigai Score Trend ───────────────────────────── */
function renderTrendChart(entries) {
  const ctx = document.getElementById('trendChart');
  if (!ctx) return;

  if (trendChartInst) trendChartInst.destroy();

  const labels = entries.map((e, i) => e.date || `Entry ${i + 1}`);
  const values = entries.map(e => e.ikigai?.ikigai_score ?? 0);

  trendChartInst = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Ikigai Score',
        data: values,
        borderColor:     PALETTE.red,
        borderWidth:     2,
        backgroundColor: 'rgba(176,58,46,0.06)',
        fill: true,
        tension: 0.35,
        pointBackgroundColor: PALETTE.red,
        pointBorderColor:     PALETTE.paper,
        pointRadius:     4,
        pointHoverRadius: 6,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          min: 0, max: 100,
          grid: { color: PALETTE.border },
          ticks: { font: { size: 10 } },
        },
        x: {
          grid: { display: false },
          ticks: { font: { size: 9 }, maxRotation: 30 },
        }
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => ` Ikigai: ${ctx.parsed.y.toFixed(1)}`
          }
        }
      }
    }
  });
}