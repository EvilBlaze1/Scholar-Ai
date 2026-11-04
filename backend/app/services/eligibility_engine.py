from datetime import date, datetime

COURSE_SYNONYM_CLUSTERS = [
    {"b.tech", "btech", "b.e.", "be", "bachelor of technology", "bachelor of engineering", "engineering", "computer science"},
    {"b.sc", "bsc", "bachelor of science"},
    {"b.com", "bcom", "bachelor of commerce"},
    {"bba", "bachelor of business administration"},
    {"b.a.", "ba", "bachelor of arts"},
    {"mbbs", "medicine", "medical"},
    {"m.tech", "mtech", "m.e.", "me", "master of technology", "master of engineering"},
    {"mba", "master of business administration"},
    {"mca", "master of computer applications"},
    {"m.sc", "msc", "master of science"},
    {"b.pharm", "bpharm", "pharmacy"},
    {"diploma", "polytechnic"},
    {"law", "llb", "b.a. ll.b", "ballb"},
]


def evaluate_income(
    student_income: float | None,
    maximum_income: float | None,
) -> dict:
    if maximum_income is None:
        return {
            "status": "PASS",
            "reason": "No maximum income requirement.",
        }

    if student_income is None:
        return {
            "status": "UNKNOWN",
            "reason": "Student family income is missing.",
        }

    if student_income <= maximum_income:
        return {
            "status": "PASS",
            "reason": "Student family income is within the allowed limit.",
        }

    return {
        "status": "FAIL",
        "reason": "Student family income exceeds the allowed limit.",
    }


def evaluate_category(
    student_category: str | None,
    eligible_categories: list[str],
) -> dict:
    if not eligible_categories:
        return {
            "status": "PASS",
            "reason": "No category restriction.",
        }

    if student_category is None:
        return {
            "status": "UNKNOWN",
            "reason": "Student category is missing.",
        }

    clean_student = student_category.strip().upper()
    clean_eligible = [c.strip().upper() for c in eligible_categories if isinstance(c, str)]

    if clean_student in clean_eligible or "ALL" in clean_eligible:
        return {
            "status": "PASS",
            "reason": "Student category is eligible.",
        }

    return {
        "status": "FAIL",
        "reason": "Student category is not eligible.",
    }


def evaluate_state(
    student_state: str | None,
    eligible_states: list[str],
) -> dict:
    if not eligible_states:
        return {
            "status": "PASS",
            "reason": "No state restriction.",
        }

    if student_state is None:
        return {
            "status": "UNKNOWN",
            "reason": "Student state is missing.",
        }

    s_clean = student_state.strip().lower()
    e_clean = [st.strip().lower() for st in eligible_states if isinstance(st, str)]

    if any(s_clean == st or s_clean in st or st in s_clean for st in e_clean) or "all" in e_clean or "pan india" in e_clean or "all india" in e_clean:
        return {
            "status": "PASS",
            "reason": "Student state is eligible.",
        }

    return {
        "status": "FAIL",
        "reason": "Student state is not eligible.",
    }


def evaluate_education_level(
    student_education_level: str | None,
    eligible_education_levels: list[str],
) -> dict:
    if not eligible_education_levels:
        return {
            "status": "PASS",
            "reason": "No education-level restriction.",
        }

    if student_education_level is None:
        return {
            "status": "UNKNOWN",
            "reason": "Student education level is missing.",
        }

    l_clean = student_education_level.strip().lower()
    e_clean = [el.strip().lower() for el in eligible_education_levels if isinstance(el, str)]

    if any(l_clean == el or l_clean in el or el in l_clean for el in e_clean):
        return {
            "status": "PASS",
            "reason": "Student education level is eligible.",
        }

    return {
        "status": "FAIL",
        "reason": "Student education level is not eligible.",
    }


def courses_match(student_course: str, eligible_course: str) -> bool:
    s = student_course.strip().lower()
    e = eligible_course.strip().lower()

    if s == e or s in e or e in s:
        return True

    for cluster in COURSE_SYNONYM_CLUSTERS:
        if any(term in s for term in cluster) and any(term in e for term in cluster):
            return True

    return False


