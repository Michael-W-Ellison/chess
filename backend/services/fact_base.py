"""
The facts in knowledge/facts.json, compiled for checking the child's statements against them
("spiders have 6 legs", "the capital of France is Berlin"). See the file's "_comment" for the
fact types. Used by ResponseEngine.check_fact and scripts/build_facts.py.

"is" facts are indexed by the value after "is" ("a mammal", "berlin"), so a statement is only
compared with the facts that mention its value; the other types are few and tried in order.
An "is" statement is also read the other way around ("venus is the hottest planet" as "the
hottest planet is venus").
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# "spiders are really insects": words between "is" and the value
_IS_ADVERBS_RE = re.compile(r"^(?:(?:really|very|so|super|totally|kind of|kinda|actually|just|only|all|also|even"
                            r"|definitely|probably|not even) )+")
_IS_RE = re.compile(r" (?:is|are|r|was|were)(?P<neg>nt| not| never)? ")
# "penguins can fly high": words after the verb that still say the same thing (not "dogs fly kites")
_CAN_ENDINGS = (r"(?: (?:really |very |so |super )?(?:high|fast|far|well|good|at all|too|either|around|away"
                r"|south|in the sky|in the air|like (?:a )?birds?|like (?:a )?fish|really well|very well))?")
_NEGATED_MODALS = ("can not", "cannot", "cant", "couldnt", "dont", "do not", "doesnt", "does not")

_CACHE: Dict[Tuple[str, float], "FactBase"] = {}

# "no", "I think", "did you know" before the statement
FACT_OPENERS_RE = re.compile(
    r"^(?:(?:no+|nope|nah|actually|well|um+|uh+|hey|buddy|so|but|and|guess what|did you know|you know what"
    r"|fun fact|i think|i know|i heard|i learned|i read|i bet|my (?:teacher|mom|dad|friend|brother|sister) said"
    r"|everybody knows|everyone knows)\b(?: that)?[\s,]*)+"
)
# Not a statement about the real world: "my spider has 6 legs", "in my game penguins can fly"
_NOT_REAL_RE = re.compile(
    r"\b(?:my|your|his|her|their|our|pretend|imagine|imagined|if|wish|story|game|dream|dreamed|cartoon|movie"
    r"|book|minecraft|roblox|show|toy|stuffed|drawing|joke|kidding|jk|lol|haha|maybe|might|some|sometimes"
    r"|this|that|these|those|one of)\b"
)
_QUESTION_RE = re.compile(r"(?:do|does|did|is|are|can|could|how|what|why|which|who|where|when|will|would|should)\b")


def fact_text(message: str) -> str:
    """The message lowercased, without apostrophes and punctuation"""
    text = re.sub(r"[^\w ]+", " ", message.lower().replace("'", "").replace("\u2019", ""))
    return " ".join(text.split())


class FactBase:
    def __init__(self, data: Dict):
        self.data = data
        self.numbers: Dict[str, int] = data.get("numbers", {})
        self.replies: Dict[str, List[str]] = data.get("replies", {})
        self.sets: Dict[str, List[str]] = {name: values for name, values in data.get("sets", {}).items()}
        self.facts: List[Dict] = list(data.get("facts", [])) + list(data.get("generated", []))
        number_words = "|".join(sorted(self.numbers, key=len, reverse=True))
        self._number = rf"(?:only |just |exactly |like |about )?(?P<n>\d+|{number_words})"
        self._ordered: List[Tuple[Dict, "re.Pattern"]] = []  # count, there_are and can facts
        # value -> [(fact, subject pattern, whether the value is right)], in file order
        self._is_index: Dict[str, List[Tuple[Dict, "re.Pattern", bool]]] = {}
        subjects: Dict[str, "re.Pattern"] = {}
        self._values: Dict[str, Tuple[set, set]] = {}  # "is" fact id -> (right values, wrong values)
        for fact in self.facts:
            if fact["type"] == "is":
                subject = subjects.get(fact["subject"]) or subjects.setdefault(
                    fact["subject"], re.compile(fact["subject"]))
                true = set(fact["true"])
                false = set(fact.get("false", []))
                for name in fact.get("false_from", []):
                    false.update(v for v in self.sets[name] if v not in true)
                self._values[fact["id"]] = (true, false - true)
                for value in true:
                    self._is_index.setdefault(value, []).append((fact, subject, True))
                for value in false - true:
                    self._is_index.setdefault(value, []).append((fact, subject, False))
            else:
                self._ordered.append((fact, self._pattern(fact)))

    @classmethod
    def load(cls, path: Path) -> "FactBase":
        """The facts in a file, compiled once per version of the file"""
        if not path.exists():
            return cls({"facts": []})
        key = (str(path), path.stat().st_mtime)
        if key not in _CACHE:
            _CACHE[key] = cls(json.loads(path.read_text(encoding="utf-8")))
        return _CACHE[key]

    def _pattern(self, fact: Dict) -> "re.Pattern":
        adverb = r"(?:only |just |really |actually |all |also |even )?"
        if fact["type"] == "count":
            return re.compile(rf"{fact['subject']} {adverb}(?P<neg>(?:do not|dont|doesnt|does not) )?"
                              rf"(?:have|has|got|have got|has got|get) {self._number} {fact['noun']}")
        if fact["type"] == "there_are":
            return re.compile(rf"there (?:are|is|r|re)(?P<neg>nt| not)? {self._number} {fact['noun']}")
        if fact["type"] == "can":
            return re.compile(rf"{fact['subject']} {adverb}(?P<mod>can not |cannot |cant |can |could |couldnt |dont "
                              rf"|do not |doesnt |does not )?(?:really )?{fact['verb']}{_CAN_ENDINGS}")
        raise ValueError(f"Unknown fact type {fact['type']!r} for {fact['id']}")

    def judge_value(self, fact: Dict, value: str) -> Optional[bool]:
        """Whether a value is right for an "is" fact ("canberra" for the capital of Australia), None if unknown"""
        true, false = self._values.get(fact["id"], (set(), set()))
        for said in dict.fromkeys((value, _IS_ADVERBS_RE.sub("", value))):
            if said in true:
                return True
            if said in false:
                return False
        return None

    def number(self, word: str) -> int:
        return int(word) if word.isdigit() else self.numbers[word]

    def check_message(self, message: str) -> Optional[Tuple[Dict, bool]]:
        """
        (fact, right) when the message states something about a fact: right is False for
        "spiders have 6 legs", True for "spiders have 8 legs". None for anything else,
        including questions and pretend or personal statements ("my spider has 6 legs").
        """
        if message.strip().endswith("?"):
            return None
        text = FACT_OPENERS_RE.sub("", fact_text(message)).strip()
        if not text or len(text.split()) > 14 or _NOT_REAL_RE.search(text) or _QUESTION_RE.match(text):
            return None
        return self.check(text)

    def check(self, text: str) -> Optional[Tuple[Dict, bool]]:
        """
        (fact, right) for a statement (lowercase, no punctuation or apostrophes, openers
        removed) that says something about a fact, else None
        """
        for fact, pattern in self._ordered:
            match = pattern.fullmatch(text)
            if not match:
                continue
            groups = match.groupdict()
            if fact["type"] == "can":
                says_can = (groups.get("mod") or "").strip() not in _NEGATED_MODALS
                return fact, says_can == fact["value"]
            negated = bool((groups.get("neg") or "").strip())
            accepted = fact["value"] if isinstance(fact["value"], list) else [fact["value"]]
            return fact, (self.number(groups["n"]) in accepted) != negated
        matches = list(_IS_RE.finditer(text))
        # "venus is the hottest planet" is also read the other way around, as "the hottest planet
        # is venus", so it is checked against that fact
        for swapped in (False, True):
            for match in matches:
                subject, value = text[:match.start()], text[match.end():]
                if swapped:
                    subject, value = value, subject
                negated = bool(match.group("neg"))
                for said in dict.fromkeys((value, _IS_ADVERBS_RE.sub("", value))):
                    for fact, pattern, right in self._is_index.get(said, []):
                        if pattern.fullmatch(subject):
                            return fact, right != negated
        return None
