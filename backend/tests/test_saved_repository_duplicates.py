from unittest.mock import MagicMock, patch
from app.database.saved_scholarship_repository import (
    save_scholarship,
    delete_saved_scholarship,
)


@patch("app.database.saved_scholarship_repository.saved_scholarships_collection")
def test_save_scholarship_detects_existing_by_source_url(mock_collection):
    # Simulate existing item found
    mock_collection.find_one.return_value = {
        "_id": "mock_obj_id",
        "scholarship_id": "https://scholarships.gov.in/scheme1",
    }

    result = save_scholarship(
        user_id="user_123",
        scholarship_id="https://scholarships.gov.in/scheme1",
        scholarship_data={"name": "Govt Scheme", "source_url": "https://scholarships.gov.in/scheme1"},
    )

    assert result["already_saved"] is True
    assert result["id"] == "mock_obj_id"
    mock_collection.insert_one.assert_not_called()


@patch("app.database.saved_scholarship_repository.saved_scholarships_collection")
def test_delete_saved_scholarship_multi_criteria(mock_collection):
    # Simulate successful deletion by query
    mock_delete_result = MagicMock()
    mock_delete_result.deleted_count = 1
    mock_collection.delete_one.return_value = mock_delete_result

    deleted = delete_saved_scholarship(
        user_id="user_123",
        scholarship_id="https://scholarships.gov.in/scheme1",
    )

    assert deleted is True
    mock_collection.delete_one.assert_called_once()
    called_query = mock_collection.delete_one.call_args[0][0]
    assert called_query["user_id"] == "user_123"
    assert "$or" in called_query
