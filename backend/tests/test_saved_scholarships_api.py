from unittest.mock import patch
import pytest
from fastapi import HTTPException
from app.api.saved_scholarship import (
    save_scholarship,
    save_scholarship_root,
    delete_saved_scholarship,
    delete_saved_scholarship_query,
    get_saved_ids,
    get_saved_scholarships,
    SaveScholarshipRequest,
)


@patch("app.api.saved_scholarship.add_saved_scholarship")
def test_save_scholarship_url_path(mock_save):
    mock_save.return_value = {"id": "rec_1", "already_saved": False}
    url_id = "https://scholarships.gov.in/scheme1"

    req = SaveScholarshipRequest(scholarship={"name": "Central Scheme", "source_url": url_id})
    res = save_scholarship(scholarship_id=url_id, payload=req, user_id="user_1")

    assert res["already_saved"] is False
    assert res["id"] == "rec_1"
    mock_save.assert_called_once_with("user_1", url_id, req.scholarship)


@patch("app.api.saved_scholarship.add_saved_scholarship")
def test_save_scholarship_via_body(mock_save):
    mock_save.return_value = {"id": "rec_2", "already_saved": False}

    req = SaveScholarshipRequest(
        scholarship_id="scheme_99",
        scholarship={"name": "Merit Scholarship"}
    )
    res = save_scholarship_root(payload=req, user_id="user_1")

    assert res["id"] == "rec_2"
    mock_save.assert_called_once_with("user_1", "scheme_99", req.scholarship)


def test_save_scholarship_empty_id_raises():
    req = SaveScholarshipRequest(scholarship_id="")
    with pytest.raises(HTTPException) as exc:
        save_scholarship_root(payload=req, user_id="user_1")
    assert exc.value.status_code == 400


@patch("app.api.saved_scholarship.remove_saved_scholarship")
def test_delete_saved_scholarship_success(mock_del):
    mock_del.return_value = True
    url_id = "https://scholarships.gov.in/scheme1"

    res = delete_saved_scholarship(scholarship_id=url_id, user_id="user_1")
    assert res["message"] == "Scholarship removed from saved list"
    assert res["scholarship_id"] == url_id

    res_q = delete_saved_scholarship_query(scholarship_id=url_id, user_id="user_1")
    assert res_q["message"] == "Scholarship removed from saved list"


@patch("app.api.saved_scholarship.remove_saved_scholarship")
def test_delete_saved_scholarship_not_found(mock_del):
    mock_del.return_value = False

    with pytest.raises(HTTPException) as exc:
        delete_saved_scholarship(scholarship_id="missing_id", user_id="user_1")
    assert exc.value.status_code == 404


@patch("app.api.saved_scholarship.fetch_saved_scholarships")
def test_get_saved_ids_endpoint(mock_get):
    mock_get.return_value = [
        {"scholarship_id": "sch_1", "scholarship": {"id": "sch_1", "source_url": "https://gov.in/1"}},
        {"scholarship_id": "sch_2", "scholarship": {"id": "sch_2"}},
    ]

    res = get_saved_ids(user_id="user_1")
    saved_ids = res["saved_ids"]
    assert "sch_1" in saved_ids
    assert "https://gov.in/1" in saved_ids
    assert "sch_2" in saved_ids


@patch("app.api.saved_scholarship.fetch_saved_scholarships")
def test_get_saved_scholarships_privacy(mock_get):
    mock_get.return_value = [{"scholarship_id": "sch_user1"}]
    res = get_saved_scholarships(user_id="user_1")
    assert len(res) == 1
    mock_get.assert_called_once_with("user_1")
