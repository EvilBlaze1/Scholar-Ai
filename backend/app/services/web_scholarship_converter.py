
from app.services.web_eligibility_parser import parse_eligibility_rules


def _clean_string(value):
    """Normalize optional text fields without inventing missing data."""
    if not isinstance(value, str):
        return None

    value = " ".join(value.split())
    return value or None


def _clean_list(values):
    """Return a normalized list of distinct, non-empty strings."""
    if not isinstance(values, list):
        return []

    cleaned = []
    seen = set()

    for value in values:
        if not isinstance(value, str):
            continue

        value = " ".join(value.split())

        if value and value.casefold() not in seen:
            cleaned.append(value)
            seen.add(value.casefold())

    return cleaned


def convert_web_scholarship_to_schema(data: dict) -> dict:
    """
    Convert extracted webpage data into the normalized scholarship
    structure expected by the existing eligibility engine.
    """
    if not isinstance(data, dict):
        raise ValueError("Scholarship data must be a dictionary.")

    name = _clean_string(data.get("name"))
    provider = _clean_string(data.get("provider"))
    description = _clean_string(data.get("description"))
    source_url = _clean_string(data.get("source_url"))

    eligibility_sentences = _clean_list(data.get("eligibility", []))
    eligibility_text = " ".join(eligibility_sentences)

    rules = parse_eligibility_rules(eligibility_text) or {}

    required_documents = _clean_list(
        data.get("required_documents", [])
    )
    benefits = _clean_list(data.get("benefits", []))

    scholarship_amount = data.get("scholarship_amount")
    if not isinstance(scholarship_amount, (str, int, float)):
        scholarship_amount = None

    deadline = _clean_string(data.get("application_deadline"))

    verification_status = _clean_string(
        data.get("verification_status")
    ) or "UNVERIFIED"

    return {
        # The source URL is a temporary external identifier, not a MongoDB ID.
        "id": source_url,

        "name": name or "Unknown Scholarship",
        "provider": provider or "Unknown Provider",
        "description": description,
        "source_url": source_url,

        # Do not infer dates or eligibility requirements from missing data.
        "application_start_date": None,
        "application_deadline": deadline,
        "academic_year": None,
        "minimum_age": None,
        "maximum_age": None,

        "eligible_categories": rules.get("eligible_categories", []),
        "eligible_states": [],
        "eligible_education_levels": [],
        "eligible_courses": [],
        "eligible_genders": rules.get("eligible_genders", []),

        "maximum_family_income": rules.get("maximum_family_income"),
        "minimum_score": None,
        "minimum_score_type": None,
        "disability_required": rules.get("disability_required"),

        "scholarship_amount": scholarship_amount,
        "amount_type": None,
        "benefits_description": " ".join(benefits) or None,
        "required_documents": required_documents,

        # Retrieval is not proof that the details are correct.
        "verification_status": verification_status,
        "last_verified_at": None,
    }
