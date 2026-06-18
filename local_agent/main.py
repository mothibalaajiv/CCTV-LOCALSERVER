import time
import threading
import datetime
from typing import List
import sys
import os

# Ensure the parent directory is in the Python path so 'local_agent' can be resolved
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from local_agent.config.settings import settings
from local_agent.logging.logger import setup_logger

from local_agent.discovery.network_scanner import NetworkScanner
from local_agent.discovery.change_detector import CameraChangeDetector
from local_agent.metadata.local_server_info import LocalServerMetadataService
from local_agent.metadata.camera_metadata import CameraMetadataAggregator
from local_agent.rtsp.rtsp_validator import RTSPValidator
from local_agent.rtsp.stream_verifier import StreamVerifier
from local_agent.rtsp.stream_pusher import StreamPusherService

from local_agent.cloud.api_client import CloudAPIClient
from local_agent.cloud.communication import CloudCommunicationService

from local_agent.heartbeat.heartbeat_service import HeartbeatService
from local_agent.monitoring.health_checker import HealthChecker
from local_agent.monitoring.transmission_verifier import TransmissionVerifier
from local_agent.recovery.cloud_recovery import CloudRecoveryService
from local_agent.models.data_models import CloudMetadataPayload

logger = setup_logger("main")

class LocalServerAgent:
    def __init__(self):
        self.api_client = CloudAPIClient()
        self.cloud_service = CloudCommunicationService(self.api_client)
        
        # Local state
        self.local_server_info = LocalServerMetadataService.get_server_info()
        self.network_scanner = NetworkScanner(settings.LOCAL_SUBNET)
        self.change_detector = CameraChangeDetector()
        self.camera_aggregator = CameraMetadataAggregator()
        self.rtsp_validator = RTSPValidator()
        self.stream_verifier = StreamVerifier(self.api_client)
        self.stream_pusher = StreamPusherService()
        
        self.heartbeat_service = HeartbeatService(self.api_client, self.local_server_info.mac_address)
        self.health_checker = HealthChecker(self.api_client)
        self.transmission_verifier = TransmissionVerifier(self.api_client)
        self.recovery_service = CloudRecoveryService(self.api_client)
        
        # Thread control
        self.running = False
        self.current_cameras = []
        
    def start(self):
        """Starts background threads for the agent."""
        logger.info("Starting Local Server Agent...")
        self.running = True
        
        # Start Discovery thread
        discovery_thread = threading.Thread(target=self._discovery_loop, daemon=True)
        discovery_thread.start()
        
        # Start Heartbeat thread
        heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        heartbeat_thread.start()
        
        # Start Health Monitor thread
        health_thread = threading.Thread(target=self._health_loop, daemon=True)
        health_thread.start()

        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Stopping Local Server Agent...")
            self.running = False
            
    def _discovery_loop(self):
        while self.running:
            try:
                # 1. Discover IPs
                active_ips = self.network_scanner.scan()
                
                # 2. Collect Metadata
                new_camera_list = []
                import socket
                for ip in active_ips:
                    cam_info = self.camera_aggregator.create_camera_info(ip)
                    
                    # Check if it's actually a camera (has ONVIF, RTSP URL, or port 554 open)
                    is_camera = False
                    if cam_info.onvif_info or cam_info.rtsp_url:
                        is_camera = True
                    else:
                        try:
                            with socket.create_connection((ip, 554), timeout=1):
                                is_camera = True
                        except Exception:
                            pass
                            
                    if is_camera:
                        if cam_info.rtsp_url:
                            cam_info.validation_status = self.rtsp_validator.validate_url(cam_info.rtsp_url)
                        new_camera_list.append(cam_info)
                    
                # 3. Detect Changes
                new_cams, removed_cams, changed_cams = self.change_detector.detect_changes(new_camera_list)
                
                # Update local state
                self.current_cameras = new_camera_list
                
                # 4. Transmit changes or full state
                if new_cams or removed_cams or changed_cams:
                    # Send full payload sync
                    payload = CloudMetadataPayload(
                        local_server_mac=self.local_server_info.mac_address,
                        local_server_info=self.local_server_info,
                        cameras=self.current_cameras,
                        timestamp=datetime.datetime.utcnow().isoformat() + "Z"
                    )
                    self.cloud_service.send_metadata(payload)
                    
                    # Manage stream pushing
                    if new_cams:
                        self.stream_pusher.start_pushing(new_cams)
                    if removed_cams:
                        self.stream_pusher.stop_pushing(removed_cams)
                        
                # Check health of ffmpeg processes
                self.stream_pusher.check_health()
                    
                if new_cams or removed_cams or changed_cams:
                    for cam in new_cams:
                        self.cloud_service.notify_camera_change("added", cam.model_dump())
                    for cam in removed_cams:
                        self.cloud_service.notify_camera_change("removed", cam.model_dump())
                    for cam in changed_cams:
                        self.cloud_service.notify_camera_change("changed", cam.model_dump())
                        
            except Exception as e:
                logger.error(f"Error in discovery loop: {e}")
                
            time.sleep(settings.DISCOVERY_INTERVAL)

    def _heartbeat_loop(self):
        while self.running:
            try:
                self.heartbeat_service.send_heartbeat(len(self.current_cameras))
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
            time.sleep(settings.HEARTBEAT_INTERVAL)

    def _health_loop(self):
        while self.running:
            try:
                # Check Cloud Health
                health_status = self.health_checker.check_health()
                
                # Trigger Recovery if anything is down
                if not all([
                    health_status.api_status, 
                    health_status.metadata_status, 
                    health_status.stream_receiver_status, 
                    health_status.hls_status, 
                    health_status.database_status
                ]):
                    logger.warning("Cloud services degraded. Attempting recovery.")
                    self.recovery_service.attempt_recovery(health_status)
                    
                # Verify streams are being received
                for cam in self.current_cameras:
                    if cam.mac_address:
                        # Periodically verify
                        self.transmission_verifier.verify_metadata_received(cam.mac_address)
                        self.transmission_verifier.verify_stream_publishing(cam.mac_address)
                        
            except Exception as e:
                logger.error(f"Error in health loop: {e}")
                
            time.sleep(settings.HEALTH_CHECK_INTERVAL)

if __name__ == "__main__":
    agent = LocalServerAgent()
    agent.start()
