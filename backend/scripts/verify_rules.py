"""
Check that every rule in knowledge/conversation_rules.json still answers its listed examples
and does not answer its non-examples (see services/rule_examples.py).

Usage (from backend/):
    python scripts/verify_rules.py              # all rules
    python scripts/verify_rules.py achievement  # only the named rules

Exits with status 1 if any example fails.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from services.rule_examples import check_examples, rules_without_examples  # noqa: E402
from services.utterance_parser import utterance_parser  # noqa: E402


def main(argv):
    if not utterance_parser.is_available():
        print("spaCy model en_core_web_sm is not installed; rule examples cannot be checked")
        return 2
    failures = check_examples(rule_ids=argv or None)
    for failure in failures:
        print(failure)
    missing = rules_without_examples()
    if missing and not argv:
        print(f"{len(missing)} rules list no examples: {', '.join(missing)}")
    print(f"{len(failures)} failing" if failures else "All rule examples pass")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
