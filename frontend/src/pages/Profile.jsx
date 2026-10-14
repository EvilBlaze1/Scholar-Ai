
import { useEffect, useMemo, useState } from 'react';
import api from '../api/client';
import { Icon } from '../components/Icons';

const fields = [
  ['full_name', 'Full name', 'text'],
  ['date_of_birth', 'Date of birth', 'date'],
  ['gender', 'Gender', 'text'],
  ['state', 'Current state', 'text'],
  ['education_level', 'Education level', 'text'],
  ['course', 'Course', 'text'],
  ['specialization', 'Specialization', 'text'],
  ['college', 'College / university', 'text'],
  ['academic_year', 'Academic year', 'text'],
  ['score', 'Academic score', 'number'],
  ['score_type', 'Score type', 'text'],
  ['annual_family_income', 'Annual family income (₹)', 'number'],
  ['category', 'Category', 'text'],
  ['domicile_state', 'Domicile state', 'text'],
];

const sections = [
  {
    number: '01',
    title: 'Personal details',
    description: 'Basic information about you.',
    fields: fields.slice(0, 4),
  },
  {
    number: '02',
    title: 'Academic details',
    description: 'Information used for academic eligibility.',
    fields: fields.slice(4, 11),
  },
  {
    number: '03',
    title: 'Eligibility details',
    description: 'These details can unlock additional opportunities.',
    fields: fields.slice(11),
  },
];

const importantFields = [
  'full_name',
  'date_of_birth',
  'gender',
  'state',
  'education_level',
  'course',
  'score',
  'score_type',
  'annual_family_income',
  'category',
  'domicile_state',
];

function getStudentId(student) {
  return student.id || student._id || student.student_id;
}

function getErrorMessage(error) {
  const detail = error.response?.data?.detail;

  if (typeof detail === 'string') return detail;

  if (Array.isArray(detail)) {
    return detail
      .map((item) => item.msg || 'Invalid field')
      .join('. ');
  }

  return 'Could not save your profile. Please check your information and try again.';
}

