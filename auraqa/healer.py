"""healer.py - the core. Re-find an element after its selector breaks.

When a step fails, we snapshot the page as it looks NOW, tell the AI what the
step was trying to do (its intent), and ask for a fresh selector. We verify the
AI's answer actually exists on the page before trusting it.
"""

from __future__ import annotations

from . import dom_utils, llm
from .models import TestStep

_SYSTEM = (
    "You are a web automation expert. Given a goal and the current elements on "
    "a page, you pick the single best CSS selector to reach that goal."
)

_PROMPT_TEMPLATE = """\
A test step is failing because its selector no longer matches anything.

What the step is trying to do (its intent): "{intent}"
The old selector that broke: {old_selector}

Here are the elements currently on the page:

{elements}

Pick the ONE element that best matches the intent and return its selector.
Return JSON: {{"selector": "the css selector", "index": <the [number] shown>}}
If nothing on the page matches the intent, return {{"selector": ""}}.
"""


def _selector_works(page, selector: str) -> bool:
    """Check the selector matches at least one visible element."""
    if not selector:
        return False
    try:
        locator = page.locator(selector)
        return locator.count() > 0 and locator.first.is_visible()
    except Exception:
        return False


def heal(page, step: TestStep) -> str | None:
    """Return a working selector for the step, or None if the AI can't find it."""
    elements = dom_utils.snapshot(page)
    prompt = _PROMPT_TEMPLATE.format(
        intent=step.intent,
        old_selector=step.selector or "(none)",
        elements=dom_utils.to_prompt_text(elements),
    )

    try:
        data = llm.ask(prompt, system=_SYSTEM, expect_json=True)
    except Exception:
        return None

    candidate = (data or {}).get("selector", "").strip()

    # Trust, but verify - the AI's selector must actually exist on the page.
    if _selector_works(page, candidate):
        return candidate

    # Fall back to the selector of the index the AI pointed at, if any.
    idx = (data or {}).get("index")
    if isinstance(idx, int) and 0 <= idx < len(elements):
        backup = elements[idx]["selector"]
        if _selector_works(page, backup):
            return backup

    return None
