from app.services.web_scholarship_converter import convert_web_scholarship_to_schema


def test_convert_web_scholarship_populates_rules():
    extracted_data = {
        "name": "Tata Trusts Medical and Engineering Scholarship",
        "provider": "Tata Trusts",
        "description": "Financial assistance for needy students in India.",
        "source_url": "https://tatatrusts.org/scholarships/2026",
        "scholarship_amount": "₹1.5 Lakh per year",
        "application_deadline": "31 October 2026",
        "eligibility": [
            "Applicant must be pursuing B.Tech in Engineering.",
            "Family income should not exceed 2.5 LPA.",
            "Must be resident of Maharashtra state.",
            "Undergraduate students with minimum 60% marks.",
            "Only for SC and ST students.",
        ],
        "required_documents": [
            "Income certificate",
            "Marksheet",
            "Aadhaar card",
        ],
        "benefits": [
            "Tuition fee waiver and annual stipend",
        ],
        "verification_status": "OFFICIAL",
    }

    converted = convert_web_scholarship_to_schema(extracted_data)

    assert converted["name"] == "Tata Trusts Medical and Engineering Scholarship"
    assert converted["provider"] == "Tata Trusts"
    assert converted["scholarship_amount"] == "₹1.5 Lakh per year"
    assert converted["application_deadline"] == "31 October 2026"
    assert converted["maximum_family_income"] == 250000.0
    assert "Maharashtra" in converted["eligible_states"]
    assert "B.Tech" in converted["eligible_courses"]
    assert "UNDERGRADUATE" in converted["eligible_education_levels"]
    assert "SC" in converted["eligible_categories"]
    assert "ST" in converted["eligible_categories"]
    assert converted["minimum_score"] == 60.0
    assert converted["minimum_score_type"] == "percentage"
    assert converted["verification_status"] == "OFFICIAL"
