import { useEffect, useMemo, useState } from 'react';
import api from '../api/client';
import ScholarshipCard from '../components/ScholarshipCard';
import { Icon } from '../components/Icons';

function parseAmount(val) {
  if (val == null || val === '') return 0;
  if (typeof val === 'number') return val;
  if (typeof val === 'string') {
    const cleaned = val.replace(/,/g, '');
    const match = cleaned.match(/(\d+(?:\.\d+)?)/);
    if (match) return parseFloat(match[1]);
  }
  return 0;
}

function parseDeadline(val) {
  if (!val) return null;
  const d = new Date(val);
  return Number.isNaN(d.getTime()) ? null : d;
}

const STATUS_ORDER = {
  ELIGIBLE: 3,
  NEEDS_VERIFICATION: 2,
  INELIGIBLE: 1,
};

const PAGE_SIZE = 9;

function matchesEducation(item, level) {
  if (level === 'all') return true;
  const levels = Array.isArray(item.eligible_education_levels)
    ? item.eligible_education_levels.map((l) => String(l).toLowerCase())
    : [];
  const text = `${item.name || ''} ${item.description || ''} ${levels.join(' ')}`.toLowerCase();

  if (level === 'UG') {
    return (
      levels.some((l) =>
        l.includes('undergraduate') ||
        l.includes('b.tech') ||
        l.includes('degree') ||
        l.includes('bachelor') ||
        l.includes('ug')
      ) ||
      text.includes('undergraduate') ||
      text.includes('b.tech') ||
      text.includes('btech') ||
      text.includes('bachelor') ||
      text.includes('b.sc') ||
      text.includes('college')
    );
  }

  if (level === 'PG') {
    return (
      levels.some((l) =>
        l.includes('postgraduate') ||
        l.includes('m.tech') ||
        l.includes('master') ||
        l.includes('pg') ||
        l.includes('phd')
      ) ||
      text.includes('postgraduate') ||
      text.includes('m.tech') ||
      text.includes('mtech') ||
      text.includes('master') ||
      text.includes('m.sc') ||
      text.includes('phd')
    );
  }

  if (level === 'SCHOOL') {
    return (
      levels.some((l) =>
        l.includes('school') ||
        l.includes('class 1') ||
        l.includes('10th') ||
        l.includes('12th')
      ) ||
      text.includes('class 10') ||
      text.includes('class 12') ||
      text.includes('school') ||
      text.includes('higher secondary')
    );
  }

  return true;
}

function matchesCategory(item, cat) {
  if (cat === 'all') return true;
  const cats = Array.isArray(item.eligible_categories)
    ? item.eligible_categories.map((c) => String(c).toUpperCase())
    : [];
  if (cats.length === 0) return true;
  return cats.includes(cat);
}

function matchesDeadline(item, filterType) {
  if (filterType === 'all') return true;
  const deadlineDate = parseDeadline(item.application_deadline || item.deadline);
  if (!deadlineDate) {
    return filterType === 'active';
  }

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  if (filterType === 'active') {
    return deadlineDate >= today;
  }

  if (filterType === 'closing_soon') {
    const thirtyDays = new Date(today);
    thirtyDays.setDate(today.getDate() + 30);
    return deadlineDate >= today && deadlineDate <= thirtyDays;
  }

  return true;
}

