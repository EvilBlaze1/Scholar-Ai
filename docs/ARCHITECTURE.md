# Scholar AI — System Architecture & Workflow Specifications

This document outlines the software architecture, data flow pipelines, component responsibilities, and process workflows for **Scholar AI**, an AI-assisted scholarship discovery and eligibility matching platform for Indian college students.

---

## 1. High-Level System Architecture

Scholar AI follows a decoupled Client-Server architecture with a single-page React frontend, an asynchronous FastAPI REST backend, a managed MongoDB Atlas cloud database, and external search and crawling services.

```mermaid
flowchart TB
    subgraph Client["Frontend Client (React + Vite)"]
        UI["UI Layer\n(Plus Jakarta Sans / Linear SaaS Style)"]
        State["State Management\n(React Hooks & Local Storage)"]
        AxiosClient["API Client (Axios Interceptors)\nBearer JWT Auth"]
    end

    subgraph CDN["Edge & Static Hosting"]
        Vercel["Vercel Edge Network\n(Frontend SPA Hosting)"]
    end

    subgraph Backend["FastAPI Backend (Render Cloud Platform)"]
        RouterLayer["API Router Layer (12 Endpoints)\nFastAPI & Pydantic v2"]
        SecurityLayer["Security & Auth Middleware\nHS256 JWT & Argon2/Bcrypt"]
        ServiceLayer["Service Layer\n(Business Logic, Rule Engine, Search)"]
        RepoLayer["Repository Layer\n(PyMongo Data Access Objects)"]
        CacheLayer["L1 In-Memory + L2 MongoDB Cache\n(TTL & Circuit Breaker)"]
    end

    subgraph DataStore["Cloud Data Store"]
        Atlas[("MongoDB Atlas Cloud Database\n(6 Collections, PyMongo)")]
    end

    subgraph External["External Cloud APIs & Web"]
        SerperAPI["Google Serper.dev API\n(Live Organic Search)"]
        TargetWeb["Scholarship Webpages\n(HTTP Scrape / BeautifulSoup4)"]
    end

    Vercel -.-> UI
    UI --> State
    State --> AxiosClient
    AxiosClient -- "HTTPS / JSON\nCORS Whitelisted" --> RouterLayer
    RouterLayer --> SecurityLayer
    RouterLayer --> ServiceLayer
    ServiceLayer --> CacheLayer
    ServiceLayer --> RepoLayer
    ServiceLayer -- "Query Dispatch" --> SerperAPI
    ServiceLayer -- "Webpage Retrieval" --> TargetWeb
    RepoLayer --> Atlas
    CacheLayer -. "L2 Persistent Cache" .-> Atlas
```

---

## 2. Frontend-Backend Communication Flow

The frontend communicates with the backend exclusively via RESTful HTTPS requests using Axios with Bearer token authorization interceptors.

```mermaid
sequenceDiagram
    autonumber
    actor Student as Student (Browser)
    participant React as React Frontend (Vite)
    participant Axios as Axios Interceptor (client.js)
    participant FastAPI as FastAPI Router (/api)
    participant AuthSec as Auth & Security (security.py)
    participant Service as Business Service Layer
    participant Mongo as MongoDB Atlas (PyMongo)

    Student->>React: Action (e.g. "Save Scholarship")
    React->>Axios: POST /saved-scholarships/
    Note over Axios: Reads 'scholar_token' from localStorage
    Axios->>FastAPI: HTTP POST + Headers (Authorization: Bearer <token>)
    FastAPI->>AuthSec: decode_access_token(token)
    alt Token Invalid or Expired
        AuthSec-->>FastAPI: None
        FastAPI-->>Axios: HTTP 401 Unauthorized
        Axios-->>React: Interceptor clears token
        React-->>Student: Redirects to Auth Screen
    else Token Valid
        AuthSec-->>FastAPI: user_id: "6724..."
        FastAPI->>Service: add_saved_scholarship(user_id, scholarship_id)
        Service->>Mongo: saved_scholarships.update_one(...)
        Mongo-->>Service: WriteResult(upserted)
        Service-->>FastAPI: Saved record dict
        FastAPI-->>Axios: HTTP 200 OK + JSON
        Axios-->>React: Response Data
        React-->>Student: Update UI State & Show Toast Notification
    end
```

---

## 3. Authentication & Session Flow

Scholar AI uses JSON Web Tokens (JWT) signed with the HMAC-SHA256 algorithm. Password security utilizes a resilient multi-hasher architecture combining modern Argon2 with legacy Bcrypt fallback and automatic password rehashing.

