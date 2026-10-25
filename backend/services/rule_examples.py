"""
Sample messages stored with each rule in knowledge/conversation_rules.json, and a check that
the rules still answer them.

A rule can list "examples" (messages it must answer) and "non_examples" (messages it must not
answer). Each message is checked on its own, in a fresh engine, so no example depends on
earlier conversation. For a rule with replies, "answer" means the engine chose that rule's
reply; for a rule without replies (one that only stores a memory), it means the rule matched.
Entries in the "keywords" section (the parse-free fallback) and the "recall" questions list
examples the same way; for them, "answer" means the reply came from that keyword
("fallback_keyword_<id>") or question ("recall_<id>").

Run the check from backend/ with: python scripts/verify_rules.py
"""

import random
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Callable, List, Optional


@dataclass
class ExampleFailure:
    """A sample message whose rule no longer behaves as listed"""

    rule_id: str
    kind: str  # "example" or "non_example"
    message: str
    actual: Optional[str]  # the rule (or fallback) that answered instead

    def __str__(self) -> str:
        if self.kind == "example":
            return f"{self.rule_id}: {self.message!r} was answered by {self.actual}"
        return f"{self.rule_id}: non-example {self.message!r} was answered by this rule"


def _personality():
    return SimpleNamespace(id=1, user_id=1, name="Buddy", mood="happy", friendship_level=1,
                           energy=0.7, curiosity=0.0, formality=0.3, get_interests=lambda: [])


def _new_engine():
    from services.response_engine import ResponseEngine
    return ResponseEngine(rng=random.Random(0))


def answering_rule(engine, message: str) -> Optional[str]:
    """The rule (or fallback) the engine uses to reply to the message"""
    features = {}
    resolved = engine.resolve_references(message, 1)
    engine.generate_response(resolved, _personality(), features=features)
    return features.get("rule")


def check_examples(engine_factory: Callable = _new_engine, rule_ids: Optional[List[str]] = None) -> List[ExampleFailure]:
    """Every listed example and non-example that its rule no longer handles as listed"""
    kb = engine_factory().kb
    rules = kb["rules"] + [dict(k, id=f"keyword_{k['id']}", _answered_by=f"fallback_keyword_{k['id']}")
                           for k in kb.get("keywords", [])] + \
        [dict(q, id=f"recall_{q['id']}", responses=q["unknown"]) for q in kb.get("recall", {}).get("questions", [])]
    failures = []
    for rule in rules:
        if rule_ids is not None and rule["id"] not in rule_ids:
            continue
        has_replies = bool(rule.get("responses") or rule.get("responses_by"))
        answered_by = rule.get("_answered_by", rule["id"])
        for kind in ("examples", "non_examples"):
            for message in rule.get(kind, []):
                engine = engine_factory()
                if has_replies:
                    actual = answering_rule(engine, message)
                    answered = actual == answered_by
                else:
                    matched = [f.rule_id for f in engine.analyze(engine.resolve_references(message, 1)).frames]
                    answered = rule["id"] in matched
                    actual = rule["id"] if answered else (matched[0] if matched else None)
                if kind == "examples" and not answered:
                    failures.append(ExampleFailure(rule["id"], "example", message, actual))
                elif kind == "non_examples" and answered:
                    failures.append(ExampleFailure(rule["id"], "non_example", message, actual))
    return failures


def rules_without_examples(engine_factory: Callable = _new_engine) -> List[str]:
    """Ids of rules (and keyword entries, as "keyword_<id>") that list no examples"""
    kb = engine_factory().kb
    return [r["id"] for r in kb["rules"] if not r.get("examples")] + \
        [f"keyword_{k['id']}" for k in kb.get("keywords", []) if not k.get("examples")] + \
        [f"recall_{q['id']}" for q in kb.get("recall", {}).get("questions", []) if not q.get("examples")]
