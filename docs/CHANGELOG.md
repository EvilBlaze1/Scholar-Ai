# Scholar AI — Changelog & Milestone History

All notable changes, architectural milestones, bug fixes, and feature additions to the **Scholar AI** platform are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.1.0] - 2026-11-04 (Current Production-Ready State)

### Added
- **53-Test Automated Regression Suite**: Added comprehensive unit and integration tests across:
  - `test_auth_security.py` & `test_auth_login_resilience.py`: Multi-hasher verification (Argon2id + legacy Bcrypt), 3-tier email normalization, duplicate registration protection.
  - `test_eligibility_engine_enhancements.py`: 9-rule evaluation, course synonym clustering, CGPA $\times 9.5 \leftrightarrow \%$ conversion, boundary conditions.
  - `test_scholarship_extraction.py`: Serper snippet parsing, Lakh/Crore amount parser, junk domain blacklist, deadline extraction, rejection of $< ₹500$ false positives.
  - `test_search_cache.py`: L1 in-memory LRU + L2 MongoDB TTL index, deterministic SHA-256 cache key generation, circuit-breaker fallback on DB outage.
  - `test_saved_scholarships_api.py` & `test_saved_repository_duplicates.py`: Save/unsave lifecycle, compound unique index deduplication, per-user privacy isolation.
  - `test_application_service.py` & `test_dashboard_deadlines.py`: Application state machine (DRAFT $\to$ APPLIED $\to$ UNDER_REVIEW $\to$ ACCEPTED/REJECTED $\to$ AWARDED), deadline parsing, urgent deadline dashboard calculation.
- **Enterprise Documentation Suite**:
  - `docs/ARCHITECTURE.md`: Complete system architecture with 7 Mermaid diagrams.
  - `docs/DATABASE_DOCUMENTATION.md`: MongoDB schema documentation, collection models, compound indexes, and entity-relationship models.
  - `docs/API_DOCUMENTATION.md`: Exhaustive reference of all 12 backend routers and endpoints.
  - `docs/INTERVIEW_PREPARATION.md`: 30s/1m/2m elevator pitches, technical Q&A, and 3 production debugging case studies.
  - `docs/SETUP_AND_DEPLOYMENT.md`: Step-by-step local development setup on Windows 11 and production deployment on Render & Vercel.
  - `docs/SCHOLAR_AI_COMPLETE_DOCUMENTATION.md`: 24-chapter master documentation guide.

### Fixed
- **Bcrypt Hash Format Crash (`UnknownHashError`)**: Upgraded `backend/app/core/security.py` to use a dual-hasher `PasswordHash((Argon2Hasher(), BcryptHasher()))` with a raw `bcrypt.checkpw` fallback to safely authenticate legacy `$2b$` password hashes and seamlessly upgrade them to Argon2id on successful login.
- **Case-Sensitive & Whitespace Email Login Failures**: Enforced whitespace trimming and lowercase conversion in Pydantic schemas, and implemented a 3-tier database lookup in `user_repository.py` (Exact $\to$ Lowercase $\to$ Case-Insensitive Regex).
- **Windows TLS / SSL Verification Handshake (`SSL: CERTIFICATE_VERIFY_FAILED`)**: Injected `certifi.where()` as `tlsCAFile` into PyMongo's `MongoClient` in `backend/app/database/connection.py`.
- **Duplicate Desktop Navigation Bar**: Removed `<nav className="mobile-bottom-nav">` from `frontend/src/components/Layout.jsx` and eliminated bottom padding reserved in `frontend/src/App.css`.
- **Profile Strength Calculation Bug**: Fixed `calculateProfileScore` in `frontend/src/pages/Dashboard.jsx` to check both new and legacy field alias names (`annual_family_income`, `family_income`, `domicile_state`, `state_of_domicile`, `score`, `academic_percentage`), correctly restoring 100% completion scores for fully populated student profiles.
- **Serper Extractor False-Positive Minimum Rule**: Added a ₹500 floor check in `scholarship_extraction_service.py` to reject erroneous ₹2 extractions caused by stray numbers like "Part 2" or "Section 2".

### Changed
- **Frontend UI Redesign (Concept 1: Modern Clean SaaS / Linear & Stripe Style)**:
  - Deep dark slate palette (`#0B0F19`, `#111827`, `#1F2937`) with electric indigo/violet gradients (`#6366F1` $\to$ `#8B5CF6`).
  - Glassmorphic translucent cards with subtle borders (`rgba(255,255,255,0.08)`).
  - Clean monospace badge typography for match percentages, eligibility tags, and deadline countdowns.
  - Responsive collapsible sidebar with smooth micro-interactions.

---

## [2.0.0] - 2026-10-19 (Live Scholarship Discovery & Production Logging)

### Added
- **Serper Google Search Integration**: Implemented `backend/app/search/web_search.py` and `scholarship_search_service.py` to query live scholarship data via Serper API.
- **Web Extraction & Normalization Pipeline**: Implemented `scholarship_extraction_service.py` to scrape and parse scholarship HTML/snippets with BeautifulSoup4.
- **Two-Tier Search Cache**: Introduced `search_cache.py` to cache Serper search query results (L1 in-memory + L2 MongoDB TTL index) to minimize API latency and quota consumption.
- **Discovery Error Logging**: Added structured logging for scholarship discovery pipeline failures (`51731a0`, `3f27db6`).

### Fixed
- **CORS Allowed Origins**: Updated `backend/app/main.py` to allow requests from deployed Vercel frontend domains (`c086de8`, `eb1e467`).

---

## [1.1.0] - 2026-10-14 (Deployment Preparation & Cloud Config)

### Added
- Production deployment configuration for Render (FastAPI backend) and Vercel (React Vite frontend) (`11003d5`).
- Environment variable configuration templates (`.env.example`).
- MongoDB Atlas cloud connection string integration.

---

## [1.0.0] - 2026-10-04 (Core Backend & Eligibility Rule Engine)

### Added
- **FastAPI Application Initialization**: Set up main application with modular router architecture (`b6aefcc`).
- **Deterministic Eligibility Engine**: Implemented `eligibility_engine.py` evaluating 9 criteria (Income, Category, State, Education, Course, Score, Age, Gender, Disability).
- **Provisional Match Scoring Algorithm**: Implemented `matching_service.py` computing normalized match score $\frac{\text{passed}}{\text{evaluated}} \times 100$ and sorting by status priority (`ELIGIBLE` $\to$ `NEEDS_VERIFICATION` $\to$ `INELIGIBLE`).
- **Student Profile Management**: Added CRUD operations for student profiles in `student_repository.py`.
- **JWT Authentication**: Implemented user signup and login with JWT bearer tokens.

---

## [0.1.0] - 2026-10-03 (Initial Repository Inception)

### Added
- Project initialization with React (Vite) frontend and FastAPI backend (`2569315`).
- Initial folder layout (`frontend/`, `backend/`, `docs/`).
- Initial Pydantic schemas and database connection stubs.
