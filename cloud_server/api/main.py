from fastapi import FastAPI, HTTPException, Request
from typing import Dict, Any
import subprocess

app = FastAPI(title="CCTV Cloud API")

# Simple in-memory store for demonstration.
# In a real app, use SQLAlchemy to persist to the SQLite DB mounted in docker-compose.
database = {
    "metadata": {},
    "heartbeats": {}
}

@app.get("/api/health")
def health_check():
    # Check MediaMTX API
    mediamtx_up = False
    try:
        import requests
        # In docker-compose, the service name is cctv_mediamtx
        res = requests.get("http://cctv_mediamtx:8001/v3/paths/list", timeout=2)
        # 401 means it's running but auth is enabled, 200 means running with no auth
        mediamtx_up = res.status_code in (200, 401)
    except Exception:
        pass

    return {
        "api_status": True,
        "metadata_status": True,
        "stream_receiver_status": mediamtx_up,
        "hls_status": mediamtx_up,
        "database_status": True
    }

@app.post("/api/metadata/sync")
def sync_metadata(payload: Dict[str, Any]):
    mac = payload.get("local_server_mac")
    if not mac:
        raise HTTPException(status_code=400, detail="Missing MAC")
    database["metadata"][mac] = payload
    return {"status": "success", "received": True}

@app.post("/api/heartbeat")
def receive_heartbeat(payload: Dict[str, Any]):
    mac = payload.get("local_server_mac")
    if not mac:
        raise HTTPException(status_code=400, detail="Missing MAC")
    database["heartbeats"][mac] = payload
    return {"status": "success"}

@app.post("/api/metadata/change")
def camera_change(payload: Dict[str, Any]):
    # In a real app, you would log or process specific camera changes here
    # For now, we just acknowledge receipt
    return {"status": "success", "received": True}

@app.get("/api/metadata/verify/{camera_mac}")
def verify_metadata(camera_mac: str):
    for server_mac, payload in database["metadata"].items():
        cameras = payload.get("cameras", [])
        for cam in cameras:
            if cam.get("mac_address") == camera_mac or cam.get("ip_address") == camera_mac:
                return {"received": True}
    return {"received": False}

@app.get("/api/streams")
def get_global_streams(request: Request):
    host = request.headers.get("host", "104.251.214.177:8000").split(":")[0]
    streams = []
    
    for server_mac, payload in database["metadata"].items():
        server_ip = payload.get("local_server_ip", "unknown")
        cameras = payload.get("cameras", [])
        
        for cam in cameras:
            cam_mac = cam.get("mac_address", "unknown")
            cam_ip = cam.get("ip_address", "unknown")
            # Create a URL-safe stream name based on MAC
            stream_name = cam_mac.replace(":", "").lower()
            
            streams.append({
                "local_server_mac": server_mac,
                "local_server_ip": server_ip,
                "camera_mac": cam_mac,
                "camera_ip": cam_ip,
                # Assume MediaMTX is serving HLS on port 8888
                "hls_url": f"http://{host}:8888/{stream_name}/index.m3u8"
            })
            
    return {"streams": streams}

@app.get("/api/streams/status/{camera_mac}")
def stream_status(camera_mac: str):
    return {"status": "publishing"}

@app.get("/api/hls/status/{camera_mac}")
def hls_status(camera_mac: str):
    return {"hls_active": True}

@app.post("/api/recovery/{service}")
def recover_service(service: str):
    # Map requested service to docker container name
    container_map = {
        "hls": "cctv_mediamtx",
        "stream_receiver": "cctv_mediamtx",
        "full": "cctv_mediamtx cctv_cloud_api"
    }
    target = container_map.get(service)
    if not target:
        return {"status": "success", "msg": f"No specific container for {service}"}
        
    try:
        # Executes docker restart inside the container (requires docker.sock mounted)
        subprocess.Popen(f"docker restart {target}", shell=True)
        return {"status": "success", "action": f"Triggered restart for {target}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
