import logging
import re
from urllib.parse import urlsplit, urlunsplit

from app.services.webpage_reader_service import fetch_webpage

logger = logging.getLogger(__name__)

# Known official domains mapped to official provider names
OFFICIAL_DOMAINS = {
    "scholarships.gov.in": "National Scholarship Portal (Govt of India)",
    "ugc.gov.in": "University Grants Commission (UGC)",
    "ugc.ac.in": "University Grants Commission (UGC)",
    "aicte-india.org": "All India Council for Technical Education (AICTE)",
    "dst.gov.in": "Department of Science and Technology (DST)",
    "dbtindia.gov.in": "Department of Biotechnology (DBT)",
    "education.gov.in": "Ministry of Education (Govt of India)",
    "mhrd.gov.in": "Ministry of Education (Govt of India)",
    "tribal.nic.in": "Ministry of Tribal Affairs (Govt of India)",
    "socialjustice.gov.in": "Ministry of Social Justice and Empowerment",
    "minorityaffairs.gov.in": "Ministry of Minority Affairs",
    "licindia.in": "Life Insurance Corporation of India (LIC)",
    "sbifoundation.in": "SBI Foundation",
    "tatatrusts.org": "Tata Trusts",
    "reliancefoundation.org": "Reliance Foundation",
    "hdfcbank.com": "HDFC Bank Parivartan",
    "adityabirlascholars.net": "Aditya Birla Group",
    "ongcindia.com": "ONGC Foundation",
    "drdo.gov.in": "Defence Research & Development Organisation (DRDO)",
    "isro.gov.in": "Indian Space Research Organisation (ISRO)",
    "kvdav.org": "KVPY / DST",
}

# Domains that represent generic articles, discussions, or videos (not actual scholarship programs)
DISQUALIFIED_DOMAINS = {
    "wikipedia.org",
    "youtube.com",
    "quora.com",
    "reddit.com",
    "facebook.com",
    "twitter.com",
    "instagram.com",
    "linkedin.com",
}

# Regex to detect listicles / informational guides that are not single scholarship announcements
ARTICLE_TITLE_PATTERNS = [
    r"^(?:top\s+\d+|list\s+of|\d+\s+best|\d+\s+scholarships|how\s+to\s+apply|guide\s+to|everything\s+you\s+need|tips\s+for)\b",
    r"\b(?:frequently\s+asked\s+questions|faq|sample\s+paper|exam\s+pattern|syllabus)\b",
]

# Patterns for amounts with Indian currency denominations
# Matches e.g. "₹2 Lakh", "₹2.5 Lakhs", "₹20,000", "Rs. 50,000 per year", "INR 1,00,000"
AMOUNT_PATTERNS = [
    # Explicit currency + number + optional Lakh/Crore/Thousand + frequency
    r"(?:₹|rs\.?|inr)\s*([\d,]+(?:\.\d+)?)\s*(lakhs?|lac|crores?|cr|thousand|k)?(?:\s*(?:per|/)\s*(?:year|month|annum|semester|pm|pa|annually))?",
    # Number + Lakh/Crore without symbol if near scholarship context
    r"\b([\d,]+(?:\.\d+)?)\s*(lakhs?|lac|crores?|cr)\s*(?:per|/)?\s*(?:year|month|annum|semester|pm|pa)?\b",
]

# Context keywords indicating award/scholarship value
SCHOLARSHIP_AMOUNT_CONTEXT = [
    "scholarship amount",
    "financial assistance",
    "stipend of",
    "award of",
    "grant of",
    "cash prize of",
    "worth up to",
    "worth",
    "amount of",
    "benefits of",
    "reward of",
    "annual scholarship",
]

# Disqualifying contexts: numbers related to application fees or family income caps
DISQUALIFYING_AMOUNT_CONTEXT = [
    "application fee",
    "exam fee",
    "processing fee",
    "registration fee",
    "family income",
    "annual income",
    "household income",
    "cost of form",
]

