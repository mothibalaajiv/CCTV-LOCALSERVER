import subprocess
import threading
from typing import Dict, List
from local_agent.models.data_models import CameraInfo
from local_agent.config.settings import settings
from local_agent.logging.logger import setup_logger

logger = setup_logger("stream_pusher")

class StreamPusherService:
    def __init__(self):
        self.active_processes: Dict[str, subprocess.Popen] = {}
        self.lock = threading.Lock()
        
    def start_pushing(self, cameras: List[CameraInfo]):
        """Starts an FFmpeg process to push the RTSP stream for each new camera."""
        if not settings.CLOUD_SSH_HOST:
            logger.error("CLOUD_SSH_HOST not set, cannot push streams.")
            return

        with self.lock:
            for cam in cameras:
                if not cam.rtsp_url:
                    logger.warning(f"No RTSP URL for camera {cam.mac_address}, skipping stream push.")
                    continue
                    
                mac_clean = cam.mac_address.replace(":", "").lower()
                if mac_clean in self.active_processes:
                    continue # Already pushing

                stream_id = mac_clean
                cloud_url = f"rtsp://{settings.CLOUD_SSH_HOST}:8554/{stream_id}"
                
                # Use TCP transport for reliability over WAN, copy codec to save CPU
                cmd = [
                    "ffmpeg",
                    "-hide_banner", "-loglevel", "error",
                    "-rtsp_transport", "tcp",
                    "-i", cam.rtsp_url,
                    "-c", "copy",
                    "-f", "rtsp",
                    "-rtsp_transport", "tcp",
                    cloud_url
                ]
                
                logger.info(f"Starting stream push for {cam.mac_address} to {cloud_url}")
                try:
                    # Open a log file for this specific stream to capture ffmpeg errors
                    log_file = open(f"ffmpeg_{mac_clean}.log", "w")
                    process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=log_file)
                    self.active_processes[mac_clean] = process
                except FileNotFoundError:
                    logger.error("FFmpeg not found! Please ensure FFmpeg is installed and added to your system PATH.")
                    break # Stop trying if ffmpeg is totally missing
                except Exception as e:
                    logger.error(f"Failed to start FFmpeg for {cam.mac_address}: {e}")

    def stop_pushing(self, cameras: List[CameraInfo]):
        """Stops the FFmpeg process for removed cameras."""
        with self.lock:
            for cam in cameras:
                mac_clean = cam.mac_address.replace(":", "").lower()
                process = self.active_processes.pop(mac_clean, None)
                if process:
                    logger.info(f"Stopping stream push for {cam.mac_address}")
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()

    def check_health(self) -> List[str]:
        """Checks if any FFmpeg processes crashed and returns their MACs."""
        dead_streams = []
        with self.lock:
            for mac, process in self.active_processes.items():
                if process.poll() is not None:
                    logger.warning(f"FFmpeg process for stream {mac} died unexpectedly.")
                    dead_streams.append(mac)
            
            for mac in dead_streams:
                del self.active_processes[mac]
        return dead_streams
