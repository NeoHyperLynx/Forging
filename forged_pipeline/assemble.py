"""
Stitches generated clips (+ optional per-shot voice audio) into a rough-cut
timeline, in shot order. Requires ffmpeg on PATH.
"""
import subprocess
from pathlib import Path

from config import OUTPUT_DIR
from schema import ShotList


def mux_voice_over_clip(clip_path: str, voice_path: str, out_path: str) -> None:
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", clip_path,
            "-i", voice_path,
            "-c:v", "copy",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
            out_path,
        ],
        check=True,
    )


def concat_clips(clip_paths: list, out_path: str) -> None:
    list_file = Path(OUTPUT_DIR) / "concat_list.txt"
    list_file.parent.mkdir(parents=True, exist_ok=True)
    list_file.write_text(
        "\n".join(f"file '{Path(p).resolve()}'" for p in clip_paths), encoding="utf-8"
    )
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", out_path],
        check=True,
    )


def assemble_rough_cut(shot_list: ShotList, clip_files: dict, voice_files: dict, out_path: str) -> str:
    """clip_files / voice_files: {shot_id: filepath}, filled in as each shot
    finishes generating. Shots with no clip (editorial-only, e.g. title
    cards) are skipped -- those get added by hand in DaVinci/CapCut."""
    ordered_clips = []
    for shot in shot_list.shots:
        clip = clip_files.get(shot.id)
        if not clip:
            continue
        voice = voice_files.get(shot.id)
        if voice:
            muxed = str(Path(OUTPUT_DIR) / "muxed" / f"{shot.id}.mp4")
            Path(muxed).parent.mkdir(parents=True, exist_ok=True)
            mux_voice_over_clip(clip, voice, muxed)
            ordered_clips.append(muxed)
        else:
            ordered_clips.append(clip)

    if not ordered_clips:
        raise RuntimeError("No clips to assemble -- did any wan_video shots actually generate?")

    concat_clips(ordered_clips, out_path)
    return out_path
