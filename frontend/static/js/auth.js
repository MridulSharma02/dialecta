// ══ AUTH.JS — Token management and authenticated fetch ══

const Auth = (() => {
  // Access token lives only in JS memory — never localStorage
  let _accessToken = null;

  const BACKEND = 'https://dialecta-backend.onrender.com';

  // ── Store token in memory ──────────────────────────────────
  function setAccessToken(token) {
    _accessToken = token;
  }

  // ── Get current token ──────────────────────────────────────
  function getAccessToken() {
    return _accessToken;
  }

  // ── Clear token (logout) ───────────────────────────────────
  function clearAccessToken() {
    _accessToken = null;
  }

  // ── Authenticated fetch wrapper ────────────────────────────
  async function fetchWithAuth(path, options = {}) {
    const headers = {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    };

    if (_accessToken) {
      headers['Authorization'] = `Bearer ${_accessToken}`;
    }

    let response = await fetch(`${BACKEND}${path}`, {
      ...options,
      headers,
      credentials: 'include', // sends httpOnly refresh cookie
    });

    // If 401 — try to refresh token once
    if (response.status === 401) {
      const refreshed = await _tryRefresh();
      if (refreshed) {
        headers['Authorization'] = `Bearer ${_accessToken}`;
        response = await fetch(`${BACKEND}${path}`, {
          ...options,
          headers,
          credentials: 'include',
        });
      }
    }

    return response;
  }

  // ── Try to refresh access token using httpOnly cookie ──────
  async function _tryRefresh() {
    try {
      const res = await fetch(`${BACKEND}/auth/refresh`, {
        method: 'POST',
        credentials: 'include',
      });
      if (!res.ok) {
        clearAccessToken();
        return false;
      }
      const data = await res.json();
      if (data.data?.access_token) {
        setAccessToken(data.data.access_token);
        return true;
      }
      return false;
    } catch {
      return false;
    }
  }

  // ── Login ──────────────────────────────────────────────────
  async function login(email, password) {
    const res = await fetch(`${BACKEND}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error?.message || 'Login failed');
    setAccessToken(data.data.access_token);
    return data.data;
  }

  // ── Signup ─────────────────────────────────────────────────
  async function signup(email, password, display_name) {
    const res = await fetch(`${BACKEND}/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, display_name }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error?.message || 'Signup failed');
    return data;
  }

  // ── Logout ─────────────────────────────────────────────────
  async function logout() {
    try {
      await fetchWithAuth('/auth/logout', { method: 'POST' });
    } catch {
      // Continue logout even if request fails
    }
    clearAccessToken();
  }

  // ── Get backend base URL ───────────────────────────────────
  function getBackendUrl() {
    return BACKEND;
  }

  // ── Update password (after reset email link) ───────────────
  async function updatePassword(newPassword) {
    const hash = window.location.hash;
    const params = new URLSearchParams(hash.replace('#', '?'));
    const accessToken = params.get('access_token');

    if (!accessToken) throw new Error('No reset token found. Please request a new password reset.');

    const res = await fetch(`${BACKEND}/auth/update-password`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`,
      },
      body: JSON.stringify({ password: newPassword }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error?.message || 'Failed to update password');
    return data;
  }

  // ── OAuth (Google / GitHub) ────────────────────────────────
  async function loginWithOAuth(provider) {
    window.location.href = `${BACKEND}/auth/oauth/${provider}?redirect_to=${encodeURIComponent(window.location.origin)}`;
  }

  return {
    setAccessToken,
    getAccessToken,
    clearAccessToken,
    fetchWithAuth,
    login,
    signup,
    logout,
    getBackendUrl,
    updatePassword,
    loginWithOAuth,
  };
})();