from local_agent.logging.logger import setup_logger
# we import Any to avoid circular import issues temporarily
from typing import Any

logger = setup_logger("stream_verifier")

class StreamVerifier:
    def __init__(self, api_client: Any):
        self.api_client = api_client

    def verify_cloud_stream_status(self, camera_mac: str) -> bool:
        """Verifies if the cloud recognizes the stream as active."""
        try:
            # Example endpoint: GET /api/streams/verify/{mac}
            response = self.api_client.get(f"/streams/verify/{camera_mac}")
            if response and response.get("status") == "active":
                return True
            return False
        except Exception as e:
            logger.debug(f"Failed to verify cloud stream status for {camera_mac}: {e}")
            return False
