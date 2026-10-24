"""
The rewrite steps in knowledge/normalizations.json: each step's examples come out of
normalize() as listed, and every step is described. Needs no spaCy model.
"""

import json
from pathlib import Path

import pytest

from services.utterance_parser import _CODE_STEPS, UtteranceParser

DATA = json.loads((Path(__file__).resolve().parent.parent / "knowledge" / "normalizations.json").read_text("utf-8"))
EXAMPLES = [(i, message, expected) for i, step in enumerate(DATA["steps"]) for message, expected in step["examples"]]


@pytest.mark.parametrize("step,message,expected", EXAMPLES)
def test_step_example(step, message, expected):
    assert UtteranceParser.normalize(message) == expected, DATA["steps"][step]["note"]


@pytest.mark.parametrize("step", DATA["steps"], ids=lambda s: s.get("code") or s["note"][:40])
def test_step_is_described_and_has_examples(step):
    assert step.get("note") and step.get("examples")
    assert ("code" in step) != ("pattern" in step)
    if "code" in step:
        assert step["code"] in _CODE_STEPS
    else:
        assert ("replace" in step) != ("template" in step)
