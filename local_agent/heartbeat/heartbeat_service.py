import datetime
from local_agent.cloud.api_client import CloudAPIClient
from local_agent.models.data_models import HeartbeatPayload
from local_agent.logging.logger import setup_logger

logger = setup_logger("heartbeat")

class HeartbeatService:
    def __init__(self, api_client: CloudAPIClient, mac_address: str):
        self.api_client = api_client
        self.mac_address = mac_address

    def send_heartbeat(self, online_cameras_count: int, agent_status: str = "active") -> bool:
        """Sends a periodic heartbeat to the cloud."""
        timestamp = datetime.datetime.utcnow().isoformat() + "Z"
        payload = HeartbeatPayload(
            local_server_mac=self.mac_address,
            online_cameras_count=online_cameras_count,
            agent_status=agent_status,
            timestamp=timestamp
        )
        
        logger.debug("Sending heartbeat...")
        response = self.api_client.post("/heartbeat", payload.model_dump())
        if response is not None:
            logger.debug("Heartbeat successful.")
            return True
            
        logger.warning("Heartbeat failed.")
        return False
