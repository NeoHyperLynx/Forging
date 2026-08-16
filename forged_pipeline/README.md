# Forged Pipeline (free-tier build)

Director agent → Wan 2.2 / Flux (via ComfyUI) → XTTS voice → rough-cut
assembly. Built entirely against free/self-hosted tools — no paid Wan tiers,
no paid voice API.

This is real, runnable code, not a mockup — but it can't be tested from
inside the environment it was written in (no network access to ComfyUI,
DeepSeek, or model weight downloads there). You're the first one to actually
run it. Expect to debug node IDs and paths against your specific setup.

## What you need running first

1. **ComfyUI**, installed locally (or on a rented GPU), with Wan 2.2 and
   Flux checkpoints downloaded and working in the UI.
2. **Two exported workflows**, from ComfyUI's menu — Workflow → Export (API):
   - A Flux text-to-image workflow → save as `flux_api.json`
   - A Wan 2.2 image-to-video workflow → save as `wan_i2v_api.json`
   Open each JSON and find the node IDs for your prompt (`CLIPTextEncode`)
   and, for the Wan workflow, your `LoadImage` node. You'll pass these as
   `--flux-prompt-node`, `--wan-prompt-node`, `--wan-image-node`.
3. **ffmpeg** on your PATH (`ffmpeg -version` to check).
4. **API keys for the director agent's fallback chain** — DeepSeek, then
   GLM, then Gemini, then OpenRouter, tried automatically in that order. Set
   whichever ones you have as env vars / Colab secrets:
   `DEEPSEEK_API_KEY`, `ZAI_API_KEY`, `GEMINI_API_KEY`, `OPENROUTER_API_KEY`.
   You don't need all four to start — one is enough — but the chain means
   the pipeline keeps working as any single free tier runs out or tightens,
   instead of failing silently until you notice.
   - For `ZAI_API_KEY`, sign up at **z.ai** (the global platform, email
     signup) — not `open.bigmodel.cn`, which requires a Chinese phone number
     and is a different account entirely.
5. **Voice reference clips** — 5–15 seconds of clean audio per character,
   saved as `voices/kessler_ref.wav`, `voices/demi_ref.wav`, etc. Nothing
   generates these for you; see the earlier scene 2 production packet for
   why this is a real dependency, not a model limitation.

## Install

```bash
pip install -r requirements.txt
export DEEPSEEK_API_KEY=your_deepseek_key
export ZAI_API_KEY=your_zai_key                # optional but recommended, genuinely free
export GEMINI_API_KEY=your_gemini_key          # optional but recommended
export OPENROUTER_API_KEY=your_openrouter_key  # optional but recommended
export COMFYUI_URL=http://127.0.0.1:8188   # or wherever ComfyUI is running
```

## Run

```bash
python main.py \
  --script scene2.txt \
  --workflow-flux flux_api.json --flux-prompt-node 6 \
  --workflow-wan wan_i2v_api.json --wan-prompt-node 6 --wan-image-node 10 \
  --out output/scene2_rough_cut.mp4
```

This will:
1. Send the script to the director agent, save `output/shot_list.json`,
   print any open questions it flagged.
2. Generate each `flux_still` shot first (character references, document
   inserts), then each `wan_video` shot (using the matching reference).
3. Generate cloned-voice audio for any shot with dialogue.
4. Mux voice onto video per shot and concatenate everything into one file.

## What will probably break the first time

- **Node IDs won't match.** Every ComfyUI workflow graph has different node
  numbering — `flux_prompt_node`/`wan_prompt_node`/`wan_image_node` are
  almost certainly not `6`/`6`/`10` on your actual export. Open the JSON,
  search for `CLIPTextEncode` and `LoadImage`, use the real keys.
- **Video output key.** `wan_video.py` looks for `gifs` or `videos` in the
  ComfyUI response, depending on which video-combine custom node your
  workflow uses. If neither key appears, print `result["outputs"]` and see
  what your specific node actually returns.
- **XTTS model download.** First call to `voice_tts.generate_line` downloads
  the XTTS v2 weights — this takes a while and needs disk space.

## Files

- `director_agent.py` — script in, structured shot list out (JSON)
- `schema.py` — the `Shot` / `ShotList` data shapes
- `workers/comfy_client.py` — generic ComfyUI API driver (submit/poll/fetch)
- `workers/flux_stills.py`, `workers/wan_video.py` — the two ComfyUI-backed
  generation steps
- `workers/voice_tts.py` — local XTTS v2 cloning, no external API
- `assemble.py` — ffmpeg-based stitching into a rough cut
- `main.py` — wires all of the above together
