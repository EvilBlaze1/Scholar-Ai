# Scholar AI — AI-Powered Scholarship Discovery & Eligibility Matching

[![React 18](https://img.shields.io/badge/Frontend-React%2018%20%7C%20Vite%205-61DAFB?style=flat-square&logo=react)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%200.115+-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python)](https://python.org/)
[![MongoDB Atlas](https://img.shields.io/badge/Database-MongoDB%20Atlas-47A248?style=flat-square&logo=mongodb)](https://www.mongodb.com/atlas)
[![Tests Passing](https://img.shields.io/badge/Tests-53%20Passed-success?style=flat-square&logo=pytest)](https://docs.pytest.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

> **Scholar AI** is an intelligent, full-stack web platform built for Indian college students to discover, evaluate, and track higher education scholarships. By pairing **real-time Google Serper search** and **automated web scraping** with a **transparent, deterministic 9-point rule evaluation engine**, Scholar AI eliminates information asymmetry, rejects spam and clickbait portals, and provides students with clear eligibility breakdowns and application tracking.

---

## Key Highlights

- **Live Web Discovery:** Queries live public web sources using Google Serper API with personalized student demographic and academic queries.
- **Smart Rupee Extraction & Cleaning:** Intelligently extracts stipend amounts (parsing Lakhs and Crores) with a ₹500 minimum floor guard to reject spurious false positives, filtering out junk commercial domains.
- **Deterministic 9-Rule Engine:** Evaluates income, social category, state domicile, education level, course synonyms (e.g. B.Tech $\leftrightarrow$ Engineering), academic cutoffs (with CGPA $\times 9.5 \leftrightarrow \%$ conversion), age limits, gender quotas, and disability status.
- **Explainable Match Scoring:** Computes an auditable match score ($\frac{\text{Passed}}{\text{Evaluated}} \times 100$) and prioritizes verified opportunities without "black-box" hallucinations.
- **Linear & Stripe SaaS Aesthetic:** Modern dark UI (`#0B0F19`, `#111827`) featuring electric violet accents, glassmorphic translucent panels, and responsive desktop/mobile views.
- **Private Persistence:** Bookmark opportunities and manage application lifecycles (`DRAFT` $\to$ `APPLIED` $\to$ `UNDER_REVIEW` $\to$ `ACCEPTED` / `REJECTED` $\to$ `AWARDED`) stored in MongoDB Atlas with compound uniqueness guarantees.
- **Dual-Hasher Security:** State-of-the-art Argon2id hashing with automatic migration fallback for legacy Bcrypt hashes and stateless 7-day JWT tokens.

---

## System Architecture

```
   +-----------------------------------------------------------+
   |             React 18 SPA (Vite 5) [Vercel]                |
   | - Linear/Stripe Dark SaaS UI | React Router v6 | Context |
   +-----------------------------+-----------------------------+
                                 | HTTPS REST (JSON + JWT)
                                 v
   +-----------------------------------------------------------+
   |               FastAPI Backend [Render]                    |
   | - 12 Routers | Lifespan Lifecycle | CORS Security        |
   +-----------------------------+-----------------------------+
                                 |
        +------------------------+------------------------+
        |                                                 |
        v                                                 v
+-------------------------------+             +---------------------------+
|    Domain Services            |             |   Data Repositories       |
| - 9-Point Rule Engine         |             | - PyMongo + TLS CA        |
| - Proportional Match Scoring  |             | - Compound Unique Indexes |
| - HTML Scraper & Rupee Parser |             +-------------+-------------+
| - Two-Tier Cache (L1/L2)      |                           |
+---------------+---------------+                           v
                |                             +---------------------------+
                v                             |    MongoDB Atlas Cloud    |
+-------------------------------+             | (Users, Students, Saved,  |
|   Serper Google Search API    |             |  Applications, Cache)     |
+-------------------------------+             +---------------------------+
```

---

## Project Structure

```
Scholar AI/
├── backend/                       # FastAPI Python Backend
│   ├── app/
│   │   ├── api/                   # 12 Modular REST Routers
│   │   ├── core/                  # Security (Argon2/JWT), Config, Search Cache
│   │   ├── database/              # Repositories & MongoDB Connection
│   │   ├── models/                # Domain & Database Models
│   │   ├── schemas/               # Pydantic DTOs & Validation
│   │   ├── search/                # Serper Search API Client
│   │   ├── services/              # Rule Engine, Scraper, Matching Services
│   │   └── main.py                # App Initialization & Lifespan
│   ├── tests/                     # 53 Automated Pytest Tests
│   └── requirements.txt           # Python Dependencies
│
├── frontend/                      # React Vite Frontend
│   ├── src/
│   │   ├── components/            # Layout, ScholarshipCard, SVG Icons
│   │   ├── context/               # AuthContext State
│   │   ├── pages/                 # Dashboard, Scholarships, Saved, Applications, Profile
│   │   ├── services/              # API Client (api.js)
│   │   ├── App.css                # Modern Linear/Stripe CSS System
│   │   └── main.jsx               # Application Entry Point
│   └── package.json               # Node Dependencies
│
└── docs/                          # Comprehensive Technical Documentation
    ├── SCHOLAR_AI_COMPLETE_DOCUMENTATION.md # 24-Chapter Master Document
    ├── ARCHITECTURE.md            # System Architecture & 7 Mermaid Diagrams
    ├── DATABASE_DOCUMENTATION.md  # MongoDB Atlas Schemas & ER Models
    ├── API_DOCUMENTATION.md       # 12-Router REST Endpoint Reference
    ├── INTERVIEW_PREPARATION.md   # Pitches, Technical Q&A & Debugging Stories
    ├── SETUP_AND_DEPLOYMENT.md    # Windows 11 & Cloud Deployment Guide
    └── CHANGELOG.md               # Version History & Milestones
```

---

## Quickstart Guide

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- MongoDB Atlas cluster connection string

### 2. Backend Setup
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Run automated tests to verify setup
pytest -v

# Start FastAPI development server
uvicorn app.main:app --reload --port 8000
```
API Documentation will be live at `http://127.0.0.1:8000/docs`.

### 3. Frontend Setup
```powershell
cd frontend
npm install
npm run dev
```
Open your browser to `http://localhost:5173`.

---

## Automated Test Suite

Scholar AI maintains a complete automated test suite verifying all core algorithms, security mechanisms, and persistence layers:

```powershell
pytest backend/tests/ -v
```
```
============================== 53 passed in 4.82s ==============================
```

Tests cover:
- Password security: Argon2id verification, legacy Bcrypt auto-upgrade, 3-tier email normalization.
- Rule engine: 9 rules, course synonym clustering, CGPA to percentage conversion.
- Extractor: Rupee parsing with Lakhs/Crores, blacklist domain scrubbing, false positive rejection.
- Two-tier cache: Deterministic SHA-256 keys, L1 in-memory + L2 MongoDB TTL index.
- Saved & Application repositories: Compound unique deduplication, user isolation, state transitions.

---

## Comprehensive Documentation Directory

Explore the complete technical documentation suite in the [`docs/`](file:///d:/Scholar%20AI/docs) folder:

- **[Master Documentation](file:///d:/Scholar%20AI/docs/SCHOLAR_AI_COMPLETE_DOCUMENTATION.md):** 24 exhaustive chapters covering every aspect of the project.
- **[System Architecture](file:///d:/Scholar%20AI/docs/ARCHITECTURE.md):** Architectural patterns, layer responsibilities, and 7 Mermaid sequence & flow diagrams.
- **[Database Documentation](file:///d:/Scholar%20AI/docs/DATABASE_DOCUMENTATION.md):** Detailed MongoDB collection schemas, compound indexes, and BSON representations.
- **[API Reference](file:///d:/Scholar%20AI/docs/API_DOCUMENTATION.md):** All 12 backend routers and 32 REST endpoints with request/response schemas.
- **[Interview Preparation](file:///d:/Scholar%20AI/docs/INTERVIEW_PREPARATION.md):** 30s/1m/2m pitches, in-depth architectural Q&A, and 3 production debugging case studies.
- **[Setup & Deployment Guide](file:///d:/Scholar%20AI/docs/SETUP_AND_DEPLOYMENT.md):** Step-by-step Windows 11 setup and Render/Vercel production deployment.
- **[Changelog](file:///d:/Scholar%20AI/docs/CHANGELOG.md):** Development history, release milestones, and bug fixes.

---

## License & Credits

Built with dedication to empower Indian students with fair and accessible educational financing.  
Licensed under the [MIT License](LICENSE).
