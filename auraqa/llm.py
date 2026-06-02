"""llm.py - the single doorway to the AI model.

Every AI call in the project goes through ask(). Swap providers by changing
AURAQA_PROVIDER in your .env. Free tiers are supported (Gemini and Groq).
"""

from __future__ import annotations

import json
import os
import re
import time

from dotenv import load_dotenv

load_dotenv()

PROVIDER = os.getenv("AURAQA_PROVIDER", "gemini").lower()
# Model names drift over time - override with AURAQA_MODEL in .env if needed.
GEMINI_MODEL = os.getenv("AURAQA_MODEL", "gemini-2.5-flash")
GROQ_MODEL = os.getenv("AURAQA_MODEL", "llama-3.3-70b-versatile")


def _strip_json_fences(text: str) -> str:
    """Models often wrap JSON in ```json ... ``` - remove that."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _call_gemini(prompt: str, system: str | None) -> str:
    import google.generativeai as genai

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set (see .env.example)")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        GEMINI_MODEL, system_instruction=system if system else None
    )
    resp = model.generate_content(prompt)
    return resp.text or ""


def _call_groq(prompt: str, system: str | None) -> str:
    from groq import Groq

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set (see .env.example)")
    client = Groq(api_key=api_key)
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    resp = client.chat.completions.create(model=GROQ_MODEL, messages=messages)
    return resp.choices[0].message.content or ""


def ask(prompt: str, system: str | None = None, expect_json: bool = True,
        retries: int = 3):
    """Send a prompt to the model and return the answer.

    If expect_json is True, the reply is parsed and returned as a dict/list.
    Otherwise the raw text is returned. Retries with backoff on rate limits.
    """
    if expect_json:
        prompt += (
            "\n\nReply with ONLY valid JSON. No prose, no explanation, "
            "no markdown code fences."
        )

    last_error = None
    for attempt in range(retries):
        try:
            if PROVIDER == "groq":
                raw = _call_groq(prompt, system)
            else:
                raw = _call_gemini(prompt, system)

            if not expect_json:
                return raw

            cleaned = _strip_json_fences(raw)
            return json.loads(cleaned)

        except json.JSONDecodeError as exc:
            # The model produced something un-parseable - try once more.
            last_error = exc
            time.sleep(1.5 * (attempt + 1))
        except Exception as exc:  # rate limits, network, etc.
            last_error = exc
            time.sleep(2.0 * (attempt + 1))

    raise RuntimeError(f"LLM call failed after {retries} attempts: {last_error}")
