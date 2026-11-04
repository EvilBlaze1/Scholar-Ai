
import { useCallback, useEffect, useState } from 'react';

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

  // Global state for saved and tracked scholarship IDs
  const [savedIds, setSavedIds] = useState(new Set());
  const [savedCount, setSavedCount] = useState(0);
  const [trackedIds, setTrackedIds] = useState(new Set());

  // Fetch all saved scholarships to populate savedIds Set and count
  const loadSaved = useCallback(async () => {
    if (!token) {
      setSavedIds(new Set());
      setSavedCount(0);
      return;
    }
    try {
      const response = await api.get('/saved-scholarships/');
      const records = Array.isArray(response.data)
        ? response.data
        : response.data?.items || [];

      const ids = new Set();
      records.forEach((rec) => {
        if (rec.scholarship_id) ids.add(String(rec.scholarship_id).trim());
        if (rec.id) ids.add(String(rec.id).trim());
        const snap = rec.scholarship;
        if (snap && typeof snap === 'object') {
          if (snap.id) ids.add(String(snap.id).trim());
          if (snap.scholarship_id) ids.add(String(snap.scholarship_id).trim());
          if (snap.source_url) ids.add(String(snap.source_url).trim());
          if (snap.url) ids.add(String(snap.url).trim());
        }
      });
      setSavedIds(ids);
      setSavedCount(records.length);
    } catch (err) {
      console.error('Failed to load saved scholarships', err);
    }
  }, [token]);

  // Fetch all tracked applications to populate trackedIds Set
  const loadTracked = useCallback(async () => {
    if (!token) {
      setTrackedIds(new Set());
      return;
    }
    try {
      const response = await api.get('/applications/');
      const items = Array.isArray(response.data)
        ? response.data
        : response.data?.applications || [];

      const ids = new Set();
      items.forEach((it) => {
        if (it.scholarship_id) ids.add(String(it.scholarship_id).trim());
        if (it.id) ids.add(String(it.id).trim());
      });
      setTrackedIds(ids);
    } catch (err) {
      console.error('Failed to load tracked applications', err);
    }
  }, [token]);

  // Load user information and sync saved/tracked records
  useEffect(() => {
    if (!token) {
      setUser(null);
      setSavedIds(new Set());
      setTrackedIds(new Set());
      return;
    }

    api
      .get('/auth/me')
      .then((response) => {
        setUser({
          id: response.data.user_id,
          email:
            response.data?.email ||
            localStorage.getItem('scholar_email') ||
            'Student',
        });
        loadSaved();
        loadTracked();
      })
      .catch(() => {
        localStorage.removeItem('scholar_token');
        localStorage.removeItem('scholar_email');

        setToken(null);
        setUser(null);
        setSavedIds(new Set());
        setTrackedIds(new Set());
      });
  }, [token, loadSaved, loadTracked]);

  // Handle successful login
  const login = (loggedInUser) => {
    localStorage.setItem(
      'scholar_email',
      loggedInUser.email
    );

    setUser(loggedInUser);
    setToken(localStorage.getItem('scholar_token'));
    setPage('dashboard');
    setDetail(null);
  };

  // Log out the current user
  const logout = () => {
    localStorage.removeItem('scholar_token');
    localStorage.removeItem('scholar_email');

    setToken(null);
    setUser(null);
    setSavedIds(new Set());
    setSavedCount(0);
    setTrackedIds(new Set());
    setDetail(null);
    setPage('dashboard');
    setToast('');
  };

  // Open scholarship details
  const open = (scholarship) => {
    setDetail(scholarship);
    setPage('detail');
  };

  // Display a temporary notification
  const showToast = (message) => {
    setToast(message);
    setTimeout(() => {
      setToast('');
    }, 2500);
  };

  // Toggle saving and unsaving a scholarship with optimistic UI update
  const toggleSave = async (scholarship) => {
    if (!scholarship || typeof scholarship !== 'object') {
      showToast('Invalid scholarship data.');
      return;
    }

    const rawId =
      scholarship.id ||
      scholarship.scholarship_id ||
      scholarship.source_url ||
      scholarship.url;

    if (!rawId) {
      showToast('Scholarship ID is missing.');
      return;
    }

    const normalizedId = String(rawId).trim();
    const sourceUrl = scholarship.source_url || scholarship.url;
    const urlStr = sourceUrl ? String(sourceUrl).trim() : null;

    const isCurrentlySaved =
      savedIds.has(normalizedId) ||
      (urlStr && savedIds.has(urlStr));

    if (isCurrentlySaved) {
      // Optimistic Unsave
      setSavedIds((prev) => {
        const next = new Set(prev);
        next.delete(normalizedId);
        if (urlStr) next.delete(urlStr);
        return next;
      });
      setSavedCount((prev) => Math.max(0, prev - 1));
      showToast('Removed from saved scholarships.');

      try {
        await api.delete('/saved-scholarships/', {
          params: { scholarship_id: normalizedId },
        });
        loadSaved();
      } catch (err) {
        // Revert on failure
        loadSaved();
        showToast(
          err.response?.data?.detail || 'Could not remove scholarship.'
        );
      }
    } else {
      // Optimistic Save
      setSavedIds((prev) => {
        const next = new Set(prev);
        next.add(normalizedId);
        if (urlStr) next.add(urlStr);
        return next;
      });
      setSavedCount((prev) => prev + 1);
      showToast('Scholarship saved.');

      try {
        const payload = {
          scholarship_id: normalizedId,
          scholarship: {
            ...scholarship,
            id: normalizedId,
          },
        };
        await api.post('/saved-scholarships/', payload);
        loadSaved();
      } catch (err) {
        if (err.response?.status === 409 || err.data?.already_saved) {
          return;
        }
        // Revert on failure
        loadSaved();
        showToast(
          err.response?.data?.detail || 'Could not save scholarship.'
        );
      }
    }
  };

  // Track scholarship in application tracker
  const trackApplication = async (scholarship) => {
    if (!scholarship || typeof scholarship !== 'object') return;

    const trackId =
      scholarship.id ||
      scholarship.scholarship_id ||
      scholarship.source_url ||
      scholarship.url;

    if (!trackId) {
      showToast('Scholarship ID missing.');
      return;
    }

    const trackIdStr = String(trackId).trim();
    setTrackedIds((prev) => new Set(prev).add(trackIdStr));
    showToast('Added to Application Tracker!');

    try {
      await api.post('/applications/', {
        scholarship_id: trackIdStr,
        status: 'APPLIED',
        applied_at: new Date().toISOString().split('T')[0],
        scholarship_name:
          scholarship.name || scholarship.title || 'Scholarship opportunity',
        provider: scholarship.provider || 'Scholarship Authority',
        scholarship_amount:
          scholarship.scholarship_amount ?? scholarship.amount,
      });
      loadTracked();
    } catch (err) {
      if (err.response?.status === 409) {
        showToast('Already in your application tracker.');
      } else {
        loadTracked();
        showToast(
          err.response?.data?.detail || 'Could not track application.'
        );
      }
    }
  };

  // Show the authentication page when logged out
  if (!token) {
    return <Auth onLogin={login} />;
  }

  // Check if current detail view item is saved/tracked
  const detailId = detail?.id || detail?.scholarship_id || detail?.source_url;
  const isDetailSaved = detailId
    ? savedIds.has(String(detailId).trim()) ||
      (detail.source_url && savedIds.has(String(detail.source_url).trim()))
    : false;
  const isDetailTracked = detailId
    ? trackedIds.has(String(detailId).trim()) ||
      (detail.source_url && trackedIds.has(String(detail.source_url).trim()))
    : false;

  // Render the selected page
  let content;

  if (page === 'dashboard') {
    content = (
      <Dashboard
        setPage={setPage}
        onOpen={open}
        onSave={toggleSave}
        savedIds={savedIds}
        savedCount={savedCount}
      />
    );
  } else if (page === 'scholarships') {
    content = (
      <Scholarships
        onOpen={open}
        onSave={toggleSave}
        savedIds={savedIds}
      />
    );
  } else if (page === 'saved') {
    content = (
      <Saved
        onOpen={open}
        onUnsave={toggleSave}
        savedIds={savedIds}
        onRefreshSaved={loadSaved}
      />
    );
  } else if (page === 'applications') {
    content = (
      <Applications
        onOpen={open}
        onRefreshTracked={loadTracked}
      />
    );
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
        onSave={toggleSave}
        isSaved={isDetailSaved}
        isTracked={isDetailTracked}
        onTrack={trackApplication}
      />
    );
  } else {
    content = (
      <Dashboard
        setPage={setPage}
        onOpen={open}
        onSave={toggleSave}
        savedIds={savedIds}
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
