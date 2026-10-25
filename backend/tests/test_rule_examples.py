"""
Every rule in knowledge/conversation_rules.json answers its listed examples and not its
non-examples (services/rule_examples.py). Skipped when spaCy or its English model is not
installed.
"""

import pytest

from services.rule_examples import check_examples, rules_without_examples
from services.utterance_parser import UtteranceParser

pytestmark = pytest.mark.skipif(
    not UtteranceParser().is_available(), reason="spaCy model en_core_web_sm not installed"
)


def test_rules_answer_their_examples():
    failures = check_examples()
    assert not failures, "\n".join(str(f) for f in failures)


def test_every_rule_lists_examples():
    assert rules_without_examples() == []
