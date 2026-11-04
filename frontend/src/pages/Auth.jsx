import { useState } from 'react';
import api from '../api/client';
import { Icon } from '../components/Icons';

export default function Auth({ onLogin }) {
  const [mode, setMode] = useState('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const submit = async (e) => {
    e.preventDefault();
    setError('');

    const cleanEmail = (email || '').trim().toLowerCase();
    if (!cleanEmail) {
      setError('Please enter your email address.');
      return;
    }

    if (mode === 'register') {
      if (password !== confirm) {
        setError('Passwords do not match.');
        return;
      }
      if (password.length < 8) {
        setError('Password must be at least 8 characters long.');
        return;
      }
    }

    setLoading(true);

    try {
      if (mode === 'register') {
        await api.post('/auth/register', {
          email: cleanEmail,
          password: password,
        });
      }

      const res = await api.post('/auth/login', {
        email: cleanEmail,
        password: password,
      });

      const token = res.data?.access_token;
      if (!token) {
        throw new Error('Authentication token not received.');
      }

      const userEmail = res.data?.user?.email || cleanEmail;
      localStorage.setItem('scholar_token', token);
      localStorage.setItem('scholar_email', userEmail);

      onLogin({
        email: userEmail,
        id: res.data?.user?.id,
      });
    } catch (err) {
      if (err.response) {
        const { status, data } = err.response;
        const detail = data?.detail;

        if (typeof detail === 'string') {
          setError(detail);
        } else if (Array.isArray(detail)) {
          // Pydantic validation error array
          const messages = detail
            .map((item) => item.msg || item.message || JSON.stringify(item))
            .filter(Boolean);
          setError(messages.join('. ') || 'Validation error. Please check your inputs.');
        } else if (status === 401) {
          setError('Invalid email or password. Please verify your credentials and try again.');
        } else if (status === 409) {
          setError('An account with this email already exists. Please sign in instead.');
        } else if (status === 503) {
          setError('Database service temporarily unavailable. Please verify MongoDB connection.');
        } else {
          setError(data?.message || 'Authentication failed. Please try again.');
        }
      } else if (err.code === 'ERR_NETWORK') {
        setError('Cannot connect to backend server. Please verify the backend is running.');
      } else {
        setError(err.message || 'An unexpected error occurred. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const switchMode = (newMode) => {
    setMode(newMode);
    setError('');
    setPassword('');
    setConfirm('');
  };

  return (
    <div className="auth-page">
      <div className="auth-panel auth-brand-panel">
        <div className="auth-brand">
          <div className="brand-mark large">S</div>
          <span>Scholar AI</span>
        </div>
        <div className="auth-copy">
          <p className="kicker">SCHOLARSHIP DISCOVERY</p>
          <h1>Find funding that fits <em>your</em> profile.</h1>
          <p>
            One place to discover scholarships, understand your eligibility,
            and stay on top of every application.
          </p>
        </div>
        <div className="auth-proof">
          <div>
            <strong>Personalized</strong>
            <span>Matches based on your profile</span>
          </div>
          <div>
            <strong>Transparent</strong>
            <span>Clear eligibility reasoning</span>
          </div>
        </div>
      </div>

      <div className="auth-panel auth-form-panel">
        <div className="auth-form-wrap">
          <div className="mobile-auth-brand">
            <div className="brand-mark">S</div>
            <strong>Scholar AI</strong>
          </div>
          <p className="kicker">
            {mode === 'login' ? 'WELCOME BACK' : 'GET STARTED'}
          </p>
          <h2>
            {mode === 'login' ? 'Sign in to your account' : 'Create your account'}
          </h2>
          <p className="muted">
            {mode === 'login'
              ? 'Continue your scholarship search.'
              : 'Build your profile and discover opportunities.'}
          </p>

          {error && (
            <div className="form-error" role="alert">
              {error}
            </div>
          )}

          <form onSubmit={submit}>
            <label>
              Email address
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                autoCapitalize="none"
                autoCorrect="off"
                spellCheck="false"
                required
              />
            </label>

            <label>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>Password</span>
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: 'var(--text-muted, #64748b)',
                    fontSize: '0.8rem',
                    cursor: 'pointer',
                    padding: 0,
                  }}
                >
                  {showPassword ? 'Hide' : 'Show'}
                </button>
              </div>
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={mode === 'register' ? 'At least 8 characters' : 'Enter your password'}
                minLength={mode === 'register' ? 8 : undefined}
                autoComplete={mode === 'register' ? 'new-password' : 'current-password'}
                required
              />
            </label>

            {mode === 'register' && (
              <label>
                Confirm password
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  placeholder="Repeat your password"
                  autoComplete="new-password"
                  required
                />
              </label>
            )}

            <button
              type="submit"
              className="primary-btn wide"
              disabled={loading}
            >
              {loading
                ? 'Please wait...'
                : mode === 'login'
                ? 'Sign in'
                : 'Create account'}
              <Icon name="arrow" size={18} />
            </button>
          </form>

          <div className="switch-auth">
            {mode === 'login' ? (
              <>
                New to Scholar AI?{' '}
                <button type="button" onClick={() => switchMode('register')}>
                  Create an account
                </button>
              </>
            ) : (
              <>
                Already have an account?{' '}
                <button type="button" onClick={() => switchMode('login')}>
                  Sign in
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
