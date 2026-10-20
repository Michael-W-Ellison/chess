"""
Reference Tracker
Resolves pronouns in a message to the people and things mentioned in earlier turns

Before rules are matched, third-person pronouns are replaced with what they refer to:

    turn 1: "My best friend Maya moved away"
    turn 2: "She said she would call me"  ->  "My best friend Maya said she would call me"

Only the first matching pronoun per person is replaced; later ones are left as they are.

The tracker keeps, per user, the people (name, relation, plural, the pronoun the child used
for them) and things mentioned recently. Entries older than MAX_AGE turns are ignored.
"it", "that" and "this" are only resolved where they clearly refer back to a thing:
as the subject of "was fun/hard/..." or the object of like/love/hate. "It is raining"
is left alone.

The bot always refers to people by name or relation in its replies, so it never has to
guess anyone's pronouns itself.
"""

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional

MAX_AGE = 3  # turns a person or thing stays available as an antecedent

_PERSON_PRONOUNS = {
    "he": "he", "him": "he", "his": "he",
    "she": "she", "her": "she", "hers": "she",
    "they": "they", "them": "they", "their": "they", "theirs": "they",
}
_THING_PRONOUNS = {"it", "that", "this"}
_POSSESSIVE_FORMS = {"his", "hers", "their", "theirs"}
_TIME_WORDS = {"today", "tomorrow", "yesterday", "tonight", "morning", "afternoon", "evening",
               "night", "week", "weekend", "month", "year", "time", "day", "lot", "thing", "something"}
_PREFERENCE_VERBS = {"like", "love", "enjoy", "adore", "hate", "dislike"}
# Verbs whose object is usually a person, for names spaCy does not tag ("I saw Maya at school")
_SOCIAL_VERBS = {"see", "meet", "visit", "call", "text", "hug", "help", "invite", "ask", "tell", "miss", "beat", "follow"}


@dataclass
class Person:
    name: Optional[str] = None
    relation: Optional[str] = None
    plural: bool = False
    pronoun: Optional[str] = None  # learned from the child's own usage
    turn: int = 0

    def phrase(self, possessive: bool = False) -> str:
        """How the person is written in place of a pronoun (from the child's point of view)"""
        if self.relation and self.name:
            base = f"my {self.relation} {self.name}"
        elif self.relation:
            base = f"my {self.relation}"
        else:
            base = self.name or ""
        if possessive:
            base += "'" if base.endswith("s") else "'s"
        return base

    def matches(self, other: "Person") -> bool:
        if self.name and other.name:
            return self.name.lower() == other.name.lower()
        return bool(self.relation and other.relation and self.relation.lower() == other.relation.lower())


@dataclass
class Thing:
    text: str
    turn: int = 0


@dataclass
class DiscourseState:
    turn: int = 0
    people: List[Person] = field(default_factory=list)  # most recent first
    things: List[Thing] = field(default_factory=list)  # most recent first


