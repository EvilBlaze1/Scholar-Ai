import { useEffect, useState } from 'react';
import api from '../api/client';
import { Icon } from '../components/Icons';

function displayList(value, fallback = 'Not specified') {
  if (Array.isArray(value)) {
    return value.length ? value.join(', ') : fallback;
  }

  return typeof value === 'string' && value.trim()
    ? value
    : fallback;
}

function formatAmount(value) {
  if (value === null || value === undefined || value === '') {
    return 'Varies';
  }

  if (typeof value === 'number') {
    return `₹${value.toLocaleString('en-IN')}`;
  }

  return String(value);
}

function formatDeadline(value) {
  if (!value) return 'Not specified';

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return date.toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
}

function safeExternalUrl(value) {
  if (!value || typeof value !== 'string') return null;

  try {
    const url = new URL(value);

    if (url.protocol === 'https:' || url.protocol === 'http:') {
      return url.href;
    }
  } catch {
    return null;
  }

  return null;
}

function Requirement({ label, value }) {
  return (
    <div className="requirement">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

export default function Details({
  id,
  scholarship,
  onBack,
  onSave,
  isSaved = false,
  isTracked = false,
  onTrack,
}) {
  const [item, setItem] = useState(scholarship || null);
  const [loading, setLoading] = useState(!scholarship);
  const [loadError, setLoadError] = useState('');
  const [savedMessage, setSavedMessage] = useState('');
  const [trackingMessage, setTrackingMessage] = useState('');
  const [isTracking, setIsTracking] = useState(false);

  // Document readiness checklist state
  const targetId =
    scholarship?.id ||
    scholarship?._id ||
    scholarship?.scholarship_id ||
    id ||
    'default';
  const docStorageKey = `scholar_docs_${targetId}`;

  const [checkedDocs, setCheckedDocs] = useState(() => {
    try {
      const saved = localStorage.getItem(docStorageKey);
      return saved ? JSON.parse(saved) : {};
    } catch {
      return {};
    }
  });

  const toggleDoc = (doc) => {
    setCheckedDocs((prev) => {
      const updated = { ...prev, [doc]: !prev[doc] };
      try {
        localStorage.setItem(docStorageKey, JSON.stringify(updated));
      } catch {}
      return updated;
    });
  };

  useEffect(() => {
    let cancelled = false;

    async function loadScholarship() {
      setLoadError('');

      if (scholarship) {
        setItem(scholarship);
        setLoading(false);
        return;
      }

      if (!id) {
        setItem(null);
        setLoading(false);
        return;
      }

      setLoading(true);

      try {
        const response = await api.get(
          `/scholarships/${encodeURIComponent(id)}`
        );

        if (!cancelled) {
          setItem(response.data);
        }
      } catch (error) {
        if (!cancelled) {
          setItem(null);
          setLoadError(
            error.response?.data?.detail ||
              'We could not load this scholarship. Please try again.'
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadScholarship();

    return () => {
      cancelled = true;
    };
  }, [id, scholarship]);

  if (loading) {
    return (
      <div className="page-loading">
        <div className="spinner" />
        Loading scholarship...
      </div>
    );
  }

  if (!item) {
    return (
      <div className="empty-page">
        <h2>Scholarship not found</h2>
        <p>{loadError || 'This scholarship may no longer be available.'}</p>

        <button type="button" className="secondary-btn" onClick={onBack}>
          Go back
        </button>
      </div>
    );
  }

  const status = item.eligibility_status || item.status;
  const eligible = status === 'ELIGIBLE';
  const ineligible = status === 'INELIGIBLE';
  const verification = status === 'NEEDS_VERIFICATION';

  const sourceUrl = safeExternalUrl(
    item.source_url || item.url
  );

  const applicationUrl = safeExternalUrl(
    item.application_url ||
      item.apply_url ||
      item.official_application_url
  );

  const amount = item.scholarship_amount ?? item.amount;
  const deadline = item.application_deadline || item.deadline;

  const deadlineDate = deadline ? new Date(deadline) : null;
  const validDeadline =
    deadlineDate && !Number.isNaN(deadlineDate.getTime());

  const deadlinePassed =
    validDeadline &&
    deadlineDate.getTime() < new Date().setHours(0, 0, 0, 0);

  const isOfficial =
    item.verification_status === 'OFFICIAL' ||
    item.verification_status === 'VERIFIED';

  const verificationRequired =
    verification ||
    (item.verification_required === true && !isOfficial);

  const ruleResults = Array.isArray(item.rule_results)
    ? item.rule_results
    : [];

  const requiredDocuments = Array.isArray(item.required_documents)
    ? item.required_documents
    : [];

  const readyDocCount = requiredDocuments.filter(
    (d) => checkedDocs[d]
  ).length;

  const docReadinessPct =
    requiredDocuments.length > 0
      ? Math.round((readyDocCount / requiredDocuments.length) * 100)
      : 0;

  async function saveScholarship() {
    setSavedMessage('');

    try {
      if (typeof onSave !== 'function') {
        setSavedMessage('Saving is not available right now.');
        return;
      }

      await onSave(item);
    } catch {
      setSavedMessage('Could not update saved status. Please try again.');
    }
  }

  async function trackApplication() {
    setTrackingMessage('');
    setIsTracking(true);

    if (typeof onTrack === 'function') {
      try {
        await onTrack(item);
        setIsTracking(false);
        return;
      } catch {}
    }

    const trackId =
      item.id || item._id || item.scholarship_id || sourceUrl || id;

    if (!trackId) {
      setTrackingMessage('Unable to track: scholarship ID missing.');
      setIsTracking(false);
      return;
    }

    try {
      await api.post('/applications/', {
        scholarship_id: String(trackId),
        status: 'APPLIED',
        applied_at: new Date().toISOString().split('T')[0],
        scholarship_name: item.name || item.title || 'Scholarship opportunity',
        provider: item.provider || 'Scholarship Authority',
        scholarship_amount: item.scholarship_amount ?? item.amount,
      });
      setTrackingMessage('Added to your Application Tracker!');
    } catch (error) {
      if (error.response?.status === 409) {
        setTrackingMessage('Already in your application tracker.');
      } else {
        setTrackingMessage(
          error.response?.data?.detail || 'Could not track application.'
        );
      }
    } finally {
      setIsTracking(false);
    }
  }

  function getGoogleCalendarUrl() {
    if (!validDeadline) return null;
    const y = deadlineDate.getFullYear();
    const m = String(deadlineDate.getMonth() + 1).padStart(2, '0');
    const d = String(deadlineDate.getDate()).padStart(2, '0');
    const dateStr = `${y}${m}${d}`;
    const title = encodeURIComponent(
      `${item.name || 'Scholarship'} - Application Deadline`
    );
    const details = encodeURIComponent(
      `Application deadline for ${item.name || 'Scholarship'}.\nProvider: ${
        item.provider || 'Scholarship Authority'
      }\nWebsite: ${sourceUrl || ''}\n\nTracked via Scholar AI`
    );
    return `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${title}&dates=${dateStr}/${dateStr}&details=${details}`;
  }

  function downloadIcs() {
    if (!validDeadline) return;
    const y = deadlineDate.getFullYear();
    const m = String(deadlineDate.getMonth() + 1).padStart(2, '0');
    const d = String(deadlineDate.getDate()).padStart(2, '0');
    const dateStr = `${y}${m}${d}`;
    const cleanTitle = (item.name || 'Scholarship')
      .replace(/,/g, '')
      .replace(/[^\w\s-]/g, '');

    const icsContent = [
      'BEGIN:VCALENDAR',
      'VERSION:2.0',
      'PRODID:-//Scholar AI//Scholarship Reminder//EN',
      'BEGIN:VEVENT',
      `UID:${Date.now()}@scholarai.local`,
      `DTSTAMP:${dateStr}T090000Z`,
      `DTSTART;VALUE=DATE:${dateStr}`,
      `DTEND;VALUE=DATE:${dateStr}`,
      `SUMMARY:${cleanTitle} Deadline`,
      `DESCRIPTION:Application deadline for ${cleanTitle}. Provider: ${
        item.provider || 'Authority'
      }. Official source: ${sourceUrl || ''}`,
      'STATUS:CONFIRMED',
      'END:VEVENT',
      'END:VCALENDAR',
    ].join('\r\n');

    const blob = new Blob([icsContent], {
      type: 'text/calendar;charset=utf-8',
    });
    const link = document.createElement('a');
    link.href = window.URL.createObjectURL(blob);
    link.setAttribute(
      'download',
      `${(item.name || 'scholarship')
        .slice(0, 30)
        .replace(/[^a-zA-Z0-9]/g, '_')}_deadline.ics`
    );
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  return (
    <section className="page detail-page">
      <button
        type="button"
        className="back-btn"
        onClick={onBack}
      >
        <Icon name="back" size={18} />
        Back to scholarships
      </button>

      <div className="detail-header">
        <div className="provider-logo xl">
          {(item.provider || item.name || item.title || 'S')
            .trim()
            .charAt(0)
            .toUpperCase()}
        </div>

        <div className="detail-heading-content">
          <p className="eyebrow">
            {item.provider || 'Scholarship provider'}
          </p>

          <h1>
            {item.name || item.title || 'Scholarship opportunity'}
          </h1>

          <p className="muted">
            {item.description || 'No description provided.'}
          </p>

          <div className="detail-badges">
            {status && (
              <span
                className={`application-status status-${String(
                  status
                ).toLowerCase()}`}
              >
                {status.replaceAll('_', ' ')}
              </span>
            )}

            {isOfficial ? (
              <span className="application-status status-selected">
                ✓ Official Portal / Verified Scheme
              </span>
            ) : verificationRequired ? (
              <span className="application-status status-needs-verification">
                Verify details
              </span>
            ) : null}
          </div>
        </div>

        <button
          type="button"
          className={`secondary-btn ${isSaved ? 'btn-saved' : ''}`}
          onClick={saveScholarship}
          style={
            isSaved
              ? {
                  background: 'var(--soft-green, #eaf3ef)',
                  color: 'var(--green, #173f35)',
                  borderColor: '#c0ded0',
                  fontWeight: 600,
                }
              : {}
          }
        >
          <Icon name="bookmark" size={17} />
          {isSaved ? 'Saved' : 'Save scholarship'}
        </button>
      </div>

      {verificationRequired && !isOfficial && (
        <div className="notice notice-warning" role="note">
          <strong>Verify before applying</strong>
          <p>
            Some eligibility details may be incomplete or unverified.
            Check the official scholarship website for the final rules,
            application dates, and required documents.
          </p>
        </div>
      )}

      {ineligible && (
        <div className="notice notice-warning" role="note">
          <strong>Potential eligibility mismatch</strong>
          <p>
            The available information indicates that you may not meet one
            or more listed requirements. Review the rules before deciding
            whether to apply.
          </p>
        </div>
      )}

      {savedMessage && (
        <p className="muted" role="status">
          {savedMessage}
        </p>
      )}

      <div className="detail-grid">
        <div>
          <div className="detail-card">
            <h3>About this scholarship</h3>
            <p>
              {item.description || 'No description provided.'}
            </p>

            {item.benefits_description && (
              <>
                <h3 style={{ marginTop: '16px' }}>Benefits and financial support</h3>
                <p>{item.benefits_description}</p>
              </>
            )}

            {item.amount_type && (
              <Requirement
                label="Award type"
                value={item.amount_type}
              />
            )}
          </div>

          <div className="detail-card">
            <h3>Eligibility requirements</h3>

            <div className="requirements">
              <Requirement
                label="Eligibility status"
                value={
                  eligible
                    ? 'Eligible based on available rules'
                    : verification
                      ? 'Needs verification'
                      : ineligible
                        ? 'Potential mismatch'
                        : status || 'Not verified'
                }
              />

              <Requirement
                label="Categories"
                value={displayList(item.eligible_categories)}
              />

              <Requirement
                label="States"
                value={displayList(item.eligible_states)}
              />

              <Requirement
                label="Education levels"
                value={displayList(item.eligible_education_levels)}
              />

              <Requirement
                label="Courses"
                value={displayList(item.eligible_courses)}
              />

              <Requirement
                label="Gender"
                value={displayList(item.eligible_genders)}
              />

              <Requirement
                label="Minimum score"
                value={
                  item.minimum_score != null
                    ? `${item.minimum_score} ${
                        item.minimum_score_type || ''
                      }`.trim()
                    : 'Not specified'
                }
              />

              <Requirement
                label="Maximum family income"
                value={
                  item.maximum_family_income != null
                    ? `₹${Number(
                        item.maximum_family_income
                      ).toLocaleString('en-IN')}`
                    : 'Not specified'
                }
              />
            </div>
          </div>

          {ruleResults.length > 0 && (
            <div className="detail-card">
              <h3>Eligibility rule breakdown</h3>

              <div className="requirements">
                {ruleResults.map((rule, index) => (
                  <div className="requirement" key={rule.rule_id || index}>
                    <span>
                      {String(rule.rule_id || rule.rule_type || 'Requirement')
                        .replaceAll('_', ' ')}
                    </span>

                    <strong>
                      {rule.status || 'UNKNOWN'}
                    </strong>

                    {rule.reason && (
                      <p className="muted">{rule.reason}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Interactive Document Readiness Checklist */}
          {requiredDocuments.length > 0 && (
            <div className="detail-card">
              <div className="checklist-header">
                <div>
                  <h3>Document Readiness Checklist</h3>
                  <p className="muted" style={{ fontSize: '12px', marginTop: '2px' }}>
                    Tick the documents you have prepared for application.
                  </p>
                </div>
                <div className="checklist-progress">
                  <span className="checklist-pct">{docReadinessPct}% Ready</span>
                  <span className="checklist-count">({readyDocCount}/{requiredDocuments.length})</span>
                </div>
              </div>

              <div className="progress-bar-bg">
                <div
                  className="progress-bar-fill"
                  style={{ width: `${docReadinessPct}%` }}
                />
              </div>

              <ul className="interactive-document-list">
                {requiredDocuments.map((document, index) => {
                  const isChecked = Boolean(checkedDocs[document]);
                  return (
                    <li
                      key={`${document}-${index}`}
                      className={`checklist-item ${isChecked ? 'ready' : ''}`}
                      onClick={() => toggleDoc(document)}
                    >
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => {}}
                        aria-label={`Mark ${document} as ready`}
                      />
                      <span className="doc-name">{document}</span>
                      <span className="doc-status-chip">
                        {isChecked ? 'Ready' : 'Pending'}
                      </span>
                    </li>
                  );
                })}
              </ul>
            </div>
          )}

          {sourceUrl && (
            <div className="detail-card">
              <h3>Official source and further information</h3>
              <p>
                Visit the source to review the original scholarship
                announcement and confirm the details.
              </p>

              <a
                href={sourceUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-btn"
                style={{ marginTop: '10px' }}
              >
                View source webpage
                <Icon name="arrow" size={15} />
              </a>
            </div>
          )}
        </div>

        <aside className="detail-side">
          <div className="amount-card">
            <span>Award amount</span>
            <strong>{formatAmount(amount)}</strong>
            <small>
              {item.amount_type ||
                item.benefits_description ||
                'Scholarship support; confirm the amount with the provider.'}
            </small>
          </div>

          <div className="deadline-card">
            <span>
              <Icon name="calendar" size={17} />
              Application deadline
            </span>

            <strong>{formatDeadline(deadline)}</strong>

            {deadlinePassed && (
              <p className="muted" style={{ color: '#a04d4d' }}>
                This listed deadline has passed. Check the official source
                for any extensions or a new application cycle.
              </p>
            )}

            {!deadline && (
              <p className="muted">
                No deadline was found in the available information.
              </p>
            )}

            {/* Deadline Reminders Widget */}
            {validDeadline && !deadlinePassed && (
              <div className="calendar-actions">
                <a
                  href={getGoogleCalendarUrl()}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="calendar-btn"
                  title="Add reminder to Google Calendar"
                >
                  <Icon name="calendar" size={14} />
                  Add to Google Calendar
                </a>

                <button
                  type="button"
                  className="calendar-btn"
                  onClick={downloadIcs}
                  title="Download .ics file for Apple/Outlook/Desktop calendars"
                >
                  <Icon name="file" size={14} />
                  Download .ics Reminder
                </button>
              </div>
            )}

            <button
              type="button"
              className={`secondary-btn wide ${isSaved ? 'btn-saved' : ''}`}
              style={{
                marginTop: '14px',
                ...(isSaved
                  ? {
                      background: 'var(--soft-green, #eaf3ef)',
                      color: 'var(--green, #173f35)',
                      borderColor: '#c0ded0',
                      fontWeight: 600,
                    }
                  : {}),
              }}
              onClick={saveScholarship}
            >
              <Icon name="bookmark" size={17} />
              {isSaved ? 'Saved' : 'Save scholarship'}
            </button>

            <button
              type="button"
              className={`wide ${isTracked ? 'secondary-btn' : 'primary-btn'}`}
              style={{
                marginTop: '10px',
                ...(isTracked
                  ? {
                      background: '#f1f5f9',
                      color: '#475569',
                      borderColor: '#cbd5e1',
                      cursor: 'default',
                    }
                  : {}),
              }}
              onClick={isTracked ? undefined : trackApplication}
              disabled={isTracking}
            >
              <Icon name={isTracked ? 'check' : 'file'} size={17} />
              {isTracked
                ? 'Tracked in Applications'
                : isTracking
                ? 'Adding...'
                : 'Track in Applications'}
            </button>

            {trackingMessage && (
              <p
                className="success-text"
                style={{ marginTop: '6px', textAlign: 'center' }}
              >
                {trackingMessage}
              </p>
            )}

            {applicationUrl ? (
              <a
                href={applicationUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="secondary-btn wide"
                style={{ marginTop: '10px' }}
              >
                Open application page
                <Icon name="arrow" size={15} />
              </a>
            ) : sourceUrl ? (
              <a
                href={sourceUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="secondary-btn wide"
                style={{ marginTop: '10px' }}
              >
                Visit scholarship website
                <Icon name="arrow" size={15} />
              </a>
            ) : null}
          </div>
        </aside>
      </div>
    </section>
  );
}
