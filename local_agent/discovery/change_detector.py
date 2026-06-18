from typing import Dict, List, Set, Tuple
from local_agent.models.data_models import CameraInfo
from local_agent.logging.logger import setup_logger

logger = setup_logger("change_detector")

class CameraChangeDetector:
    def __init__(self):
        # Maps IP address to CameraInfo for simple tracking
        self.known_cameras: Dict[str, CameraInfo] = {}

    def detect_changes(self, current_cameras: List[CameraInfo]) -> Tuple[List[CameraInfo], List[CameraInfo], List[CameraInfo]]:
        """
        Compares current scan results with known cameras.
        Returns (new_cameras, removed_cameras, changed_cameras)
        """
        # Using IP as primary key since some cameras might not have MAC initially
        current_map = {cam.ip_address: cam for cam in current_cameras}
        
        known_ips = set(self.known_cameras.keys())
        current_ips = set(current_map.keys())
        
        new_ips = current_ips - known_ips
        removed_ips = known_ips - current_ips
        common_ips = known_ips.intersection(current_ips)
        
        new_cameras = [current_map[ip] for ip in new_ips]
        removed_cameras = [self.known_cameras[ip] for ip in removed_ips]
        
        changed_cameras = []
        for ip in common_ips:
            known_cam = self.known_cameras[ip]
            current_cam = current_map[ip]
            
            # Check for changes
            if known_cam.mac_address != current_cam.mac_address or known_cam.rtsp_url != current_cam.rtsp_url:
                changed_cameras.append(current_cam)
                
        # Update known state
        self.known_cameras = current_map
        
        if new_cameras:
            logger.info(f"Detected {len(new_cameras)} new cameras.")
        if removed_cameras:
            logger.info(f"Detected {len(removed_cameras)} removed cameras.")
        if changed_cameras:
            logger.info(f"Detected changes in {len(changed_cameras)} cameras.")
            
        return new_cameras, removed_cameras, changed_cameras
