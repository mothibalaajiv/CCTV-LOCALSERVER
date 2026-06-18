import subprocess
import platform
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional
from local_agent.utils.network_utils import get_ips_in_subnet, get_local_subnet
from local_agent.logging.logger import setup_logger

logger = setup_logger("network_scanner")

def ping_ip(ip: str) -> bool:
    """Pings an IP address and returns True if it responds."""
    system = platform.system().lower()
    if system == "windows":
        command = ["ping", "-n", "1", "-w", "500", ip]
    else:
        command = ["ping", "-c", "1", "-W", "1", ip]
    
    try:
        # Hide output
        result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return result.returncode == 0
    except Exception as e:
        logger.debug(f"Error pinging {ip}: {e}")
        return False

class NetworkScanner:
    def __init__(self, subnet: Optional[str] = None):
        self.subnet = subnet
        self.active_ips: List[str] = []

    def scan(self) -> List[str]:
        """Scans the subnet and returns a list of active IPs."""
        target_subnet = self.subnet
        if not target_subnet or target_subnet.lower() == "auto":
            target_subnet = get_local_subnet()
            logger.debug(f"Dynamically resolved subnet: {target_subnet}")
            
        if not target_subnet:
            logger.warning("No subnet configured and failed to dynamically resolve. Skipping ping sweep.")
            return []
            
        logger.info(f"Starting network scan on subnet: {target_subnet}")
        ips_to_scan = get_ips_in_subnet(target_subnet)
        
        active_ips = []
        with ThreadPoolExecutor(max_workers=50) as executor:
            results = executor.map(lambda ip: (ip, ping_ip(ip)), ips_to_scan)
            for ip, is_active in results:
                if is_active:
                    active_ips.append(ip)
                    
        self.active_ips = active_ips
        logger.info(f"Network scan completed. Found {len(active_ips)} active devices.")
        return active_ips
