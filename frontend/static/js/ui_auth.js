// ══ UI_AUTH.JS — Auth screen DOM and transitions ══

const UIAuth = (() => {
  let _initialized = false;

  function init() {
    if (_initialized) return;
    _initialized = true;

    // ── Element refs ─────────────────────────────────────────
    const formLogin     = document.getElementById('form-login');
    const formSignup    = document.getElementById('form-signup');
    const linkToSignup  = document.getElementById('link-to-signup');
    const linkToLogin   = document.getElementById('link-to-login');
    const btnLogin      = document.getElementById('btn-login');
    const btnSignup     = document.getElementById('btn-signup');
    const loginError    = document.getElementById('login-error');
    const signupError   = document.getElementById('signup-error');

    // ── Switch between login and signup ──────────────────────
    linkToSignup.addEventListener('click', (e) => {
      e.preventDefault();
      formLogin.classList.remove('active');
      formSignup.classList.add('active');
      _clearErrors();
    });

    linkToLogin.addEventListener('click', (e) => {
      e.preventDefault();
      formSignup.classList.remove('active');
      formLogin.classList.add('active');
      _clearErrors();
    });

    // ── Login ─────────────────────────────────────────────────
    btnLogin.addEventListener('click', async () => {
      const email    = document.getElementById('login-email').value.trim();
      const password = document.getElementById('login-password').value;

      if (!email || !password) {
        loginError.textContent = 'Please fill in all fields.';
        return;
      }

      _setLoading(btnLogin, true);
      loginError.textContent = '';

      try {
        await Auth.login(email, password);
        // Fire global event — app.js will handle navigation
        window.dispatchEvent(new Event('dialecta:auth-success'));
      } catch (err) {
        loginError.textContent = err.message || 'Login failed. Please try again.';
      } finally {
        _setLoading(btnLogin, false);
      }
    });

    // ── Signup ────────────────────────────────────────────────
    btnSignup.addEventListener('click', async () => {
      const name     = document.getElementById('signup-name').value.trim();
      const email    = document.getElementById('signup-email').value.trim();
      const password = document.getElementById('signup-password').value;

      if (!email || !password) {
        signupError.textContent = 'Please fill in all fields.';
        return;
      }

      _setLoading(btnSignup, true);
      signupError.textContent = '';

      try {
        await Auth.signup(email, password, name);
        signupError.style.color = 'var(--color-green)';
        signupError.textContent = 'Check your email for a verification link.';
      } catch (err) {
        signupError.style.color = 'var(--color-accent-b)';
        signupError.textContent = err.message || 'Signup failed. Please try again.';
      } finally {
        _setLoading(btnSignup, false);
      }
    });

    // ── Enter key support ─────────────────────────────────────
    document.getElementById('login-password').addEventListener('keydown', (e) => {
      if (e.key === 'Enter') btnLogin.click();
    });

    document.getElementById('signup-password').addEventListener('keydown', (e) => {
      if (e.key === 'Enter') btnSignup.click();
    });
  }

  // ── Helpers ───────────────────────────────────────────────
  function _setLoading(btn, loading) {
    btn.disabled = loading;
    btn.textContent = loading ? 'Please wait...' : (
      btn.id === 'btn-login' ? 'Sign In' : 'Create Account'
    );
  }

  function _clearErrors() {
    document.getElementById('login-error').textContent = '';
    document.getElementById('signup-error').textContent = '';
  }

  return { init };
})();