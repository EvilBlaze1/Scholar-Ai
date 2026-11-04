# Scholar AI — Complete API Reference & Endpoint Documentation

This document provides a comprehensive reference for all REST API endpoints implemented in **Scholar AI**. All routes are served by the FastAPI application rooted at [`backend/app/main.py`](file:///d:/Scholar AI/backend/app/main.py).

---

## 1. Global Endpoints

### 1.1. Root Welcome
- **Method**: `GET`
- **Path**: `/`
- **Auth**: None
- **Response**: `{"message": "Scholar AI API is running"}`
- **Status**: `200 OK`

### 1.2. Health Check
- **Method**: `GET`
- **Path**: `/health`
- **Auth**: None
- **Response**: `{"status": "ok", "service": "Scholar AI API"}`
- **Status**: `200 OK`

---

## 2. Authentication Router (`/auth`)
*Source: [`backend/app/api/auth.py`](file:///d:/Scholar AI/backend/app/api/auth.py)*

### 2.1. User Registration
- **Method**: `POST`
- **Path**: `/auth/register`
- **Auth**: None
- **Request Body**:
  ```json
  {
    "email": "student@example.com",
    "password": "strongPassword123"
  }
  ```
- **Validation**: Email is trimmed and lowercased automatically; password minimum length is 8 characters.
- **Success Response (`200 OK`)**:
  ```json
  {
    "id": "6724a1b2c3d4e5f6a7b8c9d0",
    "email": "student@example.com"
  }
  ```
- **Error Responses**:
  - `409 Conflict`: `{"detail": "Email already registered"}`
  - `422 Unprocessable Entity`: Validation failure on email or password length.
  - `503 Service Unavailable`: MongoDB Atlas connectivity failure.

### 2.2. User Login
- **Method**: `POST`
- **Path**: `/auth/login`
- **Auth**: None
- **Request Body**:
  ```json
  {
    "email": "student@example.com",
    "password": "strongPassword123"
  }
  ```
- **Success Response (`200 OK`)**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "user": {
      "id": "6724a1b2c3d4e5f6a7b8c9d0",
      "email": "student@example.com"
    }
  }
  ```
- **Error Responses**:
  - `401 Unauthorized`: `{"detail": "Invalid email or password"}`
  - `503 Service Unavailable`: MongoDB Atlas connectivity error with diagnosis hint.

### 2.3. Current User Identification
- **Method**: `GET`
- **Path**: `/auth/me`
- **Auth**: Bearer Token
- **Headers**: `Authorization: Bearer <access_token>`
- **Success Response (`200 OK`)**:
  ```json
  {
    "user_id": "6724a1b2c3d4e5f6a7b8c9d0",
    "email": "student@example.com"
  }
  ```
- **Error Response**: `401 Unauthorized` for missing, expired, or corrupted token.

---

## 3. Student Profile Router (`/students`)
*Source: [`backend/app/api/student.py`](file:///d:/Scholar AI/backend/app/api/student.py)*

### 3.1. Create Authenticated Profile
- **Method**: `POST`
- **Path**: `/students/me`
- **Auth**: Bearer Token
- **Request Body**: `StudentCreate` schema (name, course, income, score, state, category, etc.)
- **Success Response (`200 OK`)**: Created student record with auto-populated `user_id`.
- **Side Effect**: Invalidates `student_search` cache to force fresh match calculation.
- **Error Response**: `409 Conflict` if a profile already exists for the authenticated user.

### 3.2. Fetch Authenticated Profile
- **Method**: `GET`
- **Path**: `/students/me`
- **Auth**: Bearer Token
- **Success Response (`200 OK`)**: Full student profile document.
- **Error Response**: `404 Not Found` if profile has not been created yet.

### 3.3. Fetch Profile by ID
- **Method**: `GET`
- **Path**: `/students/{student_id}`
- **Auth**: None (Internal / Admin lookup)
- **Status**: `200 OK` or `404 Not Found`

### 3.4. Update Profile by ID
- **Method**: `PUT`
- **Path**: `/students/{student_id}`
- **Auth**: None
- **Request Body**: `StudentCreate`
- **Status**: `200 OK` or `404 Not Found`

---

## 4. Scholarship Repository Router (`/scholarships`)
*Source: [`backend/app/api/scholarship.py`](file:///d:/Scholar AI/backend/app/api/scholarship.py)*

### 4.1. Register Curated Scholarship
- **Method**: `POST`
- **Path**: `/scholarships/`
- **Request Body**: `ScholarshipCreate`
- **Success Response (`200 OK`)**: Saved scholarship dictionary.

### 4.2. List Curated Scholarships
- **Method**: `GET`
- **Path**: `/scholarships/`
- **Query Parameters**:
  - `category` (`str`, optional)
  - `state` (`str`, optional)
  - `education_level` (`str`, optional)
  - `course` (`str`, optional)
- **Success Response (`200 OK`)**: List of matching curated scholarship records.

### 4.3. Fetch Single Scholarship by ID
- **Method**: `GET`
- **Path**: `/scholarships/{scholarship_id:path}`
- **Status**: `200 OK` or `404 Not Found`

---

## 5. Eligibility Evaluation Router (`/eligibility`)
*Source: [`backend/app/api/eligibility.py`](file:///d:/Scholar AI/backend/app/api/eligibility.py)*

### 5.1. Evaluate Single Student Against Scholarship
- **Method**: `POST`
- **Path**: `/eligibility/check/{student_id}/{scholarship_id}`
- **Auth**: None
- **Success Response (`200 OK`)**:
  ```json
  {
    "status": "ELIGIBLE",
    "rule_results": [
      {
        "rule_id": "income",
        "rule_type": "income",
        "status": "PASS",
        "reason": "Student family income is within the allowed limit."
      },
      {
        "rule_id": "score",
        "rule_type": "score",
        "status": "PASS",
        "reason": "Student score meets the minimum requirement."
      }
    ],
    "passed_rules": 9,
    "failed_rules": 0,
    "verification_required": false
  }
  ```
- **Error Responses**: `404 Not Found` if student or scholarship ID does not exist.

---

## 6. Matching Router (`/matching`)
*Source: [`backend/app/api/matching.py`](file:///d:/Scholar AI/backend/app/api/matching.py)*

### 6.1. Get Ranked Stored Scholarships for Student
- **Method**: `GET`
- **Path**: `/matching/student/{student_id}`
- **Success Response (`200 OK`)**:
  ```json
  {
    "student_id": "6724a2c3d4e5f6a7b8c9d0e1",
    "total": 12,
    "matches": [
      {
        "scholarship_id": "6724a3d4e5f6a7b8c9d0e1f2",
        "name": "Reliance Foundation Undergraduate Scholarship",
        "provider": "Reliance Foundation",
        "status": "ELIGIBLE",
        "match_score": 100.0,
        "passed_rules": 9,
        "failed_rules": 0,
        "verification_required": false
      }
    ]
  }
  ```

---

## 7. Explanation Router (`/explanations`)
*Source: [`backend/app/api/explanation.py`](file:///d:/Scholar AI/backend/app/api/explanation.py)*

### 7.1. Explain Scholarship Match Reasoning
- **Method**: `GET`
- **Path**: `/explanations/student/{student_id}/scholarship/{scholarship_id}`
- **Success Response (`200 OK`)**: Structured reasoning for each pass/fail rule and clear verification guidance.

---

## 8. Dashboard Router (`/dashboard`)
*Source: [`backend/app/api/dashboard.py`](file:///d:/Scholar AI/backend/app/api/dashboard.py)*

### 8.1. Student Dashboard Aggregation
- **Method**: `GET`
- **Path**: `/dashboard/me`
- **Auth**: Bearer Token
- **Success Response (`200 OK`)**:
  ```json
  {
    "student": {
      "full_name": "Tanish Sharma",
      "course": "B.Tech",
      "state": "Maharashtra"
    },
    "summary": {
      "total_scholarships": 14,
      "eligible_scholarships": 8,
      "needs_verification": 4,
      "ineligible_scholarships": 2,
      "saved_scholarships": 3,
      "applications": 2
    },
    "matches": [ ... ],
    "saved_scholarships": [ ... ],
    "applications": [ ... ],
    "upcoming_deadlines": [ ... ]
  }
  ```

---

## 9. Saved Scholarships Router (`/saved-scholarships`)
*Source: [`backend/app/api/saved_scholarship.py`](file:///d:/Scholar AI/backend/app/api/saved_scholarship.py)*

### 9.1. Save Scholarship
- **Method**: `POST`
- **Path**: `/saved-scholarships/`
- **Auth**: Bearer Token
- **Request Body**:
  ```json
  {
    "scholarship_id": "https://scholarships.gov.in/scheme-123",
    "scholarship": {
      "id": "https://scholarships.gov.in/scheme-123",
      "name": "National Merit Scholarship",
      "scholarship_amount": "₹50,000",
      "application_deadline": "2026-12-31"
    }
  }
  ```
- **Success Response (`200 OK`)**: Saved document or `{"already_saved": true}` if duplicate.

### 9.2. List Saved Scholarships
- **Method**: `GET`
- **Path**: `/saved-scholarships/`
- **Auth**: Bearer Token
- **Success Response (`200 OK`)**: Array of saved scholarship items.

### 9.3. List Saved IDs Set
- **Method**: `GET`
- **Path**: `/saved-scholarships/ids`
- **Auth**: Bearer Token
- **Success Response (`200 OK`)**: `{"saved_ids": ["id1", "id2", "url3"]}`

### 9.4. Remove Saved Scholarship
- **Method**: `DELETE`
- **Path**: `/saved-scholarships/?scholarship_id={scholarship_id}` OR `/saved-scholarships/{scholarship_id:path}`
- **Auth**: Bearer Token
- **Success Response (`200 OK`)**: `{"message": "Scholarship removed from saved list"}`

---

## 10. Application Tracker Router (`/applications`)
*Source: [`backend/app/api/application.py`](file:///d:/Scholar AI/backend/app/api/application.py)*

### 10.1. Track Application
- **Method**: `POST`
- **Path**: `/applications/`
- **Auth**: Bearer Token
- **Request Body**:
  ```json
  {
    "scholarship_id": "https://scholarships.gov.in/scheme-123",
    "status": "APPLIED",
    "applied_at": "2026-11-04",
    "notes": "Submitted all documents online",
    "scholarship_name": "National Merit Scholarship",
    "provider": "Ministry of Education",
    "scholarship_amount": 50000
  }
  ```
- **Error Response**: `409 Conflict` if application is already tracked.

### 10.2. Fetch Applications
- **Method**: `GET`
- **Path**: `/applications/`
- **Auth**: Bearer Token
- **Success Response (`200 OK`)**: List of tracked application items for the authenticated user.

### 10.3. Update Status
- **Method**: `PATCH`
- **Path**: `/applications/{scholarship_id}/status`
- **Auth**: Bearer Token
- **Request Body**: `{"status": "UNDER_REVIEW"}`

### 10.4. Update Application Notes & Details
- **Method**: `PUT`
- **Path**: `/applications/{scholarship_id:path}`
- **Auth**: Bearer Token
- **Request Body**: `{"status": "SELECTED", "notes": "Received award email"}`

### 10.5. Remove Tracked Application
- **Method**: `DELETE`
- **Path**: `/applications/?scholarship_id={id}` OR `/applications/{scholarship_id:path}`
- **Auth**: Bearer Token

---

## 11. Personalized Search Router (`/search/student`)
*Source: [`backend/app/api/personalized_search.py`](file:///d:/Scholar AI/backend/app/api/personalized_search.py)*

### 11.1. Execute Personalized Web Discovery
- **Method**: `GET`
- **Path**: `/search/student/{student_id}`
- **Query Parameters**: `refresh` (`bool`, default `false`)
- **Process**:
  1. Checks multi-tier cache.
  2. Dispatches tailored search queries based on course, state, category, and gender.
  3. Scrapes live pages and normalizes extracted criteria.
  4. Runs eligibility evaluation engine on each discovered opportunity.
  5. Ranks results by eligibility status and rule-match score.
- **Success Response (`200 OK`)**:
  ```json
  {
    "student_id": "6724a2c3d4e5f6a7b8c9d0e1",
    "queries": ["B.Tech scholarships Maharashtra India", "..."],
    "count": 14,
    "results": [ ... ],
    "search_errors": 0,
    "cached": false
  }
  ```

---

## 12. General Discovery Search Router (`/discovery`)
*Source: [`backend/app/api/scholarship_discovery.py`](file:///d:/Scholar AI/backend/app/api/scholarship_discovery.py)*

### 12.1. Keyword Scholarship Discovery
- **Method**: `GET`
- **Path**: `/discovery/search`
- **Query Parameters**:
  - `q` (`str`, min 2, max 200 chars): Search keywords.
  - `refresh` (`bool`, default `false`): Bypass cache.
- **Success Response (`200 OK`)**: Array of verified web discovery items.