def evaluate_course(
    student_course: str | None,
    eligible_courses: list[str],
) -> dict:
    if not eligible_courses:
        return {
            "status": "PASS",
            "reason": "No course restriction.",
        }

    if student_course is None:
        return {
            "status": "UNKNOWN",
            "reason": "Student course is missing.",
        }

    if any(courses_match(student_course, ec) for ec in eligible_courses if isinstance(ec, str)):
        return {
            "status": "PASS",
            "reason": "Student course is eligible.",
        }

    return {
        "status": "FAIL",
        "reason": "Student course is not eligible.",
    }


def normalize_score_to_type(
    score: float,
    from_type: str,
    to_type: str,
) -> tuple[float | None, str | None]:
    """
    Standard conversion between CGPA (10-point scale) and Percentage.
    Formula widely used in India (AICTE/CBSE): Percentage = CGPA * 9.5
    """
    f_type = from_type.strip().lower()
    t_type = to_type.strip().lower()

    if f_type == t_type:
        return score, None

    if f_type in ("cgpa", "gpa") and t_type in ("percentage", "percent", "%"):
        converted = min(100.0, round(score * 9.5, 2))
        return converted, f"{score} CGPA converted to ~{converted}% (using standard 9.5 multiplier)"

    if f_type in ("percentage", "percent", "%") and t_type in ("cgpa", "gpa"):
        converted = min(10.0, round(score / 9.5, 2))
        return converted, f"{score}% converted to ~{converted} CGPA (using standard 9.5 divisor)"

    return None, None


def evaluate_score(
    student_score: float | None,
    student_score_type: str | None,
    minimum_score: float | None,
    required_score_type: str | None,
) -> dict:
    if minimum_score is None:
        return {
            "status": "PASS",
            "reason": "No minimum score requirement.",
        }

    if student_score is None or student_score_type is None:
        return {
            "status": "UNKNOWN",
            "reason": "Student score information is missing.",
        }

    if required_score_type is None:
        return {
            "status": "UNKNOWN",
            "reason": "Scholarship score type is missing.",
        }

    norm_student_type = student_score_type.strip().lower()
    norm_required_type = required_score_type.strip().lower()

    effective_score = student_score
    conversion_note = ""

    if norm_student_type != norm_required_type:
        converted, note = normalize_score_to_type(student_score, norm_student_type, norm_required_type)
        if converted is not None:
            effective_score = converted
            conversion_note = f" ({note})"
        else:
            return {
                "status": "UNKNOWN",
                "reason": f"Student score type ({student_score_type}) does not match the scholarship requirement ({required_score_type}).",
            }

    if effective_score >= minimum_score:
        return {
            "status": "PASS",
            "reason": f"Student score meets the minimum requirement{conversion_note}.",
        }

    return {
        "status": "FAIL",
        "reason": f"Student score is below the minimum requirement{conversion_note}.",
    }


def calculate_age(date_of_birth: str) -> int:
    birth_date = datetime.strptime(date_of_birth, "%Y-%m-%d").date()
    today = date.today()

    age = today.year - birth_date.year

    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1

    return age


def evaluate_age(
    date_of_birth: str | None,
    minimum_age: int | None,
    maximum_age: int | None,
) -> dict:
    if minimum_age is None and maximum_age is None:
        return {
            "status": "PASS",
            "reason": "No age restriction.",
        }

    if date_of_birth is None:
        return {
            "status": "UNKNOWN",
            "reason": "Student date of birth is missing.",
        }

    student_age = calculate_age(date_of_birth)

    if minimum_age is not None and student_age < minimum_age:
        return {
            "status": "FAIL",
            "reason": "Student is below the minimum age requirement.",
        }

    if maximum_age is not None and student_age > maximum_age:
        return {
            "status": "FAIL",
            "reason": "Student exceeds the maximum age requirement.",
        }

    return {
        "status": "PASS",
        "reason": "Student age satisfies the scholarship requirement.",
    }


