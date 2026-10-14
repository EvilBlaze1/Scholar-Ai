
import { useCallback, useEffect, useState } from 'react';
import api from '../api/client';
import { Icon } from '../components/Icons';

const STATUSES = [
  { value: 'APPLIED', label: 'Applied' },
  { value: 'UNDER_REVIEW', label: 'Under Review' },
  { value: 'SELECTED', label: 'Selected' },
  { value: 'REJECTED', label: 'Rejected' },
];

function formatDate(value) {
  if (!value) return 'Date not recorded';

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return value;

  return date.toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}

function getScholarshipName(item) {
  return (
    item.scholarship?.name ||
    item.scholarship?.title ||
    item.scholarship_data?.name ||
    item.scholarship_data?.title ||
    item.scholarship_name ||
    item.scholarship_id ||
    'Scholarship'
  );
}

export default function Applications() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [updatingId, setUpdatingId] = useState(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [filter, setFilter] = useState('ALL');

  const loadApplications = useCallback(async () => {
    setLoading(true);
    setError('');

    try {
      const response = await api.get('/applications/');
      const data = response.data;

      setItems(Array.isArray(data) ? data : data?.applications || []);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          'Could not load applications. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadApplications();
  }, [loadApplications]);

  async function updateStatus(item, status) {
    const scholarshipId = item.scholarship_id;

    if (!scholarshipId || status === item.status) return;

    setUpdatingId(scholarshipId);
    setError('');
    setNotice('');

    try {
      const response = await api.put(
        `/applications/${encodeURIComponent(scholarshipId)}`,
        { status }
      );

      const updatedItem =
        response.data && typeof response.data === 'object'
          ? response.data
          : null;

      setItems((current) =>
        current.map((existing) =>
          existing.scholarship_id === scholarshipId
            ? { ...existing, ...(updatedItem || {}), status }
            : existing
        )
      );

      setNotice('Application status updated.');
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          'Could not update the application status. Please try again.'
      );
    } finally {
      setUpdatingId(null);
    }
  }

  const visibleItems =
    filter === 'ALL'
      ? items
      : items.filter((item) => item.status === filter);

  const counts = {
    ALL: items.length,
    APPLIED: items.filter((item) => item.status === 'APPLIED').length,
    UNDER_REVIEW: items.filter((item) => item.status === 'UNDER_REVIEW').length,
    SELECTED: items.filter((item) => item.status === 'SELECTED').length,
    REJECTED: items.filter((item) => item.status === 'REJECTED').length,
  };

  return (
    <section className="page">
      <div className="page-heading">
        <div>
          <p className="kicker">TRACK PROGRESS</p>
          <h1>Applications</h1>
          <p className="muted">
            Keep track of your scholarship applications and their progress.
          </p>
        </div>

        <button
          className="btn btn-secondary"
          type="button"
          onClick={loadApplications}
          disabled={loading}
        >
          <Icon name="refresh-cw" size={16} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="notice notice-error" role="alert">
          {error}
        </div>
      )}

      {notice && (
        <div className="notice notice-success" role="status">
          {notice}
        </div>
      )}

      <div className="application-summary">
        <button
          type="button"
          className={`application-filter ${filter === 'ALL' ? 'active' : ''}`}
          onClick={() => setFilter('ALL')}
        >
          <span>All</span>
          <b>{counts.ALL}</b>
        </button>

        {STATUSES.map((status) => (
          <button
            type="button"
            key={status.value}
            className={`application-filter ${
              filter === status.value ? 'active' : ''
            }`}
            onClick={() => setFilter(status.value)}
          >
            <span>{status.label}</span>
            <b>{counts[status.value]}</b>
          </button>
        ))}
      </div>

      {loading ? (
        <div className="page-loading">
          <div className="spinner" />
          Loading applications...
        </div>
      ) : visibleItems.length ? (
        <div className="application-list">
          {visibleItems.map((item, index) => {
            const scholarshipId = item.scholarship_id || item.id || index;
            const currentStatus = item.status || 'APPLIED';
            const isUpdating = updatingId === item.scholarship_id;

            return (
              <article
                className="application-row"
                key={scholarshipId}
              >
                <div className="provider-logo">S</div>

                <div className="application-main">
                  <b>{getScholarshipName(item)}</b>

                  <span>
                    {item.applied_at
                      ? `Applied ${formatDate(item.applied_at)}`
                      : 'Application date not recorded'}
                  </span>

                  {item.notes && (
                    <span className="muted">{item.notes}</span>
                  )}
                </div>

                <div className="application-actions">
                  <span
                    className={`application-status status-${String(
                      currentStatus
                    ).toLowerCase()}`}
                  >
                    {currentStatus.replaceAll('_', ' ')}
                  </span>

                  <label className="application-status-control">
                    <span className="muted">Update status</span>
                    <select
                      value={currentStatus}
                      disabled={isUpdating}
                      onChange={(event) =>
                        updateStatus(item, event.target.value)
                      }
                      aria-label={`Update status for ${getScholarshipName(item)}`}
                    >
                      <option value="NOT_APPLIED">Not Applied</option>
                      {STATUSES.map((status) => (
                        <option key={status.value} value={status.value}>
                          {status.label}
                        </option>
                      ))}
                    </select>
                  </label>

                  {isUpdating && (
                    <span className="muted">Saving...</span>
                  )}
                </div>
              </article>
            );
          })}
        </div>
      ) : (
        <div className="empty-page small">
          <div className="empty-icon">
            <Icon name="file" size={27} />
          </div>
          <h2>
            {filter === 'ALL'
              ? 'No applications yet'
              : `No ${STATUSES.find((s) => s.value === filter)?.label || ''} applications`}
          </h2>
          <p>
            {filter === 'ALL'
              ? 'When you start tracking a scholarship application, it will appear here.'
              : 'Try another status filter or update an existing application.'}
          </p>

          {filter !== 'ALL' && (
            <button
              className="btn btn-secondary"
              type="button"
              onClick={() => setFilter('ALL')}
            >
              Show all applications
            </button>
          )}
        </div>
      )}
    </section>
  );
}
