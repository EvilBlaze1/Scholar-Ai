
import { useCallback, useEffect, useState } from 'react';
import api from '../api/client';
import { Icon } from '../components/Icons';

function formatDeadline(value) {
  if (!value) return 'No deadline listed';

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return String(value);

  return date.toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}

function getAmount(scholarship) {
  const amount =
    scholarship.scholarship_amount ?? scholarship.amount;

  if (amount === null || amount === undefined || amount === '') {
    return null;
  }

  return typeof amount === 'number'
    ? `₹${amount.toLocaleString('en-IN')}`
    : String(amount);
}

function getScholarshipId(scholarship) {
  return scholarship.scholarship_id || scholarship.id;
}

export default function Saved({ onOpen, onUnsave, savedIds, onRefreshSaved }) {
  const [saved, setSaved] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [removingId, setRemovingId] = useState(null);

  const loadSavedScholarships = useCallback(async () => {
    setLoading(true);
    setError('');

    try {
      const response = await api.get('/saved-scholarships/');
      const records = Array.isArray(response.data)
        ? response.data
        : response.data?.items || [];

      const scholarships = await Promise.all(
        records.map(async (record) => {
          const scholarshipId = record.scholarship_id || record.id;

          if (
            record.scholarship &&
            typeof record.scholarship === 'object'
          ) {
            return {
              ...record.scholarship,
              id: record.scholarship.id || scholarshipId,
              scholarship_id: scholarshipId,
              saved_record_id: record.id,
              saved_at: record.saved_at,
            };
          }

          if (!scholarshipId) {
            return {
              name: 'Saved scholarship',
              description: 'Scholarship details are unavailable.',
              saved_record_id: record.id,
              saved_at: record.saved_at,
            };
          }

          try {
            const detail = await api.get(
              `/scholarships/${encodeURIComponent(scholarshipId)}`
            );

            return {
              ...detail.data,
              id: detail.data.id || scholarshipId,
              scholarship_id: scholarshipId,
              saved_record_id: record.id,
              saved_at: record.saved_at,
            };
          } catch {
            return {
              id: scholarshipId,
              scholarship_id: scholarshipId,
              name: 'Saved scholarship',
              provider: 'Details unavailable',
              description:
                'The original scholarship details could not be loaded. You can still remove this saved entry.',
              saved_record_id: record.id,
              saved_at: record.saved_at,
            };
          }
        })
      );

      setSaved(scholarships);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          'Could not load your saved scholarships.'
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSavedScholarships();
  }, [loadSavedScholarships]);

  async function removeSaved(event, scholarship) {
    event.stopPropagation();

    const scholarshipId = getScholarshipId(scholarship);

    if (!scholarshipId || removingId) return;

    setRemovingId(scholarshipId);
    setError('');

    // Optimistically update local UI
    setSaved((current) =>
      current.filter(
        (item) => getScholarshipId(item) !== scholarshipId
      )
    );

    try {
      if (typeof onUnsave === 'function') {
        await onUnsave(scholarship);
      } else {
        await api.delete('/saved-scholarships/', {
          params: { scholarship_id: scholarshipId },
        });
      }
      onRefreshSaved?.();
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          'Could not remove this scholarship. Please try again.'
      );
      loadSavedScholarships();
    } finally {
      setRemovingId(null);
    }
  }

  if (loading) {
    return (
      <div className="page-loading">
        <div className="spinner" />
        Loading saved scholarships...
      </div>
    );
  }

  return (
    <section className="page">
      <div className="page-heading">
        <div>
          <p className="kicker">YOUR LIST</p>
          <h1>Saved scholarships</h1>
          <p className="muted">
            Keep opportunities you want to revisit in one place.
          </p>
        </div>

        <button
          type="button"
          className="secondary-btn"
          onClick={loadSavedScholarships}
          disabled={loading}
        >
          <Icon name="refresh-cw" size={16} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="form-error" role="alert">
          {error}
          {!saved.length && (
            <button
              type="button"
              className="text-btn"
              onClick={loadSavedScholarships}
            >
              Try again
            </button>
          )}
        </div>
      )}

      {saved.length > 0 ? (
        <div className="saved-list">
          {saved.map((scholarship, index) => {
            const key =
              scholarship.saved_record_id ||
              getScholarshipId(scholarship) ||
              index;

            const scholarshipId = getScholarshipId(scholarship);
            const amount = getAmount(scholarship);
            const name =
              scholarship.name ||
              scholarship.title ||
              'Untitled scholarship';

            return (
              <div className="saved-row" key={key}>
                <button
                  type="button"
                  className="saved-row-main"
                  onClick={() => onOpen?.(scholarship)}
                >
                  <div className="provider-logo">
                    {(scholarship.provider || name)
                      .trim()
                      .charAt(0)
                      .toUpperCase()}
                  </div>

                  <div className="saved-row-info">
                    <b>{name}</b>

                    <span>
                      {scholarship.provider || 'Provider not listed'}
                    </span>

                    {amount && <span>Amount: {amount}</span>}

                    {scholarship.saved_at && (
                      <span className="muted">
                        Saved {formatDeadline(scholarship.saved_at)}
                      </span>
                    )}
                  </div>

                  <div className="saved-row-meta">
                    <span>
                      Deadline:{' '}
                      {formatDeadline(
                        scholarship.application_deadline ||
                          scholarship.deadline
                      )}
                    </span>

                    <Icon name="arrow" size={17} />
                  </div>
                </button>

                <button
                  type="button"
                  className="saved-remove"
                  aria-label={`Remove ${name} from saved scholarships`}
                  title="Remove from saved"
                  disabled={!scholarshipId || removingId === scholarshipId}
                  onClick={(event) => removeSaved(event, scholarship)}
                >
                  <Icon name="bookmark" size={17} />
                  {removingId === scholarshipId ? 'Removing...' : ''}
                </button>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="empty-page small">
          <div className="empty-icon">
            <Icon name="bookmark" size={27} />
          </div>

          <h2>Your saved list is empty</h2>

          <p>
            Save scholarships from the discovery page to keep them here.
          </p>
        </div>
      )}
    </section>
  );
}
