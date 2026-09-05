/**
 * RazorRecover AI - Authentication Handlers
 */
document.addEventListener('DOMContentLoaded', () => {
  const loginForm = document.getElementById('login-form');
  const signupForm = document.getElementById('signup-form');
  const tabLogin = document.getElementById('tab-login');
  const tabSignup = document.getElementById('tab-signup');
  const demoLoginBtn = document.getElementById('btn-demo-login');
  const errorBox = document.getElementById('auth-error-box');

  // Tab switching
  if (tabLogin && tabSignup) {
    tabLogin.addEventListener('click', () => {
      tabLogin.classList.add('active');
      tabSignup.classList.remove('active');
      loginForm.style.display = 'block';
      signupForm.style.display = 'none';
      if (errorBox) errorBox.style.display = 'none';
    });

    tabSignup.addEventListener('click', () => {
      tabSignup.classList.add('active');
      tabLogin.classList.remove('active');
      signupForm.style.display = 'block';
      loginForm.style.display = 'none';
      if (errorBox) errorBox.style.display = 'none';
    });
  }

  // Instant demo login
  if (demoLoginBtn) {
    demoLoginBtn.addEventListener('click', async (e) => {
      e.preventDefault();
      try {
        const res = await API.post('/api/auth/login', {
          email: 'merchant@razorpay.com',
          password: 'demo123'
        });
        if (res.success) {
          window.location.href = '/app';
        } else {
          showError(res.error || 'Failed to authenticate demo account.');
        }
      } catch (err) {
        showError('Could not connect to authentication service.');
      }
    });
  }

  // Handle Login
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const email = document.getElementById('login-email').value;
      const password = document.getElementById('login-password').value;

      try {
        const res = await API.post('/api/auth/login', { email, password });
        if (res.success) {
          window.location.href = '/app';
        } else {
          showError(res.error || 'Invalid email or password.');
        }
      } catch (err) {
        showError('Login request failed.');
      }
    });
  }

  // Handle Signup
  if (signupForm) {
    signupForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const merchant_name = document.getElementById('signup-merchant').value;
      const email = document.getElementById('signup-email').value;
      const password = document.getElementById('signup-password').value;

      try {
        const res = await API.post('/api/auth/signup', { merchant_name, email, password });
        if (res.success) {
          window.location.href = '/app';
        } else {
          showError(res.error || 'Signup failed.');
        }
      } catch (err) {
        showError('Signup request failed.');
      }
    });
  }

  function showError(msg) {
    if (errorBox) {
      errorBox.textContent = msg;
      errorBox.style.display = 'block';
    } else {
      alert(msg);
    }
  }
});

// Global Logout function used in Dashboard: redirects to public landing page
async function handleLogout() {
  try {
    await API.post('/api/auth/logout');
    window.location.replace('/');
  } catch (err) {
    window.location.replace('/');
  }
}
