import os

DIRECTOR_PROVIDERS = [
    {
        "name": "deepseek",
        "base_url": "https://api.deepseek.com",
        "api_key_env": "DEEPSEEK_API_KEY",
        "model": "deepseek-v4-flash",
    },
    {
        "name": "glm",
        "base_url": "https://api.z.ai/api/paas/v4/",
        "api_key_env": "ZAI_API_KEY",
        "model": "glm-4.7-flash",
    },
    {
        "name": "gemini",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "api_key_env": "GEMINI_API_KEY",
        "model": "gemini-2.5-flash",
    },
    {
        "name": "openrouter",
        "base_url": "https://openrouter.ai/api/v1",
        "api_key_env": "OPENROUTER_API_KEY",
        "model": "openrouter/free",
    },
]

COMFYUI_URL = os.environ.get("COMFYUI_URL", "http://127.0.0.1:8188")

VOICE_REFERENCES = {
    "Kessler": os.environ.get("KESSLER_VOICE_REF", "voices/kessler_ref.wav"),
    "Demi": os.environ.get("DEMI_VOICE_REF", "voices/demi_ref.wav"),
}

OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "./output")
