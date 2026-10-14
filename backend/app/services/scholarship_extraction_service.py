
import re
from urllib.parse import urlsplit, urlunsplit

from app.services.webpage_reader_service import fetch_webpage


AMOUNT_PATTERNS = [
    r"₹\s?[\d,]+(?:\.\d+)?(?:\s*(?:per|/)\s*(?:year|month|annum|semester))?",
    r"\bRs\.?\s?[\d,]+(?:\.\d+)?(?:\s*(?:per|/)\s*(?:year|month|annum|semester))?",
    r"\bINR\s?[\d,]+(?:\.\d+)?(?:\s*(?:per|/)\s*(?:year|month|annum|semester))?",
]

DEADLINE_PATTERNS = [
    r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
    r"\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b",
    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b",
]

DEADLINE_KEYWORDS = [
    "application deadline",
    "last date to apply",
    "last date for application",
    "apply before",
    "applications close",
    "application closes",
    "closing date",
    "deadline",
]

ELIGIBILITY_KEYWORDS = [
    "eligibility",
    "eligible",
    "income",
    "category",
    "domicile",
    "qualification",
    "academic",
    "minimum marks",
    "percentage",
    "family income",
    "undergraduate",
    "postgraduate",
    "students must",
]

BENEFIT_KEYWORDS = [
    "tuition fee",
    "maintenance allowance",
    "stipend",
    "financial assistance",
    "scholarship amount",
    "reimbursement",
    "hostel allowance",
    "book allowance",
    "annual award",
]

DOCUMENT_KEYWORDS = [
    "income certificate",
    "caste certificate",
    "domicile certificate",
    "marksheet",
    "mark sheet",
    "aadhaar",
    "bank passbook",
    "admission letter",
    "bonafide certificate",
    "passport size photograph",
    "disability certificate",
]

MAX_TEXT_LENGTH = 100_000


def clean_text(text: str) -> str:
    """Normalize whitespace and safely handle missing text."""
    if not isinstance(text, str):
        return ""

    return re.sub(r"\s+", " ", text).strip()


def normalize_source_url(url: str) -> str | None:
    """Accept only HTTP(S) URLs and normalize them for deduplication."""
    if not isinstance(url, str):
        return None

    url = url.strip()

    try:
        parsed = urlsplit(url)

        if parsed.scheme.lower() not in {"http", "https"}:
            return None

        if not parsed.hostname or parsed.username or parsed.password:
            return None

        # Accessing port also validates malformed port values.
        _ = parsed.port

        return urlunsplit((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path or "/",
            parsed.query,
            "",
        ))
    except (ValueError, TypeError):
        return None


def find_amount(text: str) -> str | None:
    """Return the first amount-like value found in the text."""
    text = clean_text(text)[:MAX_TEXT_LENGTH]

    for pattern in AMOUNT_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0).strip()

    return None


def find_deadline(text: str) -> str | None:
    """Find a date near explicit deadline wording; never guess from any date."""
    text = clean_text(text)[:MAX_TEXT_LENGTH]

    if not text:
        return None

    date_pattern = "|".join(DEADLINE_PATTERNS)
    keyword_pattern = "|".join(
        re.escape(keyword) for keyword in DEADLINE_KEYWORDS
    )

    # Allow a short section of text between the deadline wording and date.
    pattern = (
        r"(?:"
        + keyword_pattern
        + r")\b[^.!?]{0,160}?\b("
        + date_pattern
        + r")\b"
    )

    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group(1)

    return None


def split_sentences(text: str) -> list[str]:
    """Split webpage text into manageable sentence-like sections."""
    text = clean_text(text)[:MAX_TEXT_LENGTH]

    if not text:
        return []

    return [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", text)
        if sentence.strip()
    ]


def extract_matching_sentences(
    text: str,
    keywords: list[str],
    limit: int = 10,
) -> list[str]:
    """Extract distinct sentences containing relevant keywords."""
    if limit <= 0:
        return []

    results = []
    seen = set()

    for sentence in split_sentences(text):
        sentence_lower = sentence.lower()

        if not any(
            keyword.strip().lower() in sentence_lower
            for keyword in keywords
        ):
            continue

        normalized = sentence_lower

        if normalized not in seen:
            results.append(sentence)
            seen.add(normalized)

        if len(results) >= limit:
            break

    return results


def extract_eligibility(text: str) -> list[str]:
    return extract_matching_sentences(text, ELIGIBILITY_KEYWORDS, limit=10)


def extract_benefits(text: str) -> list[str]:
    return extract_matching_sentences(text, BENEFIT_KEYWORDS, limit=8)


def extract_required_documents(text: str) -> list[str]:
    return extract_matching_sentences(text, DOCUMENT_KEYWORDS, limit=10)


def extract_provider(text: str) -> str | None:
    """Extract a provider only when explicit wording gives a reasonable clue."""
    text = clean_text(text)[:MAX_TEXT_LENGTH]

    patterns = [
        r"(?:offered|provided|funded|sponsored)\s+by\s+"
        r"([A-Z][A-Za-z&.,'() -]{2,80})",
        r"(?:government|department|ministry)\s+of\s+"
        r"([A-Z][A-Za-z&.,'() -]{2,80})",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if not match:
            continue

        provider = match.group(1).strip(" .,:;-")
        provider = re.split(
            r"\b(?:for|to|under|and|which|that)\b",
            provider,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0].strip()

        if provider:
            return provider[:100]

    return None


def extract_scholarship_info(result: dict) -> dict:
    """Extract scholarship details without treating extraction as verification."""
    if not isinstance(result, dict):
        result = {}

    original_url = result.get("url") or result.get("source_url")
    source_url = normalize_source_url(original_url)

    title = clean_text(result.get("title") or result.get("name") or "")
    description = clean_text(result.get("description") or "")

    webpage_text = ""

    if source_url:
        try:
            webpage_text = fetch_webpage(source_url) or ""
        except Exception:
            # Search-result metadata can still be used as a fallback.
            webpage_text = ""

    webpage_text = clean_text(webpage_text)[:MAX_TEXT_LENGTH]
    search_text = clean_text(f"{title}. {description}")
    combined_text = clean_text(
        f"{search_text}. {webpage_text}"
    )[:MAX_TEXT_LENGTH]

    # Prefer a deadline found on the webpage. Use search-result text only
    # when the webpage does not provide one.
    deadline = find_deadline(webpage_text) or find_deadline(search_text)

    return {
        "name": title or None,
        "provider": extract_provider(webpage_text)
        or extract_provider(search_text),
        "description": description or None,
        "source_url": source_url,
        "application_deadline": deadline,
        "scholarship_amount": find_amount(combined_text),
        "eligibility": extract_eligibility(combined_text),
        "benefits": extract_benefits(combined_text),
        "required_documents": extract_required_documents(combined_text),
        # Retrieved content is not independently verified.
        "verification_status": (
            "EXTRACTED" if webpage_text else "UNVERIFIED"
        ),
    }


def extract_from_search_results(results: list[dict]) -> list[dict]:
    """Extract unique search results while preserving source URLs."""
    if not isinstance(results, list):
        return []

    scholarships = []
    seen_urls = set()

    for result in results:
        if not isinstance(result, dict):
            continue

        original_url = result.get("url") or result.get("source_url")
        normalized_url = normalize_source_url(original_url)

        if not normalized_url or normalized_url in seen_urls:
            continue

        normalized_result = {
            **result,
            "url": normalized_url,
        }

        scholarship = extract_scholarship_info(normalized_result)
        scholarships.append(scholarship)
        seen_urls.add(normalized_url)

    return scholarships
