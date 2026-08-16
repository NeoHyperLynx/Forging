"""
Generates a video clip via a Wan 2.2 image-to-video workflow in ComfyUI.

Requires a Wan 2.2 API-format workflow exported from your own ComfyUI setup,
with a LoadImage node (for the reference still) and a CLIPTextEncode node
(for the motion prompt). Node IDs vary by graph -- pass yours in.
"""
from pathlib import Path

from config import OUTPUT_DIR
from workers.comfy_client import fetch_output_file, load_workflow_template, submit_workflow, upload_image, wait_for_result


def generate_video(
    prompt: str,
    reference_image_path: str,
    workflow_path: str,
    prompt_node_id: str,
    image_node_id: str,
    out_name: str,
) -> str:
    workflow = load_workflow_template(workflow_path)
    for node_id in (prompt_node_id, image_node_id):
        if node_id not in workflow:
            raise KeyError(f"Node '{node_id}' not found in {workflow_path}.")

    uploaded_name = upload_image(reference_image_path)
    workflow[prompt_node_id]["inputs"]["text"] = prompt
    workflow[image_node_id]["inputs"]["image"] = uploaded_name

    prompt_id = submit_workflow(workflow)
    # Video jobs run much longer than stills -- give them real headroom,
    # especially on a rented/shared GPU where you're queued.
    result = wait_for_result(prompt_id, timeout=1200.0)

    video_info = None
    for node_output in result.get("outputs", {}).values():
        for key in ("gifs", "videos"):  # depends on which video-combine node you use
            if node_output.get(key):
                video_info = node_output[key][0]
                break
        if video_info:
            break
    if video_info is None:
        raise RuntimeError(f"No video output found for job {prompt_id} -- check your video-combine node.")

    data = fetch_output_file(video_info["filename"], video_info.get("subfolder", ""), video_info.get("type", "output"))
    out_path = Path(OUTPUT_DIR) / "clips" / out_name
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(data)
    return str(out_path)
