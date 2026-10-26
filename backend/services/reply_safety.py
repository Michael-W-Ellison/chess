"""
Checks on replies written by the language model before the child sees them.

The safety filter (services/safety_filter.py) is written for the child's messages; a model
reply can be unsafe in other ways: advice to hit someone, to mix cleaning products, to keep a
secret from parents, to share an address or photos. unsafe_reason() finds those, unless the
reply says not to ("don't hit them back", "never share your address").

The rule-based replies are written by hand and are not checked here.
"""

import re
from typing import Optional

_ADVICE = [
    ("violence", r"\b(?:punch|hit|kick|slap|bite|shove|beat up|hurt|fight)\s+(?:them|him|her|back|that (?:kid|boy|girl"
                 r"|bully)|the (?:kid|boy|girl|bully)|bullies)\b"),
    ("violence", r"\b(?:in the face|make them bleed|get revenge|teach them a lesson)\b"),
    ("weapons", r"\b(?:grab|use|get|bring|take)\s+(?:a |the |your )?(?:knife|gun|weapon)\b"),
    ("dangerous", r"\b(?:bleach|ammonia|lighter fluid|gasoline|rubbing alcohol)\b"),
    ("dangerous", r"\b(?:play with|light|start)\s+(?:a )?(?:fire|matches|a lighter)\b"),
    ("dangerous", r"\btake\s+(?:some |a lot of |extra )?(?:pills|medicine|medication)\b"),
    ("secrecy", r"\b(?:don'?t|do not|never)\s+tell\s+(?:your\s+)?(?:parents?|mom|dad|anyone|any grown[- ]?ups?"
                r"|a grown[- ]?up|adults?|teachers?)\b"),
    ("secrecy", r"\b(?:our|a)\s+(?:little\s+)?secret\b|\bkeep\s+(?:this|it)\s+(?:a\s+)?secret\b"),
    ("secrecy", r"\bsneak\s+out\b|\bwithout\s+(?:telling|asking)\s+(?:your\s+)?(?:parents?|mom|dad)\b"),
    ("personal_info", r"\b(?:send|share|tell|give)\s+(?:me|them|him|her|someone)\s+(?:your\s+)?(?:address|phone number"
                      r"|pictures?|photos?|pics?|password)\b"),
    ("personal_info", r"\bmeet\s+(?:up\s+)?with\s+(?:a\s+)?(?:stranger|someone you met online|people you met online)\b"),
]
_PATTERNS = [(reason, re.compile(pattern, re.IGNORECASE)) for reason, pattern in _ADVICE]
# Words just before a match that make it advice against it ("don't hit them back", "it's not
# okay to keep a secret")
_NEGATED_RE = re.compile(
    r"\b(?:don'?t|do not|never|not|no|shouldn'?t|should not|stop|avoid|isn'?t okay|not okay|instead of|rather than)\b"
    r"[^.!?]{0,25}$", re.IGNORECASE
)


def unsafe_reason(reply: str) -> Optional[str]:
    """Why a model reply should not be sent ("violence", "secrecy", ...), or None if it can be"""
    for reason, pattern in _PATTERNS:
        for match in pattern.finditer(reply):
            before = reply[max(0, match.start() - 40):match.start()]
            # "never tell" itself is the advice in a secrecy pattern
            if reason != "secrecy" and _NEGATED_RE.search(before):
                continue
            # "It's not okay to keep a secret", "if someone asks you to keep a secret, tell a grown-up"
            if reason == "secrecy" and re.search(r"\b(?:(?:it'?s|is) (?:not okay|never okay|wrong)|(?:asks?|wants?|tells?)"
                                                 r" you to)\b[^.!?]*$", before, re.IGNORECASE):
                continue
            return reason
    return None
