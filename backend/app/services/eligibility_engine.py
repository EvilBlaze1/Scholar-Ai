from datetime import date, datetime
def evaluate_income(
    student_income: float | None,
    maximum_income: float | None
) -> dict:
    if maximum_income is None:
        return {
            "status": "PASS",
            "reason": "No maximum income requirement."
        }

    if student_income is None:
        return {
            "status": "UNKNOWN",
            "reason": "Student family income is missing."
        }

    if student_income <= maximum_income:
        return {
            "status": "PASS",
            "reason": "Student family income is within the allowed limit."
        }

    return {
        "status": "FAIL",
        "reason": "Student family income exceeds the allowed limit."
    }

def evaluate_category(
    student_category: str | None,
    eligible_categories: list[str]
) -> dict:
    if not eligible_categories:
        return {
            "status": "PASS",
            "reason": "No category restriction."
        }

    if student_category is None:
        return {
            "status": "UNKNOWN",
            "reason": "Student category is missing."
        }

    if student_category in eligible_categories:
        return {
            "status": "PASS",
            "reason": "Student category is eligible."
        }

    return {
        "status": "FAIL",
        "reason": "Student category is not eligible."
    }


def evaluate_state(
    student_state: str | None,
    eligible_states: list[str]
) -> dict:
    if not eligible_states:
        return {
            "status": "PASS",
            "reason": "No state restriction."
        }

    if student_state is None:
        return {
            "status": "UNKNOWN",
            "reason": "Student state is missing."
        }

    if student_state in eligible_states:
        return {
            "status": "PASS",
            "reason": "Student state is eligible."
        }

    return {
        "status": "FAIL",
        "reason": "Student state is not eligible."
    }

def evaluate_education_level(
    student_education_level: str | None,
    eligible_education_levels: list[str]
) -> dict:
    if not eligible_education_levels:
        return {
            "status": "PASS",
            "reason": "No education-level restriction."
        }

    if student_education_level is None:
        return {
            "status": "UNKNOWN",
            "reason": "Student education level is missing."
        }

    if student_education_level in eligible_education_levels:
        return {
            "status": "PASS",
            "reason": "Student education level is eligible."
        }

    return {
        "status": "FAIL",
        "reason": "Student education level is not eligible."
    }

def evaluate_course(
    student_course: str | None,
    eligible_courses: list[str]
) -> dict:
    if not eligible_courses:
        return {
            "status": "PASS",
            "reason": "No course restriction."
        }

    if student_course is None:
        return {
            "status": "UNKNOWN",
            "reason": "Student course is missing."
        }

    if student_course in eligible_courses:
        return {
            "status": "PASS",
            "reason": "Student course is eligible."
        }

    return {
        "status": "FAIL",
        "reason": "Student course is not eligible."
    }

def evaluate_score(
    student_score: float | None,
    student_score_type: str | None,
    minimum_score: float | None,
    required_score_type: str | None
) -> dict:
    if minimum_score is None:
        return {
            "status": "PASS",
            "reason": "No minimum score requirement."
        }

    if student_score is None or student_score_type is None:
        return {
            "status": "UNKNOWN",
            "reason": "Student score information is missing."
        }

    if required_score_type is None:
        return {
            "status": "UNKNOWN",
            "reason": "Scholarship score type is missing."
        }

    if student_score_type != required_score_type:
        return {
            "status": "UNKNOWN",
            "reason": "Student score type does not match the scholarship requirement."
        }

    if student_score >= minimum_score:
        return {
            "status": "PASS",
            "reason": "Student score meets the minimum requirement."
        }

    return {
        "status": "FAIL",
        "reason": "Student score is below the minimum requirement."
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
    maximum_age: int | None
) -> dict:
    if minimum_age is None and maximum_age is None:
        return {
            "status": "PASS",
            "reason": "No age restriction."
        }

    if date_of_birth is None:
        return {
            "status": "UNKNOWN",
            "reason": "Student date of birth is missing."
        }

    student_age = calculate_age(date_of_birth)

    if minimum_age is not None and student_age < minimum_age:
        return {
            "status": "FAIL",
            "reason": "Student is below the minimum age requirement."
        }

    if maximum_age is not None and student_age > maximum_age:
        return {
            "status": "FAIL",
            "reason": "Student exceeds the maximum age requirement."
        }

    return {
        "status": "PASS",
        "reason": "Student age satisfies the scholarship requirement."
    }


def evaluate_gender(
    student_gender: str | None,
    eligible_genders: list[str]
) -> dict:
    if not eligible_genders:
        return {
            "status": "PASS",
            "reason": "No gender restriction."
        }

    if student_gender is None:
        return {
            "status": "UNKNOWN",
            "reason": "Student gender is missing."
        }

    if student_gender in eligible_genders:
        return {
            "status": "PASS",
            "reason": "Student gender is eligible."
        }

    return {
        "status": "FAIL",
        "reason": "Student gender is not eligible."
    }

def evaluate_disability(
    student_disability_status: bool | None,
    disability_required: bool | None
) -> dict:
    if disability_required is None or disability_required is False:
        return {
            "status": "PASS",
            "reason": "No disability requirement."
        }

    if student_disability_status is None:
        return {
            "status": "UNKNOWN",
            "reason": "Student disability status is missing."
        }

    if student_disability_status is True:
        return {
            "status": "PASS",
            "reason": "Student satisfies the disability requirement."
        }

    return {
        "status": "FAIL",
        "reason": "Student does not satisfy the disability requirement."
    }

def evaluate_eligibility(student: dict, scholarship: dict) -> dict:
    rule_results = []

    rule_results.append({
        "rule_id": "income",
        "rule_type": "income",
        **evaluate_income(
            student.get("annual_family_income"),
            scholarship.get("maximum_family_income")
        )
    })

    rule_results.append({
        "rule_id": "category",
        "rule_type": "category",
        **evaluate_category(
            student.get("category"),
            scholarship.get("eligible_categories", [])
        )
    })

    rule_results.append({
        "rule_id": "state",
        "rule_type": "state",
        **evaluate_state(
            student.get("domicile_state"),
            scholarship.get("eligible_states", [])
        )
    })

    rule_results.append({
        "rule_id": "education",
        "rule_type": "education",
        **evaluate_education_level(
            student.get("education_level"),
            scholarship.get("eligible_education_levels", [])
        )
    })

    rule_results.append({
        "rule_id": "course",
        "rule_type": "course",
        **evaluate_course(
            student.get("course"),
            scholarship.get("eligible_courses", [])
        )
    })

    rule_results.append({
        "rule_id": "score",
        "rule_type": "score",
        **evaluate_score(
            student.get("score"),
            student.get("score_type"),
            scholarship.get("minimum_score"),
            scholarship.get("minimum_score_type")
        )
    })

    rule_results.append({
        "rule_id": "age",
        "rule_type": "age",
        **evaluate_age(
            student.get("date_of_birth"),
            scholarship.get("minimum_age"),
            scholarship.get("maximum_age")
        )
    })

    rule_results.append({
        "rule_id": "gender",
        "rule_type": "gender",
        **evaluate_gender(
            student.get("gender"),
            scholarship.get("eligible_genders", [])
        )
    })

    rule_results.append({
        "rule_id": "disability",
        "rule_type": "disability",
        **evaluate_disability(
            student.get("disability_status"),
            scholarship.get("disability_required")
        )
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
        "verification_required": verification_required
    }