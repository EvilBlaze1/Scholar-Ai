import { useState } from 'react';
import { Icon } from './Icons';

const items = [
  ['dashboard', 'Overview', 'dashboard'],
  ['search', 'Scholarships', 'scholarships'],
  ['bookmark', 'Saved', 'saved'],
  ['file', 'Applications', 'applications'],
  ['user', 'Profile', 'profile'],
];

export default function Layout({ page, setPage, user, onLogout, children }) {
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleNav = (key) => {
    setPage(key);
    setMobileOpen(false);
    document.body.classList.remove('menu-open');
  };

  const toggleMobile = () => {
    setMobileOpen((prev) => {
      const next = !prev;
      if (next) {
        document.body.classList.add('menu-open');
      } else {
        document.body.classList.remove('menu-open');
      }
      return next;
    });
  };

  const closeMobile = () => {
    setMobileOpen(false);
    document.body.classList.remove('menu-open');
  };

  return (
    <div className="app-shell">
      {/* Mobile Drawer Backdrop */}
      {mobileOpen && (
        <div
          className="sidebar-backdrop"
          onClick={closeMobile}
          aria-hidden="true"
        />
      )}

      <aside className={`sidebar ${mobileOpen ? 'open' : ''}`}>
        <div className="brand">
          <div className="brand-mark">S</div>
          <div>
            <strong>Scholar AI</strong>
            <span>Scholarship finder</span>
          </div>
          <button
            type="button"
            className="mobile-close-btn"
            onClick={closeMobile}
            aria-label="Close navigation"
          >
            <Icon name="close" size={18} />
          </button>
        </div>

        <nav className="nav-list">
          {items.map(([icon, label, key]) => (
            <button
              key={key}
              type="button"
              className={`nav-item ${page === key ? 'active' : ''}`}
              onClick={() => handleNav(key)}
            >
              <Icon name={icon} />
              <span>{label}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <button
            type="button"
            className={`nav-item ${page === 'settings' ? 'active' : ''}`}
            onClick={() => handleNav('settings')}
          >
            <Icon name="settings" />
            <span>Settings</span>
          </button>

          <div className="user-mini">
            <div className="avatar">
              {(user?.email || 'S')[0].toUpperCase()}
            </div>
            <div>
              <b>{user?.email?.split('@')[0] || 'Student'}</b>
              <span>Student account</span>
            </div>
            <button
              type="button"
              title="Log out"
              onClick={onLogout}
              aria-label="Log out"
            >
              <Icon name="logout" size={18} />
            </button>
          </div>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <button
            className="mobile-menu"
            type="button"
            onClick={toggleMobile}
            aria-label="Toggle navigation menu"
          >
            <Icon name="menu" size={20} />
          </button>

          <div
            className="top-search"
            onClick={() => handleNav('scholarships')}
            role="button"
            tabIndex={0}
            aria-label="Search scholarships"
          >
            <Icon name="search" size={18} />
            <span>Search scholarships...</span>
            <kbd>⌘ K</kbd>
          </div>

          <div className="top-actions">
            <div className="top-avatar">
              {(user?.email || 'S')[0].toUpperCase()}
            </div>
          </div>
        </header>

        <div className="content">{children}</div>
      </main>
    </div>
  );
}
