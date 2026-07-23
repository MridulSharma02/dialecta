// ══ UI_REPORT.JS — Full report overlay ══

const UIReport = (() => {

  // ── Load and render report ─────────────────────────────────
  async function load(debateId) {
    const container = document.getElementById('report-content');
    container.innerHTML = '<p style="color:var(--color-text-mid);text-align:center;padding:48px;">Loading report...</p>';

    try {
      const res = await Auth.fetchWithAuth(`/reports/${debateId}/download?format=json`);
      if (!res.ok) throw new Error('Failed to load report');
      const raw = await res.json();
      const report = raw.dialecta_report;
      _render(report, debateId);
    } catch (err) {
      container.innerHTML = `<p style="color:var(--color-accent-b);text-align:center;padding:48px;">
        Failed to load report: ${err.message}</p>`;
    }
  }

  // ── Render report into DOM ─────────────────────────────────
  function _render(report, debateId) {
    const container = document.getElementById('report-content');
    const debate = report.debate || {};
    const summary = report.summary || {};

    container.innerHTML = `
      ${_renderDownloadBar(debateId)}
      ${_renderHeader(debate, summary)}
      ${_renderSection('Summary Statistics', _renderSummaryTable(summary), true)}
      ${(report.sub_debates || []).map((sub, i) =>
          _renderSection(`Sub-Debate ${i + 1}: ${sub.sub_topic}`, _renderSubDebate(sub))
        ).join('')}
      ${report.agent_events?.length
          ? _renderSection('Agent Events Log', _renderEventsTable(report.agent_events))
          : ''}
    `;

    // ── Wire collapsible sections ────────────────────────────
    container.querySelectorAll('.report-section-header').forEach(header => {
      header.addEventListener('click', () => {
        header.parentElement.classList.toggle('open');
      });
    });

    // ── Wire close button ────────────────────────────────────
    document.getElementById('btn-close-report').addEventListener('click', () => {
      window.dispatchEvent(new Event('dialecta:close-report'));
    });
  }

  // ── Download bar ───────────────────────────────────────────
  function _renderDownloadBar(debateId) {
    return `
      <div class="report-download-bar">
        <button class="btn-download" onclick="UIReport.download('${debateId}','pdf')">⬇ PDF</button>
        <button class="btn-download" onclick="UIReport.download('${debateId}','json')">⬇ JSON</button>
        <button class="btn-download" onclick="UIReport.download('${debateId}','markdown')">⬇ MD</button>
      </div>
    `;
  }

  // ── Header ─────────────────────────────────────────────────
  function _renderHeader(debate, summary) {
    const winnerClass = debate.winner === 'debater_a' ? 'debater-a'
                      : debate.winner === 'debater_b' ? 'debater-b'
                      : 'tie';
    return `
      <div class="report-heading">
        <h1>DIALECTA</h1>
        <div class="report-topic">${debate.topic || 'Unknown Topic'}</div>
        <div class="report-meta">
          Generated ${new Date().toLocaleDateString()} ·
          Quality Score: ${debate.quality_score?.toFixed(2) || 'N/A'}
        </div>
        <div style="text-align:center;">
          <span class="winner-badge ${winnerClass}">
            Winner: ${(debate.winner || 'unknown').replace('_', ' ').toUpperCase()}
          </span>
        </div>
      </div>
    `;
  }

  // ── Collapsible section ────────────────────────────────────
  function _renderSection(title, body, openByDefault = false) {
    return `
      <div class="report-section ${openByDefault ? 'open' : ''}">
        <div class="report-section-header">
          <span class="report-section-title">${title}</span>
          <span class="report-section-chevron">▼</span>
        </div>
        <div class="report-section-body">${body}</div>
      </div>
    `;
  }

  // ── Summary table ──────────────────────────────────────────
  function _renderSummaryTable(summary) {
    const rows = [
      ['Total Sub-Debates', summary.total_sub_debates],
      ['Total Rounds',      summary.total_rounds],
      ['Debater A Wins',    summary.debater_a_wins],
      ['Debater B Wins',    summary.debater_b_wins],
      ['Ties',              summary.ties],
      ['Overall Winner',    (summary.overall_winner || '').replace('_', ' ')],
      ['Quality Score',     summary.quality_score?.toFixed(2) || 'N/A'],
    ];
    return `
      <table class="report-table">
        <tr><th>Metric</th><th>Value</th></tr>
        ${rows.map(([k, v]) => `<tr><td>${k}</td><td>${v}</td></tr>`).join('')}
      </table>
    `;
  }

  // ── Sub-debate ─────────────────────────────────────────────
  function _renderSubDebate(sub) {
    return `
      <table class="report-table" style="margin-bottom:16px;">
        <tr><th>Field</th><th>Value</th></tr>
        <tr><td>Stance A</td><td>${sub.stance_a || 'N/A'}</td></tr>
        <tr><td>Stance B</td><td>${sub.stance_b || 'N/A'}</td></tr>
        <tr><td>Winner</td><td>${(sub.winner || 'N/A').replace('_', ' ')}</td></tr>
        <tr><td>Rounds Run</td><td>${sub.rounds_run || 0}</td></tr>
      </table>
      ${(sub.rounds || []).map(rnd => _renderRound(rnd)).join('')}
    `;
  }

  // ── Round ──────────────────────────────────────────────────
  function _renderRound(rnd) {
    const winnerA = rnd.round_winner === 'debater_a';
    const winnerB = rnd.round_winner === 'debater_b';
    return `
      <div class="round-label">Round ${rnd.round_number}</div>
      <div class="score-pills">
        <span class="score-pill ${winnerA ? 'winner-a' : ''}">
          Debater A: ${rnd.scores?.debater_a ?? 'N/A'}
        </span>
        <span class="score-pill ${winnerB ? 'winner-b' : ''}">
          Debater B: ${rnd.scores?.debater_b ?? 'N/A'}
        </span>
      </div>
      ${rnd.key_insight
        ? `<div class="insight-box">💡 ${rnd.key_insight}</div>`
        : ''}
      ${(rnd.arguments || []).map(arg => `
        <div class="report-argument ${arg.speaker === 'debater_a' ? 'debater-a' : 'debater-b'}">
          <div class="arg-speaker">${(arg.speaker || '').replace('_', ' ').toUpperCase()}</div>
          ${arg.content || ''}
        </div>
      `).join('')}
    `;
  }

  // ── Agent events table ─────────────────────────────────────
  function _renderEventsTable(events) {
    return `
      <table class="report-table">
        <tr><th>Agent</th><th>Event</th><th>Details</th></tr>
        ${events.map(e => `
          <tr>
            <td>${e.agent_name || 'N/A'}</td>
            <td>${e.event_type || 'N/A'}</td>
            <td>${String(e.details || '').slice(0, 100)}</td>
          </tr>
        `).join('')}
      </table>
    `;
  }

  // ── Download from report view ──────────────────────────────
  async function download(debateId, format) {
    try {
      const res = await Auth.fetchWithAuth(
        `/reports/${debateId}/download?format=${format}`
      );
      if (!res.ok) throw new Error('Download failed');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `dialecta_report_${debateId.slice(0, 8)}.${format === 'markdown' ? 'md' : format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Download failed:', err);
    }
  }

  return { load, download };
})();