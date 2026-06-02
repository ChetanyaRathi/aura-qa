"""generator.py - the AI writes test cases from a URL.

Opens the page, hands the AI a clean list of what's on it, and asks for
realistic user flows. Saves the result as a JSON suite in tests_store/.
"""

from __future__ import annotations

import json
import os

from playwright.sync_api import sync_playwright

from . import dom_utils, llm
from .models import TestCase, TestStep

STORE_DIR = os.path.join(os.getcwd(), "tests_store")

_SYSTEM = (
    "You are a senior QA engineer. You write clear, realistic end-to-end "
    "test flows for web pages."
)

_PROMPT_TEMPLATE = """\
Here is a web page at {url}. Below are the interactive elements on it:

{elements}

Write up to {n_flows} realistic end-to-end test flows a real user might do
(for example: search for something, submit a form, navigate, log in).

Return JSON with this exact shape:
{{
  "name": "short suite name",
  "steps": [
    {{"action": "goto", "intent": "open the page", "value": "{url}"}},
    {{"action": "click", "intent": "describe the element in plain English",
      "selector": "css selector from the list above"}},
    {{"action": "fill", "intent": "...", "selector": "...", "value": "text to type"}},
    {{"action": "assert_visible", "intent": "...", "selector": "..."}},
    {{"action": "assert_text", "intent": "...", "selector": "...",
      "expected": "text that should appear"}}
  ]
}}

Rules:
- The first step must be a "goto" to {url}.
- Use only selectors that appear in the element list above.
- Always include an "intent" written in plain English - it must stay true even
  if the page changes later.
- Allowed actions: goto, click, fill, assert_visible, assert_text.
"""
def _normalize_suite(data, url: str) -> dict:
    """The model sometimes returns a list or an odd shape.
    Coerce whatever it returns into {"name": ..., "steps": [...]}."""
    steps = []

    def collect(obj):
        if isinstance(obj, dict):
            if "action" in obj:
                steps.append(obj)
            for key in ("steps", "flows"):
                if isinstance(obj.get(key), list):
                    for item in obj[key]:
                        collect(item)
        elif isinstance(obj, list):
            for item in obj:
                collect(item)

    if isinstance(data, dict) and isinstance(data.get("steps"), list) \
            and all("action" in s for s in data["steps"]):
        return data  # already the right shape

    collect(data)
    name = data.get("name") if isinstance(data, dict) else None
    return {"name": name or "generated_suite", "steps": steps}


def generate_suite(url: str, n_flows: int = 3, save: bool = True) -> TestCase:
    """Visit the URL and produce a test suite using the AI."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(1500)  # let dynamic content settle
        elements = dom_utils.snapshot(page)
        browser.close()

    prompt = _PROMPT_TEMPLATE.format(
        url=url, elements=dom_utils.to_prompt_text(elements), n_flows=n_flows
    )
    data = llm.ask(prompt, system=_SYSTEM, expect_json=True)
    data = _normalize_suite(data, url)
    suite = TestCase.from_dict(data)

    # Guarantee a goto step is present at the front.
    if not suite.steps or suite.steps[0].action != "goto":
        suite.steps.insert(
            0, TestStep(action="goto", intent="open the page", value=url)
        )

    if save:
        os.makedirs(STORE_DIR, exist_ok=True)
        safe = "".join(c if c.isalnum() else "_" for c in suite.name).lower()
        path = os.path.join(STORE_DIR, f"{safe or 'suite'}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(suite.to_dict(), f, indent=2)
        print(f"Saved suite to {path}")

    return suite


def load_suite(path: str) -> TestCase:
    with open(path, "r", encoding="utf-8") as f:
        return TestCase.from_dict(json.load(f))


def save_suite(suite: TestCase, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(suite.to_dict(), f, indent=2)
