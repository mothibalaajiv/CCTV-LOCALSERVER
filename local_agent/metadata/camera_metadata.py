import datetime
import subprocess
import re
import platform
from typing import Dict, Any, Optional
from local_agent.models.data_models import CameraInfo
from local_agent.discovery.onvif_discovery import ONVIFDiscoveryService
from local_agent.logging.logger import setup_logger

logger = setup_logger("camera_metadata")

def get_mac_from_arp(ip: str) -> str:
    """Attempts to resolve MAC address for a given IP using ARP table."""
    try:
        system = platform.system().lower()
        if system == "windows":
            res = subprocess.run(["arp", "-a", ip], capture_output=True, text=True)
            match = re.search(r"([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})", res.stdout)
            if match:
                return match.group(0).replace('-', ':').lower()
        else:
            res = subprocess.run(["arp", "-n", ip], capture_output=True, text=True)
            match = re.search(r"([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})", res.stdout)
            if match:
                return match.group(0).lower()
    except Exception as e:
        logger.debug(f"Failed to get MAC for {ip}: {e}")
    return ""

class CameraMetadataAggregator:
    def __init__(self):
        self.onvif_service = ONVIFDiscoveryService()

    def create_camera_info(self, ip: str, known_mac: str = "") -> CameraInfo:
        """Aggregates all metadata for a specific camera IP."""
        timestamp = datetime.datetime.utcnow().isoformat() + "Z"
        
        mac = known_mac if known_mac else get_mac_from_arp(ip)
        
        # We try to get ONVIF info
        onvif_info = self.onvif_service.get_camera_info(ip)
        rtsp_url = self.onvif_service.get_rtsp_uri(ip)
        
        vendor = onvif_info.get("vendor") if onvif_info else None
        model = onvif_info.get("model") if onvif_info else None
        
        return CameraInfo(
            ip_address=ip,
            mac_address=mac,
            vendor=vendor,
            model=model,
            hostname=None, 
            onvif_info=onvif_info,
            rtsp_url=rtsp_url,
            validation_status=False,
            discovery_timestamp=timestamp
        )