```mermaid
sequenceDiagram
    autonumber
    actor User as User
    participant AuthUI as Auth.jsx
    participant AuthRouter as /auth/login (FastAPI)
    participant AuthService as auth_service.py
    participant UserRepo as user_repository.py
    participant Security as security.py (Argon2 / Bcrypt)
    participant DB as users collection (MongoDB)

    User->>AuthUI: Enters Email & Password
    Note over AuthUI: Normalizes email (trim & lowercase)
    AuthUI->>AuthRouter: POST /auth/login {email, password}
    AuthRouter->>AuthService: login_user(email, password)
    AuthService->>UserRepo: get_user_by_email(clean_email)
    Note over UserRepo: 3-Tier Case-Insensitive Lookup:\n1. Exact -> 2. Lowercase -> 3. Regex ^email$
    UserRepo->>DB: find_one({"email": ...})
    DB-->>UserRepo: User Record (with password_hash)
    UserRepo-->>AuthService: user dict

    AuthService->>Security: verify_password(plain, stored_hash)
    Note over Security: Tries Argon2Hasher,\nthen direct Bcrypt checkpw fallback ($2b$)
    alt Password Mismatch
        Security-->>AuthService: False
        AuthService-->>AuthRouter: None
        AuthRouter-->>AuthUI: HTTP 401 "Invalid email or password"
    else Password Match
        Security-->>AuthService: True
        opt Legacy Bcrypt Detected
            AuthService->>Security: hash_password(plain) [Argon2]
            AuthService->>UserRepo: update_user_password(user_id, new_argon2_hash)
            UserRepo->>DB: update_one(...)
        end
        AuthService->>Security: create_access_token(user_id)
        Security-->>AuthService: JWT Token String (HS256, 7 Days Exp)
        AuthService-->>AuthRouter: {access_token, token_type, user: {id, email}}
        AuthRouter-->>AuthUI: HTTP 200 OK + Tokens
        Note over AuthUI: Sets localStorage: scholar_token, scholar_email
        AuthUI->>User: Renders Dashboard
    end
```

---

## 4. Scholarship Discovery & Web Extraction Pipeline

The scholarship discovery pipeline enables students to find live Indian scholarship opportunities.

```mermaid
flowchart TD
    Start([Student Requests Discovery]) --> FetchProfile[Fetch Student Profile from MongoDB]
    FetchProfile --> BuildQueries[Generate Personalized Queries\nbuild_search_queries()]
    
    subgraph QueryBuilder["Personalized Search Strategy"]
        Q1["Course + State (e.g. B.Tech scholarships Maharashtra India)"]
        Q2["Course + Category (e.g. B.Tech OBC scholarships India)"]
        Q3["Specialization (e.g. Computer Science scholarships India)"]
        Q4["Gender Specific (e.g. Women girls scholarships B.Tech India)"]
    end
    BuildQueries --> QueryBuilder

    QueryBuilder --> CacheCheck{Check Search Cache\nL1 Memory / L2 MongoDB}
    CacheCheck -- Cache Hit --> ServeCache[Return Cached & Evaluated Results]
    
    CacheCheck -- Cache Miss --> SearchDispatch[Dispatch Search Queries to Serper.dev API]
    SearchDispatch --> DeduplicateURLs[Normalize & Deduplicate URLs\nFilter Out Junk & Video Domains]
    
    DeduplicateURLs --> ScrapePages[Webpage Reader Service\nFetch Live HTML Text]
    
    subgraph Extraction["Extraction & Normalization Service"]
        ExtName[Extract Scholarship Name & Provider]
        ExtAmount[find_amount: Parse Rupees, Lakhs, Crores\nFilter Out False Positives & Small Fees]
        ExtDeadline[find_deadline: Parse Indian & ISO Dates\nAssociate with Deadline Keywords]
        ExtRules[web_eligibility_parser: Extract Criteria Sentences]
        ExtTrust[get_trust_level: Check Official Domains (.gov.in, .nic.in, etc.)]
    end
    
    ScrapePages --> Extraction
    Extraction --> ConvertSchema[convert_web_scholarship_to_schema()]
    ConvertSchema --> EvalEngine[Eligibility Evaluation Engine]
    EvalEngine --> CalcScore[calculate_match_score(): Rule-Match %]
    CalcScore --> RankSort[Sort: Status Priority > Match Score > Deadline]
    RankSort --> StoreCache[Store in Cache TTL=1800s]
    StoreCache --> OutputJSON([Return Personalized Results to Frontend])
```

---

## 5. Eligibility Rule Engine Workflow

The eligibility engine evaluates student data against scholarship requirements across 9 distinct criteria.

