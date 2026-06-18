from typing import List, Dict, Any, Optional
from onvif import ONVIFCamera
# Note: wsdl files might be needed locally depending on the onvif-zeep version
from local_agent.logging.logger import setup_logger
import socket

logger = setup_logger("onvif_discovery")

class ONVIFDiscoveryService:
    def __init__(self):
        pass

    def get_camera_info(self, ip: str, port: int = 80, user: str = "", password: str = "") -> Optional[Dict[str, Any]]:
        """Connects to a specific IP to get ONVIF details."""
        try:
            # We assume no auth or default auth if not provided
            # A timeout should be set, but onvif-zeep relies on zeep transport
            mycam = ONVIFCamera(ip, port, user, password, no_cache=True)
            device_info = mycam.devicemgmt.GetDeviceInformation()
            return {
                "vendor": getattr(device_info, 'Manufacturer', 'Unknown'),
                "model": getattr(device_info, 'Model', 'Unknown'),
                "firmware": getattr(device_info, 'FirmwareVersion', 'Unknown'),
                "serial_number": getattr(device_info, 'SerialNumber', 'Unknown'),
                "hardware_id": getattr(device_info, 'HardwareId', 'Unknown')
            }
        except Exception as e:
            logger.debug(f"Could not get ONVIF info from {ip}:{port}: {e}")
            return None
            
    def get_rtsp_uri(self, ip: str, port: int = 80, user: str = "", password: str = "") -> Optional[str]:
        """Attempts to retrieve the RTSP URI from the ONVIF media service."""
        try:
            mycam = ONVIFCamera(ip, port, user, password, no_cache=True)
            media_service = mycam.create_media_service()
            profiles = media_service.GetProfiles()
            if not profiles:
                return None
                
            # Get the first profile's stream URI
            profile_token = profiles[0].token
            obj = media_service.create_type('GetStreamUri')
            obj.ProfileToken = profile_token
            obj.StreamSetup = {'Stream': 'RTP-Unicast', 'Transport': {'Protocol': 'RTSP'}}
            res = media_service.GetStreamUri(obj)
            return res.Uri
        except Exception as e:
            logger.debug(f"Could not get RTSP URI via ONVIF from {ip}:{port}: {e}")
            return None
