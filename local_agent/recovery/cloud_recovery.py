import paramiko
from local_agent.cloud.api_client import CloudAPIClient
from local_agent.models.data_models import CloudHealthStatus
from local_agent.config.settings import settings
from local_agent.logging.logger import setup_logger

logger = setup_logger("cloud_recovery")

class CloudRecoveryService:
    def __init__(self, api_client: CloudAPIClient):
        self.api_client = api_client

    def attempt_recovery(self, health_status: CloudHealthStatus) -> bool:
        """
        Triggers cloud recovery endpoints based on which services are failing.
        Returns True if any recovery request was successfully sent.
        """
        recovery_triggered = False
        
        if not health_status.api_status:
            logger.warning("API is down. Attempting full system recovery via SSH fallback...")
            return self._ssh_hard_restart()

        if not health_status.metadata_status:
            logger.info("Triggering metadata service recovery...")
            if self._trigger_endpoint("/recovery/metadata"):
                recovery_triggered = True

        if not health_status.stream_receiver_status:
            logger.info("Triggering stream receiver recovery...")
            if self._trigger_endpoint("/recovery/stream_receiver"):
                recovery_triggered = True

        if not health_status.hls_status:
            logger.info("Triggering HLS service recovery...")
            if self._trigger_endpoint("/recovery/hls"):
                recovery_triggered = True

        if not health_status.database_status:
            logger.info("Triggering database recovery...")
            if self._trigger_endpoint("/recovery/database"):
                recovery_triggered = True

        return recovery_triggered

    def _trigger_endpoint(self, endpoint: str) -> bool:
        response = self.api_client.post(endpoint, payload={"action": "restart"})
        if response is not None:
            logger.info(f"Recovery request to {endpoint} successful.")
            return True
        logger.error(f"Recovery request to {endpoint} failed.")
        return False

    def _ssh_hard_restart(self) -> bool:
        """Connects via SSH using credentials from .env to restart cloud services."""
        if not settings.CLOUD_SSH_HOST or not settings.CLOUD_SSH_USER or not settings.CLOUD_SSH_PASSWORD:
            logger.error("SSH credentials not configured. Cannot perform hard recovery.")
            return False
            
        logger.info(f"Connecting to {settings.CLOUD_SSH_HOST} via SSH...")
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                hostname=settings.CLOUD_SSH_HOST,
                username=settings.CLOUD_SSH_USER,
                password=settings.CLOUD_SSH_PASSWORD,
                timeout=10
            )
            
            # Default placeholder command assuming a systemd service or docker-compose
            # Change this to match the actual cloud deployment setup.
            restart_command = "systemctl restart cctv-cloud-services || docker restart $(docker ps -q)"
            
            logger.info(f"Executing hard restart command: {restart_command}")
            stdin, stdout, stderr = ssh.exec_command(restart_command)
            
            exit_status = stdout.channel.recv_exit_status()
            ssh.close()
            
            if exit_status == 0:
                logger.info("SSH hard restart executed successfully.")
                return True
            else:
                error_msg = stderr.read().decode('utf-8').strip()
                logger.error(f"SSH hard restart failed with exit code {exit_status}: {error_msg}")
                return False
                
        except Exception as e:
            logger.error(f"SSH connection failed: {e}")
            return False
