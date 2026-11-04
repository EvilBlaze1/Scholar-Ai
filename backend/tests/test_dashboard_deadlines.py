from datetime import date
from app.services.dashboard_service import _parse_deadline, _upcoming_deadlines


def test_parse_deadline_various_formats():
    assert _parse_deadline("2026-12-31") == date(2026, 12, 31)
    assert _parse_deadline("31/10/2026") == date(2026, 10, 31)
    assert _parse_deadline("31-10-2026") == date(2026, 10, 31)
    assert _parse_deadline("31.10.2026") == date(2026, 10, 31)
    assert _parse_deadline("31st October 2026") == date(2026, 10, 31)
    assert _parse_deadline("31st Oct 2026") == date(2026, 10, 31)
    assert _parse_deadline("1st January 2027") == date(2027, 1, 1)
    assert _parse_deadline("2nd Feb 2027") == date(2027, 2, 2)
    assert _parse_deadline("3rd March 2027") == date(2027, 3, 3)
    assert _parse_deadline("Invalid Date") is None
    assert _parse_deadline("") is None
    assert _parse_deadline(None) is None


def test_upcoming_deadlines_merging_matches_and_saved():
    matches = [
        {
            "scholarship_id": "match_1",
            "name": "State Merit Scholarship",
            "application_deadline": "31st Dec 2029",
            "status": "ELIGIBLE",
            "source_url": "https://scholarships.gov.in/m1",
        },
        {
            "scholarship_id": "match_2",
            "name": "Expired Scholarship",
            "application_deadline": "01 Jan 2020",
            "status": "ELIGIBLE",
            "source_url": "https://scholarships.gov.in/m2",
        },
    ]

    saved_scholarships = [
        {
            "scholarship_id": "saved_1",
            "scholarship": {
                "id": "saved_1",
                "name": "Central Sector Scheme",
                "application_deadline": "30 Nov 2029",
                "status": "ELIGIBLE",
                "source_url": "https://scholarships.gov.in/s1",
            },
        }
    ]

    upcoming = _upcoming_deadlines(matches, saved_scholarships, limit=5)
    assert len(upcoming) == 2
    # Check that Central Sector Scheme (30 Nov 2029) is sorted before State Merit (31 Dec 2029)
    assert upcoming[0]["scholarship_id"] == "saved_1"
    assert upcoming[0]["name"] == "Central Sector Scheme"
    assert upcoming[1]["scholarship_id"] == "match_1"
    assert upcoming[1]["name"] == "State Merit Scholarship"
