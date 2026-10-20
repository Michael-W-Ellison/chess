"""
Reference Tracker
Resolves pronouns in a message to the people, things and events mentioned in earlier turns

Before rules are matched, third-person pronouns are replaced with what they refer to:

    turn 1: "My best friend Maya moved away"
    turn 2: "She said she would call me"  ->  "My best friend Maya said she would call me"

    turn 1: "We went swimming"
    turn 2: "That was so fun"             ->  "Going swimming was so fun"

    turn 1: "My dad got mad"
    turn 2: "That was scary"              ->  "My dad getting mad was scary"

    bot:    "...Did you know? Sea otters hold hands while sleeping!"
    child:  "That's so cool"              ->  "Your fun fact is so cool"

Only the first matching pronoun per person is replaced; later ones are left as they are.

The tracker keeps, per user:
- people (name, relation, plural, their pronoun if known),
- things (noun phrases from the child's messages and new ones from the bot's replies),
- events (the last action the child told about, as phrases like "going to the zoo" or
  "my dad getting mad"),
mentioned in the last MAX_AGE turns.

"it" prefers a thing and "that"/"this" prefer an event or what the bot just said.
In "That's a cool color" the pronoun refers to a recent thing named by the noun if there
is one, even if something else was mentioned after it, and the repeated noun is dropped
("Your favorite color is cool"). In "That's a hard question" it is left as it is.
They are only resolved as a subject, object or object of a preposition, and not in
"It is raining", "It's time to go", "That sounds fun", "I get it", "I made it!",
"I think that...", or "the game that I played".

A person's pronoun is known once the child has used one for them, or from a gendered
relation word ("my mom", "my brother"). If "she"/"he" could mean two or more recent people
whose pronouns are not known (and no more recent person is known to be "she"/"he"),
nothing is guessed: the pronoun stays, ambiguous_options() names the people so
the bot can ask "Do you mean Maya or Jake?", and if the child answers with one of the
names, the earlier message is resolved with that person.

The bot always refers to people by name or relation in its replies, so it never has to
guess anyone's pronouns itself.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple

MAX_AGE = 3  # turns a person, thing or event stays available as an antecedent

_PERSON_PRONOUNS = {
    "he": "he", "him": "he", "his": "he",
    "she": "she", "her": "she", "hers": "she",
    "they": "they", "them": "they", "their": "they", "theirs": "they",
}
_THING_PRONOUNS = {"it", "that", "this"}
_EVENT_PRONOUNS = {"that", "this"}
_POSSESSIVE_FORMS = {"his", "hers", "their", "theirs"}
# "That's a hard question" is about the question just asked, which is not tracked
_UNTRACKED_COMPLEMENTS = {"question"}
_GENDERED_RELATIONS = {
    **dict.fromkeys(("mom", "mother", "mum", "mommy", "grandma", "grandmother", "nana", "aunt",
                     "sister", "stepmom", "stepsister"), "she"),
    **dict.fromkeys(("dad", "father", "daddy", "grandpa", "grandfather", "uncle", "brother",
                     "stepdad", "stepbrother"), "he"),
}
_TIME_WORDS = {"today", "tomorrow", "yesterday", "tonight", "morning", "afternoon", "evening",
               "night", "week", "weekend", "month", "year", "time", "day", "lot", "thing", "something",
               "one", "anything", "everything", "nothing"}
# Verbs whose object is usually a person, for names spaCy does not tag ("I saw Maya at school")
_SOCIAL_VERBS = {"see", "meet", "visit", "call", "text", "hug", "help", "invite", "ask", "tell", "miss", "beat", "follow"}
# "it" that refers to nothing: weather ("it is raining"), time ("it's time", "it's late"), turns
_WEATHER_VERBS = {"rain", "snow", "hail", "thunder", "storm", "drizzle", "pour", "sleet"}
_NON_REFERENTIAL_COMPLEMENTS = {"time", "turn", "cold", "hot", "warm", "sunny", "cloudy", "rainy", "windy",
                                "dark", "late", "early", "night", "morning", "raining", "snowing", "freezing"}
_NON_REFERENTIAL_SUBJECT_VERBS = {"seem", "happen", "matter", "depend"}
# "That sounds fun" is a reaction whose reply does not need the referent, and a gerund
# subject is misparsed ("Playing a game sounds fun" makes "fun" an object)
_REACTION_VERBS = {"sound", "look"}
# Idioms with "it" as object: "I made it" (succeeded), "I get it" (understand), "I mean it"
_IDIOM_OBJECT_VERBS = {"make", "get", "take", "mean", "fake", "nail"}
# Verbs that describe a state or wish rather than something the child did
_NON_EVENT_VERBS = {"be", "have", "feel", "think", "want", "like", "love", "know", "need", "hope", "wish",
                    "guess", "mean", "seem", "hate", "enjoy", "say", "tell", "ask", "can", "will"}


def gerund(lemma: str) -> str:
    """"go" -> "going", "swim" -> "swimming", "bake" -> "baking", "lie" -> "lying\""""
    if lemma in ("be", "see", "flee", "agree"):
        return lemma + "ing"
    if lemma.endswith("ie"):
        return lemma[:-2] + "ying"
    if lemma.endswith("e") and not lemma.endswith(("ee", "ye", "oe")) and len(lemma) > 2:
        return lemma[:-1] + "ing"
    # One-syllable consonant-vowel-consonant words double the last letter
    if len(re.findall(r"[aeiou]+", lemma)) == 1 and re.search(r"[^aeiou][aeiou][^aeiouwxy]$", lemma):
        return lemma + lemma[-1] + "ing"
    return lemma + "ing"


