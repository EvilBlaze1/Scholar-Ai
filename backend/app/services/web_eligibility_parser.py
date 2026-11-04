import re

INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
    "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
    "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Delhi", "Jammu and Kashmir", "Ladakh", "Chandigarh", "Puducherry"
]

COURSE_PATTERNS = {
    "B.Tech": [r"\bb\.?tech\b", r"\bbachelor of technology\b", r"\bb\.?e\b", r"\bbachelor of engineering\b", r"\bengineering\b"],
    "B.Sc": [r"\bb\.?sc\b", r"\bbachelor of science\b"],
    "B.Com": [r"\bb\.?com\b", r"\bbachelor of commerce\b"],
    "BBA": [r"\bbba\b", r"\bbachelor of business administration\b"],
    "B.A.": [r"\bb\.?a\b", r"\bbachelor of arts\b"],
    "MBBS": [r"\bmbbs\b", r"\bmedicine\b", r"\bmedical\b"],
    "B.Pharm": [r"\bb\.?pharm\b", r"\bpharmacy\b"],
    "M.Tech": [r"\bm\.?tech\b", r"\bmaster of technology\b", r"\bm\.?e\b"],
    "M.Sc": [r"\bm\.?sc\b", r"\bmaster of science\b"],
    "MBA": [r"\bmba\b", r"\bmaster of business administration\b"],
    "MCA": [r"\bmca\b", r"\bmaster of computer applications\b"],
    "Diploma": [r"\bdiploma\b", r"\bpolytechnic\b"],
    "Law": [r"\bllb\b", r"\blaw\b", r"\bb\.?a\.?\s*ll\.?b\b"],
}

EDUCATION_LEVEL_PATTERNS = {
    "UNDERGRADUATE": [r"\bundergraduate\b", r"\bug\b", r"\bbachelor\b", r"\bdegree\b", r"\bfirst year college\b"],
    "POSTGRADUATE": [r"\bpostgraduate\b", r"\bpg\b", r"\bmaster\b", r"\bmasters\b"],
    "DIPLOMA": [r"\bdiploma\b", r"\bpolytechnic\b"],
    "PHD": [r"\bph\.?d\b", r"\bdoctorate\b", r"\bresearch scholar\b"],
    "SCHOOL": [r"\bclass\s*(?:9|10|11|12)(?:th)?\b", r"\bschool\b", r"\bintermediate\b", r"\bhigher secondary\b"],
}

INCOME_PATTERNS = [
    r"(?:annual|family|parental|household)\s+income"
    r"[^.\n]{0,80}?"
    r"(?:must\s+be\s+below|must\s+not\s+exceed|does\s+not\s+exceed|"
    r"should\s+not\s+exceed|not\s+exceeding|less\s+than|below|"
    r"up\s+to|within|maximum\s+of|limited\s+to|is\s+less\s+than)"
    r"\s*(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)\s*(lakhs?|lac|crores?|cr|thousand|k|lpa)?",

    r"(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)\s*(lakhs?|lac|crores?|cr|thousand|k|lpa)?"
    r"[^.\n]{0,60}?"
    r"(?:is\s+the\s+maximum|maximum\s+annual\s+income|"
    r"annual\s+income\s+limit|income\s+limit)",

    r"(?:income\s+of\s+the\s+family|family\s+income|"
    r"annual\s+family\s+income)"
    r"[^.\n]{0,60}?"
    r"(?:should\s+not\s+exceed|must\s+not\s+exceed|"
    r"not\s+exceed|up\s+to|less\s+than|below)"
    r"\s*(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)\s*(lakhs?|lac|crores?|cr|thousand|k|lpa)?",
]


def _parse_rupee_amount(raw_number: str, unit: str | None) -> float | None:
    """Safely parse numbers including Indian denominations like Lakh and LPA."""
    try:
        val = float(raw_number.replace(",", "").strip())
    except (ValueError, TypeError):
        return None

    if not unit:
        if 1 <= val <= 20:
            return val * 100_000
        return val

    unit = unit.lower().strip()
    if unit in ("lakh", "lakhs", "lac", "lpa"):
        return val * 100_000
    if unit in ("crore", "crores", "cr"):
        return val * 10_000_000
    if unit in ("thousand", "k"):
        return val * 1_000

    return val


def parse_income_requirement(text: str) -> float | None:
    """Extract maximum family-income threshold supporting LPA and Lakh."""
    if not isinstance(text, str) or not text.strip():
        return None

    for pattern in INCOME_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            continue

        raw_num = match.group(1)
        unit = match.group(2) if len(match.groups()) >= 2 else None
        amount = _parse_rupee_amount(raw_num, unit)

        if amount and amount >= 10_000:
            return amount

    return None


def parse_categories(text: str) -> list[str]:
    """Detect explicitly named reservation categories."""
    if not isinstance(text, str):
        return []

    category_patterns = {
        "SC": [
            r"\bscheduled castes?\b",
            r"\bsc\b",
            r"\bcategory\s*[:\-]?\s*sc\b",
        ],
        "ST": [
            r"\bscheduled tribes?\b",
            r"\bst\b",
            r"\bcategory\s*[:\-]?\s*st\b",
        ],
        "OBC": [
            r"\bother backward classes?\b",
            r"\bobc(?:-ncl)?\b",
            r"\bcategory\s*[:\-]?\s*obc\b",
        ],
        "EWS": [
            r"\beconomically weaker sections?\b",
            r"\bews\b",
        ],
        "GENERAL": [
            r"\bgeneral category\b",
            r"\bgeneral-category\b",
            r"\bunreserved\b",
            r"\bur\b",
        ],
    }

    categories = []
    for category, patterns in category_patterns.items():
        if any(re.search(p, text, re.IGNORECASE) for p in patterns):
            categories.append(category)

    return categories


