
import { Icon } from './Icons';

function formatAmount(value) {
  if (value === null || value === undefined || value === '') {
    return 'Amount not listed';
  }

  if (typeof value === 'number') {
    return `₹${value.toLocaleString('en-IN')}`;
  }

  return String(value);
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

  const provider = item.provider || 'Scholarship provider';

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

  const statusLabel = eligible
    ? 'Eligible'
    : ineligible
      ? 'Potential mismatch'
      : 'Needs verification';

  const statusClass = eligible
    ? 'success'
    : ineligible
      ? 'neutral'
      : 'warning';

  const verificationRequired =
    verify || item.verification_required === true;

  return (
    <article className="scholarship-card">
      <div className="card-top">
        <div className="provider-logo">
          {provider.trim().charAt(0).toUpperCase() || 'S'}
        </div>

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
        >
          <Icon name="bookmark" size={18} />
        </button>
      </div>

      <div className="card-body">
        <div className="eyebrow">{provider}</div>

        <h3>{scholarshipName}</h3>

        <p>
          {item.description ||
            item.benefits_description ||
            'Financial support for eligible students.'}
        </p>
      </div>

      <div className="card-meta">
        <span>
          <Icon name="money" size={16} />
          {amount}
        </span>

        <span>
          <Icon name="calendar" size={16} />
          {deadline}
        </span>
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

        {matchScore !== null && (
          <strong
            className="match"
            title="Provisional rule-match score, not a probability of receiving the award."
          >
            {matchScore}% match
          </strong>
        )}

        <button
          type="button"
          className="text-btn"
          onClick={() => onOpen?.(item)}
          aria-label={`View details for ${scholarshipName}`}
        >
          View details
          <Icon name="arrow" size={16} />
        </button>
      </div>

      {verificationRequired && (
        <p className="muted scholarship-verification-note">
          Confirm the requirements and deadline with the official source.
        </p>
      )}
    </article>
  );
}
