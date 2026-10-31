"""Negative API Test Cases for Restful-Booker.

Evaluates requirement (b):
- (i) Update a booking without a token
- (ii) Fetch a booking id that does not exist
- (iii) Fetch the deleted booking again
- Deep negative-case awareness: status codes, exact body assertions, authorization checks, and edge cases.
"""
import pytest
from core.booker_client import BookerClient
from utils.data_generator import BookingDataFactory
from utils.logger import get_logger

logger = get_logger("TestNegativeCases")


@pytest.mark.negative
class TestNegativeCases:
    """Negative test suite validating error handling and security controls."""

    def test_update_booking_without_token(self, api_client: BookerClient, created_booking):
        """Requirement (b)(i): Assert the response when updating a booking without a token."""
        booking_id, original_payload = created_booking
        logger.info(f"Testing unauthorized update on booking ID: {booking_id}")

        tamper_payload = BookingDataFactory.create_updated_payload(
            original_payload,
            firstname="Unauthorized_Attempt",
            totalprice=99999,
        )

        # 1. Attempt PUT without any token or Cookie header
        response = api_client.update_booking(
            booking_id=booking_id,
            payload=tamper_payload,
            token=None,  # No token provided
        )

        # Assert status code and response body
        assert response.status_code == 403, (
            f"Expected status 403 Forbidden when updating without token, got {response.status_code}. "
            f"Response body: {response.text}"
        )
        assert response.text == "Forbidden", (
            f"Expected response text 'Forbidden', got '{response.text}'"
        )

        # 2. Attempt PUT with an invalid / forged token
        response_invalid_token = api_client.update_booking(
            booking_id=booking_id,
            payload=tamper_payload,
            token="invalid_token_xyz_9999",
        )
        assert response_invalid_token.status_code == 403, (
            f"Expected status 403 Forbidden with invalid token, got {response_invalid_token.status_code}. "
            f"Response body: {response_invalid_token.text}"
        )
        assert response_invalid_token.text == "Forbidden", (
            f"Expected response text 'Forbidden', got '{response_invalid_token.text}'"
        )

        # 3. Verify original booking was NOT modified (data integrity check)
        verify_resp = api_client.get_booking(booking_id)
        assert verify_resp.status_code == 200
        current_data = verify_resp.json()
        assert current_data["firstname"] == original_payload["firstname"], (
            "Booking firstname was modified despite 403 Forbidden!"
        )
        logger.info("Unauthorized update was rejected and data integrity maintained.")

    def test_fetch_booking_id_that_does_not_exist(self, api_client: BookerClient):
        """Requirement (b)(ii): Assert the response when fetching a booking ID that does not exist."""
        non_existent_id = 999999999
        logger.info(f"Fetching non-existent booking ID: {non_existent_id}")

        response = api_client.get_booking(non_existent_id)

        # Assert status code and response body
        assert response.status_code == 404, (
            f"Expected status 404 Not Found for non-existent ID {non_existent_id}, "
            f"got {response.status_code}. Response: {response.text}"
        )
        assert response.text == "Not Found", (
            f"Expected response text 'Not Found', got '{response.text}'"
        )
        logger.info("Non-existent booking lookup correctly returned 404 Not Found.")

    def test_fetch_deleted_booking_again(self, api_client: BookerClient, auth_token: str):
        """Requirement (b)(iii): Assert the response when fetching a deleted booking again."""
        # Step 1: Create a dedicated booking for deletion
        create_payload = BookingDataFactory.create_booking_payload(
            firstname="To_Be_Deleted",
            lastname="User",
        )
        create_resp = api_client.create_booking(create_payload)
        assert create_resp.status_code == 200, f"Failed to create booking: {create_resp.text}"
        booking_id = create_resp.json()["bookingid"]
        logger.info(f"Created temporary booking ID {booking_id} for deletion test.")

        # Step 2: Delete the booking with token
        delete_resp = api_client.delete_booking(booking_id, token=auth_token)
        assert delete_resp.status_code == 201, (
            f"Expected status 201 on DELETE, got {delete_resp.status_code}. Response: {delete_resp.text}"
        )
        assert delete_resp.text == "Created"
        logger.info(f"Booking ID {booking_id} successfully deleted.")

        # Step 3: Fetch the deleted booking again
        fetch_again_resp = api_client.get_booking(booking_id)

        # Assert status code and response body
        assert fetch_again_resp.status_code == 404, (
            f"Expected status 404 when fetching deleted booking {booking_id}, "
            f"got {fetch_again_resp.status_code}. Response: {fetch_again_resp.text}"
        )
        assert fetch_again_resp.text == "Not Found", (
            f"Expected response text 'Not Found', got '{fetch_again_resp.text}'"
        )
        logger.info("Fetching deleted booking confirmed 404 Not Found.")

    def test_delete_booking_without_token(self, api_client: BookerClient, created_booking):
        """Assert the response when attempting to delete a booking without an auth token."""
        booking_id, _ = created_booking
        logger.info(f"Attempting unauthorized delete on booking ID {booking_id}")

        response = api_client.delete_booking(booking_id, token=None)

        assert response.status_code == 403, (
            f"Expected status 403 Forbidden for DELETE without token, got {response.status_code}."
        )
        assert response.text == "Forbidden", (
            f"Expected response text 'Forbidden', got '{response.text}'"
        )

        # Verify booking still exists
        check_resp = api_client.get_booking(booking_id)
        assert check_resp.status_code == 200, "Booking was deleted despite lack of authorization!"
        logger.info("Unauthorized delete properly prevented.")

    def test_auth_with_invalid_credentials(self, api_client: BookerClient):
        """Assert the response when authenticating with incorrect credentials."""
        logger.info("Testing auth with invalid credentials.")
        response = api_client.create_token(username="invalid_user", password="wrong_password")

        assert response.status_code == 200, (
            f"Expected status 200 for auth response, got {response.status_code}"
        )
        data = response.json()
        assert "token" not in data, "Token should not be issued for invalid credentials"
        assert data.get("reason") == "Bad credentials", (
            f"Expected reason 'Bad credentials', got '{data.get('reason')}'"
        )
        logger.info("Invalid authentication properly rejected with Bad credentials reason.")
