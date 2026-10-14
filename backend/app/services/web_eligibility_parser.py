
import re


INCOME_PATTERNS = [
    # Income requirement followed by an explicit upper-limit phrase.
    r"(?:annual|family|parental|household)\s+income"
    r"[^.\n]{0,100}?"
    r"(?:must\s+be\s+below|must\s+not\s+exceed|does\s+not\s+exceed|"
    r"should\s+not\s+exceed|not\s+exceeding|less\s+than|below|"
    r"up\s+to|within|maximum\s+of|limited\s+to)"
    r"\s*(?:₹|rs\.?|inr)?\s*([\d,]+)",

    # Explicit currency amount followed by a stated income limit.
    r"(?:₹|rs\.?|inr)\s*([\d,]+)"
    r"[^.\n]{0,80}?"
    r"(?:is\s+the\s+maximum|maximum\s+annual\s+income|"
    r"annual\s+income\s+limit|income\s+limit)",

    # Common wording: income should not exceed an amount.
    r"(?:income\s+of\s+the\s+family|family\s+income|"
    r"annual\s+family\s+income)"
    r"[^.\n]{0,80}?"
    r"(?:should\s+not\s+exceed|must\s+not\s+exceed|"
    r"not\s+exceed|up\s+to|less\s+than|below)"
    r"\s*(?:₹|rs\.?|inr)?\s*([\d,]+)",
]


def parse_income_requirement(text: str):
    """Extract a likely maximum family-income threshold."""
    if not isinstance(text, str) or not text.strip():
        return None

    for pattern in INCOME_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)

        if not match:
            continue

        try:
            amount = float(match.group(1).replace(",", ""))
        except (ValueError, TypeError):
            continue

        if amount > 0:
            return amount

    return None


def parse_categories(text: str):
    """Detect explicitly named reservation categories."""
    if not isinstance(text, str):
        return []

    category_patterns = {
        "SC": [
            r"\bscheduled castes?\b",
            r"\bsc category\b",
            r"\bcategory\s*[:\-]?\s*sc\b",
        ],
        "ST": [
            r"\bscheduled tribes?\b",
            r"\bst category\b",
            r"\bcategory\s*[:\-]?\s*st\b",
        ],
        "OBC": [
            r"\bother backward classes?\b",
            r"\bobc(?:-ncl)? category\b",
            r"\bcategory\s*[:\-]?\s*obc\b",
        ],
        "EWS": [
            r"\beconomically weaker sections?\b",
            r"\bews category\b",
        ],
        "GENERAL": [
            r"\bgeneral category\b",
            r"\bgeneral-category students\b",
        ],
    }

    categories = []

    for category, patterns in category_patterns.items():
        if any(
            re.search(pattern, text, re.IGNORECASE)
            for pattern in patterns
        ):
            categories.append(category)

    return categories


def parse_gender(text: str):
    """
    Detect explicit gender restrictions.

    General mentions of women, girls, men, or boys do not establish
    a restriction unless the wording indicates exclusivity.
    """
    if not isinstance(text, str):
        return []

    female_patterns = [
        r"\bonly\s+(?:for\s+)?female students\b",
        r"\bonly\s+(?:for\s+)?girl students\b",
        r"\bfor women students only\b",
        r"\bfemale candidates only\b",
        r"\bgirls only\b",
        r"\bexclusively\s+for\s+(?:women|girls|female students)\b",
    ]

    male_patterns = [
        r"\bonly\s+(?:for\s+)?male students\b",
        r"\bmale candidates only\b",
        r"\bboys only\b",
        r"\bexclusively\s+for\s+(?:men|boys|male students)\b",
    ]

    female = any(
        re.search(pattern, text, re.IGNORECASE)
        for pattern in female_patterns
    )

    male = any(
        re.search(pattern, text, re.IGNORECASE)
        for pattern in male_patterns
    )

    # Conflicting restrictions should remain unknown.
    if female and male:
        return []

    if female:
        return ["FEMALE"]

    if male:
        return ["MALE"]

    return []


def parse_disability(text: str):
    """
    Return True only when the wording clearly establishes
    disability as a requirement. Otherwise return None.
    """
    if not isinstance(text, str) or not text.strip():
        return None

    mandatory_patterns = [
        r"\bonly\s+(?:for\s+)?(?:students|persons|candidates)"
        r"\s+with disabilities\b",
        r"\bdisability is mandatory\b",
        r"\bmust have a (?:benchmark )?disability\b",
        r"\bminimum disability of\s*\d+\s*%\b",
        r"\bdisability certificate is required\b",
        r"\bapplicants must be persons with disabilities\b",
    ]

    if any(
        re.search(pattern, text, re.IGNORECASE)
        for pattern in mandatory_patterns
    ):
        return True

    return None


def parse_eligibility_rules(text: str):
    """Convert eligibility text into the existing converter fields."""
    if not isinstance(text, str):
        text = ""

    return {
        "maximum_family_income": parse_income_requirement(text),
        "eligible_categories": parse_categories(text),
        "eligible_genders": parse_gender(text),
        "disability_required": parse_disability(text),
    }
