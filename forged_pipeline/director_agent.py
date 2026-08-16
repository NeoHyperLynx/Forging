"""
Director agent: takes a script and returns a structured shot list as JSON.

Tries each provider in config.DIRECTOR_PROVIDERS in order, falling through
to the next on any failure (missing key, quota exhausted, rate limited,
model retired, etc.) rather than hard-failing the whole run because one
free tier ran out.
"""
import json
import os

from openai import OpenAI  # pip install openai

from config import DIRECTOR_PROVIDERS
from schema import ShotList

SYSTEM_PROMPT = """You are a production director. You take a finished script
(or scene) and break it into a shot-by-shot production plan. You do not
generate any media yourself -- you decide what each shot needs and which
tool is best suited to make it.

You never silently guess on creative ambiguity. When the script doesn't
specify tone, pacing, music, or visual style for a moment, flag it in
open_questions rather than picking for the writer.

TOOLBOX (free tier only -- do not assume paid models):
- wan_video: Wan 2.2, open-source, self-hosted via ComfyUI. Strong for
  stylized/animated motion, environments, objects, wide/medium shots,
  camera moves. Weak at holding a consistent human face across separate
  generations, especially in tight realistic close-ups. Always prefer
  image-to-video (a reference still) over generating a face from scratch.
- flux_still: Flux, open-source, self-hosted. Character reference sheets,
  single hero frames, documents/on-screen text, and the reference image
  fed into wan_video.
- editorial: not a generation task -- title cards, graphic text overlays,
  color grading, cuts. Assign this when the shot doesn't need a model at
  all.
- voice_tts: XTTS v2, open-source, clones a character's voice from a short
  reference sample. Used automatically for any shot with dialogue --
  you don't need to select it as `tool`, just fill in `dialogue` and
  `speaker` on any shot that has a line.

FACE-CONSISTENCY RULE: for any shot involving a named character's face,
apply one of: obscure it (shadow, distance, angle), use a still instead of
video, fragment it (hands/eyes, never a full face twice in a row), or
substitute an object. Note which applies in consistency_note. This
constraint is real and current -- do not assume it's solved.

Return ONLY valid JSON, no prose, no markdown fences, matching exactly:
{
  "title": "string",
  "shots": [
    {
      "id": "1",
      "scene": "short scene label",
      "visual": "what's on screen, shot size, camera movement",
      "audio": "dialogue and/or music/SFX intent, in words",
      "tool": "wan_video | flux_still | editorial",
      "prompt": "the actual generation prompt for that tool",
      "dialogue": "quoted line, or null",
      "speaker": "character name matching a VOICE_REFERENCES key, or null",
      "reference_image": "id of the flux_still shot this depends on, or null",
      "consistency_note": "only if a named character's face is involved, else null"
    }
  ],
  "open_questions": ["string", "..."]
}
"""


def _call_provider(provider: dict, script_text: str, extra_notes: str) -> str:
    api_key = os.environ.get(provider["api_key_env"], "")
    if not api_key:
        raise RuntimeError(f"{provider['name']}: no {provider['api_key_env']} set, skipping")

    client = OpenAI(base_url=provider["base_url"], api_key=api_key)
    resp = client.chat.completions.create(
        model=provider["model"],
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT + ("\n\n" + extra_notes if extra_notes else "")},
            {"role": "user", "content": script_text},
        ],
        temperature=0.4,
    )
    return resp.choices[0].message.content.strip()


def break_down_script(script_text: str, extra_notes: str = "") -> ShotList:
    errors = []
    for provider in DIRECTOR_PROVIDERS:
        try:
            raw = _call_provider(provider, script_text, extra_notes)
            print(f"  (director agent ran on {provider['name']})")
            break
        except Exception as e:  # noqa: BLE001 -- deliberately broad, this is a fallback chain
            errors.append(f"{provider['name']}: {e}")
            continue
    else:
        raise RuntimeError(
            "All director agent providers failed:\n" + "\n".join(errors)
        )

    if raw.startswith("```"):
        raw = raw.strip("`")
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw
    data = json.loads(raw)
    return ShotList.from_json(data)


if __name__ == "__main__":
    import sys

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        script_text = f.read()
    result = break_down_script(script_text)
    print(json.dumps(result.to_json(), indent=2))
