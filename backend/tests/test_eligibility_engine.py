from app.services.eligibility_engine import evaluate_eligibility


def test_eligible_student():
    student = {
        "annual_family_income": 250000,
        "category": "OBC",
        "domicile_state": "Uttar Pradesh",
        "education_level": "B.Tech",
        "course": "Computer Science",
        "score": 82.5,
        "score_type": "percentage",
        "date_of_birth": "2004-01-15",
        "gender": "Male",
        "disability_status": False,
    }

    scholarship = {
        "maximum_family_income": 300000,
        "eligible_categories": ["SC", "ST", "OBC"],
        "eligible_states": ["Uttar Pradesh"],
        "eligible_education_levels": ["B.Tech"],
        "eligible_courses": ["Computer Science"],
        "minimum_score": 60,
        "minimum_score_type": "percentage",
        "minimum_age": 18,
        "maximum_age": 25,
        "eligible_genders": ["Male", "Female"],
        "disability_required": False,
    }

    result = evaluate_eligibility(student, scholarship)

    assert result["status"] == "ELIGIBLE"
    assert result["passed_rules"] == 9
    assert result["failed_rules"] == 0
    assert result["verification_required"] is False

def test_ineligible_student():
    student = {
        "annual_family_income": 500000,
        "category": "General",
        "domicile_state": "Delhi",
        "education_level": "B.Tech",
        "course": "Computer Science",
        "score": 55,
        "score_type": "percentage",
        "date_of_birth": "2004-01-15",
        "gender": "Male",
        "disability_status": False,
    }

    scholarship = {
        "maximum_family_income": 300000,
        "eligible_categories": ["SC", "ST", "OBC"],
        "eligible_states": ["Uttar Pradesh"],
        "eligible_education_levels": ["B.Tech"],
        "eligible_courses": ["Computer Science"],
        "minimum_score": 60,
        "minimum_score_type": "percentage",
        "minimum_age": 18,
        "maximum_age": 25,
        "eligible_genders": ["Male", "Female"],
        "disability_required": False,
    }

    result = evaluate_eligibility(student, scholarship)

    assert result["status"] == "INELIGIBLE"
    assert result["failed_rules"] == 4
    assert result["verification_required"] is False

def test_needs_verification():
    student = {
        "annual_family_income": None,
        "category": None,
        "domicile_state": "Uttar Pradesh",
        "education_level": "B.Tech",
        "course": "Computer Science",
        "score": 82.5,
        "score_type": "percentage",
        "date_of_birth": None,
        "gender": "Male",
        "disability_status": None,
    }

    scholarship = {
        "maximum_family_income": 300000,
        "eligible_categories": ["SC", "ST", "OBC"],
        "eligible_states": ["Uttar Pradesh"],
        "eligible_education_levels": ["B.Tech"],
        "eligible_courses": ["Computer Science"],
        "minimum_score": 60,
        "minimum_score_type": "percentage",
        "minimum_age": 18,
        "maximum_age": 25,
        "eligible_genders": ["Male", "Female"],
        "disability_required": True,
    }

    result = evaluate_eligibility(student, scholarship)

    assert result["status"] == "NEEDS_VERIFICATION"
    assert result["failed_rules"] == 0
    assert result["verification_required"] is True