from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class CameraInfo(BaseModel):
    ip_address: str
    mac_address: str
    vendor: Optional[str] = None
    model: Optional[str] = None
    hostname: Optional[str] = None
    onvif_info: Optional[Dict[str, Any]] = None
    rtsp_url: Optional[str] = None
    validation_status: bool = False
    discovery_timestamp: str

class LocalServerInfo(BaseModel):
    mac_address: str
    hostname: str
    ip_address: str
    os_information: str
    agent_version: str
    timestamp: str

class CloudMetadataPayload(BaseModel):
    local_server_mac: str
    local_server_info: LocalServerInfo
    cameras: List[CameraInfo]
    timestamp: str

class HeartbeatPayload(BaseModel):
    local_server_mac: str
    online_cameras_count: int
    agent_status: str
    timestamp: str

class CloudHealthStatus(BaseModel):
    api_status: bool
    metadata_status: bool
    stream_receiver_status: bool
    hls_status: bool
    database_status: bool
