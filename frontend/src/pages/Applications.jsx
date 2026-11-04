
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

function formatAmount(amount) {
  if (amount === null || amount === undefined || amount === '') return null;
  return typeof amount === 'number'
    ? `₹${amount.toLocaleString('en-IN')}`
    : String(amount);
}

export default function Applications({ onOpen, onRefreshTracked }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [updatingId, setUpdatingId] = useState(null);
  const [deletingId, setDeletingId] = useState(null);
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

  async function deleteApp(item) {
    const scholarshipId = item.scholarship_id;
    if (!scholarshipId || deletingId) return;

    const name = getScholarshipName(item);
    if (!window.confirm(`Stop tracking "${name}"?`)) {
      return;
    }

    setDeletingId(scholarshipId);
    setError('');
    setNotice('');

    try {
      await api.delete(`/applications/${encodeURIComponent(scholarshipId)}`);
      setItems((current) =>
        current.filter((existing) => existing.scholarship_id !== scholarshipId)
      );
      setNotice('Application removed from tracking.');
      onRefreshTracked?.();
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          'Could not remove application. Please try again.'
      );
    } finally {
      setDeletingId(null);
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
          className="secondary-btn"
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
            const scholarshipName = getScholarshipName(item);
            const provider = item.provider || item.scholarship?.provider || null;
            const amount = formatAmount(
              item.scholarship_amount ?? item.scholarship?.scholarship_amount
            );
            const logoLetter = (provider || scholarshipName || 'S')
              .trim()
              .charAt(0)
              .toUpperCase();

            return (
              <article
                className="application-row"
                key={scholarshipId}
              >
                <div className="provider-logo">{logoLetter}</div>

                <div className="application-main">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                    <b>{scholarshipName}</b>
                    {provider && (
                      <span
                        className="chip chip-outline"
                        style={{ fontSize: '11px', padding: '1px 8px' }}
                      >
                        {provider}
                      </span>
                    )}
                    {amount && (
                      <span
                        className="chip"
                        style={{
                          fontSize: '11px',
                          padding: '1px 8px',
                          background: 'var(--color-surface-hover, #f1f5f9)',
                          color: 'var(--color-primary, #059669)',
                          fontWeight: 600,
                        }}
                      >
                        {amount}
                      </span>
                    )}
                  </div>

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
                      aria-label={`Update status for ${scholarshipName}`}
                    >
                      <option value="NOT_APPLIED">Not Applied</option>
                      {STATUSES.map((status) => (
                        <option key={status.value} value={status.value}>
                          {status.label}
                        </option>
                      ))}
                    </select>
                  </label>

                  {onOpen && (
                    <button
                      type="button"
                      className="secondary-btn"
                      style={{ height: '32px', padding: '0 10px', fontSize: '12px' }}
                      onClick={() =>
                        onOpen(
                          item.scholarship || {
                            id: scholarshipId,
                            scholarship_id: scholarshipId,
                            name: scholarshipName,
                            provider,
                            scholarship_amount: item.scholarship_amount,
                          }
                        )
                      }
                    >
                      Details
                    </button>
                  )}

                  <button
                    type="button"
                    className="icon-btn"
                    style={{
                      color: '#ef4444',
                      borderColor: '#fee2e2',
                      background: '#fff5f5',
                    }}
                    title="Stop tracking this application"
                    aria-label={`Remove application for ${scholarshipName}`}
                    onClick={() => deleteApp(item)}
                    disabled={deletingId === scholarshipId}
                  >
                    <Icon name="close" size={15} />
                  </button>

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
