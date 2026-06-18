import socket
from urllib.parse import urlparse
from local_agent.logging.logger import setup_logger

logger = setup_logger("rtsp_validator")

class RTSPValidator:
    @staticmethod
    def validate_url(rtsp_url: str, timeout: int = 5) -> bool:
        """Validates an RTSP URL by attempting to open a TCP connection to its host/port."""
        if not rtsp_url:
            return False
            
        try:
            parsed = urlparse(rtsp_url)
            host = parsed.hostname
            port = parsed.port or 554
            
            if not host:
                return False

            with socket.create_connection((host, port), timeout=timeout):
                # Simply connecting is a basic test. 
                # For more robust validation, we could send an RTSP OPTIONS request.
                return True
        except Exception as e:
            logger.debug(f"RTSP validation failed for {rtsp_url}: {e}")
            return False
