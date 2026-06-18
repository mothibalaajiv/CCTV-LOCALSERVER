from local_agent.cloud.api_client import CloudAPIClient
from local_agent.logging.logger import setup_logger

logger = setup_logger("transmission_verifier")

class TransmissionVerifier:
    def __init__(self, api_client: CloudAPIClient):
        self.api_client = api_client

    def verify_metadata_received(self, camera_mac: str) -> bool:
        """Verifies if the cloud has received metadata for a given camera."""
        response = self.api_client.get(f"/metadata/verify/{camera_mac}")
        return response is not None and response.get("received") is True

    def verify_stream_publishing(self, camera_mac: str) -> bool:
        """Verifies if the cloud is actively receiving and publishing the stream."""
        response = self.api_client.get(f"/streams/status/{camera_mac}")
        return response is not None and response.get("status") == "publishing"

    def verify_hls_available(self, camera_mac: str) -> bool:
        """Verifies if the HLS playlist URL is accessible and active."""
        response = self.api_client.get(f"/hls/status/{camera_mac}")
        return response is not None and response.get("hls_active") is True
