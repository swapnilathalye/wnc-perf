# python/ai/insights.py
import textwrap
import requests
import logging
from app.services.config import load_config

def build_insight_prompt(rows, table_name: str, granularity: str):
    """
    rows: list of dicts from your existing endpoint
    """
    preview = rows[:100]  # keep prompt bounded

    return textwrap.dedent(f"""
    You are an expert observability assistant.

    You are given JVM active context data from the table "{table_name}".
    Each row has fields like:
    - iso: ISO timestamp
    - max_active: maximum active contexts in this bucket
    - (optionally) JVM_ID if by-JVM

    Granularity: {granularity}

    Here is a sample of the data in JSON:
    {preview}

    In 3–6 concise bullet points, explain:
    - Key trends over time
    - Any spikes or drops
    - Anything that looks anomalous or worth investigating

    Respond in plain text, no markdown, no JSON.
    """)

logger = logging.getLogger(__name__)

LANGUAGE_MAP = {
    "en": "English",
    "fr": "French",
    "de": "German",
    "es": "Spanish",
    "ja": "Japanese",
}

def call_ai_model(prompt: str) -> str:
    """
    Calls Ollama AI model and forces response language
    based on config.json (default: English).
    """
    try:
        # 1️⃣ Read language from config.json
        config = load_config()
        lang_code = config.get("language", "en")
        language = LANGUAGE_MAP.get(lang_code, "English")

        logger.info("🤖 Calling AI model with language: %s (%s)", language, lang_code)

        # 2️⃣ Inject language instruction into prompt (industry standard)
        final_prompt = f"""
You are an intelligent observability and performance assistant.
Always respond in {language}.

{prompt}
""".strip()

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": final_prompt,
                "stream": False
            },
            timeout=180
        )

        response.raise_for_status()
        data = response.json()

        return data.get("response", "").strip()

    except Exception as e:
        logger.error("❌ AI model error: %s", e)
        return f"AI model error: {e}"

