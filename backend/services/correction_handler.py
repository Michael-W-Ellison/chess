"""
Corrections from the child: "no its Sammy", "oops his name is Rex", "I meant a cat",
"I didn't say that", "that's not my name", "my name isn't Lily".

detect() reads the message on its own and says what kind of correction it is and the new
value, if it names one. MemoryManager.apply_correction() decides what the correction is
about: the memories written for the child's previous message (or the child's stored name),
and changes or removes them. reply() says what the bot now remembers.
"""

import re
from dataclasses import dataclass
from typing import Optional

# Kinds of correction
REPLACE = "replace"  # "no its Sammy": the last memory gets a new value
RETRACT = "retract"  # "I didn't say that": the last memory is removed
NOT_NAME = "not_name"  # "that's not my name": the stored name is removed

_CUE = (r"(?:no+|nope|nah|oops+|whoops|oopsie|sorry|actually|wait|no wait|jk|j/k|just kidding|"
        r"i mean|i meant|i said|i ment)")
# "no, it's Sammy", "oops i meant a cat", "actually its green", "i said frogs"
_REPLACE_RE = re.compile(rf"^(?:{_CUE}\b[\s,!.]*)+(?P<rest>.+)$")
# "not dogs, cats", "not dogs its cats", "not max rex"
_NOT_X_Y_RE = re.compile(
    r"^(?:no+[\s,!.]+)?not (?P<old>[a-z0-9 ]{1,30}?)(?:[\s,!.]+(?:but |its |it is )?)(?P<rest>[a-z0-9 ]+)$"
)
# "his name is actually rex"
_ACTUALLY_RE = re.compile(r"^(?P<lead>(?:his|her|its|their|my \w+s?) name is) actually (?P<rest>.+)$")
# "i didnt say that", "thats not what i said", "no i never said that i said frogs" (not "I didn't
# mean it", an apology)
_RETRACT_RE = re.compile(
    r"^(?:no+[\s,!.]+|nope[\s,!.]+)?(?:i (?:didnt|did not|never|dont|do not) (?:say|said|type|typed)"
    r" (?:that|it|this)|that(?:s| is| was|s not| isnt| wasnt)?(?: not)? what i (?:said|meant|say|mean|typed))"
    r"(?:[\s,!.]+(?P<rest>.*))?$"
)
# "thats not my name", "that isnt my name", "dont call me lily", "my name isnt lily its lila"
_NOT_NAME_RE = re.compile(
    r"^(?:no+[\s,!.]+)?(?:(?:that|thats|that is|its|it is|that isnt|thats not|that is not)\s*(?:not )?my name"
    r"|my name (?:isnt|is not|aint|is nt) (?P<old>[a-z][a-z'-]{0,19})"
    r"|(?:dont|do not) call me (?P<old2>[a-z][a-z'-]{0,19})"
    r"|(?:im|i am) not (?P<old3>[a-z][a-z'-]{0,19}))"
    r"(?:[\s,!.]+(?:but |its |it is |my name is |my names |its actually |call me )?(?P<rest>[a-z][a-z'-]{0,19}))?$"
)
# Words that open the value part ("it's Sammy", "his name is Rex")
_VALUE_LEAD_RE = re.compile(
    r"^(?:(?:it|its|it is|it was|thats|that is|that was|his|her|their|its|the|my|my \w+s?)\s*name(?:s| is| was)"
    r"|its|it is|it was|thats|that is|i meant|i mean|i said|i ment|actually|its actually|it was actually)\s+"
)
# Words that make the rest a sentence, not a value ("no she works there")
_CLAUSE_WORDS = {
    "i", "im", "ive", "id", "me", "you", "youre", "he", "hes", "she", "shes", "they", "theyre", "we",
    "were", "it", "is", "was", "are", "am", "be", "been", "do", "does", "did", "didnt", "dont", "doesnt",
    "not", "have", "has", "had", "can", "cant", "will", "wont", "would", "should", "could", "there",
    "this", "that", "what", "why", "how", "who", "when", "where", "works", "work", "went", "go", "goes",
    "like", "likes", "love", "hate", "want", "got", "get", "said", "say", "mean", "meant", "just", "kidding",
    "joking", "too", "so", "very", "really", "okay", "ok", "yes", "yeah", "no", "nothing", "never", "anymore",
    "lol", "haha", "jk", "wrong", "right", "true", "false", "sorry", "thanks", "thank", "please", "way",
    "problem", "fair", "more", "worries", "idea", "clue", "one", "body", "fun", "u", "ur", "your", "to", "at",
    "with", "for", "in", "on", "from", "about", "of", "by", "and", "but", "because", "cuz", "if",
}
_DETERMINERS = ("a", "an", "the", "my", "some", "two", "three")
_NUMBER_WORDS = {"one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven",
                 "twelve", "thirteen", "fourteen", "fifteen"}
_MAX_VALUE_WORDS = 4


@dataclass
class Correction:
    kind: str
    value: Optional[str] = None  # the new value ("Sammy", "a cat"), if the message names one
    old: Optional[str] = None  # the value the child says is wrong ("Lily" in "my name isn't Lily")
    about_name: bool = False  # the message says "name" ("his name is Rex")
    plain_no: bool = False  # opens with only "no" ("no, burgers"), which can answer a yes/no question


