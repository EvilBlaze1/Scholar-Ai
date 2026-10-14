
import { useEffect, useMemo, useState } from 'react';
import api from '../api/client';
import ScholarshipCard from '../components/ScholarshipCard';
import { Icon } from '../components/Icons';

export default function Scholarships({ onOpen, onSave }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [q, setQ] = useState('');
  const [activeQuery, setActiveQuery] = useState('');
  const [mode, setMode] = useState('personalized');
  const [filter, setFilter] = useState('all');
  const [error, setError] = useState('');
  const [searched, setSearched] = useState(false);

  const findScholarships = async () => {
    setLoading(true);
    setError('');
    setMode('personalized');
    setActiveQuery('');

    try {
      const profileResponse = await api.get('/students/me');
      const profile = profileResponse.data;

      const studentId =
        profile.id || profile._id || profile.student_id;

      if (!studentId) {
        throw new Error(
          'Your student profile was not found. Please complete your profile first.'
        );
      }

      const response = await api.get(
        `/search/student/${encodeURIComponent(studentId)}`
      );

      const results = response.data?.results;
      setItems(Array.isArray(results) ? results : []);
      setSearched(true);
    } catch (err) {
      console.error('Personalized scholarship search failed:', err);
      setItems([]);
      setError(
        err.response?.data?.detail ||
          err.message ||
          'Unable to find scholarships. Please try again.'
      );
      setSearched(true);
    } finally {
      setLoading(false);
    }
  };

  const searchByKeyword = async (event) => {
    event?.preventDefault();

    const query = q.trim();

    if (query.length < 2) {
      setError('Enter at least 2 characters to search.');
      return;
    }

    setLoading(true);
    setError('');
    setMode('keyword');
    setActiveQuery(query);

    try {
      const response = await api.get('/discovery/search', {
        params: { q: query },
      });

      const results = response.data?.results;
      setItems(Array.isArray(results) ? results : []);
      setSearched(true);
    } catch (err) {
      console.error('Keyword scholarship search failed:', err);
      setItems([]);
      setError(
        err.response?.data?.detail ||
          'Unable to search the Internet right now. Please try again.'
      );
      setSearched(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    findScholarships();
  }, []);

  const filtered = useMemo(() => {
    return items.filter((item) => {
      const text = [
        item.name,
        item.title,
        item.provider,
        item.description,
        item.benefits_description,
        item.source_url,
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase();

      // In keyword mode, the backend already searched for this query.
      // Do not hide results just because their descriptions omit the query.
      const matchesSearch =
        mode === 'keyword' ||
        !q.trim() ||
        text.includes(q.trim().toLowerCase());

      const status = item.eligibility_status || item.status;

      const matchesFilter =
        filter === 'all' ||
        (mode === 'keyword' && !status && filter === 'NEEDS_VERIFICATION') ||
        status === filter;

      return matchesSearch && matchesFilter;
    });
  }, [items, q, filter, mode]);

  return (
    <section className="page">
      <div className="page-heading">
        <div>
          <p className="kicker">DISCOVER</p>
          <h1>Scholarships</h1>
          <p className="muted">
            Discover funding opportunities matched to your profile or search
            the Internet using your own keywords.
          </p>
        </div>

        <button
          type="button"
          className="primary-btn"
          onClick={findScholarships}
          disabled={loading}
        >
          <Icon name="search" size={17} />
          {loading ? 'Searching...' : 'Find for me'}
        </button>
      </div>

      <form className="scholarship-toolbar" onSubmit={searchByKeyword}>
        <div className="search-field">
          <Icon name="search" size={18} />
          <input
            value={q}
            onChange={(event) => setQ(event.target.value)}
            placeholder="e.g. merit scholarships for BTech students"
            aria-label="Scholarship search keywords"
            maxLength={200}
          />
        </div>

        <button
          type="submit"
          className="primary-btn"
          disabled={loading || q.trim().length < 2}
        >
          Search Internet
        </button>

        <select
          value={filter}
          onChange={(event) => setFilter(event.target.value)}
          aria-label="Filter scholarships by eligibility"
        >
          <option value="all">All opportunities</option>
          <option value="ELIGIBLE">Eligible</option>
          <option value="NEEDS_VERIFICATION">Needs verification</option>
          <option value="INELIGIBLE">Not eligible</option>
        </select>
      </form>

      <div className="muted">
        {mode === 'keyword' && activeQuery
          ? `Internet search: "${activeQuery}"`
          : 'Showing scholarships discovered for your student profile.'}
      </div>

      {loading ? (
        <div className="card-grid">
          {[1, 2, 3].map((number) => (
            <div className="skeleton-card" key={number} />
          ))}
        </div>
      ) : error ? (
        <div className="empty-page small">
          <div className="empty-icon">
            <Icon name="search" size={27} />
          </div>
          <h2>Search couldn't be completed</h2>
          <p>{error}</p>

          <button
            type="button"
            className="primary-btn"
            onClick={
              mode === 'keyword'
                ? () => searchByKeyword()
                : findScholarships
            }
          >
            Try again
          </button>
        </div>
      ) : filtered.length > 0 ? (
        <>
          <p className="muted">
            Showing {filtered.length} {filtered.length === 1 ? 'result' : 'results'}
          </p>

          <div className="card-grid">
            {filtered.map((item, index) => {
              const normalizedItem = {
                ...item,
                name: item.name || item.title || 'Scholarship opportunity',
                source_url: item.source_url || item.url || '',
                eligibility_status:
                  item.eligibility_status ||
                  item.status ||
                  (mode === 'keyword' ? 'NEEDS_VERIFICATION' : undefined),
              };

              return (
                <ScholarshipCard
                  key={
                    item.id ||
                    item._id ||
                    item.source_url ||
                    item.url ||
                    index
                  }
                  item={normalizedItem}
                  onOpen={onOpen}
                  onSave={onSave}
                />
              );
            })}
          </div>
        </>
      ) : (
        <div className="empty-page small">
          <div className="empty-icon">
            <Icon name="search" size={27} />
          </div>

          <h2>
            {searched ? 'No scholarships found' : 'Discover scholarships'}
          </h2>

          <p>
            {filter !== 'all'
              ? 'No results match this eligibility filter. Try another filter.'
              : mode === 'keyword'
                ? 'Try different keywords, such as your course, state, category, or scholarship type.'
                : 'Search for scholarships matched to your profile or use custom keywords.'}
          </p>

          {filter !== 'all' ? (
            <button
              type="button"
              className="primary-btn"
              onClick={() => setFilter('all')}
            >
              Clear filter
            </button>
          ) : (
            <button
              type="button"
              className="primary-btn"
              onClick={findScholarships}
            >
              <Icon name="search" size={17} />
              Find for me
            </button>
          )}
        </div>
      )}
    </section>
  );
}
