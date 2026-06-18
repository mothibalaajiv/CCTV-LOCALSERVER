# Local Server Agent

The Local Server Agent runs on a laptop at a local site. It discovers IP cameras on the local network, gathers metadata, and communicates with the Cloud Server for the Multi-Site Camera Streaming Platform.

## Features
- **Network Discovery**: Discovers devices on the local subnet.
- **ONVIF Support**: Queries ONVIF devices for metadata and RTSP URIs.
- **RTSP Validation**: Validates RTSP endpoints.
- **Cloud Integration**: Sends metadata payloads and continuous heartbeats to the cloud.
- **Monitoring & Recovery**: Monitors the health of cloud services and triggers recovery endpoints when needed.
- **Change Detection**: Detects newly added or removed cameras.

## Configuration
Copy `.env.example` to `.env` and configure the settings such as `CLOUD_API_URL`, `LOCAL_SUBNET`, and `CLOUD_API_KEY`.

## Requirements
Requires Python 3.9+ and the libraries listed in `requirements.txt`.

## Running
Install dependencies:
```bash
pip install -r requirements.txt
```

Run the agent:
```bash
python main.py
```

The agent will run in the background and logs will be written to the `logs/` directory.
