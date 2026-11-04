from app.services.eligibility_engine import (
    evaluate_score,
    evaluate_course,
    evaluate_category,
    evaluate_state,
    evaluate_education_level,
    evaluate_eligibility,
)


def test_cgpa_to_percentage_conversion_pass():
    # Student with 8.0 CGPA applying for scholarship requiring 60%
    # 8.0 * 9.5 = 76.0% >= 60% -> PASS
    res = evaluate_score(
        student_score=8.0,
        student_score_type="cgpa",
        minimum_score=60.0,
        required_score_type="percentage",
    )
    assert res["status"] == "PASS"
    assert "converted to ~76.0%" in res["reason"]


def test_cgpa_to_percentage_conversion_fail():
    # Student with 5.5 CGPA applying for scholarship requiring 60%
    # 5.5 * 9.5 = 52.25% < 60% -> FAIL
    res = evaluate_score(
        student_score=5.5,
        student_score_type="cgpa",
        minimum_score=60.0,
        required_score_type="percentage",
    )
    assert res["status"] == "FAIL"
    assert "converted to ~52.25%" in res["reason"]


def test_percentage_to_cgpa_conversion():
    # Student with 75% applying for scholarship requiring 7.0 CGPA
    # 75 / 9.5 = 7.89 CGPA >= 7.0 -> PASS
    res = evaluate_score(
        student_score=75.0,
        student_score_type="percentage",
        minimum_score=7.0,
        required_score_type="cgpa",
    )
    assert res["status"] == "PASS"
    assert "converted to ~7.89 CGPA" in res["reason"]


def test_course_synonym_matching():
    # Student with "Computer Science Engineering" vs scholarship requiring "B.Tech"
    res1 = evaluate_course(
        student_course="Computer Science Engineering",
        eligible_courses=["B.Tech"],
    )
    assert res1["status"] == "PASS"

    # Student with "B.E." vs "Bachelor of Technology"
    res2 = evaluate_course(
        student_course="B.E.",
        eligible_courses=["Bachelor of Technology"],
    )
    assert res2["status"] == "PASS"

    # Student with "MBBS" vs "Engineering" -> FAIL
    res3 = evaluate_course(
        student_course="MBBS",
        eligible_courses=["B.Tech", "Engineering"],
    )
    assert res3["status"] == "FAIL"


def test_case_insensitive_matching():
    # Category lowercase
    assert evaluate_category("obc", ["OBC"])["status"] == "PASS"

    # State lowercase
    assert evaluate_state("uttar pradesh", ["Uttar Pradesh"])["status"] == "PASS"

    # Education level lowercase
    assert evaluate_education_level("undergraduate", ["UNDERGRADUATE"])["status"] == "PASS"
