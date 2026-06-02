"""models.py - the data shapes the whole project agrees on.

The key field is TestStep.intent: a plain-English description of what the step
is trying to do. Selectors break when a site changes, but intent never does -
so the healer can always re-find the element from its intent.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional

# Allowed actions a step can perform.
ACTIONS = ("goto", "click", "fill", "assert_visible", "assert_text")


@dataclass
class TestStep:
    action: str                      # one of ACTIONS
    intent: str                      # plain English: "the blue Login button"
    selector: str = ""               # current best CSS selector
    value: str = ""                  # text to type, or URL for goto
    expected: str = ""               # expected text for assert_text

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "TestStep":
        return TestStep(
            action=d["action"],
            intent=d.get("intent", ""),
            selector=d.get("selector", ""),
            value=d.get("value", ""),
            expected=d.get("expected", ""),
        )


@dataclass
class TestCase:
    name: str
    steps: list[TestStep] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"name": self.name, "steps": [s.to_dict() for s in self.steps]}

    @staticmethod
    def from_dict(d: dict) -> "TestCase":
        return TestCase(
            name=d["name"],
            steps=[TestStep.from_dict(s) for s in d.get("steps", [])],
        )


@dataclass
class StepResult:
    intent: str
    action: str
    status: str                      # "pass" | "healed" | "failed"
    old_selector: str = ""
    new_selector: str = ""
    error: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class RunResult:
    suite_name: str
    results: list[StepResult] = field(default_factory=list)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.status == "pass")

    @property
    def healed(self) -> int:
        return sum(1 for r in self.results if r.status == "healed")

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if r.status == "failed")

    def to_dict(self) -> dict:
        return {
            "suite_name": self.suite_name,
            "passed": self.passed,
            "healed": self.healed,
            "failed": self.failed,
            "results": [r.to_dict() for r in self.results],
        }
