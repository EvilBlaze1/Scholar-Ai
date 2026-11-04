import { Icon } from './Icons';

function formatAmount(value) {
  if (value === null || value === undefined || value === '') {
    return 'Amount not listed';
  }

  if (typeof value === 'number') {
    return `₹${value.toLocaleString('en-IN')}`;
  }

  const s = String(value).trim();
  if (s.startsWith('₹') || s.toLowerCase().startsWith('rs') || s.toLowerCase().startsWith('inr')) {
    return s;
  }

  return `₹${s}`;
}

function formatDeadline(value) {
  if (!value) return 'Deadline not listed';

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return date.toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}

export default function ScholarshipCard({
  item = {},
  onOpen,
  onSave,
  saved = false,
}) {
  const status = item.eligibility_status || item.status;

  const eligible = status === 'ELIGIBLE';
  const ineligible = status === 'INELIGIBLE';
  const verify = status === 'NEEDS_VERIFICATION' || !status;

  const provider = item.provider || 'Scholarship Authority / Foundation';

  const scholarshipName =
    item.name || item.title || 'Scholarship opportunity';

  const amount = formatAmount(
    item.scholarship_amount ?? item.amount
  );

  const deadline = formatDeadline(
    item.application_deadline || item.deadline
  );

  const matchScore =
    typeof item.match_score === 'number' &&
    Number.isFinite(item.match_score)
      ? Math.max(0, Math.min(100, Math.round(item.match_score)))
      : null;

  const isOfficial =
    item.verification_status === 'OFFICIAL' ||
    item.verification_status === 'VERIFIED';

  const statusLabel = eligible
    ? 'Eligible'
    : ineligible
      ? 'Potential mismatch'
      : isOfficial
        ? 'Official Scheme'
        : 'Needs verification';

  const statusClass = eligible
    ? 'success'
    : ineligible
      ? 'neutral'
      : isOfficial
        ? 'official'
        : 'warning';

  const verificationRequired =
    !isOfficial && (verify || item.verification_required === true);

  return (
    <article className="scholarship-card">
      <div className="card-top">
        <div className="provider-logo" title={provider}>
          {provider.trim().charAt(0).toUpperCase() || 'S'}
        </div>

        <div className="card-top-right">
          {matchScore !== null && (
            <span
              className={`match-pill ${matchScore >= 80 ? 'high' : matchScore >= 50 ? 'med' : 'low'}`}
              title="Provisional eligibility match score based on your profile"
            >
              <span className="pulse-dot" />
              {matchScore}% Match
            </span>
          )}

          <button
            type="button"
            className={`save-btn ${saved ? 'saved' : ''}`}
            onClick={() => onSave?.(item)}
            aria-label={
              saved
                ? `Remove ${scholarshipName} from saved scholarships`
                : `Save ${scholarshipName}`
            }
            aria-pressed={saved}
            title={saved ? 'Saved to bookmarks' : 'Save scholarship'}
          >
            <Icon name="bookmark" size={17} />
          </button>
        </div>
      </div>

      <div className="card-body">
        <div className="card-provider-row">
          <span className="eyebrow">{provider}</span>
          {isOfficial && (
            <span className="official-chip" title="Verified source / Official Government Portal">
              🏛️ Official
            </span>
          )}
        </div>

        <h3 title={scholarshipName}>{scholarshipName}</h3>

        <p>
          {item.description ||
            item.benefits_description ||
            'Financial support for eligible students.'}
        </p>

        {/* Structured Financial & Deadline Box */}
        <div className="card-highlight-box">
          <div className="highlight-item">
            <span className="highlight-label">Award Value</span>
            <strong className="highlight-val">{amount}</strong>
          </div>
          <div className="highlight-divider" />
          <div className="highlight-item">
            <span className="highlight-label">Application Deadline</span>
            <span className="highlight-deadline">
              <Icon name="calendar" size={13} />
              {deadline}
            </span>
          </div>
        </div>
      </div>

      <div className="card-footer">
        <span
          className={`status ${statusClass}`}
          title={
            verificationRequired
              ? 'Confirm eligibility on the official scholarship website.'
              : undefined
          }
        >
          <i />
          {statusLabel}
        </span>

        <button
          type="button"
          className="view-btn"
          onClick={() => onOpen?.(item)}
          aria-label={`View details for ${scholarshipName}`}
        >
          View details
          <Icon name="arrow" size={15} />
        </button>
      </div>

      {verificationRequired && (
        <div className="scholarship-verification-note">
          Confirm requirements on official website
        </div>
      )}
    </article>
  );
}