def parse_gender(text: str) -> list[str]:
    """Detect explicit gender restrictions."""
    if not isinstance(text, str):
        return []

    female_patterns = [
        r"\bonly\s+(?:for\s+)?(?:female|girl|women)\s*(?:students|candidates)?\b",
        r"\bfor\s+(?:women|girls|female)\s+students\s+only\b",
        r"\bfemale\s+candidates\s+only\b",
        r"\bgirls?\s+only\b",
        r"\bexclusively\s+for\s+(?:women|girls?|female)\s*(?:students|candidates)?\b",
    ]

    male_patterns = [
        r"\bonly\s+(?:for\s+)?(?:male|boy|men)\s*(?:students|candidates)?\b",
        r"\bmale\s+candidates\s+only\b",
        r"\bboys?\s+only\b",
        r"\bexclusively\s+for\s+(?:men|boys?|male)\s*(?:students|candidates)?\b",
    ]

    female = any(re.search(p, text, re.IGNORECASE) for p in female_patterns)
    male = any(re.search(p, text, re.IGNORECASE) for p in male_patterns)

    if female and male:
        return []
    if female:
        return ["FEMALE"]
    if male:
        return ["MALE"]

    return []


def parse_disability(text: str) -> bool | None:
    """Return True only when wording clearly establishes disability as mandatory."""
    if not isinstance(text, str) or not text.strip():
        return None

    mandatory_patterns = [
        r"\bonly\s+(?:for\s+)?(?:students|persons|candidates)\s+with disabilities\b",
        r"\bdisability is mandatory\b",
        r"\bmust have a (?:benchmark )?disability\b",
        r"\bminimum disability of\s*\d+\s*%\b",
        r"\bdisability certificate is required\b",
        r"\bapplicants must be persons with disabilities\b",
        r"\bpwd students only\b",
    ]

    if any(re.search(p, text, re.IGNORECASE) for p in mandatory_patterns):
        return True

    return None


def parse_states(text: str) -> list[str]:
    """Extract Indian states mentioned in domicile/eligibility context."""
    if not isinstance(text, str) or not text.strip():
        return []

    found_states = []
    for state in INDIAN_STATES:
        pattern = r"\b(?:domicile of|resident of|students of|studying in|state of)\s+" + re.escape(state) + r"\b"
        if re.search(pattern, text, re.IGNORECASE):
            found_states.append(state)
        elif re.search(r"\b" + re.escape(state) + r"\s+domicile\b", text, re.IGNORECASE):
            found_states.append(state)

    return list(dict.fromkeys(found_states))


def parse_education_levels(text: str) -> list[str]:
    """Detect eligible education levels."""
    if not isinstance(text, str) or not text.strip():
        return []

    found_levels = []
    for level, patterns in EDUCATION_LEVEL_PATTERNS.items():
        if any(re.search(p, text, re.IGNORECASE) for p in patterns):
            found_levels.append(level)

    return found_levels


def parse_courses(text: str) -> list[str]:
    """Detect eligible courses from text."""
    if not isinstance(text, str) or not text.strip():
        return []

    found_courses = []
    for course, patterns in COURSE_PATTERNS.items():
        if any(re.search(p, text, re.IGNORECASE) for p in patterns):
            found_courses.append(course)

    return found_courses


def parse_minimum_score(text: str) -> tuple[float | None, str | None]:
    """Detect minimum academic marks requirement like 'minimum 60% marks' or '7.0 CGPA'."""
    if not isinstance(text, str) or not text.strip():
        return None, None

    pct_match = re.search(
        r"(?:minimum|at least|atleast|scoring|scored)\s+(\d{2}(?:\.\d+)?)\s*%",
        text,
        re.IGNORECASE,
    )
    if pct_match:
        try:
            val = float(pct_match.group(1))
            if 30 <= val <= 100:
                return val, "percentage"
        except (ValueError, TypeError):
            pass

    cgpa_match = re.search(
        r"(?:minimum|at least|atleast|scoring|scored)\s+(\d(?:\.\d+)?)\s*(?:cgpa|gpa|points?)",
        text,
        re.IGNORECASE,
    )
    if cgpa_match:
        try:
            val = float(cgpa_match.group(1))
            if 3.0 <= val <= 10.0:
                return val, "cgpa"
        except (ValueError, TypeError):
            pass

    return None, None


def parse_eligibility_rules(text: str) -> dict:
    """Convert eligibility text into structured rule parameters."""
    if not isinstance(text, str):
        text = ""

    score_val, score_type = parse_minimum_score(text)

    return {
        "maximum_family_income": parse_income_requirement(text),
        "eligible_categories": parse_categories(text),
        "eligible_genders": parse_gender(text),
        "disability_required": parse_disability(text),
        "eligible_states": parse_states(text),
        "eligible_education_levels": parse_education_levels(text),
        "eligible_courses": parse_courses(text),
        "minimum_score": score_val,
        "minimum_score_type": score_type,
    }
