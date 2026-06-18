from local_agent.cloud.api_client import CloudAPIClient
from local_agent.models.data_models import CloudMetadataPayload
from local_agent.logging.logger import setup_logger

logger = setup_logger("cloud_communication")

class CloudCommunicationService:
    def __init__(self, api_client: CloudAPIClient):
        self.api_client = api_client

    def send_metadata(self, payload: CloudMetadataPayload) -> bool:
        """Transmits metadata payload to cloud API."""
        logger.info("Transmitting metadata to cloud...")
        response = self.api_client.post("/metadata/sync", payload.model_dump())
        if response is not None:
            logger.info("Metadata successfully transmitted to cloud.")
            return True
        logger.warning("Failed to transmit metadata to cloud.")
        return False
        
    def notify_camera_change(self, change_type: str, camera_info: dict) -> bool:
        """Notifies the cloud of camera additions/removals/changes."""
        payload = {
            "change_type": change_type,
            "camera": camera_info
        }
        logger.info(f"Notifying cloud of camera change: {change_type}")
        response = self.api_client.post("/metadata/change", payload)
        return response is not None
