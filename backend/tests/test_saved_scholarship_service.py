from unittest.mock import patch
from app.services.saved_scholarship_service import (
    add_saved_scholarship,
    fetch_saved_scholarships,
    remove_saved_scholarship,
)


@patch("app.services.saved_scholarship_service.save_scholarship")
def test_add_saved_scholarship(mock_save):
    mock_save.return_value = {"id": "save_1", "already_saved": False}
    result = add_saved_scholarship(
        user_id="u1",
        scholarship_id="s1",
        scholarship_data={"name": "Test Scheme"},
    )
    assert result["already_saved"] is False
    mock_save.assert_called_once_with("u1", "s1", {"name": "Test Scheme"})


@patch("app.services.saved_scholarship_service.get_saved_scholarships")
def test_fetch_saved_scholarships(mock_get):
    mock_get.return_value = [{"scholarship_id": "s1"}]
    result = fetch_saved_scholarships("u1")
    assert len(result) == 1
    assert result[0]["scholarship_id"] == "s1"


@patch("app.services.saved_scholarship_service.delete_saved_scholarship")
def test_remove_saved_scholarship(mock_del):
    mock_del.return_value = True
    assert remove_saved_scholarship("u1", "s1") is True
    mock_del.return_value = False
    assert remove_saved_scholarship("u1", "s2") is False