def _clean(message: str) -> str:
    text = re.sub(r"[’'`]", "", message.lower())
    return re.sub(r"\s+", " ", text).strip(" .!?~")


def _value(rest: Optional[str]) -> Optional[str]:
    """The new value at the start of the rest of a correction, or None if the rest is a sentence"""
    if not rest:
        return None
    text = rest.strip(" ,.!?")
    for _ in range(3):  # "its actually", "his name is actually"
        text = _VALUE_LEAD_RE.sub("", text, count=1)
    text = re.sub(r"\s+(?:not \w+|lol|haha|sorry|oops)$", "", text).strip(" ,.!?")
    words = text.split()
    if not words or len(words) > _MAX_VALUE_WORDS or any(w in _CLAUSE_WORDS for w in words):
        return None
    return text


def detect(message: str) -> Optional[Correction]:
    """The correction this message makes, if it is one"""
    text = _clean(message)
    if not text:
        return None
    match = _NOT_NAME_RE.match(text)
    if match:
        old = match.group("old") or match.group("old2") or match.group("old3")
        if old in _CLAUSE_WORDS:
            return None  # "im not sad" is checked against the stored name by the caller
        return Correction(NOT_NAME, value=_value(match.group("rest")), old=old, about_name=True)
    match = _RETRACT_RE.match(text)
    if match:
        return Correction(RETRACT, value=_value(match.group("rest")))
    match = _ACTUALLY_RE.match(text)
    if match:
        return Correction(REPLACE, value=_value(match.group("rest")), about_name=True)
    match = _NOT_X_Y_RE.match(text)
    if match and _value(match.group("old")):
        value = _value(match.group("rest"))
        return Correction(REPLACE, value=value, old=match.group("old")) if value else None
    match = _REPLACE_RE.match(text)
    if match:
        rest = match.group("rest")
        plain_no = re.match(r"^(?:no+|nope|nah)\b[\s,!.]*(?![\s,!.]|(?:wait|oops|actually|i meant|i mean|i said)\b)", text)
        return Correction(REPLACE, value=_value(rest), about_name=bool(re.search(r"\bname", rest)),
                          plain_no=bool(plain_no))
    return None


_YES_NO_RE = re.compile(
    r"(?:^|[.!?]\s+)(?:do|does|did|is|are|was|were|can|could|will|would|have|has|had|should|want|wanna|ever|"
    r"you|any|anything|got)\b[^.!?]*\?", re.IGNORECASE
)


def asks_yes_no(reply: Optional[str]) -> bool:
    """Whether the bot's reply asked a yes/no question ("Do you like tacos too?")"""
    return bool(reply and _YES_NO_RE.search(reply))


def answer(message: str) -> Optional[Correction]:
    """The answer to "What did you mean?" after "I didn't say that" ("frogs", "I said frogs")"""
    correction = detect(message)
    if correction is not None:
        return correction
    value = _value(_clean(message))
    return Correction(REPLACE, value=value) if value else None


def same_kind(old: str, new: str) -> bool:
    """Whether a new value can stand in for an old one: a name for a name, "a cat" for "a dog", 8 for 7"""
    old_words, new_words = old.lower().split(), new.lower().split()
    if not old_words or not new_words:
        return False
    if old_words[0].isdigit() or old_words[0] in _NUMBER_WORDS:
        return new_words[0].isdigit() or new_words[0] in _NUMBER_WORDS
    return (old_words[0] in _DETERMINERS) == (new_words[0] in _DETERMINERS)


def styled(new: str, old: str) -> str:
    """The new value written like the old one ("rex" for "Max" -> "Rex")"""
    if old[:1].isupper() and new[:1].islower():
        return " ".join(w[:1].upper() + w[1:] for w in new.split())
    return new


def _person_relation(key: str, value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return key[: -len(slug) - 1].replace("_", " ") if slug and key.endswith("_" + slug) else key.replace("_", " ")


def reply(category: str, key: str, value: str) -> str:
    """What the bot says after correcting a memory"""
    if category == "basic" and key == "name":
        return f"Oops, sorry, {value}! I'll remember your name is {value}."
    if category == "basic" and key == "age":
        return f"Oops, got it! You're {value}. I'll remember that."
    if category == "person":
        return f"Oops, got it! Your {_person_relation(key, value)} is named {value}. I'll remember that."
    if key.startswith("has_"):
        return f"Oops, got it! You have {value}. I'll remember that."
    if key.startswith("likes_"):
        return f"Oops, got it! You like {value}. I'll remember that."
    if key.startswith("dislikes_"):
        return f"Oops, got it! You don't like {value}. I'll remember that."
    if key.startswith("favorite_"):
        return f"Oops, got it! Your favorite {key[len('favorite_'):].replace('_', ' ')} is {value}. I'll remember that."
    return f"Oops, got it: {value}! I'll remember that."


RETRACTED_REPLY = "Oops, sorry! I got that wrong, so I'll forget it. What did you mean?"
MISUNDERSTOOD_REPLY = "Oops, sorry! I must have misunderstood. What did you mean?"
NAME_REMOVED_REPLY = "Oops, sorry! I got your name wrong. What's your name?"
