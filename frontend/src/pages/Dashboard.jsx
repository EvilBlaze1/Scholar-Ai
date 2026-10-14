
import { useCallback, useEffect, useState } from 'react';
import { Icon } from '../components/Icons';
import api from '../api/client';
import ScholarshipCard from '../components/ScholarshipCard';

function formatDeadline(value) {
  if (!value) return 'Date not specified';

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return String(value);

  return date.toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}

function getScholarshipName(item) {
  return (
    item.name ||
    item.title ||
    item.scholarship_name ||
    item.scholarship_id ||
    'Scholarship opportunity'
  );
}

function Stat({ label, value, icon, tone }) {
  return (
    <div className="stat-card">
      <div className={`stat-icon ${tone}`}>
        <Icon name={icon} size={19} />
      </div>
      <div>
        <strong>{value ?? 0}</strong>
        <span>{label}</span>
      </div>
    </div>
  );
}

export default function Dashboard({ setPage, onOpen, onSave }) {
  const [data, setData] = useState(null);
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    setError('');

    try {
      const [dashboardResult, applicationResult] = await Promise.allSettled([
        api.get('/dashboard/me'),
        api.get('/applications/'),
      ]);

      if (dashboardResult.status === 'rejected') {
        throw dashboardResult.reason;
      }

      setData(dashboardResult.value.data);
      setApplications(
        applicationResult.status === 'fulfilled'
          ? Array.isArray(applicationResult.value.data)
            ? applicationResult.value.data
            : applicationResult.value.data?.applications || []
          : []
      );
    } catch (err) {
      console.error('Dashboard loading failed:', err);
      setData(null);
      setError(
        err.response?.data?.detail ||
          'Unable to load your dashboard. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  if (loading) {
    return (
      <div className="page-loading">
        <div className="spinner" />
        Loading your dashboard...
      </div>
    );
  }

  if (!data) {
    return (
      <div className="empty-page">
        <div className="empty-icon">
          <Icon name="user" size={28} />
        </div>
        <h2>{error ? 'Dashboard unavailable' : 'Complete your profile first'}</h2>
        <p>
          {error ||
            'Add your academic and personal details so Scholar AI can find relevant scholarships.'}
        </p>

        {error && (
          <button
            type="button"
            className="secondary-btn"
            onClick={loadDashboard}
          >
            Try again
          </button>
        )}

        <button
          type="button"
          className="primary-btn"
          onClick={() => setPage('profile')}
        >
          Complete profile
          <Icon name="arrow" size={17} />
        </button>
      </div>
    );
  }

  const summary = data.summary || {};
  const student = data.student || {};
  const name = student.full_name?.trim().split(/\s+/)[0] || 'there';

  const matches = (data.matches || [])
    .filter((item) => {
      const status = item.eligibility_status || item.status;
      return status !== 'INELIGIBLE';
    })
    .slice(0, 3);

  const upcomingDeadlines = (data.upcoming_deadlines || data.deadlines || [])
    .filter((item) => {
      const value = item.application_deadline || item.deadline;
      if (!value) return false;

      const date = new Date(value);
      return (
        !Number.isNaN(date.getTime()) &&
        date.getTime() >= new Date().setHours(0, 0, 0, 0)
      );
    })
    .sort(
      (a, b) =>
        new Date(a.application_deadline || a.deadline) -
        new Date(b.application_deadline || b.deadline)
    )
    .slice(0, 4);

  const applicationCounts = {
    applied: applications.filter(
      (item) => item.status === 'APPLIED'
    ).length,
    review: applications.filter(
      (item) => item.status === 'UNDER_REVIEW'
    ).length,
    selected: applications.filter(
      (item) => item.status === 'SELECTED'
    ).length,
    rejected: applications.filter(
      (item) => item.status === 'REJECTED'
    ).length,
  };

  return (
    <section className="page">
      <div className="dashboard-hero">
        <div>
          <p className="kicker">YOUR OVERVIEW</p>
          <h1>Good to see you, {name}.</h1>
          <p>
            Track your scholarship opportunities and keep your applications
            moving forward.
          </p>
        </div>

        <button
          type="button"
          className="secondary-btn"
          onClick={() => setPage('profile')}
        >
          <Icon name="user" size={17} />
          Update profile
        </button>
      </div>

      <div className="stats-grid">
        <Stat
          label="Eligible scholarships"
          value={summary.eligible_scholarships}
          icon="check"
          tone="green"
        />
        <Stat
          label="Need verification"
          value={summary.needs_verification}
          icon="file"
          tone="amber"
        />
        <Stat
          label="Saved"
          value={summary.saved_scholarships}
          icon="bookmark"
          tone="blue"
        />
        <Stat
          label="Applications"
          value={summary.applications ?? applications.length}
          icon="file"
          tone="slate"
        />
      </div>

      <div className="section-header">
        <div>
          <p className="kicker">RECOMMENDED FOR YOU</p>
          <h2>Scholarships worth a look</h2>
        </div>

        <button
          type="button"
          className="text-btn"
          onClick={() => setPage('scholarships')}
        >
          View all
          <Icon name="arrow" size={16} />
        </button>
      </div>

      {matches.length > 0 ? (
        <div className="card-grid">
          {matches.map((match, index) => (
            <ScholarshipCard
              key={
                match.scholarship_id ||
                match.id ||
                match._id ||
                index
              }
              item={{
                ...match,
                name: getScholarshipName(match),
              }}
              onOpen={onOpen}
              onSave={onSave}
            />
          ))}
        </div>
      ) : (
        <div className="inline-empty">
          No recommendations yet. Visit Scholarships to discover opportunities
          or update your profile to improve your matches.
          <button
            type="button"
            className="text-btn"
            onClick={() => setPage('scholarships')}
          >
            Discover scholarships
            <Icon name="arrow" size={16} />
          </button>
        </div>
      )}

      <div className="section-header">
        <div>
          <p className="kicker">APPLICATION TRACKER</p>
          <h2>Your progress</h2>
        </div>

        <button
          type="button"
          className="text-btn"
          onClick={() => setPage('applications')}
        >
          Manage applications
          <Icon name="arrow" size={16} />
        </button>
      </div>

      <div className="stats-grid">
        <Stat
          label="Applied"
          value={applicationCounts.applied}
          icon="file"
          tone="blue"
        />
        <Stat
          label="Under review"
          value={applicationCounts.review}
          icon="file"
          tone="amber"
        />
        <Stat
          label="Selected"
          value={applicationCounts.selected}
          icon="check"
          tone="green"
        />
        <Stat
          label="Rejected"
          value={applicationCounts.rejected}
          icon="file"
          tone="slate"
        />
      </div>

      <div className="section-header">
        <div>
          <p className="kicker">DON'T MISS OUT</p>
          <h2>Upcoming deadlines</h2>
        </div>

        <button
          type="button"
          className="text-btn"
          onClick={() => setPage('scholarships')}
        >
          Find scholarships
          <Icon name="arrow" size={16} />
        </button>
      </div>

      {upcomingDeadlines.length > 0 ? (
        <div className="application-list">
          {upcomingDeadlines.map((item, index) => (
            <div
              className="application-row"
              key={item.id || item._id || item.source_url || index}
            >
              <div className="provider-logo">
                <Icon name="calendar" size={19} />
              </div>

              <div className="application-main">
                <b>{getScholarshipName(item)}</b>
                <span>
                  Deadline: {formatDeadline(
                    item.application_deadline || item.deadline
                  )}
                </span>
              </div>

              <button
                type="button"
                className="text-btn"
                onClick={() => onOpen?.(item)}
              >
                View
                <Icon name="arrow" size={16} />
              </button>
            </div>
          ))}
        </div>
      ) : (
        <div className="inline-empty">
          No upcoming deadlines are available in your dashboard data yet.
          Discover scholarships to find opportunities with published deadlines.
        </div>
      )}

      <div className="dashboard-lower">
        <div className="tip-card">
          <div className="tip-icon">
            <Icon name="spark" size={22} />
          </div>

          <div>
            <b>Keep your profile current</b>
            <p>
              Accurate academic and personal details help Scholar AI assess
              scholarship requirements more effectively.
            </p>
          </div>

          <button
            type="button"
            className="icon-btn"
            onClick={() => setPage('profile')}
            aria-label="Update profile"
          >
            <Icon name="arrow" />
          </button>
        </div>
      </div>
    </section>
  );
}