def evaluate_gender(
    student_gender: str | None,
    eligible_genders: list[str],
) -> dict:
    if not eligible_genders:
        return {
            "status": "PASS",
            "reason": "No gender restriction.",
        }

    if student_gender is None:
        return {
            "status": "UNKNOWN",
            "reason": "Student gender is missing.",
        }

    g_clean = student_gender.strip().upper()
    e_clean = [g.strip().upper() for g in eligible_genders if isinstance(g, str)]

    if g_clean in e_clean or "ALL" in e_clean:
        return {
            "status": "PASS",
            "reason": "Student gender is eligible.",
        }

    return {
        "status": "FAIL",
        "reason": "Student gender is not eligible.",
    }


def evaluate_disability(
    student_disability_status: bool | None,
    disability_required: bool | None,
) -> dict:
    if disability_required is None or disability_required is False:
        return {
            "status": "PASS",
            "reason": "No disability requirement.",
        }

    if student_disability_status is None:
        return {
            "status": "UNKNOWN",
            "reason": "Student disability status is missing.",
        }

    if student_disability_status is True:
        return {
            "status": "PASS",
            "reason": "Student satisfies the disability requirement.",
        }

    return {
        "status": "FAIL",
        "reason": "Student does not satisfy the disability requirement.",
    }


def evaluate_eligibility(student: dict, scholarship: dict) -> dict:
    rule_results = []

    rule_results.append({
        "rule_id": "income",
        "rule_type": "income",
        **evaluate_income(
            student.get("annual_family_income"),
            scholarship.get("maximum_family_income"),
        ),
    })

    rule_results.append({
        "rule_id": "category",
        "rule_type": "category",
        **evaluate_category(
            student.get("category"),
            scholarship.get("eligible_categories", []),
        ),
    })

    rule_results.append({
        "rule_id": "state",
        "rule_type": "state",
        **evaluate_state(
            student.get("domicile_state"),
            scholarship.get("eligible_states", []),
        ),
    })

    rule_results.append({
        "rule_id": "education",
        "rule_type": "education",
        **evaluate_education_level(
            student.get("education_level"),
            scholarship.get("eligible_education_levels", []),
        ),
    })

    rule_results.append({
        "rule_id": "course",
        "rule_type": "course",
        **evaluate_course(
            student.get("course"),
            scholarship.get("eligible_courses", []),
        ),
    })

    rule_results.append({
        "rule_id": "score",
        "rule_type": "score",
        **evaluate_score(
            student.get("score"),
            student.get("score_type"),
            scholarship.get("minimum_score"),
            scholarship.get("minimum_score_type"),
        ),
    })

    rule_results.append({
        "rule_id": "age",
        "rule_type": "age",
        **evaluate_age(
            student.get("date_of_birth"),
            scholarship.get("minimum_age"),
            scholarship.get("maximum_age"),
        ),
    })

    rule_results.append({
        "rule_id": "gender",
        "rule_type": "gender",
        **evaluate_gender(
            student.get("gender"),
            scholarship.get("eligible_genders", []),
        ),
    })

    rule_results.append({
        "rule_id": "disability",
        "rule_type": "disability",
        **evaluate_disability(
            student.get("disability_status"),
            scholarship.get("disability_required"),
        ),
    })

    passed_rules = sum(
        1 for rule in rule_results
        if rule["status"] == "PASS"
    )

    failed_rules = sum(
        1 for rule in rule_results
        if rule["status"] == "FAIL"
    )

    verification_required = any(
        rule["status"] == "UNKNOWN"
        for rule in rule_results
    )

    if failed_rules > 0:
        overall_status = "INELIGIBLE"
    elif verification_required:
        overall_status = "NEEDS_VERIFICATION"
    else:
        overall_status = "ELIGIBLE"

    return {
        "status": overall_status,
        "rule_results": rule_results,
        "passed_rules": passed_rules,
        "failed_rules": failed_rules,
        "verification_required": verification_required,
    }