@dataclass
class Person:
    name: Optional[str] = None
    relation: Optional[str] = None
    plural: bool = False
    pronoun: Optional[str] = None  # from the child's own usage or a gendered relation word
    turn: int = 0
    order: int = 0  # when first mentioned, for listing people in the order the child named them

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

    def label(self) -> str:
        """How the bot names the person when asking which one the child means"""
        return self.name or f"your {self.relation}"

    def matches(self, other: "Person") -> bool:
        if self.name and other.name:
            return self.name.lower() == other.name.lower()
        return bool(self.relation and other.relation and self.relation.lower() == other.relation.lower())


@dataclass
class Thing:
    text: str
    turn: int = 0
    plural: bool = False
    order: int = 0  # increases with every recorded mention, so later mentions rank first


@dataclass
class Event:
    text: str  # e.g. "going to the zoo"
    turn: int = 0
    order: int = 0
    actor: frozenset = frozenset()  # words naming who did it, if not the child ("dad")


@dataclass
class Ambiguity:
    message: str  # the child's message with the unresolved pronoun
    pronoun: str  # "he" or "she"
    people: List[Person]


@dataclass
class DiscourseState:
    turn: int = 0
    clock: int = 0
    people: List[Person] = field(default_factory=list)  # most recent first
    things: List[Thing] = field(default_factory=list)  # most recent first
    events: List[Event] = field(default_factory=list)  # most recent first
    ambiguity: Optional[Ambiguity] = None
    last_child_words: set = field(default_factory=set)

    def tick(self) -> int:
        self.clock += 1
        return self.clock