```mermaid
flowchart LR
    subgraph Inputs
        SData["Student Profile\n- Income\n- Category\n- State\n- Education Level\n- Course\n- Score & Score Type\n- Date of Birth\n- Gender\n- Disability"]
        SchData["Scholarship Criteria\n- Max Family Income\n- Eligible Categories\n- Eligible States\n- Education Levels\n- Eligible Courses\n- Min Score & Type\n- Min / Max Age\n- Eligible Genders\n- Disability Required"]
    end

    subgraph Engine["9-Rule Evaluation Engine (eligibility_engine.py)"]
        R1["1. evaluate_income()"]
        R2["2. evaluate_category()"]
        R3["3. evaluate_state()"]
        R4["4. evaluate_education_level()"]
        R5["5. evaluate_course()\n(Synonym Clusters)"]
        R6["6. evaluate_score()\n(CGPA * 9.5 <-> % Conversion)"]
        R7["7. evaluate_age()\n(Exact Age Calculation)"]
        R8["8. evaluate_gender()"]
        R9["9. evaluate_disability()"]
    end

    SData --> Engine
    SchData --> Engine

    Engine --> DecisionTree{Aggregator Decision}

    DecisionTree -- "Any Rule == FAIL" --> Ineligible["INELIGIBLE\n(failed_rules > 0)"]
    DecisionTree -- "No FAIL, but Any Rule == UNKNOWN" --> NeedsVerif["NEEDS_VERIFICATION\n(Missing Info on Student or Source)"]
    DecisionTree -- "All Rules == PASS" --> Eligible["ELIGIBLE\n(100% Verified Match)"]

    Ineligible --> ScoreCalc["calculate_match_score()\npassed_rules / (passed + failed) * 100"]
    NeedsVerif --> ScoreCalc
    Eligible --> ScoreCalc
```

---

## 6. Saved Scholarships Architecture

```mermaid
flowchart TD
    subgraph FrontendActions["Client Actions (ScholarshipCard / Details / Saved.jsx)"]
        ClickSave["Click Bookmark Button"]
        OptimisticUI["Optimistic UI Update\n(Add/Remove ID in savedIds Set)"]
        Toast["Display Instant Feedback Toast"]
    end

    subgraph APIRoutes["FastAPI Router: /saved-scholarships"]
        PostSave["POST /saved-scholarships/\nPayload: {scholarship_id, scholarship}"]
        GetSaved["GET /saved-scholarships/"]
        GetSavedIDs["GET /saved-scholarships/ids"]
        DeleteSaved["DELETE /saved-scholarships/?scholarship_id={id}"]
    end

    subgraph ServiceAndRepo["Service & Repository Layer"]
        ServiceLogic["saved_scholarship_service.py\n- add_saved_scholarship()\n- fetch_saved_scholarships()\n- remove_saved_scholarship()"]
        RepoAccess["saved_scholarship_repository.py\n- save_scholarship()\n- get_saved_scholarships()\n- delete_saved_scholarship()"]
    end

    subgraph MongoCollection["MongoDB: saved_scholarships"]
        DocRecord[("{ user_id: '...', scholarship_id: '...', scholarship: {...}, saved_at: ISODate }")]
    end

    ClickSave --> OptimisticUI
    OptimisticUI --> Toast
    OptimisticUI --> PostSave
    PostSave --> ServiceLogic
    ServiceLogic --> RepoAccess
    RepoAccess -- "Upsert by (user_id, scholarship_id)" --> MongoCollection
    DeleteSaved --> ServiceLogic
    ServiceLogic --> RepoAccess
    RepoAccess -- "Delete by (user_id, scholarship_id)" --> MongoCollection
    GetSaved --> ServiceLogic
    ServiceLogic --> RepoAccess
    RepoAccess -- "Find by user_id" --> MongoCollection
```

---

## 7. Application Tracker Architecture

```mermaid
stateDiagram-v2
    [*] --> APPLIED: Student applies via portal & clicks "Track Application"
    APPLIED --> UNDER_REVIEW: Documents submitted & verification in progress
    UNDER_REVIEW --> SELECTED: Application approved & scholarship granted
    UNDER_REVIEW --> REJECTED: Ineligible or quota exhausted
    SELECTED --> [*]
    REJECTED --> [*]
```

```mermaid
flowchart LR
    subgraph UI["Frontend (Applications.jsx)"]
        FilterTabs["Filter Tabs (All / Applied / Under Review / Selected / Rejected)"]
        StatusDropdown["Interactive Status Selector"]
        DeleteAction["Remove Application"]
    end

    subgraph API["Backend API (/applications)"]
        PostApp["POST /applications/"]
        GetApps["GET /applications/"]
        PatchStatus["PATCH /applications/{scholarship_id}/status"]
        PutApp["PUT /applications/{scholarship_id}"]
        DeleteApp["DELETE /applications/{scholarship_id}"]
    end

    subgraph Storage["MongoDB: applications Collection"]
        AppDoc[("{ user_id: '...', scholarship_id: '...', status: 'APPLIED', notes: '...', applied_at: '2026-11-04' }")]
    end

    UI --> API
    API --> Storage
```
