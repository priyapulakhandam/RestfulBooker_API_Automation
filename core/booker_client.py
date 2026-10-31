"""High-level client for Restful-Booker API operations."""
from typing import Any, Dict, Optional, Union
import requests
from core.api_client import APIClient


class BookerClient:
    """Specialized client for Restful-Booker endpoints."""

    def __init__(self, base_url: str, timeout: int = 15):
        self.client = APIClient(base_url=base_url, timeout=timeout)

    def ping(self) -> requests.Response:
        """Health check endpoint: GET /ping."""
        return self.client.get("/ping")

    def create_token(
        self,
        username: str = "admin",
        password: str = "password123",
    ) -> requests.Response:
        """Obtain an authentication token: POST /auth."""
        payload = {"username": username, "password": password}
        return self.client.post("/auth", json=payload)

    def create_booking(self, payload: Dict[str, Any]) -> requests.Response:
        """Create a new booking: POST /booking."""
        return self.client.post("/booking", json=payload)

    def get_booking(
        self,
        booking_id: Union[int, str],
        headers: Optional[Dict[str, str]] = None,
    ) -> requests.Response:
        """Retrieve booking by ID: GET /booking/{id}."""
        return self.client.get(f"/booking/{booking_id}", headers=headers)

    def get_bookings(self, params: Optional[Dict[str, Any]] = None) -> requests.Response:
        """Get list of booking IDs: GET /booking."""
        return self.client.get("/booking", params=params)

    def update_booking(
        self,
        booking_id: Union[int, str],
        payload: Dict[str, Any],
        token: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
    ) -> requests.Response:
        """Update a booking completely: PUT /booking/{id}."""
        req_headers = dict(headers or {})
        req_cookies = dict(cookies or {})

        if token:
            req_cookies["token"] = token
            # Also support Cookie header directly for standard server compatibility
            req_headers["Cookie"] = f"token={token}"

        return self.client.put(
            f"/booking/{booking_id}",
            json=payload,
            headers=req_headers,
            cookies=req_cookies,
        )

    def partial_update_booking(
        self,
        booking_id: Union[int, str],
        payload: Dict[str, Any],
        token: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
    ) -> requests.Response:
        """Partially update a booking: PATCH /booking/{id}."""
        req_headers = dict(headers or {})
        req_cookies = dict(cookies or {})

        if token:
            req_cookies["token"] = token
            req_headers["Cookie"] = f"token={token}"

        return self.client.patch(
            f"/booking/{booking_id}",
            json=payload,
            headers=req_headers,
            cookies=req_cookies,
        )

    def delete_booking(
        self,
        booking_id: Union[int, str],
        token: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
    ) -> requests.Response:
        """Delete a booking: DELETE /booking/{id}."""
        req_headers = dict(headers or {})
        req_cookies = dict(cookies or {})

        if token:
            req_cookies["token"] = token
            req_headers["Cookie"] = f"token={token}"

        return self.client.delete(
            f"/booking/{booking_id}",
            headers=req_headers,
            cookies=req_cookies,
        )
