"""runner.py - play the test suite in a real browser.

Each step runs with a short timeout. If an element can't be found and healing
is on, we call the healer, retry once with the new selector, and (on success)
write the fix back into the suite so it stays healed.
"""

from __future__ import annotations

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

from . import healer
from .models import TestCase, TestStep, StepResult, RunResult

STEP_TIMEOUT_MS = 5000


def _do_action(page, step: TestStep) -> None:
    """Perform a single step. Raises on failure."""
    if step.action == "goto":
        page.goto(step.value, wait_until="domcontentloaded",
                  timeout=STEP_TIMEOUT_MS * 3)
        return

    locator = page.locator(step.selector).first

    if step.action == "click":
        locator.click(timeout=STEP_TIMEOUT_MS)
    elif step.action == "fill":
        locator.fill(step.value, timeout=STEP_TIMEOUT_MS)
    elif step.action == "assert_visible":
        locator.wait_for(state="visible", timeout=STEP_TIMEOUT_MS)
    elif step.action == "assert_text":
        locator.wait_for(state="visible", timeout=STEP_TIMEOUT_MS)
        actual = locator.inner_text(timeout=STEP_TIMEOUT_MS)
        if step.expected.lower() not in actual.lower():
            raise AssertionError(
                f"expected text '{step.expected}' not found in '{actual[:60]}'"
            )
    else:
        raise ValueError(f"unknown action: {step.action}")


def run_suite(suite: TestCase, heal: bool = True,
              headless: bool = True) -> RunResult:
    """Run every step, healing broken selectors along the way."""
    run = RunResult(suite_name=suite.name)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()

        for step in suite.steps:
            try:
                _do_action(page, step)
                run.results.append(StepResult(
                    intent=step.intent, action=step.action, status="pass"
                ))
                continue
            except (PWTimeout, AssertionError, Exception) as exc:
                first_error = str(exc)

            # goto failures and asserts on missing text aren't selector
            # problems - don't try to heal those.
            if not heal or step.action == "goto":
                run.results.append(StepResult(
                    intent=step.intent, action=step.action, status="failed",
                    old_selector=step.selector, error=first_error
                ))
                continue

            # Selector likely broke - ask the healer for a new one.
            new_selector = healer.heal(page, step)
            if new_selector:
                old = step.selector
                step.selector = new_selector  # persists back into the suite
                try:
                    _do_action(page, step)
                    run.results.append(StepResult(
                        intent=step.intent, action=step.action,
                        status="healed", old_selector=old,
                        new_selector=new_selector
                    ))
                    continue
                except Exception as exc:
                    first_error = str(exc)

            run.results.append(StepResult(
                intent=step.intent, action=step.action, status="failed",
                old_selector=step.selector, error=first_error
            ))

        browser.close()

    return run