export default function Scholarships({ onOpen, onSave, savedIds }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [q, setQ] = useState('');
  const [activeQuery, setActiveQuery] = useState('');
  const [mode, setMode] = useState('personalized');
  const [error, setError] = useState('');
  const [searched, setSearched] = useState(false);
  const [isCached, setIsCached] = useState(false);

  // Pagination state
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE);

  // Filter drawer toggle
  const [showFilterPanel, setShowFilterPanel] = useState(false);

  // Filters
  const [eligibilityFilter, setEligibilityFilter] = useState('all');
  const [amountFilter, setAmountFilter] = useState(0);
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [deadlineFilter, setDeadlineFilter] = useState('all');
  const [educationFilter, setEducationFilter] = useState('all');

  // Sorting
  const [sortBy, setSortBy] = useState('best_match');

  const findScholarships = async (forceRefresh = false) => {
    if (forceRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
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
        `/search/student/${encodeURIComponent(studentId)}`,
        {
          params: forceRefresh ? { refresh: true } : {},
        }
      );

      const results = response.data?.results;
      setItems(Array.isArray(results) ? results : []);
      setIsCached(Boolean(response.data?.cached));
      setSearched(true);
    } catch (err) {
      console.error('Personalized scholarship search failed:', err);
      setItems([]);
      setIsCached(false);
      setError(
        err.response?.data?.detail ||
          err.message ||
          'Unable to find scholarships. Please try again.'
      );
      setSearched(true);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const searchByKeyword = async (event, forceRefresh = false) => {
    event?.preventDefault();

    const query = q.trim();

    if (query.length < 2) {
      setError('Enter at least 2 characters to search.');
      return;
    }

    if (forceRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError('');
    setMode('keyword');
    setActiveQuery(query);

    try {
      const response = await api.get('/discovery/search', {
        params: {
          q: query,
          ...(forceRefresh ? { refresh: true } : {}),
        },
      });

      const results = response.data?.results;
      setItems(Array.isArray(results) ? results : []);
      setIsCached(Boolean(response.data?.cached));
      setSearched(true);
    } catch (err) {
      console.error('Keyword scholarship search failed:', err);
      setItems([]);
      setIsCached(false);
      setError(
        err.response?.data?.detail ||
          'Unable to search the Internet right now. Please try again.'
      );
      setSearched(true);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    findScholarships();
  }, []);

  // Reset pagination when search parameters or filters change
  useEffect(() => {
    setVisibleCount(PAGE_SIZE);
  }, [
    q,
    mode,
    eligibilityFilter,
    amountFilter,
    categoryFilter,
    deadlineFilter,
    educationFilter,
    sortBy,
  ]);

  const clearAllFilters = () => {
    setEligibilityFilter('all');
    setAmountFilter(0);
    setCategoryFilter('all');
    setDeadlineFilter('all');
    setEducationFilter('all');
  };

  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (eligibilityFilter !== 'all') count++;
    if (amountFilter > 0) count++;
    if (categoryFilter !== 'all') count++;
    if (deadlineFilter !== 'all') count++;
    if (educationFilter !== 'all') count++;
    return count;
  }, [eligibilityFilter, amountFilter, categoryFilter, deadlineFilter, educationFilter]);

  const filteredAndSorted = useMemo(() => {
    const filtered = items.filter((item) => {
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

      const matchesSearch =
        mode === 'keyword' ||
        !q.trim() ||
        text.includes(q.trim().toLowerCase());

      if (!matchesSearch) return false;

      const status = item.eligibility_status || item.status;
      if (eligibilityFilter !== 'all') {
        if (mode === 'keyword' && !status && eligibilityFilter === 'NEEDS_VERIFICATION') {
          // keep
        } else if (status !== eligibilityFilter) {
          return false;
        }
      }

      if (amountFilter > 0) {
        const itemAmount = parseAmount(item.scholarship_amount ?? item.amount);
        if (itemAmount < amountFilter) return false;
      }

      if (!matchesCategory(item, categoryFilter)) {
        return false;
      }

      if (!matchesDeadline(item, deadlineFilter)) {
        return false;
      }

      if (!matchesEducation(item, educationFilter)) {
        return false;
      }

      return true;
    });

    return [...filtered].sort((a, b) => {
      if (sortBy === 'best_match') {
        const aStatus = a.eligibility_status || a.status || '';
        const bStatus = b.eligibility_status || b.status || '';
        const statusDiff = (STATUS_ORDER[bStatus] || 0) - (STATUS_ORDER[aStatus] || 0);
        if (statusDiff !== 0) return statusDiff;
        const aScore = typeof a.match_score === 'number' ? a.match_score : 0;
        const bScore = typeof b.match_score === 'number' ? b.match_score : 0;
        return bScore - aScore;
      }

      if (sortBy === 'deadline_soon') {
        const aDate = parseDeadline(a.application_deadline || a.deadline);
        const bDate = parseDeadline(b.application_deadline || b.deadline);
        const today = new Date();
        today.setHours(0, 0, 0, 0);

        const aActive = aDate && aDate >= today;
        const bActive = bDate && bDate >= today;

        if (aActive && !bActive) return -1;
        if (!aActive && bActive) return 1;
        if (aDate && bDate) return aDate.getTime() - bDate.getTime();
        return 0;
      }

      if (sortBy === 'deadline_late') {
        const aDate = parseDeadline(a.application_deadline || a.deadline);
        const bDate = parseDeadline(b.application_deadline || b.deadline);
        if (aDate && !bDate) return -1;
        if (!aDate && bDate) return 1;
        if (aDate && bDate) return bDate.getTime() - aDate.getTime();
        return 0;
      }

      if (sortBy === 'amount_high') {
        const aAmt = parseAmount(a.scholarship_amount ?? a.amount);
        const bAmt = parseAmount(b.scholarship_amount ?? b.amount);
        return bAmt - aAmt;
      }

      if (sortBy === 'name_asc') {
        const aName = a.name || a.title || '';
        const bName = b.name || b.title || '';
        return aName.localeCompare(bName);
      }

      return 0;
    });
  }, [
    items,
    q,
    mode,
    eligibilityFilter,
    amountFilter,
    categoryFilter,
    deadlineFilter,
    educationFilter,
    sortBy,
  ]);

  const visibleScholarships = filteredAndSorted.slice(0, visibleCount);
  const hasMore = visibleCount < filteredAndSorted.length;

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

        <div className="heading-actions">
          <button
            type="button"
            className="secondary-btn"
            onClick={() => {
              if (mode === 'keyword') {
                searchByKeyword(null, true);
              } else {
                findScholarships(true);
              }
            }}
            disabled={loading || refreshing}
            title="Bypass cache and re-crawl fresh results"
          >
            <Icon name="refresh" size={16} className={refreshing ? 'spinning' : ''} />
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </button>

          <button
            type="button"
            className="primary-btn"
            onClick={() => findScholarships(false)}
            disabled={loading || refreshing}
          >
            <Icon name="search" size={17} />
            {loading ? 'Searching...' : 'Find for me'}
          </button>
        </div>
      </div>

      {/* Quick Preset Filter Chips Bar */}
      <div className="preset-chips-bar" role="group" aria-label="Quick filters">
        <span className="preset-label">Quick Presets:</span>
        <button
          type="button"
          className={`preset-chip ${eligibilityFilter === 'ELIGIBLE' ? 'active' : ''}`}
          onClick={() => setEligibilityFilter(eligibilityFilter === 'ELIGIBLE' ? 'all' : 'ELIGIBLE')}
        >
          <span>🎯 100% Eligible</span>
        </button>
        <button
          type="button"
          className={`preset-chip ${deadlineFilter === 'closing_soon' ? 'active' : ''}`}
          onClick={() => setDeadlineFilter(deadlineFilter === 'closing_soon' ? 'all' : 'closing_soon')}
        >
          <span>⏳ Closing Soon</span>
        </button>
        <button
          type="button"
          className={`preset-chip ${amountFilter === 50000 ? 'active' : ''}`}
          onClick={() => setAmountFilter(amountFilter === 50000 ? 0 : 50000)}
        >
          <span>💰 &gt; ₹50,000</span>
        </button>
        <button
          type="button"
          className={`preset-chip ${educationFilter === 'UG' ? 'active' : ''}`}
          onClick={() => setEducationFilter(educationFilter === 'UG' ? 'all' : 'UG')}
        >
          <span>🎓 College / UG</span>
        </button>
      </div>

      {/* Main Toolbar */}
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
          disabled={loading || refreshing || q.trim().length < 2}
        >
          Search Internet
        </button>

        {/* Filter Drawer Toggle */}
        <button
          type="button"
          className={`filter-toggle-btn ${activeFilterCount > 0 ? 'has-active' : ''}`}
          onClick={() => setShowFilterPanel(!showFilterPanel)}
          aria-expanded={showFilterPanel}
        >
          <Icon name="filter" size={16} />
          <span>Filters</span>
          {activeFilterCount > 0 && (
            <span className="filter-badge">{activeFilterCount}</span>
          )}
        </button>

        {/* Sort Dropdown */}
        <div className="sort-select-wrapper">
          <Icon name="sort" size={16} />
          <select
            value={sortBy}
            onChange={(event) => setSortBy(event.target.value)}
            aria-label="Sort scholarships"
          >
            <option value="best_match">Best Match</option>
            <option value="deadline_soon">Deadline (Closing soon)</option>
            <option value="deadline_late">Deadline (Furthest)</option>
            <option value="amount_high">Amount (Highest)</option>
            <option value="name_asc">Name (A - Z)</option>
          </select>
        </div>
      </form>

      {/* Expandable Advanced Filter Panel */}
      {showFilterPanel && (
        <div className="filter-panel">
          <div className="filter-panel-header">
            <h4>Refine Results</h4>
            {activeFilterCount > 0 && (
              <button
                type="button"
                className="text-btn"
                onClick={clearAllFilters}
              >
                Clear all filters
              </button>
            )}
          </div>

          <div className="filter-grid">
            <label className="filter-group">
              <span>Eligibility</span>
              <select
                value={eligibilityFilter}
                onChange={(e) => setEligibilityFilter(e.target.value)}
              >
                <option value="all">All Opportunities</option>
                <option value="ELIGIBLE">Eligible Only</option>
                <option value="NEEDS_VERIFICATION">Needs Verification</option>
                <option value="INELIGIBLE">Not Eligible</option>
              </select>
            </label>

            <label className="filter-group">
              <span>Min. Amount</span>
              <select
                value={amountFilter}
                onChange={(e) => setAmountFilter(Number(e.target.value))}
              >
                <option value={0}>Any Amount</option>
                <option value={25000}>₹25,000+</option>
                <option value={50000}>₹50,000+</option>
                <option value={100000}>₹1,00,000+</option>
              </select>
            </label>

            <label className="filter-group">
              <span>Category</span>
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
              >
                <option value="all">All Categories</option>
                <option value="GENERAL">General</option>
                <option value="OBC">OBC</option>
                <option value="SC">SC</option>
                <option value="ST">ST</option>
                <option value="EWS">EWS</option>
              </select>
            </label>

            <label className="filter-group">
              <span>Deadline</span>
              <select
                value={deadlineFilter}
                onChange={(e) => setDeadlineFilter(e.target.value)}
              >
                <option value="all">All Deadlines</option>
                <option value="active">Active Only (Unexpired)</option>
                <option value="closing_soon">Closing in 30 Days</option>
              </select>
            </label>

            <label className="filter-group">
              <span>Education Level</span>
              <select
                value={educationFilter}
                onChange={(e) => setEducationFilter(e.target.value)}
              >
                <option value="all">All Levels</option>
                <option value="UG">Undergraduate / College</option>
                <option value="PG">Postgraduate / Master's</option>
                <option value="SCHOOL">School (10th / 12th)</option>
              </select>
            </label>
          </div>
        </div>
      )}

      {/* Active Filter Chips */}
      {activeFilterCount > 0 && (
        <div className="active-filters-bar">
          <span className="active-filter-label">Active filters:</span>

          {eligibilityFilter !== 'all' && (
            <span className="filter-chip">
              Eligibility:{' '}
              {eligibilityFilter === 'ELIGIBLE'
                ? 'Eligible'
                : eligibilityFilter === 'NEEDS_VERIFICATION'
                ? 'Needs Verification'
                : 'Not Eligible'}
              <button
                type="button"
                onClick={() => setEligibilityFilter('all')}
                aria-label="Remove eligibility filter"
              >
                <Icon name="close" size={12} />
              </button>
            </span>
          )}

          {amountFilter > 0 && (
            <span className="filter-chip">
              Min. ₹{amountFilter.toLocaleString('en-IN')}+
              <button
                type="button"
                onClick={() => setAmountFilter(0)}
                aria-label="Remove amount filter"
              >
                <Icon name="close" size={12} />
              </button>
            </span>
          )}

          {categoryFilter !== 'all' && (
            <span className="filter-chip">
              Category: {categoryFilter}
              <button
                type="button"
                onClick={() => setCategoryFilter('all')}
                aria-label="Remove category filter"
              >
                <Icon name="close" size={12} />
              </button>
            </span>
          )}

          {deadlineFilter !== 'all' && (
            <span className="filter-chip">
              Deadline:{' '}
              {deadlineFilter === 'active' ? 'Active only' : 'Closing in 30 days'}
              <button
                type="button"
                onClick={() => setDeadlineFilter('all')}
                aria-label="Remove deadline filter"
              >
                <Icon name="close" size={12} />
              </button>
            </span>
          )}

          {educationFilter !== 'all' && (
            <span className="filter-chip">
              Level:{' '}
              {educationFilter === 'UG'
                ? 'Undergraduate'
                : educationFilter === 'PG'
                ? 'Postgraduate'
                : 'School'}
              <button
                type="button"
                onClick={() => setEducationFilter('all')}
                aria-label="Remove education level filter"
              >
                <Icon name="close" size={12} />
              </button>
            </span>
          )}

          <button
            type="button"
            className="chip-clear-all"
            onClick={clearAllFilters}
          >
            Clear all
          </button>
        </div>
      )}

      {/* Results Header Info & Cache status */}
      <div className="search-status-bar">
        <div className="muted">
          {mode === 'keyword' && activeQuery
            ? `Internet search: "${activeQuery}"`
            : 'Showing scholarships discovered for your student profile.'}
        </div>

        <div className="status-badges">
          {isCached && (
            <span className="cache-pill" title="Results loaded instantly from smart cache">
              <Icon name="zap" size={13} />
              Cached for speed
            </span>
          )}
        </div>
      </div>

      {loading ? (
        <div className="card-grid">
          {[1, 2, 3, 4, 5, 6].map((number) => (
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
                ? () => searchByKeyword(null, true)
                : () => findScholarships(true)
            }
          >
            Try again
          </button>
        </div>
      ) : filteredAndSorted.length > 0 ? (
        <>
          <div className="results-count-bar">
            <p className="muted">
              Showing <strong>{visibleScholarships.length}</strong> of{' '}
              <strong>{filteredAndSorted.length}</strong> matching opportunities
              {items.length !== filteredAndSorted.length && (
                <span> ({items.length - filteredAndSorted.length} filtered out)</span>
              )}
            </p>
          </div>

          <div className="card-grid">
            {visibleScholarships.map((item, index) => {
              const normalizedItem = {
                ...item,
                name: item.name || item.title || 'Scholarship opportunity',
                source_url: item.source_url || item.url || '',
                eligibility_status:
                  item.eligibility_status ||
                  item.status ||
                  (mode === 'keyword' ? 'NEEDS_VERIFICATION' : undefined),
              };

              const itemId = item.id || item._id || item.scholarship_id;
              const itemUrl = item.source_url || item.url;
              const isItemSaved = Boolean(
                (itemId && savedIds?.has(String(itemId).trim())) ||
                (itemUrl && savedIds?.has(String(itemUrl).trim()))
              );

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
                  saved={isItemSaved}
                />
              );
            })}
          </div>

          {/* Pagination Controls */}
          {hasMore && (
            <div className="pagination-bar">
              <button
                type="button"
                className="secondary-btn"
                onClick={() => setVisibleCount((prev) => prev + PAGE_SIZE)}
              >
                Load more opportunities (+{Math.min(PAGE_SIZE, filteredAndSorted.length - visibleCount)})
              </button>
              <button
                type="button"
                className="text-btn"
                onClick={() => setVisibleCount(filteredAndSorted.length)}
                style={{ marginLeft: '16px' }}
              >
                Show all ({filteredAndSorted.length})
              </button>
            </div>
          )}
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
            {activeFilterCount > 0
              ? 'No opportunities match your current combination of filters. Try clearing some filters.'
              : mode === 'keyword'
              ? 'Try different keywords, such as your course, state, category, or scholarship type.'
              : 'Search for scholarships matched to your profile or use custom keywords.'}
          </p>

          {activeFilterCount > 0 ? (
            <button
              type="button"
              className="primary-btn"
              onClick={clearAllFilters}
            >
              Clear filters
            </button>
          ) : (
            <button
              type="button"
              className="primary-btn"
              onClick={() => findScholarships(true)}
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
