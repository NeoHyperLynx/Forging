"""
Thin client for driving a local ComfyUI instance's HTTP API.

ComfyUI doesn't expose a fixed "generate video" endpoint -- it runs whatever
workflow graph you give it. Build your Wan 2.2 / Flux workflow in the
ComfyUI UI first, then export it as API-format JSON
(menu: Workflow > Export (API)), and point the workers at that file.
This client fills in prompt/image values by node ID, submits the job, and
retrieves the result.
"""
import json
import time
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

from config import COMFYUI_URL


def submit_workflow(workflow: dict) -> str:
    payload = json.dumps({"prompt": workflow, "client_id": str(uuid.uuid4())}).encode()
    req = urllib.request.Request(
        f"{COMFYUI_URL}/prompt", data=payload, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
    return result["prompt_id"]


def wait_for_result(prompt_id: str, poll_seconds: float = 2.0, timeout: float = 600.0) -> dict:
    waited = 0.0
    while waited < timeout:
        with urllib.request.urlopen(f"{COMFYUI_URL}/history/{prompt_id}") as resp:
            history = json.loads(resp.read())
        if prompt_id in history:
            return history[prompt_id]
        time.sleep(poll_seconds)
        waited += poll_seconds
    raise TimeoutError(f"ComfyUI job {prompt_id} did not finish within {timeout}s")


def fetch_output_file(filename: str, subfolder: str = "", file_type: str = "output") -> bytes:
    query = urllib.parse.urlencode({"filename": filename, "subfolder": subfolder, "type": file_type})
    with urllib.request.urlopen(f"{COMFYUI_URL}/view?{query}") as resp:
        return resp.read()


def upload_image(local_path: str) -> str:
    """Uploads a local image into ComfyUI's input directory so a LoadImage
    node can reference it by filename. Returns the filename ComfyUI stored
    it under."""
    boundary = uuid.uuid4().hex
    path = Path(local_path)
    data = path.read_bytes()
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="image"; filename="{path.name}"\r\n'
        f"Content-Type: application/octet-stream\r\n\r\n"
    ).encode() + data + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        f"{COMFYUI_URL}/upload/image",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
    return result["name"]


def load_workflow_template(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))
