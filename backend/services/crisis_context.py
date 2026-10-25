"""
Crisis Context
Reads the context of crisis phrases that also have everyday meanings, so they are not
answered with an abuse hotline when the child means something else:

- "My sister always beats me" while talking about Mario Kart: she wins at games.
  Without a game nearby, a sibling or friend "beating" the child is asked about first.
- "It makes me scared" (a thunderstorm, parents arguing): fear of something, not of a person.
- "Kids at school push me": bullying by other kids, not abuse by a caregiver.

Only messages whose crisis phrases are all of these kinds are reinterpreted. Any other
crisis phrase ("he hits me", "my dad beats me", "beat me up") keeps the crisis response.
"""

import re
from typing import Iterable, Optional

# Phrases that can mean winning a game
WIN_PHRASES = {"beat me", "beats me", "beating me"}

# Physical phrases that are bullying when other kids do them
PEER_PHYSICAL_PHRASES = {
    "push me", "pushes me", "pushed me", "shove me", "shoves me", "shoved me",
    "hit me", "hits me", "hitting me", "kick me", "kicks me", "kicking me", "kicked me",
    "punch me", "punches me", "punching me", "punched me", "slap me", "slaps me", "slapping me",
    "slapped me", "smack me", "smacks me", "smacking me", "smacked me", "throw me", "throws me",
    "threw me", "hurt me", "hurts me", "hurting me",
}

# Fear phrases that can be about a thing or event rather than a person
FEAR_PHRASES = {"makes me scared", "makes me afraid", "scared of them", "afraid of them",
                "scared of him", "afraid of him", "scared of her", "afraid of her"}

_GAME_WORDS = {
    "game", "games", "gaming", "play", "plays", "playing", "played", "match", "race", "races", "racing",
    "chess", "checkers", "cards", "uno", "monopoly", "minecraft", "fortnite", "roblox", "mario", "kart",
    "pokemon", "zelda", "video", "level", "levels", "score", "scores", "points", "won", "win", "wins",
    "xbox", "playstation", "nintendo", "switch", "controller", "tag", "soccer", "basketball", "football",
    "baseball", "tennis", "swimming", "running", "contest", "competition", "tournament", "round",
    "smash", "yoshi", "board", "dodgeball", "ball", "wrestling", "wrestle", "wrestled", "tackle",
    "dodge", "frisbee", "pillow", "tickle", "tickling", "hockey", "volleyball", "kickball",
}

_SOFT_OBJECTS = (r"\bwith (a|the|his|her|their|my) (ball|dodgeball|frisbee|pillow|balloon|water balloon|"
                 r"snowball|nerf \w+|foam \w+|beach ball|stuffed animal|plushie)\b")

_PLAY_PUSHES = (r"\bpush(ed|es|ing)? me (on|in|around in) (the|a|my|his|her) (swings?|tire swing|wagon|sled|stroller|"
                r"cart|merry-go-round|scooter|go-kart|wheelbarrow|chair)\b")

_PEERS = re.compile(
    r"\b(kids?|boys?|girls?|classmates?|students?|bull(y|ies)|other kids|someone at school|"
    r"people at school|everyone at school|older kids)\b|\bat (school|recess|lunch|the playground|practice)\b|"
    r"\bon the bus\b"
)
_ADULTS_AND_FAMILY = re.compile(
    r"\b(mom|mommy|mother|dad|daddy|father|stepmom|stepdad|stepmother|stepfather|parents?|uncle|aunt|"
    r"grandma|grandpa|grandmother|grandfather|babysitter|teacher|coach|adult|grown-?up|man|woman|"
    r"brother|sister|cousin)\b"
)
# Who might "beat" the child at a game: worth asking about rather than assuming abuse
_PLAYMATES = re.compile(r"\b(sister|brother|sis|bro|cousin|friend|bff|he|she|they|[A-Z][a-z]+)\b")
_GROWN_UPS = re.compile(
    r"\b(mom|mommy|mother|dad|daddy|father|stepmom|stepdad|parents?|uncle|aunt|grandma|grandpa|"
    r"babysitter|teacher|coach)\b"
)
_PERSON_SUBJECTS = {"he", "she", "they", "him", "her", "them", "mom", "dad", "mommy", "daddy", "mother",
                    "father", "brother", "sister", "uncle", "aunt", "teacher", "coach", "babysitter",
                    "stepdad", "stepmom", "grandpa", "grandma", "parents", "cousin"}

