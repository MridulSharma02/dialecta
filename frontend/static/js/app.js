// ══ APP.JS — Root screen router and auth state observer ══

const App = (() => {
  let currentScreen = 'welcome';

  // ── Screen references ──────────────────────────────────────
  const screens = {
    welcome: document.getElementById('screen-welcome'),
    auth:    document.getElementById('screen-auth'),
    app:     document.getElementById('screen-app'),
    report:  document.getElementById('screen-report'),
  };

  // ── Navigate to a screen ───────────────────────────────────
  function navigateTo(name) {
    if (!screens[name]) return;

    // Deactivate all
    Object.values(screens).forEach(s => s.classList.remove('active'));

    // Activate target
    screens[name].classList.add('active');
    currentScreen = name;

    console.log('[App] navigated to:', name);
  }

  // ── Boot sequence ──────────────────────────────────────────
  function boot() {
    // 1. Start welcome scene immediately
    WelcomeScene.init();
    LearnMore.init();

    // 2. Check if user already has a valid token
    const token = Auth.getAccessToken();
    if (token) {
      // Already logged in — go straight to app
      navigateTo('app');
      SceneDebate.init();
      UIApp.init();
    } else {
      // Show welcome screen
      navigateTo('welcome');
    }

    // 3. Wire welcome buttons
    document.getElementById('btn-get-started').addEventListener('click', () => {
      navigateTo('auth');
      UIAuth.init();
    });

    document.getElementById('btn-learn-more').addEventListener('click', () => {
      LearnMore.open();
    });

    // 4. Listen for auth success event (fired by UIAuth after login)
    window.addEventListener('dialecta:auth-success', () => {
      WelcomeScene.destroy();
      navigateTo('app');
      SceneDebate.init();
      UIApp.init();
    });

    // 5. Listen for logout event (fired by UIApp after logout)
    window.addEventListener('dialecta:logout', () => {
      navigateTo('welcome');
      WelcomeScene.init();
    });

    // 6. Listen for report open/close
    window.addEventListener('dialecta:open-report', () => {
      navigateTo('report');
    });

    window.addEventListener('dialecta:close-report', () => {
      navigateTo('app');
    });
  }

  // ── Public ─────────────────────────────────────────────────
  return { boot, navigateTo };
})();

// Boot when DOM is ready
document.addEventListener('DOMContentLoaded', () => App.boot());