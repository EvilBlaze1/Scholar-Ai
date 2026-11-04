from app.services.scholarship_extraction_service import (
    find_amount,
    find_deadline,
    extract_provider,
    is_article_or_junk,
)


def test_amount_extraction_lakh_and_crore():
    # Test that "₹2 Lakh" is NOT truncated to "₹2"
    text1 = "Reliance Foundation offers scholarship worth ₹2 Lakh over the degree duration."
    assert find_amount(text1) == "₹2 Lakh"

    text2 = "Financial assistance of Rs. 50,000 per year for B.Tech students."
    assert find_amount(text2) == "₹50,000 per year"

    text3 = "Eligible students will receive INR 1.5 Lakh per annum as maintenance allowance."
    assert find_amount(text3) == "₹1.5 Lakh per year"


def test_amount_fee_and_stray_number_rejection():
    # Application fee should NOT be extracted as scholarship amount
    text1 = "Application fee is ₹200. Selected students will receive an award of ₹75,000."
    assert find_amount(text1) == "₹75,000"

    # Suspicious small amounts like "₹2" or step numbers must be rejected
    text2 = "Updated on March 2. Step 2 of 4. Cost of newspaper article is ₹2."
    assert find_amount(text2) is None


def test_deadline_extraction_indian_formats():
    # Ordinal date
    text1 = "The last date to apply is 31st October 2026. Late forms will be rejected."
    assert find_deadline(text1) == "31 October 2026"

    # Dot-separated format
    text2 = "Application deadline: 15.11.2026 for all candidates."
    assert find_deadline(text2) == "15.11.2026"

    # ISO format
    text3 = "Last date for application submission is 2026-12-31."
    assert find_deadline(text3) == "2026-12-31"

    # Closing date keyword
    text4 = "Registration closes on 30 Nov 2026."
    assert find_deadline(text4) == "30 Nov 2026"


def test_provider_extraction_domain_and_title():
    # Official government portal
    p1 = extract_provider("", source_url="https://scholarships.gov.in/scheme/details")
    assert "National Scholarship Portal" in p1

    p2 = extract_provider("", source_url="https://www.ugc.gov.in/stu_Scholarship6")
    assert "University Grants Commission" in p2

    # Title-based provider recognition
    p3 = extract_provider("", title="Tata Trusts Medical & Engineering Scholarship 2026")
    assert "Tata Trusts" in p3

    p4 = extract_provider("", title="Reliance Foundation Undergraduate Scholarship 2026")
    assert "Reliance Foundation" in p4

    # Explicit text wording
    p5 = extract_provider("This initiative is funded by Life Insurance Corporation of India for needy youth.")
    assert "Life Insurance Corporation of India" in p5


def test_article_and_junk_filtering():
    # Articles / listicles should be flagged as junk
    assert is_article_or_junk("Top 10 Scholarships for Engineering Students in India", "https://example.com/top-10") is True
    assert is_article_or_junk("List of Scholarships for 12th Passed Students", "https://example.com/list") is True
    assert is_article_or_junk("How to apply for NSP scholarship 2026 step by step", "https://example.com/how-to-apply") is True

    # Social media & video domains should be flagged
    assert is_article_or_junk("Scholarship info", "https://www.youtube.com/watch?v=12345") is True
    assert is_article_or_junk("Scholarship discussion", "https://www.quora.com/best-scholarships") is True

    # Legitimate scholarship programs should NOT be flagged
    assert is_article_or_junk("UGC National Fellowship for SC Students", "https://ugc.gov.in/scholarship") is False
    assert is_article_or_junk("Tata Trusts Scholarship Scheme 2026", "https://tatatrusts.org/apply") is False
