"""Base HTTP client wrapping requests with logging and timeout handling."""
from typing import Any, Dict, Optional
import requests
from utils.logger import get_logger

logger = get_logger("APIClient")


class APIClient:
    """Wrapper around requests.Session providing standardized logging and configuration."""

    def __init__(self, base_url: str, timeout: int = 15):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.default_headers: Dict[str, str] = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def request(
        self,
        method: str,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Any] = None,
        data: Optional[Any] = None,
        cookies: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
    ) -> requests.Response:
        """Execute HTTP request with full observability."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        merged_headers = dict(self.default_headers)
        if headers:
            merged_headers.update(headers)

        req_timeout = timeout or self.timeout

        logger.info(f"--> {method.upper()} {url}")
        if json:
            logger.debug(f"Request Body: {json}")

        response = self.session.request(
            method=method.upper(),
            url=url,
            headers=merged_headers,
            params=params,
            json=json,
            data=data,
            cookies=cookies,
            timeout=req_timeout,
        )

        logger.info(f"<-- {response.status_code} {response.reason} for {method.upper()} {url} ({response.elapsed.total_seconds():.2f}s)")
        return response

    def get(self, endpoint: str, **kwargs) -> requests.Response:
        return self.request("GET", endpoint, **kwargs)

    def post(self, endpoint: str, **kwargs) -> requests.Response:
        return self.request("POST", endpoint, **kwargs)

    def put(self, endpoint: str, **kwargs) -> requests.Response:
        return self.request("PUT", endpoint, **kwargs)

    def patch(self, endpoint: str, **kwargs) -> requests.Response:
        return self.request("PATCH", endpoint, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        return self.request("DELETE", endpoint, **kwargs)
