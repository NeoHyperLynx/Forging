import os

# --- Director agent provider chain --------------------------------------
# Tried in order until one succeeds -- add, remove, or reorder as free tiers
# change (they do, often). Each needs its own API key as an env var / Colab
# secret. Model IDs shift fast on all three providers -- verify the current
# one on each provider's own dashboard before assuming these are still right.
DIRECTOR_PROVIDERS = [
    {
        "name": "deepseek",
        "base_url": "https://api.deepseek.com",
        "api_key_env": "DEEPSEEK_API_KEY",
        "model": "deepseek-chat",  # verify at platform.deepseek.com
    },
    {
        "name": "glm",
        "base_url": "https://api.z.ai/api/paas/v4/",  # global Z.AI platform, not open.bigmodel.cn (that one needs a Chinese phone number)
        "api_key_env": "ZAI_API_KEY",
        "model": "glm-4.7-flash",  # standing free tier, no card, no expiry
    },
    {
        "name": "gemini",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "api_key_env": "GEMINI_API_KEY",
        "model": "gemini-2.5-flash",  # verify at aistudio.google.com -- naming moves fast
    },
    {
        "name": "openrouter",
        "base_url": "https://openrouter.ai/api/v1",
        "api_key_env": "OPENROUTER_API_KEY",
        "model": "deepseek/deepseek-r1:free",  # free roster rotates -- check openrouter.ai/models?max_price=0
    },
]

# --- ComfyUI (Wan 2.2 + Flux, self-hosted, free) -------------------------
# Wherever you're running ComfyUI -- your own GPU, or a rented one you spin
# up per session. This is the free path: Wan 2.2 is Apache 2.0, no per-call
# cost, but you supply the compute.
COMFYUI_URL = os.environ.get("COMFYUI_URL", "http://127.0.0.1:8188")

# --- Voice references -----------------------------------------------------
# WAV files you record or source yourself -- see README. XTTS v2 needs
# 5-15 seconds of clean reference audio per character.
VOICE_REFERENCES = {
    "Kessler": os.environ.get("KESSLER_VOICE_REF", "voices/kessler_ref.wav"),
    "Demi": os.environ.get("DEMI_VOICE_REF", "voices/demi_ref.wav"),
}

OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "./output")