_VIOLENCE_ANSWER = re.compile(
    r"\b(hit|hits|hitting|hurt|hurts|hurting|punch\w*|kick\w*|slap\w*|smack\w*|push\w*|shove\w*|"
    r"bruise\w*|yes|yeah|yep|both|for real|really does)\b"
)
_GAME_ANSWER = re.compile(
    r"\b(no|nope|nah|game|games|play|plays|playing|win|wins|won|winning|at|race|match|just|chess|cards|"
    r"minecraft|fortnite|roblox|mario|video)\b"
)


def _words(text: str) -> set:
    return set(re.findall(r"[a-z']+", text.lower()))


def _subject_before(text: str, phrase: str) -> Optional[str]:
    """The word before a phrase: "it" in "it makes me scared" """
    match = re.search(rf"(\w+)\s+(?:always\s+|really\s+|just\s+|kind of\s+|sometimes\s+)?{re.escape(phrase)}",
                      text.lower())
    return match.group(1) if match else None


def classify(message: str, matched: Iterable[str], recent_messages: Iterable[str] = (),
             resolved_message: Optional[str] = None, known_people: Iterable[str] = ()) -> str:
    """
    How to treat a message with crisis phrases

    Args:
        message: The child's message
        matched: The crisis phrases found in it
        recent_messages: The child's previous few messages, for game talk
        resolved_message: The message with pronouns resolved ("it" -> "the storm")
        known_people: Names of people the child mentioned recently

    Returns:
        "crisis" (keep the crisis response), "game" (winning at a game: no safety response),
        "clarify" (ask whether it means games or hitting), "peer_bullying" (bullying response),
        or "indirect_fear" (fear of something: comfort and advice to tell a grown-up)
    """
    matched = set(matched)
    text = message.lower()
    if not matched:
        return "crisis"

    if matched <= WIN_PHRASES and not re.search(r"\bbeat(s|ing)? me up\b", text):
        if re.search(r"\bbeat(s|ing)? me (at|in)\b", text):
            return "game"
        # A grown-up who beats the child is not read as a game, even after game talk ("my dad
        # beats me when he gets mad that i play video games")
        if _GROWN_UPS.search(text):
            return "crisis"
        context_words = _words(" ".join([message, *recent_messages]))
        if context_words & _GAME_WORDS:
            return "game"
        if _PLAYMATES.search(message):
            return "clarify"
        return "crisis"

    # "My sister hit me with a pillow", "a kid hit me with the ball": play, whoever did it
    if matched <= PEER_PHYSICAL_PHRASES and re.search(_SOFT_OBJECTS, text):
        return "game"
    # "My brother pushed me on the swing": helping on playground things
    if matched <= PEER_PHYSICAL_PHRASES and re.search(_PLAY_PUSHES, text):
        return "game"

    if matched <= PEER_PHYSICAL_PHRASES and _PEERS.search(text) and not _ADULTS_AND_FAMILY.search(text):
        # A game named in the same message ("we were wrestling and he pinned me"); earlier
        # game talk is not enough, so pushing at recess still counts as bullying
        if _words(message) & (_GAME_WORDS - {"play", "plays", "playing", "played"}) and \
                not re.search(r"\b(on purpose|every day|always|bull(y|ies)|mean)\b", text):
            return "game"
        return "peer_bullying"

    if matched <= FEAR_PHRASES:
        known = {p.lower() for p in known_people}
        for phrase in matched:
            if phrase.startswith("makes me"):
                subject = _subject_before(text, phrase)
                if subject is None or subject in _PERSON_SUBJECTS or subject in known:
                    return "crisis"
            else:
                # "scared of them": who or what "them" is
                pronoun = phrase.split()[-1]
                resolved = (resolved_message or "").lower()
                if not resolved or re.search(rf"\bof {pronoun}\b", resolved):
                    return "crisis"  # not resolved to anything: could be a person
                after = resolved.split(" of ", 1)[-1]
                if _ADULTS_AND_FAMILY.search(after) or any(name in after for name in known):
                    return "crisis"
        return "indirect_fear"

    return "crisis"


