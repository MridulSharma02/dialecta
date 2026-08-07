// ══ UI_APP.JS — Main app screen DOM and state ══

const UIApp = (() => {
  let _initialized = false;
  let _currentDebateId = null;
  let _scoreA = 0;
  let _scoreB = 0;
  let _currentSubIndex = 0;
  let _totalSubs = 0;

  function init() {
    if (_initialized) return;
    _initialized = true;

    // ── Element refs ─────────────────────────────────────────
    const btnStartDebate = document.getElementById('btn-start-debate');
    const btnLogout      = document.getElementById('btn-logout');
    const btnNewDebate   = document.getElementById('btn-new-debate');
    const btnViewReport  = document.getElementById('btn-view-report');
    const btnDlPdf       = document.getElementById('btn-dl-pdf');
    const btnDlJson      = document.getElementById('btn-dl-json');
    const btnDlMd        = document.getElementById('btn-dl-md');

    // ── Start Debate ──────────────────────────────────────────
    btnStartDebate.addEventListener('click', () => {
      const topic   = document.getElementById('topic-input').value.trim();
      const persona = document.getElementById('persona-select').value;

      if (!topic) {
        _log('Please enter a debate topic.', 'agent-orchestrator');
        return;
      }

      _resetState();
      _showProgress(true);
      _collapseSidebar();

      // Start WebSocket debate
      DebateClient.start(topic, persona);
    });

    // ── Logout ────────────────────────────────────────────────
    btnLogout.addEventListener('click', async () => {
      await Auth.logout();
      window.dispatchEvent(new Event('dialecta:logout'));
    });

    // ── New Debate ────────────────────────────────────────────
    btnNewDebate.addEventListener('click', () => {
      _hideReportPanel();
      _expandSidebar();
      _showProgress(false);
      _resetState();
    });

    // ── View Full Report ──────────────────────────────────────
    btnViewReport.addEventListener('click', () => {
      if (_currentDebateId) {
        UIReport.load(_currentDebateId);
        window.dispatchEvent(new Event('dialecta:open-report'));
      }
    });

    // ── Download buttons ──────────────────────────────────────
    btnDlPdf.addEventListener('click',  () => _download('pdf'));
    btnDlJson.addEventListener('click', () => _download('json'));
    btnDlMd.addEventListener('click',   () => _download('markdown'));

    // ── Listen for debate events from DebateClient ────────────
    window.addEventListener('dialecta:debate-event', (e) => {
      _handleDebateEvent(e.detail);
    });

    // ── Load history ──────────────────────────────────────────
    _loadHistory();
  }

  // ── Handle incoming WebSocket events ──────────────────────
  function _handleDebateEvent(event) {
    const { type, data } = event;

    switch (type) {

      case 'debate_started':
        _log(`Debate started: ${data.topic}`, 'agent-orchestrator');
        break;

      case 'sub_debate_started':
        _currentSubIndex = data.sub_index;
        _totalSubs = data.total_subs;
        _log(`Sub-debate ${data.sub_index}: ${data.sub_topic}`, 'agent-decomposer');
        _updateProgress(data.sub_index, data.total_subs, 0, 0);
        break;

      case 'round_started':
        _log(`Round ${data.round_number} started`, 'agent-orchestrator');
        _updateProgress(_currentSubIndex, _totalSubs, data.round_number, 5);
        break;

      case 'agent_thinking':
        if (SceneDebate) SceneDebate.pulseAgent(_agentIdMap(data.agent));
        break;

      case 'argument_made':
        _log(`Debater ${data.debater}: ${data.argument?.slice(0, 80)}...`, 'agent-orchestrator');
        if (SceneDebate) {
          if (data.debater === 'A') SceneDebate.fireParticle('fact_checker', 'debater_a');
          if (data.debater === 'B') SceneDebate.fireParticle('debater_a', 'debater_b');
        }
        break;

      case 'round_scored':
        _scoreA = data.scores?.debater_a?.total ?? data.total_a ?? _scoreA;
        _scoreB = data.scores?.debater_b?.total ?? data.total_b ?? _scoreB;
        _updateScoreBar(_scoreA, _scoreB);
        _log(`Round scored — A: ${_scoreA.toFixed(1)} | B: ${_scoreB.toFixed(1)}`, 'agent-judge');
        if (SceneDebate) SceneDebate.fireParticle('debater_b', 'judge');
        break;

      case 'bias_detected':
        _log(`Bias detected in ${data.speaker}: ${data.flags?.join(', ')}`, 'agent-bias');
        break;

      case 'fact_check_complete':
        _log(`Fact check: ${data.verified_count} verified, ${data.failed_count} failed`, 'agent-fact');
        break;

      case 'devil_fired':
        _log(`Devil's Advocate helping ${data.target_debater}`, 'agent-devil');
        break;

      case 'critic_fired':
        _log(`Critic rewrote rubric — round ${data.round_number}`, 'agent-critic');
        break;

      case 'memory_stored':
        _log(`Memory stored novelty: ${(data.novelty_score * 100).toFixed(0)}%`, 'agent-memory');
        break;

      case 'summariser_complete':
        _log(`Summary: ${data.summary?.slice(0, 80)}...`, 'agent-summariser');
        break;

      case 'audience_reacted':
        _log(`Audience (${data.persona}): ${data.reaction?.slice(0, 80)}...`, 'agent-audience');
        if (SceneDebate) SceneDebate.fireParticle('summariser', 'audience_agent');
        break;

      case 'round_summary':
        _log(`Summary: ${data.summary?.slice(0, 80)}...`, 'agent-summariser');
        if (SceneDebate) SceneDebate.fireParticle('judge', 'summariser');
        break;

      case 'rubric_updated':
        _log(`Critic rewrote rubric`, 'agent-critic');
        if (SceneDebate) SceneDebate.fireParticle('judge', 'critic');
        break;

      case 'debate_complete':
        _currentDebateId = data.debate_id;
        _log(`Debate complete! Winner: ${data.winner}`, 'agent-orchestrator');
        _showProgress(false);
        _expandSidebar();
        _showReportPanel(data);
        _loadHistory();
        if (SceneDebate) SceneDebate.onDebateComplete();
        break;

      case 'error':
        _log(`Error: ${data.message}`, 'agent-orchestrator');
        _showProgress(false);
        _expandSidebar();
        break;
    }
  }

  // ── Log entry ──────────────────────────────────────────────
  function _log(message, agentClass = '') {
    const entries = document.getElementById('log-entries');
    const div = document.createElement('div');
    div.className = `log-entry ${agentClass}`;
    div.textContent = message;
    entries.appendChild(div);
    entries.scrollTop = entries.scrollHeight;

    // Keep max 100 entries
    while (entries.children.length > 100) {
      entries.removeChild(entries.firstChild);
    }
  }

  // ── Score bar ──────────────────────────────────────────────
  function _updateScoreBar(a, b) {
    const total = a + b || 1;
    const pctA = (a / total) * 100;
    const pctB = (b / total) * 100;
    document.getElementById('score-fill-a').style.width = `${pctA}%`;
    document.getElementById('score-fill-b').style.width = `${pctB}%`;
  }

  // ── Progress bar ───────────────────────────────────────────
  function _updateProgress(subN, subTotal, roundN, roundMax) {
    const pct = subTotal > 0 ? ((subN - 1) / subTotal) * 100 : 0;
    document.getElementById('progress-fill').style.width = `${pct}%`;
    document.getElementById('progress-text').textContent =
      `Sub-debate ${subN}/${subTotal} · Round ${roundN}/${roundMax}`;
  }

  function _showProgress(show) {
    document.getElementById('progress-bar').classList.toggle('visible', show);
  }

  // ── Sidebar ────────────────────────────────────────────────
  function _collapseSidebar() {
    document.getElementById('sidebar').classList.add('collapsed');
  }

  function _expandSidebar() {
    document.getElementById('sidebar').classList.remove('collapsed');
  }

  // ── Report panel ───────────────────────────────────────────
  function _showReportPanel(data) {
    const panel = document.getElementById('report-panel');
    const summary = document.getElementById('report-summary');

    summary.innerHTML = `
      <table style="width:100%;font-size:12px;border-collapse:collapse;">
        <tr><td style="color:var(--color-text-dim);padding:4px 0;">Winner</td>
            <td style="color:var(--color-text);text-align:right;">${data.winner || 'N/A'}</td></tr>
        <tr><td style="color:var(--color-text-dim);padding:4px 0;">Quality Score</td>
            <td style="color:var(--color-text);text-align:right;">${data.quality_score?.toFixed(2) || 'N/A'}</td></tr>
        <tr><td style="color:var(--color-text-dim);padding:4px 0;">Total Rounds</td>
            <td style="color:var(--color-text);text-align:right;">${data.total_rounds || 'N/A'}</td></tr>
      </table>
    `;

    panel.classList.remove('hidden');
  }

  function _hideReportPanel() {
    document.getElementById('report-panel').classList.add('hidden');
  }

  // ── Download ───────────────────────────────────────────────
  async function _download(format) {
    if (!_currentDebateId) return;
    try {
      const res = await Auth.fetchWithAuth(
        `/reports/${_currentDebateId}/download?format=${format}`
      );
      if (!res.ok) throw new Error('Download failed');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `dialecta_report_${_currentDebateId.slice(0, 8)}.${format === 'markdown' ? 'md' : format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      _log(`Download failed: ${err.message}`, 'agent-orchestrator');
    }
  }

  // ── History ────────────────────────────────────────────────
  async function _loadHistory() {
    try {
      const res = await Auth.fetchWithAuth('/reports/history?limit=5');
      if (!res.ok) return;
      const data = await res.json();
      const list = document.getElementById('history-list');
      list.innerHTML = '';
      (data.debates || []).forEach(d => {
        const div = document.createElement('div');
        div.className = 'history-item';
        div.textContent = d.topic;
        div.title = d.topic;
        div.addEventListener('click', () => {
          _currentDebateId = d.debate_id;
          _showReportPanel(d);
        });
        list.appendChild(div);
      });
    } catch {
      // Silently fail — history is not critical
    }
  }

  // ── Reset state ────────────────────────────────────────────
  function _resetState() {
    _scoreA = 0;
    _scoreB = 0;
    _currentSubIndex = 0;
    _totalSubs = 0;
    _currentDebateId = null;
    _updateScoreBar(0, 0);
    document.getElementById('log-entries').innerHTML = '';
  }

  // ── Agent helpers ──────────────────────────────────────────
  function _formatAgent(name) {
    return (name || '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  }

  function _agentClass(name) {
    const map = {
      orchestrator: 'orchestrator',
      debater_a: 'debater-a', debater_b: 'debater-b',
      judge: 'judge', bias_detector: 'bias',
      devils_advocate: 'devil', critic: 'critic',
      fact_checker: 'fact', memory_agent: 'memory',
      summariser: 'summariser', topic_decomposer: 'decomposer',
      audience_agent: 'audience', meta_evaluator: 'meta',
    };
    return map[name] || 'orchestrator';
  }

  function _agentIdMap(name) {
    const map = {
      'FactChecker': 'fact_checker',
      'DebaterA': 'debater_a',
      'DebaterB': 'debater_b',
      'Judge': 'judge',
      'BiasDetector': 'bias_detector',
      'Critic': 'critic',
      'MemoryAgent': 'memory_agent',
      'Summariser': 'summariser',
      'AudienceAgent': 'audience_agent',
      'TopicDecomposer': 'topic_decomposer',
      'MetaEvaluator': 'meta_evaluator',
      'DevilsAdvocate': 'devils_advocate',
      'Orchestrator': 'orchestrator',
    };
    return map[name] || name.toLowerCase();
  }

  return { init };
})();