"""Pytest fixtures and configuration hooks for Restful-Booker test execution."""
import os
import pytest
from config.settings import settings
from core.booker_client import BookerClient
from mock_server.local_mock import start_mock_server, stop_mock_server
from utils.data_generator import BookingDataFactory
from utils.logger import get_logger

logger = get_logger("Conftest")


def pytest_addoption(parser):
    """Add CLI flags for custom test runs."""
    parser.addoption(
        "--mock",
        action="store_true",
        default=False,
        help="Run tests against local embedded mock server instead of live Heroku API",
    )
    parser.addoption(
        "--base-url",
        action="store",
        default=None,
        help="Override base URL for testing (e.g. Postman mock or alternate environment)",
    )


@pytest.fixture(scope="session", autouse=True)
def mock_server_lifecycle(request):
    """Start local mock server if --mock flag is provided or USE_MOCK is set."""
    use_mock_flag = request.config.getoption("--mock")
    if use_mock_flag or settings.USE_MOCK:
        logger.info("Initializing in-memory Mock Booker Server...")
        server = start_mock_server(host=settings.MOCK_HOST, port=settings.MOCK_PORT)
        yield server
        logger.info("Shutting down in-memory Mock Booker Server...")
        stop_mock_server()
    else:
        yield None


@pytest.fixture(scope="session")
def base_url(request) -> str:
    """Resolve active base URL for test execution."""
    cli_base_url = request.config.getoption("--base-url")
    use_mock_flag = request.config.getoption("--mock")

    if cli_base_url:
        return cli_base_url.rstrip("/")
    if use_mock_flag or settings.USE_MOCK:
        return f"http://{settings.MOCK_HOST}:{settings.MOCK_PORT}"
    return settings.BASE_URL


@pytest.fixture(scope="session")
def api_client(base_url: str) -> BookerClient:
    """Provide BookerClient instance configured with target base URL."""
    logger.info(f"Connecting BookerClient to base URL: {base_url}")
    return BookerClient(base_url=base_url, timeout=settings.DEFAULT_TIMEOUT)


@pytest.fixture(scope="session")
def auth_token(api_client: BookerClient) -> str:
    """Session-scoped fixture to obtain an authentication token."""
    response = api_client.create_token(
        username=settings.AUTH_USERNAME,
        password=settings.AUTH_PASSWORD,
    )
    assert response.status_code == 200, f"Failed to acquire auth token: {response.text}"
    data = response.json()
    assert "token" in data, f"Token key missing from auth response: {data}"
    token = data["token"]
    assert isinstance(token, str) and len(token) > 0, "Token must be a non-empty string"
    logger.info("Session authentication token acquired successfully.")
    return token


@pytest.fixture
def created_booking(api_client: BookerClient, auth_token: str):
    """Fixture that generates a fresh booking and safely cleans it up after test execution."""
    payload = BookingDataFactory.create_booking_payload()
    response = api_client.create_booking(payload)
    assert response.status_code == 200, f"Failed to setup booking: {response.text}"
    body = response.json()
    booking_id = body["bookingid"]

    yield booking_id, payload

    # Teardown: attempt cleanup in case test did not delete it
    try:
        check_resp = api_client.get_booking(booking_id)
        if check_resp.status_code == 200:
            api_client.delete_booking(booking_id, token=auth_token)
            logger.info(f"Teardown: safely deleted test booking ID {booking_id}")
    except Exception as e:
        logger.warning(f"Teardown cleanup exception for booking ID {booking_id}: {e}")
