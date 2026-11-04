# Scholar AI — Complete Technical Interview Guide & Mentor Prep

This guide is designed for technical interviews, system design discussions, portfolio presentations, and code walkthroughs for **Scholar AI**. All explanations, pitches, and answers are directly grounded in the actual codebase.

---

## 1. Project Pitches

### 30-Second Elevator Pitch
> *"Scholar AI is an AI-powered scholarship discovery and eligibility matching platform designed for Indian college students. Instead of students spending dozens of hours manually browsing through hundreds of scholarship websites and confusing criteria PDFs, Scholar AI automatically parses their academic, financial, and demographic profile, searches official government and private portals in real time, evaluates them against a 9-rule deterministic eligibility engine with zero AI hallucinations, and lets them track their applications all in one modern dashboard."*

### 1-Minute Pitch
> *"Finding scholarships in India is difficult and fragmented. Official portals like the National Scholarship Portal (NSP), state portals like MahaDBT, and private trusts like Tata and Reliance all have different eligibility rules, income caps, and deadlines scattered across the web. Many students miss out simply because they don't know they qualify.
>
> I built Scholar AI using FastAPI, React, and MongoDB to solve this. When a student enters their degree, state, category, income, and GPA, our backend generates personalized search strategies, crawls verified web pages, extracts award amounts and deadlines while filtering out junk articles, and feeds them into our 9-rule deterministic eligibility engine. Students see transparent Pass/Fail reasons for each requirement with a provisional match score, can bookmark opportunities, and can track application milestones from submission to award."*

### 2-Minute Architectural Pitch
> *"Scholar AI is architected as an asynchronous, decoupled full-stack platform built with Python FastAPI, MongoDB Atlas, and React with Vite.
>
> On the frontend, we built a modern SaaS interface styled after Linear and Stripe using Plus Jakarta Sans, glassmorphism, responsive drawers, and optimistic UI updates for instant bookmarking and application tracking.
>
> On the backend, we prioritized two core engineering principles: accuracy and zero hallucinations. For scholarship discovery, we dispatch dynamic search queries via the Serper Google Search API, crawl source pages, and extract data using specialized heuristics that handle Indian currency denominations like Lakhs and Crores while rejecting false positives such as application fees.
>
> For matching, rather than using an unpredictable LLM that could hallucinate eligibility, we designed a deterministic 9-rule evaluation engine. It handles Indian course synonym clusters, state domicile boundaries, reservation categories, and automatic bi-directional conversions between CGPA and percentage using the AICTE 9.5 multiplier.
>
> To optimize performance and reduce third-party API costs, we implemented a two-tier caching architecture with in-memory L1 and MongoDB TTL L2 caching with a circuit breaker. Security features include Argon2/Bcrypt multi-hasher password authentication with transparent legacy re-hashing and 7-day HS256 JWT tokens."*

---

## 2. Core Technical Questions & Detailed Answers

### Q1: Why did you choose FastAPI over Flask or Django?
**Answer**:
- **Native Asynchronous Performance**: FastAPI is built on Starlette and Uvicorn with native `async`/`await` support, making it significantly faster and better suited for I/O-bound tasks like web crawling, external API requests, and database operations.
- **Pydantic v2 Type Safety**: Request validation, schema enforcement, and JSON serialization happen automatically through type hints. Invalid request payloads are rejected with descriptive 422 errors before reaching the business logic.
- **Automated OpenAPI / Swagger Documentation**: FastAPI generates interactive API documentation at `/docs` out of the box directly from Python type annotations, accelerating frontend-backend integration.

### Q2: Why did you use MongoDB instead of a Relational Database (PostgreSQL/MySQL)?
**Answer**:
- **Schema Flexibility for Web-Extracted Data**: Pre-ingested government schemes and scraped web scholarships have heterogeneous structures. Some provide explicit income caps, others specify course lists, and some only have free-text benefits. A document database (MongoDB) easily accommodates dynamic fields and embedded structures without complex multi-table joins or schema migrations.
- **TTL Indexing**: MongoDB natively supports automated Time-To-Live (TTL) expiration on collections (`search_cache`), enabling cache records to be deleted automatically by the database engine without needing external cron jobs or Redis instances.
- **Developer Velocity**: JSON documents map directly to Python dictionaries and Pydantic models.

### Q3: Why is the Eligibility Engine deterministic instead of using an LLM?
**Answer**:
- **Zero Hallucination Guarantee**: In scholarship applications, falsely telling a student they are eligible—or falsely telling them they are ineligible—has real financial consequences. LLMs can hallucinate dates, income caps, or criteria.
- **Explainability**: Our deterministic engine provides a discrete `PASS`, `FAIL`, or `UNKNOWN` verdict for every individual rule (Income, Age, Category, Domicile, Score, Course, Gender, Disability) along with an explicit human-readable reason.
- **Auditability & Speed**: The engine executes in under 2 milliseconds without latency, token costs, or rate limits.

