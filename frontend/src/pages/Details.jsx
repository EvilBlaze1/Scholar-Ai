
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

export default function Details({ id, scholarship, onBack, onSave }) {
  const [item, setItem] = useState(scholarship || null);
  const [loading, setLoading] = useState(!scholarship);
  const [loadError, setLoadError] = useState('');
  const [savedMessage, setSavedMessage] = useState('');

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

  const verificationRequired =
    verification ||
    item.verification_required === true ||
    (item.verification_status &&
      item.verification_status !== 'VERIFIED');

  const ruleResults = Array.isArray(item.rule_results)
    ? item.rule_results
    : [];

  async function saveScholarship() {
    setSavedMessage('');

    try {
      if (typeof onSave !== 'function') {
        setSavedMessage('Saving is not available right now.');
        return;
      }

      await onSave(item);
      setSavedMessage('Scholarship saved successfully.');
    } catch {
      setSavedMessage('Could not save this scholarship. Please try again.');
    }
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

            {verificationRequired && (
              <span className="application-status status-needs-verification">
                Verify details
              </span>
            )}
          </div>
        </div>

        <button
          type="button"
          className="secondary-btn"
          onClick={saveScholarship}
        >
          <Icon name="bookmark" size={17} />
          Save scholarship
        </button>
      </div>

      {verificationRequired && (
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
                <h3>Benefits and financial support</h3>
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

          {item.required_documents?.length > 0 && (
            <div className="detail-card">
              <h3>Required documents</h3>

              <ul className="document-list">
                {item.required_documents.map((document, index) => (
                  <li key={`${document}-${index}`}>
                    <Icon name="check" size={16} />
                    {document}
                  </li>
                ))}
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
              >
                View source webpage
                <Icon name="external-link" size={15} />
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
              <p className="muted">
                This listed deadline has passed. Check the official source
                for any extensions or a new application cycle.
              </p>
            )}

            {!deadline && (
              <p className="muted">
                No deadline was found in the available information.
              </p>
            )}

            <button
              type="button"
              className="primary-btn wide"
              onClick={saveScholarship}
            >
              <Icon name="bookmark" size={17} />
              Save scholarship
            </button>

            {applicationUrl ? (
              <a
                href={applicationUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="secondary-btn wide"
              >
                Open application page
                <Icon name="external-link" size={15} />
              </a>
            ) : sourceUrl ? (
              <a
                href={sourceUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="secondary-btn wide"
              >
                Visit scholarship website
                <Icon name="external-link" size={15} />
              </a>
            ) : null}
          </div>
        </aside>
      </div>
    </section>
  );
}
