/* ═══════════════════════════════════════════════════════════
   IKIGAI — auth.js
   Handles: modal open/close, login, signup, session storage,
            logout, dashboard redirect
   ═══════════════════════════════════════════════════════════ */

const SESSION_KEY = 'ikigai_user';

/* ── SESSION HELPERS ────────────────────────────────────── */
function getSession() {
  try { return JSON.parse(sessionStorage.getItem(SESSION_KEY)); }
  catch { return null; }
}

function saveSession(user) {
  sessionStorage.setItem(SESSION_KEY, JSON.stringify(user));
}

function clearSession() {
  sessionStorage.removeItem(SESSION_KEY);
}

/* ── MODAL CONTROL ──────────────────────────────────────── */
function openModal(tab) {
  const overlay = document.getElementById('auth-modal');
  if (!overlay) return;
  overlay.classList.add('active');
  switchTab(tab || 'login');
  // Focus first input
  setTimeout(() => {
    const firstInput = overlay.querySelector('input:not([type="hidden"])');
    if (firstInput) firstInput.focus();
  }, 300);
}

function closeModal() {
  const overlay = document.getElementById('auth-modal');
  if (overlay) overlay.classList.remove('active');
}

function closeOnOverlay(e) {
  if (e.target.id === 'auth-modal') closeModal();
}

function switchTab(tab) {
  const loginForm  = document.getElementById('form-login');
  const signupForm = document.getElementById('form-signup');
  const tabLogin   = document.getElementById('tab-login');
  const tabSignup  = document.getElementById('tab-signup');

  if (loginForm)  loginForm.style.display  = tab === 'login'  ? '' : 'none';
  if (signupForm) signupForm.style.display = tab === 'signup' ? '' : 'none';
  if (tabLogin)   tabLogin.classList.toggle('active',  tab === 'login');
  if (tabSignup)  tabSignup.classList.toggle('active', tab === 'signup');
  clearAllErrors();
}

/* ── ERROR HELPERS ──────────────────────────────────────── */
function clearAllErrors() {
  document.querySelectorAll('.form-err').forEach(el => {
    el.style.display = 'none'; el.textContent = '';
  });
  const succ = document.getElementById('signup-success');
  if (succ) succ.style.display = 'none';
}

function showErr(id, msg) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = msg || el.textContent;
  el.style.display = 'block';
}

/* ── LOGIN ──────────────────────────────────────────────── */
async function handleLogin() {
  clearAllErrors();
  const email = (document.getElementById('l-email')?.value || '').trim().toLowerCase();
  const pass  =  document.getElementById('l-pass')?.value  || '';

  let ok = true;
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { showErr('l-email-err', 'Enter a valid email.'); ok = false; }
  if (!pass) { showErr('l-pass-err', 'Password is required.'); ok = false; }
  if (!ok) return;

  try {
    const res  = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password: pass }),
    });
    const data = await res.json();

    if (!res.ok) {
      showErr('l-general-err', data.error || 'Login failed.');
      return;
    }
    saveSession(data.user);
    closeModal();
    // Redirect to dashboard
    window.location.href = '/dashboard';
  } catch (e) {
    showErr('l-general-err', 'Network error. Is the server running?');
  }
}

/* ── SIGNUP ─────────────────────────────────────────────── */
async function handleSignup() {
  clearAllErrors();
  const name  = (document.getElementById('s-name')?.value  || '').trim();
  const email = (document.getElementById('s-email')?.value || '').trim().toLowerCase();
  const pass  =  document.getElementById('s-pass')?.value  || '';

  let ok = true;
  if (!name)  { showErr('s-name-err',  'Name is required.'); ok = false; }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { showErr('s-email-err', 'Enter a valid email.'); ok = false; }
  if (pass.length < 6) { showErr('s-pass-err', 'Password must be ≥ 6 characters.'); ok = false; }
  if (!ok) return;

  const btn = document.getElementById('signup-btn');
  if (btn) { btn.disabled = true; btn.textContent = 'Creating…'; }

  try {
    const res  = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, password: pass }),
    });
    const data = await res.json();

    if (!res.ok) {
      showErr('s-general-err', data.error || 'Registration failed.');
      if (btn) { btn.disabled = false; btn.textContent = 'Create Account'; }
      return;
    }

    const succ = document.getElementById('signup-success');
    if (succ) succ.style.display = 'block';

    saveSession(data.user);
    setTimeout(() => { window.location.href = '/dashboard'; }, 900);
  } catch (e) {
    showErr('s-general-err', 'Network error. Is the server running?');
    if (btn) { btn.disabled = false; btn.textContent = 'Create Account'; }
  }
}

/* ── LOGOUT ─────────────────────────────────────────────── */
function doLogout() {
  clearSession();
  window.location.href = '/';
}

/* ── KEYBOARD ───────────────────────────────────────────── */
window.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeModal();
  if (e.key === 'Enter') {
    const modal = document.getElementById('auth-modal');
    if (modal && modal.classList.contains('active')) {
      const loginVisible = document.getElementById('form-login')?.style.display !== 'none';
      if (loginVisible) handleLogin();
      else handleSignup();
    }
  }
});

/* ── DASHBOARD INIT ─────────────────────────────────────── */
/* Called by dashboard.html's predict.js to set up the user */
function getDashboardUser() {
  return getSession();
}