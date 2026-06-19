import socket
import uuid
import platform
import struct
import ipaddress
import psutil
from typing import List

def get_local_ip() -> str:
    """Attempts to find the best local IP by connecting to a public DNS."""
    try:
        # We don't actually connect to the internet, just use UDP to figure out routing
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def get_mac_address() -> str:
    """Returns the MAC address of the local machine formatted with colons."""
    mac = uuid.getnode()
    return ':'.join(['{:02x}'.format((mac >> elements) & 0xff) 
                     for elements in range(40, -1, -8)])

def get_os_info() -> str:
    """Returns basic OS information."""
    return f"{platform.system()} {platform.release()} ({platform.machine()})"

def get_local_subnet() -> str:
    """Dynamically determines the local subnet by scanning Ethernet/LAN interfaces."""
    import logging
    logger = logging.getLogger("network_utils")
    
    try:
        stats = psutil.net_if_stats()
        
        # First priority: Look for active Ethernet interfaces with a valid IPv4
        for iface_name, addrs in psutil.net_if_addrs().items():
            if iface_name in stats and not stats[iface_name].isup:
                continue
                
            name_lower = iface_name.lower()
            # Explicitly ignore Wi-Fi/Wireless interfaces as per user request
            if "wi-fi" in name_lower or "wireless" in name_lower or "wlan" in name_lower or "loopback" in name_lower:
                continue
                
            for addr in addrs:
                if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                    netmask = addr.netmask
                    if netmask:
                        network = ipaddress.IPv4Network(f"{addr.address}/{netmask}", strict=False)
                        return str(network)
    except Exception as e:
        logger.error(f"Error finding Ethernet interface: {e}")
        pass
        
    # Fallback to the default routing IP if no Ethernet interface is found
    local_ip = get_local_ip()
    if local_ip != "127.0.0.1":
        return str(ipaddress.IPv4Network(f"{local_ip}/24", strict=False))
        
    return "192.168.1.0/24"

def get_ips_in_subnet(subnet_cidr: str) -> List[str]:
    """Given a subnet like 192.168.1.0/24, return list of all host IP strings in it."""
    try:
        network = ipaddress.ip_network(subnet_cidr, strict=False)
        return [str(ip) for ip in network.hosts()]
    except Exception:
        return []
