from app.services.web_eligibility_parser import (
    parse_income_requirement,
    parse_categories,
    parse_gender,
    parse_disability,
    parse_states,
    parse_courses,
    parse_education_levels,
    parse_minimum_score,
)


def test_parse_income_requirement_lpa_and_lakh():
    # 2.5 LPA
    t1 = "Annual family income of the applicant must not exceed 2.5 LPA."
    assert parse_income_requirement(t1) == 250000.0

    # 3 Lakh
    t2 = "Family income must be below ₹ 3 Lakh from all sources."
    assert parse_income_requirement(t2) == 300000.0

    # Explicit numbers
    t3 = "Gross household income should not exceed ₹ 4,50,000 per annum."
    assert parse_income_requirement(t3) == 450000.0


def test_parse_categories():
    t1 = "Candidates belonging to SC and ST categories are eligible."
    cats = parse_categories(t1)
    assert "SC" in cats
    assert "ST" in cats

    t2 = "Students from OBC-NCL and EWS groups can apply."
    cats2 = parse_categories(t2)
    assert "OBC" in cats2
    assert "EWS" in cats2


def test_parse_gender():
    t1 = "This scheme is exclusively for girl students pursuing higher education."
    assert parse_gender(t1) == ["FEMALE"]

    t2 = "Only for male students in technical education."
    assert parse_gender(t2) == ["MALE"]

    t3 = "Open for all meritorious students regardless of gender."
    assert parse_gender(t3) == []


def test_parse_disability():
    t1 = "Applicants must be persons with disabilities with benchmark disability certificate."
    assert parse_disability(t1) is True

    t2 = "All regular college students are eligible."
    assert parse_disability(t2) is None


def test_parse_states_and_courses():
    t1 = "Students with domicile of Uttar Pradesh enrolled in B.Tech Computer Science."
    assert "Uttar Pradesh" in parse_states(t1)
    assert "B.Tech" in parse_courses(t1)

    t2 = "Resident of Maharashtra pursuing MBBS or Bachelor of Science degree."
    assert "Maharashtra" in parse_states(t2)
    courses = parse_courses(t2)
    assert "MBBS" in courses
    assert "B.Sc" in courses


def test_parse_education_levels_and_minimum_score():
    t1 = "Undergraduate students having scored at least 60% marks in previous examination."
    assert "UNDERGRADUATE" in parse_education_levels(t1)
    val, score_type = parse_minimum_score(t1)
    assert val == 60.0
    assert score_type == "percentage"

    t2 = "Postgraduate candidates with minimum 7.5 CGPA."
    assert "POSTGRADUATE" in parse_education_levels(t2)
    val2, score_type2 = parse_minimum_score(t2)
    assert val2 == 7.5
    assert score_type2 == "cgpa"
