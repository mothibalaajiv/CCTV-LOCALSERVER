import paramiko
import os
import tarfile
import time
import logging

# Enable paramiko logging to debug connection issues
logging.getLogger("paramiko").setLevel(logging.DEBUG)
paramiko.util.log_to_file("paramiko.log")

# You can load this from .env in a production scenario
CLOUD_SSH_HOST = "104.251.214.177"
CLOUD_SSH_USER = "root"
CLOUD_SSH_PASSWORD = "Adacurvetechnologies*41"
REMOTE_DIR = "/opt/cctv-cloud"

def create_tarball(source_dir, output_filename):
    """Compress the cloud_server directory into a tarball."""
    print(f"Compressing {source_dir} into {output_filename}...")
    with tarfile.open(output_filename, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))

def deploy():
    print(f"Connecting to {CLOUD_SSH_HOST} as {CLOUD_SSH_USER} (this may take up to 60 seconds)...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Increased timeout to 60 seconds to handle slow server responses (e.g., DNS reverse lookup delays)
        ssh.connect(CLOUD_SSH_HOST, username=CLOUD_SSH_USER, password=CLOUD_SSH_PASSWORD, timeout=60, banner_timeout=60)
    except Exception as e:
        print(f"Failed to connect to {CLOUD_SSH_HOST}: {e}")
        return

    print("Checking if Docker is installed...")
    stdin, stdout, stderr = ssh.exec_command("docker --version")
    if stdout.channel.recv_exit_status() != 0:
        print("Installing Docker (this may take a minute)...")
        stdin, stdout, stderr = ssh.exec_command("curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh")
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            print(f"Docker installation failed: {stderr.read().decode()}")

    print("Checking if Docker Compose is installed...")
    stdin, stdout, stderr = ssh.exec_command("docker-compose --version")
    if stdout.channel.recv_exit_status() != 0:
        print("Installing Docker Compose...")
        ssh.exec_command('curl -L "https://github.com/docker/compose/releases/download/v2.24.5/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose && chmod +x /usr/local/bin/docker-compose')

    print(f"Creating remote directory {REMOTE_DIR}...")
    ssh.exec_command(f"mkdir -p {REMOTE_DIR}")

    tarball = "cloud_server.tar.gz"
    create_tarball("cloud_server", tarball)

    print("Uploading code to server...")
    sftp = ssh.open_sftp()
    sftp.put(tarball, f"{REMOTE_DIR}/{tarball}")
    sftp.close()

    print("Extracting code and starting services (this will build the API image)...")
    commands = [
        f"cd {REMOTE_DIR}",
        f"tar -xzf {tarball}",
        "cd cloud_server",
        "mkdir -p data", # Ensure data dir exists for sqlite
        "docker-compose down",
        "docker-compose up -d --build"
    ]
    stdin, stdout, stderr = ssh.exec_command(" && ".join(commands))
    
    # Stream the output
    for line in iter(stdout.readline, ""):
        print(line, end="")
    for line in iter(stderr.readline, ""):
        print(line, end="")

    print("\nDeployment completed successfully!")
    print(f"You can now check the API health at: http://{CLOUD_SSH_HOST}:8000/api/health")
    ssh.close()
    
    if os.path.exists(tarball):
        os.remove(tarball)

if __name__ == "__main__":
    deploy()