class ReferenceTracker:
    """Per-user record of recent people, things and events, used to resolve pronouns"""

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

    def ambiguous_options(self, user_id: int) -> List[str]:
        """Names of the people an unresolved "she"/"he" in the last message could mean"""
        ambiguity = self.state(user_id).ambiguity
        return [p.label() for p in ambiguity.people] if ambiguity else []

    def resolve(self, message: str, user_id: int) -> str:
        """
        Replace pronouns with their antecedents, then record the people, things and events
        this message mentions for later turns. Call once per turn.

        If the previous message had an ambiguous "she"/"he" and this message is a short
        answer naming one of the people ("Maya"), the previous message is returned,
        resolved with that person.

        Returns:
            The message with resolved references (normalized), or the original message if
            the parser is unavailable
        """
        doc = self.parser.parse(message)
        if doc is None:
            return message

        state = self.state(user_id)
        state.turn += 1
        pending, state.ambiguity = state.ambiguity, None

        chosen = self._clarification_answer(doc, pending) if pending else None
        if chosen is not None:
            chosen.pronoun = pending.pronoun
            chosen.turn = state.turn  # ahead of anyone mentioned after them
            doc = self.parser.parse(pending.message)

        parts = []
        resolved_people = set()
        named = {t.lower_ for t in doc}  # words naming who is in this message, for events
        drop = set()  # indexes of words made redundant by a replacement
        replaced_previous = False
        for token in doc:
            if token.i in drop:
                # Keep the dropped word's spacing: "a cool name!" -> "cool!"
                parts[-1] = parts[-1].rstrip() + token.whitespace_
                continue
            replacement = self._antecedent(token, state, resolved_people, doc.text, named, drop)
            if replacement is None and replaced_previous and token.lower_ == "'s" and token.lemma_ == "be":
                # "That's cool" -> "Your fun fact is cool", not the possessive "fact's"
                parts[-1] = parts[-1].rstrip() + " "
                replacement = "is"
            parts.append((replacement if replacement is not None else token.text) + token.whitespace_)
            replaced_previous = replacement is not None
        resolved = "".join(parts)

        resolved_doc = self.parser.parse(resolved) if resolved != doc.text else doc
        self._record(resolved_doc, state)
        return resolved

    def record_bot_reply(self, user_id: int, reply: str, told: Optional[str] = None,
                         mentions: Iterable[str] = ()) -> None:
        """
        Remember what the bot said so the child can refer to it ("That's so cool!").

        Args:
            user_id: User ID
            reply: The bot's reply text (without quirk additions like puns)
            told: "joke" or "fun fact" if the bot told one; it becomes the most recent thing
            mentions: Things the bot offered as its own answer (e.g. its favorite color)
        """
        doc = self.parser.parse(reply)
        state = self.state(user_id)
        if doc is not None:
            for chunk in doc.noun_chunks:
                root = chunk.root
                # Only new things the bot brought up, not echoes of the child's words or
                # anything with "my"/"your" (whose it is depends on who is speaking)
                if (root.pos_ in ("NOUN", "PROPN") and root.ent_type_ != "PERSON"
                        and not any(t.pos_ == "PRON" or t.tag_ in ("WDT", "WP") for t in chunk)
                        and root.lemma_.lower() not in self.relations
                        and root.lemma_.lower() not in _TIME_WORDS
                        and root.lemma_.lower() not in state.last_child_words
                        and not self._describes_bot(root)):
                    self._remember_thing(self._thing_text(chunk), state, plural=root.tag_ in ("NNS", "NNPS"))
        for mention in mentions:
            mention_doc = self.parser.parse(mention)
            plural = mention_doc is not None and mention_doc[:].root.tag_ in ("NNS", "NNPS")
            self._remember_thing(mention, state, plural=plural)
        if told:
            self._remember_thing(f"your {told}", state)

    # ------------------------------------------------------------------
    # Resolution
    # ------------------------------------------------------------------

    def _recent(self, items, state: DiscourseState):
        return [item for item in items if state.turn - item.turn <= MAX_AGE]

    def _antecedent(self, token, state: DiscourseState, resolved_people: set, message: str,
                    named: set, drop: set) -> Optional[str]:
        lower = token.lower_

        if lower in _PERSON_PRONOUNS and token.pos_ == "PRON":
            gender = _PERSON_PRONOUNS[lower]
            people = self._recent(state.people, state)
            if gender == "they":
                candidates = [p for p in people if p.plural]
                if not candidates and lower in ("they", "them"):
                    # "Do you like dinosaurs?" -> "Yes, I love them"
                    things = [t for t in self._recent(state.things, state) if t.plural]
                    if things and self._is_thing_reference(token):
                        return self._match_case(things[0].text, token)
            else:
                candidates = [p for p in people if not p.plural and p.pronoun in (None, gender)]
            if not candidates:
                return None

            # Most recent turn first; within a turn, someone known to be "she"/"he"
            candidates.sort(key=lambda p: (-p.turn, p.pronoun != gender))
            person = candidates[0]
            if gender != "they" and person.pronoun is None:
                # The people whose pronouns are not known, back to the most recent person
                # known to be "she"/"he" (who is less likely than anyone mentioned after them)
                unknown = []
                for candidate in candidates:
                    if candidate.pronoun is not None:
                        break
                    unknown.append(candidate)
                if len(unknown) > 1:
                    # The child has not shown which one this is: ask instead of guessing
                    if state.ambiguity is None:
                        state.ambiguity = Ambiguity(message=message, pronoun=gender,
                                                    people=sorted(unknown, key=lambda p: p.order))
                    return None
            if gender != "they":
                person.pronoun = gender
            person.turn = state.turn
            # Replace only the first mention; "Maya said she would call" keeps the second "she"
            if id(person) in resolved_people:
                return None
            resolved_people.add(id(person))
            named.update(person.phrase().lower().split())
            possessive = lower in _POSSESSIVE_FORMS or (lower == "her" and token.dep_ == "poss")
            return self._match_case(person.phrase(possessive), token)

        if lower in _THING_PRONOUNS and self._is_thing_reference(token):
            match, attr = self._named_thing(token, state)
            if match is not None:
                match.turn = state.turn
                if any(c.dep_ == "amod" for c in attr.children):
                    # "That's a cool name" -> "Your name is cool", not "Your name is a cool name"
                    drop.add(attr.i)
                    drop.update(c.i for c in attr.children if c.dep_ == "det")
                return self._match_case(match.text, token)
            things = self._recent(state.things, state)
            if lower == "it":
                # "it" is singular: prefer a singular thing ("that" can point at "cats")
                things = [t for t in things if not t.plural] or things
            # Not an event done by someone this message names: "She started it" is not
            # "My sister started my sister and my brother fighting"
            events = [e for e in self._recent(state.events, state) if not e.actor & named]
            thing = things[0] if things else None
            event = events[0] if events else None
            if lower in _EVENT_PRONOUNS:
                # "that"/"this": the latest of the child's event or something the bot said
                choice = max((c for c in (thing, event) if c is not None), key=lambda c: c.order, default=None)
            else:
                choice = thing or event
            if choice is not None:
                choice.turn = state.turn
                return self._match_case(choice.text, token)

        return None

    @staticmethod
    def _attr_noun(token):
        """The noun in "that is a <noun>", if the pronoun is the subject of one"""
        if token.dep_ != "nsubj" or token.head.lemma_ != "be":
            return None
        return next((c for c in token.head.children if c.dep_ == "attr" and c.pos_ == "NOUN"), None)

    def _named_thing(self, token, state: DiscourseState):
        """
        In "That's a cool color", the recent thing the noun names ("the color orange") and
        the noun, or (None, None)
        """
        attr = self._attr_noun(token)
        if attr is None:
            return None, None
        noun = attr.lemma_.lower()
        for thing in self._recent(state.things, state):
            last = thing.text.lower().split()[-1]
            if last in (noun, noun + "s", noun + "es"):
                return thing, attr
        return None, None

    @staticmethod
    def _describes_bot(token) -> bool:
        """A noun in the bot's "I'm a big fan" / "I'm a computer program", which is not a thing"""
        return token.dep_ == "attr" and any(
            c.dep_ == "nsubj" and c.lower_ == "i" for c in token.head.children)

    @staticmethod
    def _is_thing_reference(token) -> bool:
        """
        A pronoun in a position that can refer back to something: subject, object or
        object of a preposition, excluding weather/time "it", idioms and conjunction "that"
        """
        head = token.head
        if token.dep_ in ("expl", "mark", "det") or head.dep_ == "relcl":
            return False
        attr = ReferenceTracker._attr_noun(token)
        if attr is not None and attr.lemma_.lower() in _UNTRACKED_COMPLEMENTS:
            return False
        if token.dep_ in ("nsubj", "nsubjpass"):
            if head.lemma_ in _WEATHER_VERBS or head.lemma_ in _NON_REFERENTIAL_SUBJECT_VERBS \
                    or head.lemma_ in _REACTION_VERBS:
                return False
            complements = [c for c in head.children if c.dep_ in ("acomp", "attr")]
            if any(c.lemma_.lower() in _NON_REFERENTIAL_COMPLEMENTS for c in complements):
                return False
            if any(c.dep_ == "poss" for comp in complements for c in comp.children):
                return False  # "It's my turn"
            return head.lemma_ != "be" or bool(complements)
        if token.dep_ == "dobj":
            return head.lemma_ not in _IDIOM_OBJECT_VERBS
        return token.dep_ == "pobj"

    def _clarification_answer(self, doc, pending: Ambiguity) -> Optional[Person]:
        """The person named in a short answer like "Maya" or "I mean Maya", if any"""
        words = [t for t in doc if not t.is_punct]
        if not words or len(words) > 4:
            return None
        text = doc.text.lower()
        named = [p for p in pending.people
                 if (p.name and re.search(rf"\b{re.escape(p.name.lower())}\b", text))
                 or (not p.name and p.relation and p.relation.lower() in text)]
        return named[0] if len(named) == 1 else None

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
        state.last_child_words = {t.lemma_.lower() for t in doc if t.is_alpha}

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
                    pronoun=_GENDERED_RELATIONS.get(token.lemma_.lower()),
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

        # Record details ("out of legos") before the main objects ("a tower"), so the main
        # object of the latest sentence is the most recent thing
        salience = {"pobj": 0, "attr": 1, "nsubj": 1, "dobj": 2}
        chunks = [c for c in doc.noun_chunks
                  if c.root.pos_ == "NOUN" and c.root.dep_ in salience
                  and c.root.lemma_.lower() not in self.relations
                  and c.root.lemma_.lower() not in _TIME_WORDS]
        for chunk in sorted(chunks, key=lambda c: (c.sent.start, salience[c.root.dep_], c.start)):
            self._remember_thing(self._thing_text(chunk), state, plural=chunk.root.tag_ == "NNS")

        event = self._event_phrase(doc)
        if event:
            text, actor = event
            state.events = [e for e in state.events if e.text != text]
            state.events.insert(0, Event(text=text, turn=state.turn, order=state.tick(), actor=actor))
            del state.events[3:]

    @staticmethod
    def _thing_text(chunk) -> str:
        root = chunk.root
        # Keep determiners, possessives and compounds ("my math test", "the world's oxygen"),
        # not adjectives other than "favorite"/"best" ("the test", not "the hard test")
        words = [t.text for t in chunk
                 if t == root or t.dep_ in ("det", "poss", "compound", "nummod", "case")
                 or (t.dep_ == "amod" and t.lower_ in ("favorite", "favourite", "best"))]
        for index in range(len(words) - 1, 0, -1):
            if words[index] in ("'s", "'"):
                words[index - 1] += words.pop(index)
        # "a math test" is referred back to as "the math test"
        if words and words[0].lower() in ("a", "an"):
            words[0] = "the"
        elif chunk.start == chunk.sent.start and root.pos_ != "PROPN":
            words[0] = words[0][:1].lower() + words[0][1:]
        return " ".join(words)

    def _remember_thing(self, text: str, state: DiscourseState, plural: bool = False) -> None:
        state.things = [t for t in state.things if t.text.lower() != text.lower()]
        state.things.insert(0, Thing(text=text, turn=state.turn, plural=plural, order=state.tick()))
        del state.things[6:]

    @staticmethod
    def _event_phrase(doc) -> Optional[Tuple[str, frozenset]]:
        """
        The last action in the message as a phrase that can stand in for "that":
        "We went to the zoo yesterday" -> "going to the zoo",
        "My dad got mad" -> "my dad getting mad", with the words naming the actor ({"dad"})
        """
        for sentence in reversed(list(doc.sents)):
            root = sentence.root
            if root.pos_ != "VERB" or root.lemma_ in _NON_EVENT_VERBS or sentence.text.strip().endswith("?"):
                continue
            subject = next((c for c in root.children if c.dep_ == "nsubj"), None)
            if subject is None:
                continue
            actor_words = frozenset()
            if any(t.lower_ in ("i", "we") for t in subject.subtree):
                actor = []
            elif subject.pos_ in ("NOUN", "PROPN"):
                # Someone else's action; pronouns other than "I"/"we" were not resolved
                actor = [t.text for t in subject.subtree]
                if subject.left_edge.is_sent_start and subject.left_edge.pos_ != "PROPN":
                    actor[0] = actor[0][:1].lower() + actor[0][1:]
                actor_words = frozenset(t.lower_ for t in subject.subtree if t.pos_ in ("NOUN", "PROPN"))
            else:
                continue
            excluded = set()
            for child in root.children:
                if child.dep_ in ("nsubj", "aux", "neg", "punct", "cc", "conj", "mark", "advcl", "intj") \
                        or child.ent_type_ in ("DATE", "TIME") or child.lemma_.lower() in _TIME_WORDS:
                    excluded.update(t.i for t in child.subtree)
            rest = [t.text for t in root.subtree if t.i > root.i and t.i not in excluded]
            return " ".join([*actor, gerund(root.lemma_.lower()), *rest]), actor_words
        return None

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
        """Add a person, or move an already known one to the front (most recent)"""
        for existing in state.people:
            if existing.matches(person) or (
                person.name and existing.name and existing.name.lower() == person.name.lower()
            ):
                existing.name = existing.name or person.name
                existing.relation = existing.relation or person.relation
                existing.pronoun = existing.pronoun or person.pronoun
                existing.turn = state.turn
                state.people.remove(existing)
                state.people.insert(0, existing)
                return
        person.turn = state.turn
        person.order = state.tick()
        state.people.insert(0, person)
        del state.people[10:]