class ReferenceTracker:
    """Per-user record of recent people and things, used to resolve pronouns"""

    def __init__(self, parser, relations: Iterable[str], common_capitalized: Iterable[str] = ()):
        self.parser = parser
        self.relations = set(relations)
        self.common_capitalized = set(common_capitalized)
        self._states: Dict[int, DiscourseState] = {}

    def reset(self, user_id: int) -> None:
        """Forget all references for a user (e.g. when a new conversation starts)"""
        self._states.pop(user_id, None)

    def state(self, user_id: int) -> DiscourseState:
        return self._states.setdefault(user_id, DiscourseState())

    def resolve(self, message: str, user_id: int) -> str:
        """
        Replace pronouns with their antecedents, then record the people and things this
        message mentions for later turns. Call once per turn.

        Returns:
            The message with resolved references (normalized), or the original message if
            the parser is unavailable
        """
        doc = self.parser.parse(message)
        if doc is None:
            return message

        state = self.state(user_id)
        state.turn += 1

        parts = []
        resolved_people = set()
        for token in doc:
            replacement = self._antecedent(token, state, resolved_people)
            parts.append((replacement if replacement is not None else token.text) + token.whitespace_)
        resolved = "".join(parts)

        resolved_doc = self.parser.parse(resolved) if resolved != doc.text else doc
        self._record(resolved_doc, state)
        return resolved

    # ------------------------------------------------------------------
    # Resolution
    # ------------------------------------------------------------------

    def _recent_people(self, state: DiscourseState) -> List[Person]:
        return [p for p in state.people if state.turn - p.turn <= MAX_AGE]

    def _antecedent(self, token, state: DiscourseState, resolved_people: set) -> Optional[str]:
        lower = token.lower_

        if lower in _PERSON_PRONOUNS and token.pos_ == "PRON":
            gender = _PERSON_PRONOUNS[lower]
            people = self._recent_people(state)
            if gender == "they":
                candidates = [p for p in people if p.plural]
            else:
                candidates = [p for p in people if not p.plural and p.pronoun in (None, gender)]
            if not candidates:
                return None
            # Most recent turn first; within a turn, someone the child already called "she"/"he"
            candidates.sort(key=lambda p: (-p.turn, p.pronoun != gender))
            person = candidates[0]
            if gender != "they":
                person.pronoun = gender
            person.turn = state.turn
            # Replace only the first mention; "Maya said she would call" keeps the second "she"
            if id(person) in resolved_people:
                return None
            resolved_people.add(id(person))
            possessive = lower in _POSSESSIVE_FORMS or (lower == "her" and token.dep_ == "poss")
            return self._match_case(person.phrase(possessive), token)

        if lower in _THING_PRONOUNS and self._is_thing_reference(token):
            things = [t for t in state.things if state.turn - t.turn <= MAX_AGE]
            if things:
                things[0].turn = state.turn
                return self._match_case(things[0].text, token)

        return None

    @staticmethod
    def _is_thing_reference(token) -> bool:
        """Subject of "was fun"/"is hard", or object of like/love/hate"""
        head = token.head
        if token.dep_ == "nsubj" and head.lemma_ == "be":
            return any(c.dep_ in ("acomp", "attr") for c in head.children)
        if token.dep_ == "dobj" and head.lemma_ in _PREFERENCE_VERBS:
            return True
        return False

    @staticmethod
    def _match_case(phrase: str, token) -> str:
        if token.is_sent_start:
            return phrase[:1].upper() + phrase[1:]
        return phrase

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------

    def _record(self, doc, state: DiscourseState) -> None:
        mentioned: List[Person] = []
        named_tokens = set()

        for token in doc:
            # "my best friend Maya", "my parents", "Jake is my brother"
            if token.lemma_.lower() in self.relations and any(
                c.dep_ == "poss" and c.lower_ in ("my", "our") for c in token.children
            ):
                relation = " ".join(t.text for t in token.subtree
                                    if t == token or (t.head == token and t.dep_ in ("amod", "compound")))
                name_token = next((c for c in token.children if c.dep_ == "appos" and c.pos_ == "PROPN"), None)
                if name_token is None and token.dep_ == "attr" and token.head.lemma_ == "be":
                    name_token = next((c for c in token.head.children
                                       if c.dep_ == "nsubj" and c.pos_ == "PROPN"), None)
                if name_token is not None:
                    named_tokens.add(name_token.i)
                mentioned.append(Person(
                    name=name_token.text if name_token is not None else None,
                    relation=relation.lower(),
                    plural=token.tag_ == "NNS",
                ))

        for token in doc:
            # Names on their own: "I played with Maya", "Maya and Jake came over"
            if token.i in named_tokens or token.pos_ != "PROPN" or self._is_childs_own_name(token):
                continue
            if not self._is_person_name(token):
                continue
            mentioned.append(Person(name=token.text))
            group = [c for c in token.conjuncts if c.pos_ == "PROPN"]
            if group and token.dep_ != "conj":
                names = [token.text, *(c.text for c in group)]
                mentioned.append(Person(name=" and ".join(names), plural=True))

        for person in mentioned:
            self._remember_person(person, state)

        things = []
        for chunk in doc.noun_chunks:
            root = chunk.root
            if (root.pos_ == "NOUN" and root.dep_ in ("dobj", "pobj", "nsubj", "attr")
                    and root.lemma_.lower() not in self.relations
                    and root.lemma_.lower() not in _TIME_WORDS):
                # Keep determiners, possessives and compounds ("my math test"), not adjectives
                words = [t.text for t in chunk if t == root or t.dep_ in ("det", "poss", "compound", "nummod")]
                # "a math test" is referred back to as "the math test"
                if words and words[0].lower() in ("a", "an"):
                    words[0] = "the"
                elif chunk.start == chunk.sent.start:
                    words[0] = words[0][:1].lower() + words[0][1:]
                things.append(Thing(text=" ".join(words), turn=state.turn))
        for thing in things:  # last mentioned ends up first
            state.things = [t for t in state.things if t.text.lower() != thing.text.lower()]
            state.things.insert(0, thing)
        del state.things[5:]

    def _is_person_name(self, token) -> bool:
        """A proper noun that names a person (spaCy's tag, or its position when untagged)"""
        if token.ent_type_ == "PERSON":
            return True
        if token.dep_ == "conj" and token.head.pos_ == "PROPN":
            return self._is_person_name(token.head)
        # Places, dates, products and "School" are not people. ORG is allowed: the small
        # English model often tags first names as organizations ("I played with Zoe").
        if (token.ent_type_ and token.ent_type_ != "ORG") or token.lower_ in self.common_capitalized:
            return False
        head = token.head
        return (token.dep_ == "nsubj"
                or (token.dep_ == "pobj" and head.lower_ == "with")
                or (token.dep_ == "dobj" and head.lemma_ in _SOCIAL_VERBS))

    @staticmethod
    def _is_childs_own_name(token) -> bool:
        """The child's own name in "my name is Sam" is not a third person"""
        head = token.head
        return head.lemma_ == "be" and any(
            c.dep_ == "nsubj" and c.lower_ == "name" for c in head.children)

    @staticmethod
    def _remember_person(person: Person, state: DiscourseState) -> None:
        for existing in state.people:
            if existing.matches(person) or (
                person.name and existing.name and existing.name.lower() == person.name.lower()
            ):
                existing.name = existing.name or person.name
                existing.relation = existing.relation or person.relation
                existing.turn = state.turn
                state.people.remove(existing)
                state.people.insert(0, existing)
                return
        person.turn = state.turn
        state.people.insert(0, person)
        del state.people[10:]
