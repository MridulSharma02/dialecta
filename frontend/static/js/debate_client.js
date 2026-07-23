// ══ DEBATE_CLIENT.JS — WebSocket client and event routing ══

const DebateClient = (() => {
  let _ws = null;
  let _reconnectTimer = null;

  const WS_URL = 'ws://127.0.0.1:8000/ws/debate';

  // ── Start a debate ─────────────────────────────────────────
  function start(topic, persona) {
    _cleanup();

    const token = Auth.getAccessToken();
    if (!token) {
      _emit('error', { message: 'Not authenticated. Please log in again.' });
      return;
    }

    _ws = new WebSocket(WS_URL);

    _ws.onopen = () => {
      console.log('[DebateClient] WebSocket connected');

      // Step 1 — send JWT as first message (backend expects this)
      _ws.send(JSON.stringify({ token }));

      // Step 2 — send debate config
      setTimeout(() => {
        _ws.send(JSON.stringify({
          topic,
          audience_persona: persona,
        }));
      }, 100);
    };

    _ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        const type = msg.event || msg.type;
        const data = msg.data || msg;
        console.log('[DebateClient] event:', type, data);
        _emit(type, data);
      } catch (err) {
        console.error('[DebateClient] Failed to parse message:', err);
      }
    };

    _ws.onerror = (err) => {
      console.error('[DebateClient] WebSocket error:', err);
      _emit('error', { message: 'Connection error. Please try again.' });
    };

    _ws.onclose = (event) => {
      console.log('[DebateClient] WebSocket closed:', event.code, event.reason);
      if (event.code === 4001) {
        _emit('error', { message: 'Authentication failed. Please log in again.' });
      } else if (event.code === 4002) {
        _emit('error', { message: 'Authentication timeout. Please try again.' });
      }
    };
  }

  // ── Stop / cleanup ─────────────────────────────────────────
  function _cleanup() {
    if (_reconnectTimer) {
      clearTimeout(_reconnectTimer);
      _reconnectTimer = null;
    }
    if (_ws) {
      _ws.onopen = null;
      _ws.onmessage = null;
      _ws.onerror = null;
      _ws.onclose = null;
      if (_ws.readyState === WebSocket.OPEN) {
        _ws.close();
      }
      _ws = null;
    }
  }

  // ── Emit event to the app via CustomEvent ──────────────────
  function _emit(type, data) {
    window.dispatchEvent(new CustomEvent('dialecta:debate-event', {
      detail: { type, data }
    }));
  }

  // ── Public stop ────────────────────────────────────────────
  function stop() {
    _cleanup();
  }

  return { start, stop };
})();