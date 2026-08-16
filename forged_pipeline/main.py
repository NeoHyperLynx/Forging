"""
CLI entry point: script -> director agent -> generate each shot -> assemble.

Usage:
    python main.py --script scene2.txt \
        --workflow-flux flux_api.json --flux-prompt-node 6 \
        --workflow-wan wan_i2v_api.json --wan-prompt-node 6 --wan-image-node 10 \
        --out output/scene2_rough_cut.mp4

Node IDs come from your exported ComfyUI workflow JSON -- open it in a text
editor (or the ComfyUI UI) and find the CLIPTextEncode / LoadImage node
numbers for your specific graph.
"""
import argparse
import json
from pathlib import Path

from assemble import assemble_rough_cut
from config import OUTPUT_DIR
from director_agent import break_down_script
from workers import flux_stills, wan_video, voice_tts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--script", required=True)
    parser.add_argument("--workflow-flux", required=True, help="ComfyUI API-format Flux workflow JSON")
    parser.add_argument("--flux-prompt-node", default="6")
    parser.add_argument("--workflow-wan", required=True, help="ComfyUI API-format Wan i2v workflow JSON")
    parser.add_argument("--wan-prompt-node", default="6")
    parser.add_argument("--wan-image-node", default="10")
    parser.add_argument("--out", default=str(Path(OUTPUT_DIR) / "rough_cut.mp4"))
    args = parser.parse_args()

    script_text = Path(args.script).read_text(encoding="utf-8")

    print("Running director agent...")
    shot_list = break_down_script(script_text)
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    Path(OUTPUT_DIR, "shot_list.json").write_text(
        json.dumps(shot_list.to_json(), indent=2), encoding="utf-8"
    )
    print(f"  {len(shot_list.shots)} shots -> {OUTPUT_DIR}/shot_list.json")
    if shot_list.open_questions:
        print("  Open questions flagged by the director agent:")
        for q in shot_list.open_questions:
            print(f"    - {q}")

    clip_files, voice_files, reference_images = {}, {}, {}

    for shot in shot_list.shots:
        print(f"Shot {shot.id} ({shot.tool}): {shot.scene}")

        if shot.tool == "flux_still":
            path = flux_stills.generate_still(
                shot.prompt, args.workflow_flux, args.flux_prompt_node, f"{shot.id}.png"
            )
            reference_images[shot.id] = path

        elif shot.tool == "wan_video":
            ref = reference_images.get(shot.reference_image) or shot.reference_image
            if not ref or not Path(ref).exists():
                print(f"  skipped: no resolved reference image for '{shot.reference_image}'")
                continue
            path = wan_video.generate_video(
                shot.prompt, ref, args.workflow_wan, args.wan_prompt_node, args.wan_image_node, f"{shot.id}.mp4"
            )
            clip_files[shot.id] = path

        if shot.dialogue and shot.speaker:
            try:
                voice_files[shot.id] = voice_tts.generate_line(shot.dialogue, shot.speaker, f"{shot.id}.wav")
            except FileNotFoundError as e:
                print(f"  voice skipped: {e}")

    out = assemble_rough_cut(shot_list, clip_files, voice_files, args.out)
    print(f"Rough cut assembled: {out}")


if __name__ == "__main__":
    main()