export default function Profile({ onDone }) {
  const [form, setForm] = useState({});
  const [exists, setExists] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('');
  const [loadError, setLoadError] = useState('');

  useEffect(() => {
    let cancelled = false;

    async function loadProfile() {
      try {
        const response = await api.get('/students/me');

        if (cancelled) return;

        setForm(response.data || {});
        setExists(true);
      } catch (error) {
        if (cancelled) return;

        if (error.response?.status === 404) {
          // A missing profile can mean the student needs to create one.
          setForm({});
          setExists(false);
        } else {
          setLoadError(
            error.response?.data?.detail ||
              'Unable to load your profile. Please try again.'
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadProfile();

    return () => {
      cancelled = true;
    };
  }, []);

  const completion = useMemo(() => {
    const completed = importantFields.filter((key) => {
      const value = form[key];
      return value !== null && value !== undefined && String(value).trim() !== '';
    }).length;

    return {
      completed,
      total: importantFields.length,
      percent: Math.round((completed / importantFields.length) * 100),
    };
  }, [form]);

  function change(key, value) {
    setForm((current) => ({ ...current, [key]: value }));
    setMessage('');
    setMessageType('');
  }

  function validate() {
    if (
      form.score !== '' &&
      form.score != null &&
      (!Number.isFinite(Number(form.score)) || Number(form.score) < 0)
    ) {
      return 'Academic score must be a valid non-negative number.';
    }

    if (
      form.annual_family_income !== '' &&
      form.annual_family_income != null &&
      (!Number.isFinite(Number(form.annual_family_income)) ||
        Number(form.annual_family_income) < 0)
    ) {
      return 'Annual family income must be a valid non-negative number.';
    }

    if (form.date_of_birth) {
      const date = new Date(form.date_of_birth);

      if (Number.isNaN(date.getTime()) || date > new Date()) {
        return 'Please enter a valid date of birth.';
      }
    }

    return '';
  }

  async function save(event) {
    event.preventDefault();
    setMessage('');
    setMessageType('');

    const validationError = validate();

    if (validationError) {
      setMessage(validationError);
      setMessageType('error');
      return;
    }

    setSaving(true);

    try {
      let response;

      if (exists) {
        const studentId = getStudentId(form);

        if (!studentId) {
          throw new Error(
            'Your student ID is missing. Reload your profile and try again.'
          );
        }

        response = await api.put(
          `/students/${encodeURIComponent(studentId)}`,
          form
        );
      } else {
        response = await api.post('/students/me', form);
      }

      const savedProfile = response.data || {};

      setForm((current) => ({ ...current, ...savedProfile }));
      setExists(true);
      setMessage('Profile saved successfully.');
      setMessageType('success');

      // Do not navigate away immediately; allow the user to see confirmation.
    } catch (error) {
      setMessage(
        error.message && !error.response
          ? error.message
          : getErrorMessage(error)
      );
      setMessageType('error');
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="page-loading">
        <div className="spinner" />
        Loading your profile...
      </div>
    );
  }

  if (loadError) {
    return (
      <section className="page">
        <div className="empty-page">
          <div className="empty-icon">
            <Icon name="user" size={28} />
          </div>
          <h2>Profile unavailable</h2>
          <p>{loadError}</p>
          <button
            type="button"
            className="primary-btn"
            onClick={() => window.location.reload()}
          >
            Try again
          </button>
        </div>
      </section>
    );
  }

  return (
    <section className="page">
      <div className="page-heading">
        <div>
          <p className="kicker">YOUR PROFILE</p>
          <h1>{exists ? 'Your profile' : 'Tell us about yourself'}</h1>
          <p className="muted">
            Complete your details to help Scholar AI assess eligibility and
            find more relevant scholarships.
          </p>
        </div>
      </div>

      <div className="detail-card profile-completion">
        <div className="section-header">
          <div>
            <h3>Profile completeness</h3>
            <p className="muted">
              {completion.completed} of {completion.total} important fields completed
            </p>
          </div>
          <strong>{completion.percent}%</strong>
        </div>

        <div
          className="profile-progress-track"
          role="progressbar"
          aria-label="Profile completeness"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={completion.percent}
        >
          <div
            className="profile-progress-fill"
            style={{ width: `${completion.percent}%` }}
          />
        </div>

        <p className="muted">
          Missing information may limit the accuracy of scholarship matches.
        </p>
      </div>

      <form className="profile-form" onSubmit={save}>
        {sections.map((section) => (
          <div className="form-section" key={section.number}>
            <div className="section-title">
              <span className="section-number">{section.number}</span>
              <div>
                <h3>{section.title}</h3>
                <p>{section.description}</p>
              </div>
            </div>

            <div className="form-grid">
              {section.fields.map(([key, label, type]) => (
                <label key={key}>
                  {label}

                  <input
                    type={type}
                    value={form[key] ?? ''}
                    min={type === 'number' ? 0 : undefined}
                    step={type === 'number' ? 'any' : undefined}
                    max={key === 'date_of_birth' ? undefined : undefined}
                    onChange={(event) => {
                      const value = event.target.value;

                      change(
                        key,
                        type === 'number'
                          ? value === ''
                            ? ''
                            : Number(value)
                          : value
                      );
                    }}
                    placeholder={type === 'date' ? undefined : label}
                  />
                </label>
              ))}

              {section.number === '03' && (
                <label>
                  Disability status
                  <select
                    value={
                      form.disability_status == null
                        ? ''
                        : String(form.disability_status)
                    }
                    onChange={(event) =>
                      change(
                        'disability_status',
                        event.target.value === ''
                          ? null
                          : event.target.value === 'true'
                      )
                    }
                  >
                    <option value="">Prefer not to say</option>
                    <option value="false">No</option>
                    <option value="true">Yes</option>
                  </select>
                </label>
              )}
            </div>
          </div>
        ))}

        <div className="form-actions">
          {message && (
            <span
              className={
                messageType === 'success' ? 'success-text' : 'error-text'
              }
              role={messageType === 'error' ? 'alert' : 'status'}
            >
              {message}
            </span>
          )}

          <button
            type="submit"
            className="primary-btn"
            disabled={saving}
          >
            {saving ? 'Saving...' : 'Save profile'}
            <Icon name="check" size={17} />
          </button>

          {messageType === 'success' && onDone && (
            <button
              type="button"
              className="secondary-btn"
              onClick={onDone}
            >
              Continue
              <Icon name="arrow" size={17} />
            </button>
          )}
        </div>
      </form>
    </section>
  );
}
