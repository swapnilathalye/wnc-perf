# python/ai/insights.py
import textwrap
import requests

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

def call_ai_model(prompt: str) -> str:
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": prompt,
                "stream": False
            },
            timeout=180
        )
        data = response.json()
        return data.get("response", "").strip()
    except Exception as e:
        return f"AI model error: {e}"
