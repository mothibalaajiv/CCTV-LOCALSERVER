import datetime
import socket
from local_agent.models.data_models import LocalServerInfo
from local_agent.utils.network_utils import get_local_ip, get_mac_address, get_os_info

AGENT_VERSION = "1.0.0"

class LocalServerMetadataService:
    @staticmethod
    def get_server_info() -> LocalServerInfo:
        """Collects local server metadata."""
        return LocalServerInfo(
            mac_address=get_mac_address(),
            hostname=socket.gethostname(),
            ip_address=get_local_ip(),
            os_information=get_os_info(),
            agent_version=AGENT_VERSION,
            timestamp=datetime.datetime.utcnow().isoformat() + "Z"
        )
