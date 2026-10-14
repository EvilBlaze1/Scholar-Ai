
import { useEffect, useState } from 'react';

import Auth from './pages/Auth';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Scholarships from './pages/Scholarships';
import Profile from './pages/Profile';
import Saved from './pages/Saved';
import Applications from './pages/Applications';
import Settings from './pages/Settings';
import Details from './pages/Details';

import api from './api/client';
import './App.css';

export default function App() {
  const [token, setToken] = useState(
    localStorage.getItem('scholar_token')
  );

  const [user, setUser] = useState(null);
  const [page, setPage] = useState('dashboard');
  const [detail, setDetail] = useState(null);
  const [toast, setToast] = useState('');

  // Load the logged-in user's information.
  useEffect(() => {
    if (!token) {
      setUser(null);
      return;
    }

    api
      .get('/auth/me')
      .then((response) => {
        setUser({
          id: response.data.user_id,
          email:
            localStorage.getItem('scholar_email') ||
            'Student',
        });
      })
      .catch(() => {
        localStorage.removeItem('scholar_token');
        localStorage.removeItem('scholar_email');

        setToken(null);
        setUser(null);
      });
  }, [token]);

  // Handle successful login.
  const login = (loggedInUser) => {
    localStorage.setItem(
      'scholar_email',
      loggedInUser.email
    );

    setUser(loggedInUser);

    setToken(
      localStorage.getItem('scholar_token')
    );

    setPage('dashboard');
    setDetail(null);
  };

  // Log out the current user.
  const logout = () => {
    localStorage.removeItem('scholar_token');
    localStorage.removeItem('scholar_email');

    setToken(null);
    setUser(null);
    setDetail(null);
    setPage('dashboard');
    setToast('');
  };

  // Open scholarship details.
  const open = (scholarship) => {
    setDetail(scholarship);
    setPage('detail');
  };

  // Display a temporary notification.
  const showToast = (message) => {
    setToast(message);

    setTimeout(() => {
      setToast('');
    }, 2500);
  };

  // Save a scholarship, including live web-discovered results.
  const save = async (scholarship) => {
    if (!scholarship || typeof scholarship !== 'object') {
      showToast('Invalid scholarship data.');
      return;
    }

    const scholarshipId =
      scholarship.id ||
      scholarship.scholarship_id;

    if (
      typeof scholarshipId !== 'string' &&
      typeof scholarshipId !== 'number'
    ) {
      showToast('Scholarship ID is missing.');
      return;
    }

    const normalizedId = String(scholarshipId).trim();

    if (!normalizedId) {
      showToast('Scholarship ID is missing.');
      return;
    }

    // Send a snapshot so live web results can be revisited.
    const payload = {
      scholarship: {
        ...scholarship,
        id: normalizedId,
      },
    };

    try {
      const response = await api.post(
        `/saved-scholarships/${encodeURIComponent(normalizedId)}`,
        payload
      );

      if (response.data?.already_saved) {
        showToast('Already saved.');
      } else {
        showToast('Scholarship saved.');
      }
    } catch (error) {
      if (error.response?.status === 409) {
        showToast('Already saved.');
      } else if (error.response?.status === 401) {
        showToast('Session expired. Please log in again.');
      } else {
        showToast(
          error.response?.data?.detail ||
          'Could not save scholarship.'
        );
      }
    }
  };

  // Show the authentication page when logged out.
  if (!token) {
    return <Auth onLogin={login} />;
  }

  // Render the selected page.
  let content;

  if (page === 'dashboard') {
    content = (
      <Dashboard
        setPage={setPage}
        onOpen={open}
        onSave={save}
      />
    );
  } else if (page === 'scholarships') {
    content = (
      <Scholarships
        onOpen={open}
        onSave={save}
      />
    );
  } else if (page === 'saved') {
    content = (
      <Saved
        onOpen={open}
      />
    );
  } else if (page === 'applications') {
    content = <Applications />;
  } else if (page === 'profile') {
    content = (
      <Profile
        onDone={() => setPage('dashboard')}
      />
    );
  } else if (page === 'settings') {
    content = <Settings />;
  } else if (page === 'detail') {
    content = (
      <Details
        scholarship={detail}
        id={detail?.id || detail?.scholarship_id}
        onBack={() => setPage('scholarships')}
        onSave={save}
      />
    );
  } else {
    content = (
      <Dashboard
        setPage={setPage}
        onOpen={open}
        onSave={save}
      />
    );
  }

  return (
    <Layout
      page={page}
      setPage={(nextPage) => {
        setPage(nextPage);
        setDetail(null);
      }}
      user={user}
      onLogout={logout}
    >
      {content}

      {toast && (
        <div
          className="toast"
          role="status"
          aria-live="polite"
        >
          {toast}
        </div>
      )}
    </Layout>
  );
}
