"""
Generates a reference still via a Flux workflow running in ComfyUI.

Requires a Flux API-format workflow exported from your own ComfyUI setup.
Only the positive-prompt node is filled in here -- node IDs depend on your
specific graph, so pass the right one in (see README for how to find it).
"""
from pathlib import Path

from config import OUTPUT_DIR
from workers.comfy_client import fetch_output_file, load_workflow_template, submit_workflow, wait_for_result


def generate_still(prompt: str, workflow_path: str, prompt_node_id: str, out_name: str) -> str:
    workflow = load_workflow_template(workflow_path)
    if prompt_node_id not in workflow:
        raise KeyError(
            f"Node '{prompt_node_id}' not found in {workflow_path}. Open the "
            "workflow in ComfyUI and confirm the node ID of your positive "
            "prompt (CLIPTextEncode) node."
        )
    workflow[prompt_node_id]["inputs"]["text"] = prompt

    prompt_id = submit_workflow(workflow)
    result = wait_for_result(prompt_id)

    image_info = None
    for node_output in result.get("outputs", {}).values():
        if node_output.get("images"):
            image_info = node_output["images"][0]
            break
    if image_info is None:
        raise RuntimeError(f"No image output found for job {prompt_id} -- check your SaveImage node.")

    data = fetch_output_file(image_info["filename"], image_info.get("subfolder", ""), image_info.get("type", "output"))
    out_path = Path(OUTPUT_DIR) / "stills" / out_name
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(data)
    return str(out_path)
