"""Happy Path API Test Chain for Restful-Booker.

Evaluates requirement (a):
- Obtain auth token (POST /auth)
- Create a booking (POST /booking)
- Read it back (GET /booking/{id})
- Update it with token (PUT /booking/{id})
- Delete it (DELETE /booking/{id})
- Extract and reuse booking ID across all chained steps
- Rigorous status code and response body assertions at each step
"""
import pytest
from config.settings import settings
from core.booker_client import BookerClient
from models.booking import AuthResponse, CreateBookingResponse, BookingResponse
from utils.data_generator import BookingDataFactory
from utils.logger import get_logger

logger = get_logger("TestHappyPathChain")


@pytest.mark.chain
@pytest.mark.happy_path
class TestHappyPathChain:
    """Test suite covering the complete happy path request chain."""

    def test_booking_lifecycle_happy_path_chain(self, api_client: BookerClient):
        """Execute and validate the complete end-to-end request chain."""
        logger.info("=== STEP 1: Obtain Auth Token (POST /auth) ===")
        auth_response = api_client.create_token(
            username=settings.AUTH_USERNAME,
            password=settings.AUTH_PASSWORD,
        )

        # Assert status code
        assert auth_response.status_code == 200, (
            f"Expected status 200 on /auth, got {auth_response.status_code}. "
            f"Response: {auth_response.text}"
        )

        # Validate schema & extract token
        auth_data = auth_response.json()
        validated_auth = AuthResponse.model_validate(auth_data)
        assert validated_auth.token is not None, "Token must be present in auth response"
        assert len(validated_auth.token) > 0, "Token must be a non-empty string"
        token = validated_auth.token
        logger.info(f"Auth token obtained: {token[:4]}****")

        # -------------------------------------------------------------
        logger.info("=== STEP 2: Create a Booking (POST /booking) ===")
        initial_payload = BookingDataFactory.create_booking_payload(
            firstname="Ada",
            lastname="Lovelace",
            totalprice=550,
            depositpaid=True,
            additionalneeds="High-speed Internet & Tea",
        )
        create_response = api_client.create_booking(initial_payload)

        # Assert status code
        assert create_response.status_code == 200, (
            f"Expected status 200 on /booking, got {create_response.status_code}. "
            f"Response: {create_response.text}"
        )

        # Validate schema
        create_data = create_response.json()
        validated_create = CreateBookingResponse.model_validate(create_data)

        # Extract booking ID and assert it is a positive integer
        booking_id = validated_create.bookingid
        assert isinstance(booking_id, int) and booking_id > 0, f"Invalid booking ID: {booking_id}"
        logger.info(f"Booking created successfully with ID: {booking_id}")

        # Assert key response fields match requested payload
        created_booking = create_data["booking"]
        assert created_booking["firstname"] == initial_payload["firstname"], "First name mismatch"
        assert created_booking["lastname"] == initial_payload["lastname"], "Last name mismatch"
        assert created_booking["totalprice"] == initial_payload["totalprice"], "Total price mismatch"
        assert created_booking["depositpaid"] == initial_payload["depositpaid"], "Deposit paid mismatch"
        assert (
            created_booking["bookingdates"]["checkin"]
            == initial_payload["bookingdates"]["checkin"]
        ), "Check-in date mismatch"
        assert (
            created_booking["bookingdates"]["checkout"]
            == initial_payload["bookingdates"]["checkout"]
        ), "Check-out date mismatch"
        assert (
            created_booking["additionalneeds"] == initial_payload["additionalneeds"]
        ), "Additional needs mismatch"

        # -------------------------------------------------------------
        logger.info(f"=== STEP 3: Read Back Booking (GET /booking/{booking_id}) ===")
        get_response = api_client.get_booking(booking_id)

        # Assert status code
        assert get_response.status_code == 200, (
            f"Expected status 200 on GET /booking/{booking_id}, got {get_response.status_code}. "
            f"Response: {get_response.text}"
        )

        # Validate schema
        get_data = get_response.json()
        BookingResponse.model_validate(get_data)

        # Assert key fields match created booking
        assert get_data["firstname"] == initial_payload["firstname"], "Retrieved first name mismatch"
        assert get_data["lastname"] == initial_payload["lastname"], "Retrieved last name mismatch"
        assert get_data["totalprice"] == initial_payload["totalprice"], "Retrieved total price mismatch"
        assert get_data["depositpaid"] == initial_payload["depositpaid"], "Retrieved deposit paid mismatch"
        assert (
            get_data["bookingdates"]["checkin"]
            == initial_payload["bookingdates"]["checkin"]
        ), "Retrieved checkin mismatch"
        assert (
            get_data["bookingdates"]["checkout"]
            == initial_payload["bookingdates"]["checkout"]
        ), "Retrieved checkout mismatch"
        assert (
            get_data["additionalneeds"] == initial_payload["additionalneeds"]
        ), "Retrieved additional needs mismatch"

        # -------------------------------------------------------------
        logger.info(f"=== STEP 4: Update Booking with Token (PUT /booking/{booking_id}) ===")
        updated_payload = BookingDataFactory.create_updated_payload(
            initial_payload,
            firstname="Ada_Updated",
            lastname="Lovelace_Updated",
            totalprice=800,
            depositpaid=False,
            additionalneeds="Ocean View Suite & Breakfast",
        )
        update_response = api_client.update_booking(
            booking_id=booking_id,
            payload=updated_payload,
            token=token,
        )

        # Assert status code
        assert update_response.status_code == 200, (
            f"Expected status 200 on PUT /booking/{booking_id}, got {update_response.status_code}. "
            f"Response: {update_response.text}"
        )

        # Validate schema & verify updated response fields
        updated_data = update_response.json()
        BookingResponse.model_validate(updated_data)

        assert updated_data["firstname"] == updated_payload["firstname"], "Updated firstname mismatch"
        assert updated_data["lastname"] == updated_payload["lastname"], "Updated lastname mismatch"
        assert updated_data["totalprice"] == updated_payload["totalprice"], "Updated totalprice mismatch"
        assert updated_data["depositpaid"] == updated_payload["depositpaid"], "Updated depositpaid mismatch"
        assert (
            updated_data["bookingdates"]["checkin"]
            == updated_payload["bookingdates"]["checkin"]
        ), "Updated checkin mismatch"
        assert (
            updated_data["bookingdates"]["checkout"]
            == updated_payload["bookingdates"]["checkout"]
        ), "Updated checkout mismatch"
        assert (
            updated_data["additionalneeds"] == updated_payload["additionalneeds"]
        ), "Updated additionalneeds mismatch"

        # -------------------------------------------------------------
        logger.info(f"=== STEP 5: Delete Booking with Token (DELETE /booking/{booking_id}) ===")
        delete_response = api_client.delete_booking(
            booking_id=booking_id,
            token=token,
        )

        # Assert status code (Restful-Booker specification specifies 201 Created for DELETE)
        assert delete_response.status_code == 201, (
            f"Expected status 201 on DELETE /booking/{booking_id}, got {delete_response.status_code}. "
            f"Response: {delete_response.text}"
        )
        assert delete_response.text == "Created", (
            f"Expected response body 'Created', got '{delete_response.text}'"
        )

        # -------------------------------------------------------------
        logger.info(f"=== STEP 6: Verify Deletion (GET /booking/{booking_id}) ===")
        verify_response = api_client.get_booking(booking_id)
        assert verify_response.status_code == 404, (
            f"Expected status 404 after deletion, got {verify_response.status_code}. "
            f"Response: {verify_response.text}"
        )
        assert verify_response.text == "Not Found", (
            f"Expected response body 'Not Found', got '{verify_response.text}'"
        )
        logger.info("Happy path request chain completed successfully!")