def clarification_question(message: str) -> str:
    """ "Do you mean your sister wins when you play games, or that she hits you?" """
    match = re.search(r"\b(my \w+|[A-Z][a-z]+|he|she|they)\s+(?:always\s+|just\s+|sometimes\s+)?beat", message,
                      re.IGNORECASE)
    who = match.group(1) if match else "they"
    pronoun = {"he": "he", "she": "she", "they": "they"}.get(who.lower())
    if who.lower().startswith("my "):
        relation = who.split()[1].lower()
        pronoun = {"sister": "she", "sis": "she", "brother": "he", "bro": "he"}.get(relation, "they")
        who = f"your {relation}"
    elif pronoun is None:
        pronoun = "they"
    wins = "win" if pronoun == "they" else "wins"
    hits = "hit" if pronoun == "they" else "hits"
    return (f"Hmm, do you mean {who} {wins} when you play games together, or that {pronoun} {hits} you? "
            "You can tell me either way.")


def clarification_answer(answer: str) -> str:
    """ "violence", "game" or "unclear" for the child's answer to the clarification question"""
    text = answer.lower()
    if _VIOLENCE_ANSWER.search(text) and not re.search(r"\b(no|not|never|doesn't|doesnt|don't|dont)\b", text):
        return "violence"
    if _GAME_ANSWER.search(text):
        return "game"
    return "unclear"


def indirect_fear_reply(message: str, recent_messages: Iterable[str] = (), resolved_message: Optional[str] = None) -> str:
    """Comfort and advice for being scared of something (not of a person)"""
    context = " ".join([message, *recent_messages]).lower()
    if re.search(r"\b(parents?|mom|dad|mommy|daddy)\b", context) and \
            re.search(r"\b(fight\w*|argu\w*|yell\w*|scream\w*|shout\w*)\b", context):
        return ("It's really scary when parents argue, and it's not your fault. It can help to tell "
                "someone you trust how you feel, like your mom or dad when things are calm, another "
                "family member, or your school counselor. Do you want to talk about it?")
    source = _fear_source(resolved_message or "")
    if source:
        return (f"It's okay to be scared of {source}. When something scares you, it can really help to tell "
                "your mom, dad, or another grown-up you trust. They can help you feel safe. "
                "Do you want to talk about it?")
    return ("It's okay to feel scared. When something scares you, it can really help to tell your mom, "
            "dad, or another grown-up you trust. They can help you feel safe. What's scaring you?")


def _fear_source(resolved: str) -> Optional[str]:
    """ "the thunderstorm" from "The thunderstorm makes me scared" or "I'm scared of spiders" """
    match = re.match(r"\s*(.+?) makes? me (?:so |really |very )?(?:scared|afraid)", resolved, re.IGNORECASE) or \
        re.search(r"\b(?:scared|afraid) of (.+?)[.!?]*$", resolved, re.IGNORECASE)
    if not match:
        return None
    source = match.group(1).strip()
    if source.lower() in ("it", "that", "this", "them", "him", "her", "they"):
        return None
    source = re.sub(r"\bmy\b", "your", source[:1].lower() + source[1:])
    return source


CLARIFY_REPLY_GAME = "Oh, I see! Losing can be really frustrating. What do you like to play together?"
CLARIFY_REPLY_UNCLEAR = ("Okay! If anyone ever hurts you, please tell a grown-up you trust right away. "
                         "What do you like to play together?")

