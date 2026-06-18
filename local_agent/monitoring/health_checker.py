from local_agent.cloud.api_client import CloudAPIClient
from local_agent.models.data_models import CloudHealthStatus
from local_agent.logging.logger import setup_logger

logger = setup_logger("health_checker")

class HealthChecker:
    def __init__(self, api_client: CloudAPIClient):
        self.api_client = api_client

    def check_health(self) -> CloudHealthStatus:
        """Hits the GET /health endpoint to check cloud component status."""
        logger.debug("Checking cloud health...")
        response = self.api_client.get("/health")
        
        # Default to False if the request fails completely
        if response is None:
            logger.warning("Cloud health check failed completely (no response).")
            return CloudHealthStatus(
                api_status=False,
                metadata_status=False,
                stream_receiver_status=False,
                hls_status=False,
                database_status=False
            )
            
        health_status = CloudHealthStatus(
            api_status=response.get("api_status", False),
            metadata_status=response.get("metadata_status", False),
            stream_receiver_status=response.get("stream_receiver_status", False),
            hls_status=response.get("hls_status", False),
            database_status=response.get("database_status", False)
        )
        
        logger.debug(f"Cloud health status: {health_status.model_dump()}")
        return health_status
