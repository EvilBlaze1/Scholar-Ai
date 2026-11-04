import { useCallback, useEffect, useMemo, useState } from 'react';
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

function getDaysRemaining(value) {
  if (!value) return null;
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return null;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const diffTime = d.getTime() - today.getTime();
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  return diffDays;
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

function calculateProfileScore(student = {}) {
  if (!student || typeof student !== 'object' || Object.keys(student).length === 0) {
    return 0;
  }

  // Core profile fields supporting both current and legacy attribute aliases
  const checks = [
    Boolean(student.full_name && String(student.full_name).trim()),
    Boolean(student.gender && String(student.gender).trim()),
    Boolean(student.date_of_birth || student.age),
    Boolean(student.course || student.education_level),
    Boolean(student.domicile_state || student.state_of_domicile || student.state),
    Boolean(student.category && String(student.category).trim()),
    (student.annual_family_income != null && student.annual_family_income !== '') || (student.family_income != null && student.family_income !== ''),
    (student.score != null && student.score !== '') || (student.academic_percentage != null && student.academic_percentage !== ''),
  ];

  const completedCount = checks.filter(Boolean).length;
  const total = checks.length;

  if (completedCount === total) {
    return 100;
  }

  return Math.round((completedCount / total) * 100);
}

export default function Dashboard({ setPage, onOpen, onSave, savedIds, savedCount }) {
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

  const student = data?.student || {};
  const summary = data?.summary || {};
  const name = student.full_name?.trim().split(/\s+/)[0] || 'Student';
  const profileScore = useMemo(() => calculateProfileScore(student), [student]);

  const matches = useMemo(() => {
    return (data?.matches || [])
      .filter((item) => {
        const status = item.eligibility_status || item.status;
        return status !== 'INELIGIBLE';
      })
      .slice(0, 3);
  }, [data?.matches]);

  const upcomingDeadlines = useMemo(() => {
    return (data?.upcoming_deadlines || data?.deadlines || [])
      .filter((item) => {
        const value = item.application_deadline || item.deadline;
        if (!value) return false;
        const date = new Date(value);
        return (
          !Number.isNaN(date.getTime()) &&
          date.getTime() >= new Date().setHours(0, 0, 0, 0)
        );
      })
      .sort((a, b) => {
        const aDate = new Date(a.application_deadline || a.deadline);
        const bDate = new Date(b.application_deadline || b.deadline);
        return aDate - bDate;
      })
      .slice(0, 4);
  }, [data]);

  const applicationCounts = useMemo(() => {
    return {
      applied: applications.filter((item) => item.status === 'APPLIED').length,
      review: applications.filter((item) => item.status === 'UNDER_REVIEW').length,
      selected: applications.filter((item) => item.status === 'SELECTED').length,
      rejected: applications.filter((item) => item.status === 'REJECTED').length,
    };
  }, [applications]);

  // Total funding potential calculation (ONLY for eligible or pending verification opportunities)
  const totalFundingEstimate = useMemo(() => {
    let eligibleSum = 0;
    let pendingSum = 0;

    (data?.matches || []).forEach((m) => {
      const status = m.eligibility_status || m.status;
      const amt = m.scholarship_amount ?? m.amount;
      let val = 0;
      if (typeof amt === 'number') {
        val = amt;
      } else if (typeof amt === 'string') {
        const num = parseFloat(amt.replace(/[^0-9.]/g, ''));
        if (!isNaN(num) && num > 100) val = num;
      }

      if (status === 'ELIGIBLE') {
        eligibleSum += val;
      } else if (status === 'NEEDS_VERIFICATION') {
        pendingSum += val;
      }
    });

    if (eligibleSum > 0) {
      return `₹${eligibleSum.toLocaleString('en-IN')}`;
    }
    if (pendingSum > 0) {
      return `₹${pendingSum.toLocaleString('en-IN')}`;
    }
    return '₹0';
  }, [data?.matches]);

  if (loading) {
    return (
      <div className="page-loading">
        <div className="spinner" />
        Loading your personalized dashboard...
      </div>
    );
  }

  if (!data) {
    return (
      <div className="empty-page">
        <div className="empty-icon">
          <Icon name="user" size={28} />
        </div>
        <h2>{error ? 'Dashboard unavailable' : 'Complete your profile to unlock scholarships'}</h2>
        <p>
          {error ||
            'Add your academic degree, state domicile, and income details so Scholar AI can match you with eligible government and private scholarships.'}
        </p>

        <div style={{ display: 'flex', gap: '12px' }}>
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
            Complete profile now
            <Icon name="arrow" size={17} />
          </button>
        </div>
      </div>
    );
  }

  return (
    <section className="page dashboard-page">
      {/* 1. Interactive Hero Showcase Card */}
      <div className="overview-hero-card">
        <div className="hero-left">
          <div className="hero-badge-row">
            <span className="live-pill">
              <span className="pulse-dot" />
              AI Matching Engine Active
            </span>
            {student.course && (
              <span className="student-course-chip">
                🎓 {student.course} {(student.domicile_state || student.state_of_domicile || student.state) ? `• ${student.domicile_state || student.state_of_domicile || student.state}` : ''}
              </span>
            )}
          </div>

          <h1>Welcome back, {name}! 👋</h1>
          <p className="hero-subtitle">
            {summary.eligible_scholarships > 0 ? (
              <>
                Scholar AI discovered{' '}
                <strong>{summary.eligible_scholarships} eligible {summary.eligible_scholarships === 1 ? 'opportunity' : 'opportunities'}</strong>{' '}
                with an estimated funding potential of{' '}
                <strong className="text-emerald">{totalFundingEstimate}</strong>.
              </>
            ) : summary.needs_verification > 0 ? (
              <>
                Scholar AI found{' '}
                <strong>{summary.needs_verification} {summary.needs_verification === 1 ? 'opportunity' : 'opportunities'} pending verification</strong>{' '}
                with a potential funding of{' '}
                <strong className="text-emerald">{totalFundingEstimate}</strong>.
              </>
            ) : (
              <>
                Scholar AI discovered <strong>0 eligible opportunities</strong> matching your current profile. Click <strong>Explore All Matches</strong> or discover live scholarships.
              </>
            )}
          </p>

          <div className="hero-actions">
            <button
              type="button"
              className="primary-btn"
              onClick={() => setPage('scholarships')}
            >
              <Icon name="search" size={16} />
              Explore All Matches
              <Icon name="arrow" size={15} />
            </button>

            <button
              type="button"
              className="secondary-btn"
              onClick={() => setPage('profile')}
            >
              <Icon name="user" size={16} />
              Edit Profile
            </button>
          </div>
        </div>

        {/* Hero Right: Profile Strength Meter */}
        <div className="hero-right">
          <div className="profile-strength-card">
            <div className="strength-header">
              <span>Profile Strength</span>
              <strong className="strength-value">{profileScore}%</strong>
            </div>

            <div className="strength-bar-bg">
              <div
                className="strength-bar-fill"
                style={{ width: `${profileScore}%` }}
              />
            </div>

            <p className="strength-hint">
              {profileScore >= 100
                ? '🎉 100% Complete! Your profile is fully optimized for all matched scholarships.'
                : profileScore >= 80
                ? 'Almost there! Add remaining details to maximize matching accuracy.'
                : profileScore >= 50
                ? 'Add family income or marks to unlock 8+ additional grants.'
                : 'Complete your profile to view 100% verified opportunities.'}
            </p>

            <button
              type="button"
              className="text-btn strength-link"
              onClick={() => setPage('profile')}
            >
              {profileScore >= 100 ? 'View or edit profile details →' : 'Complete profile details (+25% match) →'}
            </button>
          </div>
        </div>
      </div>

      {/* 2. Interactive Clickable Stat Cards */}
      <div className="stats-grid">
        <div
          className="stat-card clickable"
          onClick={() => setPage('scholarships')}
          role="button"
          tabIndex={0}
          title="Click to view all eligible scholarships"
        >
          <div className="stat-icon green">
            <Icon name="check" size={20} />
          </div>
          <div className="stat-info">
            <strong>{summary.eligible_scholarships ?? 0}</strong>
            <span>Eligible Scholarships</span>
            <small className="stat-action-hint">View all eligible →</small>
          </div>
        </div>

        <div
          className="stat-card clickable"
          onClick={() => setPage('scholarships')}
          role="button"
          tabIndex={0}
          title="Click to verify requirements"
        >
          <div className="stat-icon amber">
            <Icon name="file" size={20} />
          </div>
          <div className="stat-info">
            <strong>{summary.needs_verification ?? 0}</strong>
            <span>Need Verification</span>
            <small className="stat-action-hint">Review criteria →</small>
          </div>
        </div>

        <div
          className="stat-card clickable"
          onClick={() => setPage('saved')}
          role="button"
          tabIndex={0}
          title="Click to view your saved bookmarks"
        >
          <div className="stat-icon blue">
            <Icon name="bookmark" size={20} />
          </div>
          <div className="stat-info">
            <strong>
              {typeof savedCount === 'number' && savedCount >= 0
                ? savedCount
                : (summary.saved_scholarships ?? data?.saved_scholarships?.length ?? 0)}
            </strong>
            <span>Saved Bookmarks</span>
            <small className="stat-action-hint">Open saved →</small>
          </div>
        </div>

        <div
          className="stat-card clickable"
          onClick={() => setPage('applications')}
          role="button"
          tabIndex={0}
          title="Click to view application status"
        >
          <div className="stat-icon slate">
            <Icon name="file" size={20} />
          </div>
          <div className="stat-info">
            <strong>{applications.length || summary.applications || 0}</strong>
            <span>Tracked Applications</span>
            <small className="stat-action-hint">Open tracker →</small>
          </div>
        </div>
      </div>

      {/* 3. Recommended Scholarships Section */}
      <div className="section-header">
        <div>
          <p className="kicker">TOP MATCHES</p>
          <h2>Recommended For You</h2>
        </div>

        <button
          type="button"
          className="text-btn"
          onClick={() => setPage('scholarships')}
        >
          View all opportunities
          <Icon name="arrow" size={16} />
        </button>
      </div>

      {matches.length > 0 ? (
        <div className="card-grid">
          {matches.map((match, index) => {
            const matchId = match.scholarship_id || match.id || match._id;
            const matchUrl = match.source_url || match.url;
            const isMatchSaved = Boolean(
              (matchId && savedIds?.has(String(matchId).trim())) ||
              (matchUrl && savedIds?.has(String(matchUrl).trim()))
            );

            return (
              <ScholarshipCard
                key={match.scholarship_id || match.id || match._id || index}
                item={{
                  ...match,
                  name: getScholarshipName(match),
                }}
                onOpen={onOpen}
                onSave={onSave}
                saved={isMatchSaved}
              />
            );
          })}
        </div>
      ) : (
        <div className="inline-empty">
          <p>No recommendations yet. Update your profile details to unlock personalized scholarship matches.</p>
          <button
            type="button"
            className="primary-btn"
            onClick={() => setPage('scholarships')}
            style={{ marginTop: '12px' }}
          >
            Discover scholarships
            <Icon name="arrow" size={16} />
          </button>
        </div>
      )}

      {/* 4. Visual Application Pipeline / Interactive Tracker */}
      <div className="section-header" style={{ marginTop: '36px' }}>
        <div>
          <p className="kicker">APPLICATION PIPELINE</p>
          <h2>Application Progress</h2>
        </div>

        <button
          type="button"
          className="text-btn"
          onClick={() => setPage('applications')}
        >
          Manage tracker
          <Icon name="arrow" size={16} />
        </button>
      </div>

      <div className="pipeline-container">
        <div
          className="pipeline-stage clickable"
          onClick={() => setPage('applications')}
        >
          <div className="stage-top">
            <span className="stage-dot applied" />
            <span className="stage-title">Applied</span>
          </div>
          <strong className="stage-count">{applicationCounts.applied}</strong>
          <span className="stage-desc">Submitted applications</span>
        </div>

        <div className="pipeline-arrow">→</div>

        <div
          className="pipeline-stage clickable"
          onClick={() => setPage('applications')}
        >
          <div className="stage-top">
            <span className="stage-dot review" />
            <span className="stage-title">Under Review</span>
          </div>
          <strong className="stage-count">{applicationCounts.review}</strong>
          <span className="stage-desc">Document verification</span>
        </div>

        <div className="pipeline-arrow">→</div>

        <div
          className="pipeline-stage clickable"
          onClick={() => setPage('applications')}
        >
          <div className="stage-top">
            <span className="stage-dot selected" />
            <span className="stage-title">Selected</span>
          </div>
          <strong className="stage-count">{applicationCounts.selected}</strong>
          <span className="stage-desc">Grants awarded</span>
        </div>

        <div className="pipeline-arrow">→</div>

        <div
          className="pipeline-stage clickable"
          onClick={() => setPage('applications')}
        >
          <div className="stage-top">
            <span className="stage-dot rejected" />
            <span className="stage-title">Archived</span>
          </div>
          <strong className="stage-count">{applicationCounts.rejected}</strong>
          <span className="stage-desc">Past applications</span>
        </div>
      </div>

      {/* 5. Upcoming Deadlines Urgency List */}
      <div className="section-header" style={{ marginTop: '36px' }}>
        <div>
          <p className="kicker">DON'T MISS OUT</p>
          <h2>Upcoming Deadlines</h2>
        </div>

        <button
          type="button"
          className="text-btn"
          onClick={() => setPage('scholarships')}
        >
          Browse all
          <Icon name="arrow" size={16} />
        </button>
      </div>

      {upcomingDeadlines.length > 0 ? (
        <div className="deadlines-list-card">
          {upcomingDeadlines.map((item, index) => {
            const days = getDaysRemaining(item.application_deadline || item.deadline);
            const urgencyClass = days !== null && days <= 7 ? 'urgent-red' : days !== null && days <= 21 ? 'urgent-amber' : 'urgent-slate';

            return (
              <div
                className="deadline-row"
                key={item.id || item._id || item.source_url || index}
              >
                <div className="deadline-icon-wrap">
                  <Icon name="calendar" size={18} />
                </div>

                <div className="deadline-info">
                  <b>{getScholarshipName(item)}</b>
                  <div className="deadline-sub">
                    <span>Deadline: {formatDeadline(item.application_deadline || item.deadline)}</span>
                    {days !== null && (
                      <span className={`urgency-pill ${urgencyClass}`}>
                        {days === 0 ? 'Closes today!' : days === 1 ? '1 day left!' : `${days} days left`}
                      </span>
                    )}
                  </div>
                </div>

                <button
                  type="button"
                  className="view-btn"
                  onClick={() => onOpen?.(item)}
                >
                  View Details
                  <Icon name="arrow" size={14} />
                </button>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="inline-empty">
          No upcoming deadlines found in your dashboard data. Discovered scholarships with published closing dates will appear here.
        </div>
      )}

      {/* 6. AI Readiness Tip Banner (Redesigned, Replaces the broken tip card!) */}
      <div className="ai-tip-banner">
        <div className="tip-badge">
          <Icon name="spark" size={18} />
          <span>AI Insight</span>
        </div>

        <div className="tip-content">
          <h4>Keep Your Profile Updated for Higher Match Accuracy</h4>
          <p>
            Scholarship committees in India award merit-cum-means grants on a rolling basis. Ensure your family income, domicile state, and academic percentage are up-to-date to automatically qualify for newly posted schemes.
          </p>
        </div>

        <button
          type="button"
          className="secondary-btn tip-btn"
          onClick={() => setPage('profile')}
        >
          <Icon name="user" size={15} />
          Update Student Profile
        </button>
      </div>
    </section>
  );
}