# Indian date formats: support ordinals (31st Oct), dots (31.10.2026), slashes, hyphens, ISO
DEADLINE_PATTERNS = [
    # 31st October 2026 / 15th Nov, 2026 / 1 Jan 2027
    r"\b\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)[a-z]*,?\s+\d{4}\b",
    # October 31st, 2026 / Nov 15, 2026
    r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)[a-z]*\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}\b",
    # DD/MM/YYYY or DD-MM-YYYY or DD.MM.YYYY
    r"\b\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b",
    # YYYY-MM-DD or YYYY/MM/DD (ISO)
    r"\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b",
]

DEADLINE_KEYWORDS = [
    "application deadline",
    "last date to apply",
    "last date for application",
    "last date",
    "apply before",
    "apply by",
    "applications close",
    "application closes",
    "closing date",
    "closes on",
    "ends on",
    "deadline",
    "registration closes",
    "registration close",
    "registration ends",
    "registration deadline",
    "due date",
    "submission deadline",
    "valid till",
    "valid up to",
    "apply online till",
    "end date",
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
    "cgpa",
    "family income",
    "undergraduate",
    "postgraduate",
    "students must",
    "candidate must",
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
    "concession",
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

        _ = parsed.port

        # Filter out common junk / tracking
        return urlunsplit((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path or "/",
            parsed.query,
            "",
        ))
    except (ValueError, TypeError):
        return None


def is_article_or_junk(title: str, url: str) -> bool:
    """Detect whether a search result is a generic article or disqualified domain."""
    if not isinstance(url, str):
        return True

    hostname = urlsplit(url).netloc.lower()
    for disqualified in DISQUALIFIED_DOMAINS:
        if disqualified in hostname:
            return True

    clean_title = (title or "").strip().lower()
    for pattern in ARTICLE_TITLE_PATTERNS:
        if re.search(pattern, clean_title, re.IGNORECASE):
            return True

    return False


def _parse_amount_value(raw_number: str, unit: str | None) -> float | None:
    """Convert number and unit into actual numeric rupee value."""
    try:
        num = float(raw_number.replace(",", "").strip())
    except (ValueError, TypeError):
        return None

    if not unit:
        return num

    unit = unit.lower().strip()
    if unit in ("lakh", "lakhs", "lac"):
        return num * 100_000
    if unit in ("crore", "crores", "cr"):
        return num * 10_000_000
    if unit in ("thousand", "k"):
        return num * 1_000

    return num


def _format_rupee_amount(numeric_val: float, raw_match: str) -> str:
    """Format numeric rupees into readable Indian string."""
    if numeric_val >= 10_000_000:
        cr = numeric_val / 10_000_000
        formatted = f"₹{cr:g} Crore"
    elif numeric_val >= 100_000:
        lakh = numeric_val / 100_000
        formatted = f"₹{lakh:g} Lakh"
    else:
        formatted = f"₹{int(numeric_val):,}"

    # Preserve frequency if in raw match
    raw_lower = raw_match.lower()
    for freq in ("per year", "per annum", "/year", "/annum", "annually", "p.a."):
        if freq in raw_lower:
            return f"{formatted} per year"
    for freq in ("per month", "/month", "p.m.", "monthly"):
        if freq in raw_lower:
            return f"{formatted} per month"
    for freq in ("per semester", "/semester"):
        if freq in raw_lower:
            return f"{formatted} per semester"

    return formatted


def find_amount(text: str) -> str | None:
    """
    Extract a valid scholarship award amount.
    Validates against context and avoids false positives such as '₹2' or application fees.
    """
    text = clean_text(text)[:MAX_TEXT_LENGTH]
    if not text:
        return None

    candidates = []

    # 1. Search near explicit award context keywords first
    for context_word in SCHOLARSHIP_AMOUNT_CONTEXT:
        # Search window of 120 chars around context keyword
        for match_ctx in re.finditer(re.escape(context_word), text, re.IGNORECASE):
            start = max(0, match_ctx.start() - 30)
            end = min(len(text), match_ctx.end() + 100)
            window = text[start:end]

            # Check if this window is discussing an application fee or income limit instead
            if any(disq in window.lower() for disq in DISQUALIFYING_AMOUNT_CONTEXT):
                continue

            for pattern in AMOUNT_PATTERNS:
                for match in re.finditer(pattern, window, re.IGNORECASE):
                    raw_num = match.group(1)
                    unit = match.group(2) if len(match.groups()) >= 2 else None
                    numeric_val = _parse_amount_value(raw_num, unit)

                    # Reject suspiciously small amounts < ₹500 (unless unit specifies lakh/k)
                    if numeric_val and numeric_val >= 500:
                        formatted = _format_rupee_amount(numeric_val, match.group(0))
                        return formatted

    # 2. General search across text if context search yielded no candidate
    for pattern in AMOUNT_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            raw_match = match.group(0)
            raw_num = match.group(1)
            unit = match.group(2) if len(match.groups()) >= 2 else None

            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            surrounding = text[start:end].lower()

            # Skip if explicitly attached to application fee or family income
            if any(disq in surrounding for disq in DISQUALIFYING_AMOUNT_CONTEXT):
                continue

            numeric_val = _parse_amount_value(raw_num, unit)
            if numeric_val is None:
                continue

            # CRITICAL FIX for the "₹2" bug:
            # Reject raw standalone small numbers (< 500) that aren't multiplied by a unit (Lakh, Crore, Thousand)
            if numeric_val < 500:
                continue

            candidates.append((numeric_val, raw_match))

    if candidates:
        # Pick the most plausible scholarship amount (prefer primary award amounts >= 1,000)
        best_val, best_raw = candidates[0]
        return _format_rupee_amount(best_val, best_raw)

    return None


def find_deadline(text: str) -> str | None:
    """Find a date near explicit deadline wording; never guess from any random date."""
    text = clean_text(text)[:MAX_TEXT_LENGTH]
    if not text:
        return None

    date_pattern = "|".join(DEADLINE_PATTERNS)
    keyword_pattern = "|".join(re.escape(k) for k in DEADLINE_KEYWORDS)

    # Allow up to 160 chars between keyword and date
    pattern = (
        r"(?:"
        + keyword_pattern
        + r")\b[^.!?\n]{0,160}?\b("
        + date_pattern
        + r")\b"
    )

    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        raw_date = match.group(1).strip()
        # Clean ordinals like 31st -> 31
        cleaned_date = re.sub(r"(\d+)(?:st|nd|rd|th)", r"\1", raw_date, flags=re.IGNORECASE)
        return cleaned_date

    return None


def extract_provider(text: str, title: str = "", source_url: str = "") -> str | None:
    """
    Intelligently identify the scholarship provider using:
    1. Known official government/foundation domain lookup
    2. Title pattern matching
    3. Webpage explicit text patterns
    """
    # 1. Match from source domain
    if source_url:
        try:
            hostname = urlsplit(source_url).netloc.lower()
            # Direct domain check or suffix check
            for domain, provider_name in OFFICIAL_DOMAINS.items():
                if hostname == domain or hostname.endswith("." + domain):
                    return provider_name

            # National Portal or state portal check
            if hostname.endswith(".gov.in") or hostname.endswith(".nic.in"):
                # E.g. scholarships.gov.in, up.gov.in, mahadbt.gov.in
                sub = hostname.split(".")[0].upper()
                if sub not in ("WWW", "PORTAL"):
                    return f"Government of India ({sub})"
                return "Government of India"
        except Exception:
            pass

    # 2. Extract provider from Title
    if title:
        clean_t = clean_text(title)
        # Check title against known providers
        for _, provider_name in OFFICIAL_DOMAINS.items():
            base_name = provider_name.split("(")[0].strip()
            if re.search(r"\b" + re.escape(base_name) + r"\b", clean_t, re.IGNORECASE):
                return provider_name

        # Match e.g. "Tata Trusts Scholarship 2026", "Reliance Foundation Postgraduate Scholarship"
        title_match = re.search(
            r"^([A-Z][A-Za-z0-9&.,' ]{2,50}?)\s+(?:Scholarship|Foundation|Trust|Fellowship|Scheme|Grant)\b",
            clean_t,
        )
        if title_match:
            candidate = title_match.group(1).strip()
            if candidate.lower() not in ("apply", "national", "state", "top", "list", "online"):
                return candidate

    # 3. Match from text patterns
    text = clean_text(text)[:MAX_TEXT_LENGTH]
    patterns = [
        r"(?:offered|provided|funded|sponsored|awarded)\s+by\s+([A-Za-z0-9&.,'() -]{2,80})",
        r"(?:government|department|ministry)\s+of\s+([A-Za-z0-9&.,'() -]{2,80})",
        r"([A-Za-z0-9&.,' ]{2,60})\s+invites\s+applications\s+for",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            continue

        provider = match.group(1).strip(" .,:;-")
        provider = re.split(
            r"\b(?:for|to|under|which|that|eligible|students)\b",
            provider,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0].strip()

        if len(provider) >= 3 and provider.lower() not in ("students", "the", "an", "all", "indian"):
            return provider[:100]

    return None


def extract_description(webpage_text: str, search_snippet: str, title: str) -> str:
    """Extract or synthesize a complete, informative description."""
    # If the search snippet is detailed and doesn't cut off abruptly, keep it
    clean_snippet = clean_text(search_snippet)
    if clean_snippet and len(clean_snippet) > 80 and not clean_snippet.endswith("..."):
        return clean_snippet

    # Otherwise synthesize from the webpage text
    if webpage_text:
        sentences = split_sentences(webpage_text)
        relevant_sentences = []
        for s in sentences[:15]:
            s_lower = s.lower()
            if any(k in s_lower for k in ("scholarship", "financial assistance", "eligibility", "offered", "students")):
                if len(s) > 40 and not any(skip in s_lower for skip in ("cookie", "javascript", "browser", "login")):
                    relevant_sentences.append(s)
            if len(relevant_sentences) >= 2:
                break

        if relevant_sentences:
            return " ".join(relevant_sentences)[:400]

    return clean_snippet or f"Scholarship opportunity: {title}"


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


def get_trust_level(source_url: str) -> str:
    """Determine the trust and verification status based on the domain."""
    if not source_url:
        return "UNVERIFIED"

    hostname = urlsplit(source_url).netloc.lower()
    for domain in OFFICIAL_DOMAINS:
        if hostname == domain or hostname.endswith("." + domain):
            return "OFFICIAL"

    if hostname.endswith(".gov.in") or hostname.endswith(".nic.in") or hostname.endswith(".edu.in") or hostname.endswith(".ac.in"):
        return "OFFICIAL"

    return "EXTRACTED"


def extract_scholarship_info(result: dict) -> dict:
    """Extract comprehensive scholarship details with robust validations."""
    if not isinstance(result, dict):
        result = {}

    original_url = result.get("url") or result.get("source_url")
    source_url = normalize_source_url(original_url)

    title = clean_text(result.get("title") or result.get("name") or "")
    search_snippet = clean_text(result.get("description") or "")

    webpage_text = ""
    if source_url:
        try:
            webpage_text = fetch_webpage(source_url) or ""
        except Exception:
            webpage_text = ""

    webpage_text = clean_text(webpage_text)[:MAX_TEXT_LENGTH]
    search_text = clean_text(f"{title}. {search_snippet}")
    combined_text = clean_text(f"{search_text}. {webpage_text}")[:MAX_TEXT_LENGTH]

    deadline = find_deadline(webpage_text) or find_deadline(search_text)
    amount = find_amount(webpage_text) or find_amount(search_text)
    provider = extract_provider(webpage_text, title=title, source_url=source_url or "")
    description = extract_description(webpage_text, search_snippet, title)

    trust_level = get_trust_level(source_url or "")

    return {
        "name": title or "Scholarship Opportunity",
        "provider": provider or "Scholarship Authority / Foundation",
        "description": description,
        "source_url": source_url,
        "application_deadline": deadline,
        "scholarship_amount": amount,
        "eligibility": extract_eligibility(combined_text),
        "benefits": extract_benefits(combined_text),
        "required_documents": extract_required_documents(combined_text),
        "verification_status": trust_level,
    }


def extract_from_search_results(results: list[dict]) -> list[dict]:
    """
    Extract unique search results while filtering out article listicles
    and junk domains.
    """
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

        title = result.get("title") or result.get("name") or ""

        # Filter out generic articles, blogs, YouTube, forums
        if is_article_or_junk(title, normalized_url):
            logger.info("Filtered out non-scholarship article/media URL: %s", normalized_url)
            continue

        normalized_result = {
            **result,
            "url": normalized_url,
        }

        scholarship = extract_scholarship_info(normalized_result)
        scholarships.append(scholarship)
        seen_urls.add(normalized_url)

    return scholarships