### Q4: How does your password hashing handle legacy Bcrypt and modern Argon2?
**Answer**:
- In [`backend/app/core/security.py`](file:///d:/Scholar AI/backend/app/core/security.py), we configured a multi-hasher `PasswordHash((Argon2Hasher(), BcryptHasher()))`.
- When a user logs in, `verify_password` tests Argon2 first, falls back to direct `bcrypt.checkpw()` if the hash starts with `$2a$` or `$2b$`, and handles any unrecognized hashes safely without throwing unhandled exceptions.
- **Transparent Migration**: Upon a successful login with an older Bcrypt hash, `login_user` automatically hashes the plain password with Argon2 and updates the database record in the background without requiring user intervention.

### Q5: How does the system prevent the ₹2 scholarship amount bug?
**Answer**:
- In [`backend/app/services/scholarship_extraction_service.py`](file:///d:/Scholar AI/backend/app/services/scholarship_extraction_service.py), the `find_amount()` function:
  1. Searches within a context window of 120 characters around explicit award keywords (`stipend of`, `scholarship amount`, `financial assistance`).
  2. Actively disqualifies numbers attached to application fees, exam fees, or family income caps (`application fee`, `cost of form`).
  3. Enforces a sanity threshold: raw standalone numbers under ₹500 that lack unit multipliers (`Lakh`, `Crore`, `Thousand`) are rejected as noise or UI fragments.

---

## 3. Real Debugging Stories & Technical Challenges

### Story 1: The `UnknownHashError` HTTP 500 Crash on Login
- **The Symptom**: Existing users attempting to log in received an HTTP 500 Internal Server Error.
- **The Investigation**: Inspecting the exception logs revealed `pwdlib.exceptions.UnknownHashError`. The newly configured `PasswordHash.recommended()` only knew Argon2, so when an existing user with a `$2b$` Bcrypt hash logged in, `pwdlib` crashed instead of returning `False`.
- **The Fix**: Updated `security.py` to register both `Argon2Hasher` and `BcryptHasher`, wrapped verification in safe exception handling, and implemented transparent re-hashing to Argon2 upon successful login.

### Story 2: The 55% Profile Strength Discrepancy
- **The Symptom**: A user completed all fields in their profile, but the dashboard progress meter showed only 55%.
- **The Investigation**: We audited `calculateProfileScore` against `Profile.jsx` and found attribute name mismatches:
  - Form saved `annual_family_income`, but calculator checked `family_income`.
  - Form saved `domicile_state` / `state`, but calculator checked `state_of_domicile`.
  - Form saved `score`, but calculator checked `academic_percentage`.
  The calculator was skipping those 3 fields ($15\% + 15\% + 15\% = 45\%$), yielding exactly $100\% - 45\% = 55\%$.
- **The Fix**: Refactored `calculateProfileScore` in [`frontend/src/pages/Dashboard.jsx`](file:///d:/Scholar AI/frontend/src/pages/Dashboard.jsx) to check all current and legacy attribute aliases, accurately reflecting 100% completion.

### Story 3: Windows Python TLS Certificate Failure on MongoDB Atlas
- **The Symptom**: Connecting to MongoDB Atlas on Windows threw `ServerSelectionTimeoutError: [SSL: CERTIFICATE_VERIFY_FAILED]`.
- **The Investigation**: Python on Windows does not automatically read root certificates from the Windows Certificate Store, failing the TLS handshake to MongoDB Atlas Let's Encrypt / DigiCert intermediate certificates.
- **The Fix**: Imported `certifi` in [`backend/app/database/connection.py`](file:///d:/Scholar AI/backend/app/database/connection.py) and injected `tlsCAFile=certifi.where()` into `MongoClient` configuration.

---

## 4. Scalability & System Evolution

### If 100,000 students join tomorrow, what breaks first and how do you fix it?
1. **Live Web Scraping Bottleneck**:
   - *Problem*: Live scraping via Serper and requests in the synchronous request cycle will exhaust memory and third-party rate limits.
   - *Solution*: Move scraping to a distributed background worker queue using **Celery** or **ARQ** with **Redis**. Background workers crawl and update scholarship repositories asynchronously; API endpoints serve instant results from indexed database collections.
2. **Database Read Load**:
   - *Problem*: High read traffic on student queries.
   - *Solution*: Deploy Redis for fast L1 caching, configure MongoDB Atlas read replicas with `secondaryPreferred` read preferences, and ensure compound indexes on `(user_id, scholarship_id)`.
3. **Stateless Horizontally Scaled FastAPIs**:
   - *Advantage*: Since JWTs are stateless and database connections are pooled, backend instances can scale horizontally across Kubernetes pods or Render autoscaling nodes behind a load balancer without sticky sessions.
