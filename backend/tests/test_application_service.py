from unittest.mock import patch
from app.services.application_service import (
    add_application,
    fetch_user_applications,
    change_application_status,
    update_user_application,
    remove_application,
)


@patch("app.services.application_service.get_application")
@patch("app.services.application_service.create_application")
def test_add_application(mock_create, mock_get):
    mock_get.return_value = None
    mock_create.return_value = {"id": "app_123"}

    result = add_application(
        user_id="user_1",
        scholarship_id="sch_1",
        status="APPLIED",
        scholarship_name="National Merit",
        provider="Govt of India",
        scholarship_amount="50000",
    )

    assert result == {"id": "app_123"}
    mock_create.assert_called_once()
    called_data = mock_create.call_args[0][0]
    assert called_data["user_id"] == "user_1"
    assert called_data["scholarship_id"] == "sch_1"
    assert called_data["status"] == "APPLIED"
    assert called_data["scholarship_name"] == "National Merit"
    assert called_data["provider"] == "Govt of India"
    assert called_data["scholarship_amount"] == "50000"


@patch("app.services.application_service.get_application")
def test_add_application_already_exists(mock_get):
    mock_get.return_value = {"id": "existing"}

    result = add_application(
        user_id="user_1",
        scholarship_id="sch_1",
        status="APPLIED",
    )

    assert "error" in result
    assert result["error"] == "Application already exists"


@patch("app.services.application_service.get_application")
@patch("app.services.application_service.update_application")
def test_update_application_status(mock_update, mock_get):
    mock_get.return_value = {"id": "existing", "status": "APPLIED"}
    mock_update.return_value = True

    result = change_application_status(
        user_id="user_1",
        scholarship_id="sch_1",
        status="SELECTED",
    )

    assert result["status"] == "SELECTED"
    mock_update.assert_called_once()


@patch("app.services.application_service.get_application")
@patch("app.services.application_service.update_application")
def test_update_user_application_with_notes(mock_update, mock_get):
    mock_get.return_value = {"id": "existing", "status": "APPLIED"}
    mock_update.return_value = True

    result = update_user_application(
        user_id="user_1",
        scholarship_id="sch_1",
        status="UNDER_REVIEW",
        notes="Submitted documents online",
    )

    assert result["status"] == "UNDER_REVIEW"
    assert result["notes"] == "Submitted documents online"


@patch("app.services.application_service.delete_application")
def test_remove_application(mock_delete):
    mock_delete.return_value = True
    result = remove_application("user_1", "sch_1")
    assert result == {"message": "Application deleted", "scholarship_id": "sch_1"}

    mock_delete.return_value = False
    result_err = remove_application("user_1", "sch_1")
    assert result_err == {"error": "Application not found"}
