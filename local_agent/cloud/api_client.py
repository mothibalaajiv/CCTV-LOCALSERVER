import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from local_agent.config.settings import settings
from local_agent.logging.logger import setup_logger
from typing import Dict, Any, Optional

logger = setup_logger("api_client")

class CloudAPIClient:
    def __init__(self):
        self.base_url = settings.CLOUD_API_URL.rstrip('/')
        self.api_key = settings.CLOUD_API_KEY
        self.timeout = settings.TIMEOUT_SECONDS
        
        # Configure retries
        retry_strategy = Retry(
            total=settings.RETRY_COUNT,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session = requests.Session()
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def post(self, endpoint: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = self.session.post(
                url, 
                json=payload, 
                headers=self._get_headers(), 
                timeout=self.timeout
            )
            response.raise_for_status()
            if response.text:
                return response.json()
            return {}
        except requests.exceptions.RequestException as e:
            logger.error(f"POST {url} failed: {e}")
            return None

    def get(self, endpoint: str) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = self.session.get(
                url, 
                headers=self._get_headers(), 
                timeout=self.timeout
            )
            response.raise_for_status()
            if response.text:
                return response.json()
            return {}
        except requests.exceptions.RequestException as e:
            logger.debug(f"GET {url} failed: {e}")
            return None
