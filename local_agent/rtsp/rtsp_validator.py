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

            with socket.create_connection((host, port), timeout=timeout) as s:
                # Send an RTSP OPTIONS request to ensure it's actually an RTSP server
                # and not just a random service (like a router ALG or Windows Media Service) on port 554
                request = f"OPTIONS {rtsp_url} RTSP/1.0\r\nCSeq: 1\r\nUser-Agent: CCTV-Agent\r\n\r\n"
                s.sendall(request.encode('utf-8'))
                
                # We only read the first chunk to check the protocol signature
                response = s.recv(1024).decode('utf-8', errors='ignore')
                
                # A valid RTSP server will respond with RTSP/1.0
                if response.startswith("RTSP/1."):
                    return True
                return False
        except Exception as e:
            logger.debug(f"RTSP validation failed for {rtsp_url}: {e}")
            return False
