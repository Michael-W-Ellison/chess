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

import copy
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
               "one", "anything", "everything", "nothing", "part", "stuff", "kind", "app", "fun",
               "question", "huh", "fan", "mine", "yours", "ours", "pick", "choice", "idea", "guess", "job"}
_TITLES = {"mr", "mrs", "ms", "dr"}
# Favorites that are people: "my favorite character is Hermione"
_PERSON_CATEGORIES = {"character", "person", "friend", "hero", "superhero", "singer", "youtuber", "player",
                      "athlete", "teacher", "author", "princess", "actor", "actress", "artist", "cousin"}
_DETERMINERS = {"the", "a", "an", "my", "your", "his", "her", "our", "their", "this", "that", "these", "those",
                "some", "two", "three", "all"}
# Groups of people the child talks about: "kids at school", "the boys in my class"
_GROUPS = {"kid", "boy", "girl", "classmate", "student", "bully", "teenager", "people"}
# Short answers that are not a favorite thing ("no", "idk")
_NOT_ANSWERS = {"no", "nope", "nah", "yes", "yeah", "ok", "okay", "idk", "nothing", "dunno", "why", "what", "lol",
                "haha", "same", "cool", "nice", "wow", "maybe", "um", "hmm"}
# What "it" does when it is a body part: "it stopped bleeding", "it still hurts"
_BODY_VERBS = {"bleed", "hurt", "ache", "heal", "swell", "itch", "sting", "stop", "feel"}
_BODY_PARTS = {"arm", "leg", "knee", "foot", "hand", "finger", "toe", "head", "tummy", "stomach", "elbow",
               "wrist", "ankle", "nose", "lip", "tooth", "ear", "eye", "back", "neck", "chin", "cut", "scrape"}
# Words of a reaction to a joke, fact or answer: "That was funny", not "it was even bigger"
_REACTION_WORDS = {"funny", "hilarious", "silly", "corny", "lame", "cool", "good", "great", "awesome", "interesting",
                   "weird", "true", "gross", "cute", "amazing", "bad", "dumb", "stupid", "boring", "nice", "fun",
                   "crazy", "wild", "neat", "fascinating", "joke", "one", "sad", "unfair", "okay", "ok", "right",
                   "fine", "scary", "annoying", "sweet", "bummer", "lucky", "smart", "mean", "rude", "terrible",
                   "awful", "perfect", "wonderful", "fantastic", "epic", "excellent"}
# Verbs whose "it" can be the bot's own answer: "I like it too", "I want to try it"
_ANSWER_VERBS = {"like", "love", "hate", "want", "try", "play", "eat", "see", "watch", "read", "pick", "choose",
                 "prefer", "get", "do"}
# Words before an answer: "cool mine is green"
_ANSWER_OPENERS = {"cool", "ok", "okay", "oh", "well", "um", "umm", "hmm", "yeah"}
# Verbs whose object is usually a person, for names spaCy does not tag ("I saw Maya at school")
_SOCIAL_VERBS = {"see", "meet", "visit", "call", "text", "hug", "help", "invite", "ask", "tell", "miss", "beat", "follow"}
# "it" that refers to nothing: weather ("it is raining"), time ("it's time", "it's late"), turns
_WEATHER_VERBS = {"rain", "snow", "hail", "thunder", "storm", "drizzle", "pour", "sleet"}
_NON_REFERENTIAL_COMPLEMENTS = {"time", "turn", "cold", "hot", "warm", "sunny", "cloudy", "rainy", "windy",
                                "dark", "late", "early", "night", "morning", "raining", "snowing", "freezing",
                                "fair", "unfair", "true", "ok", "okay", "alright", "boy", "girl"}
_NON_REFERENTIAL_SUBJECT_VERBS = {"seem", "happen", "matter", "depend"}
# "That sounds fun" is a reaction whose reply does not need the referent, and a gerund
# subject is misparsed ("Playing a game sounds fun" makes "fun" an object)
_REACTION_VERBS = {"sound", "look", "stink", "suck"}
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


# "My dad made me soup. It was yummy" -> "The soup was yummy"
# Made-up and drawn creatures the child may call "she" or "he"
_CREATURES = {"unicorn", "dragon", "dinosaur", "monster", "robot", "mermaid", "fairy", "princess", "prince",
              "superhero", "bunny", "bear", "teddy", "doll", "alien", "pony", "horse", "puppy", "kitty",
              "snowman", "giant", "wizard", "witch", "knight", "king", "queen", "ghost", "zombie"}
# Verbs whose subject is a person: "they" with these is not a thing
_PERSON_ACTIONS = {"give", "say", "tell", "ask", "help", "let", "teach", "show", "call", "yell", "invite", "bring"}
# Pets and babies, and what is said about them: "she is so cute"
_PETS = {"dog", "puppy", "cat", "kitten", "kitty", "hamster", "bunny", "rabbit", "fish", "bird", "horse", "pony",
         "guinea", "pig", "turtle", "lizard", "baby", "parrot", "gerbil"}
_PET_WORDS = {"cute", "fluffy", "adorable", "furry", "soft", "cuddly", "tiny", "playful", "naughty"}

_FOOD_ADJECTIVES = {"hot", "iced", "fried", "scrambled", "whipped", "mashed", "grilled", "frozen", "baked", "roasted"}
_BOT_FILLER_NOUNS = {"change", "idea", "question", "thing", "lot", "way", "part", "kind", "sort", "bit", "fun",
                     "feeling", "plan", "goal", "step", "reason", "choice", "minds", "mind", "spirit"}
_MAKING_VERBS = {"make", "cook", "bake", "buy", "get", "eat", "bring", "give", "drink", "order"}


def _plural(noun: str) -> str:
    """ "cat" -> "cats", "fish" -> "fish", "puppy" -> "puppies" (relations are stored as lemmas)"""
    irregular = {"child": "children", "fish": "fish", "sheep": "sheep", "mouse": "mice", "person": "people",
                 "grandchild": "grandchildren"}
    if noun in irregular:
        return irregular[noun]
    if noun in irregular.values() or noun.endswith("s"):
        return noun  # already plural ("my puppies")
    if noun.endswith(("sh", "ch", "x")):
        return noun + "es"
    if noun.endswith("y") and noun[-2:-1] not in "aeiou":
        return noun[:-1] + "ies"
    return noun + "s"


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
            # "I have two cats. Their names are..." -> "my cats'"
            base = f"my {_plural(self.relation) if self.plural else self.relation}"
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
    added: bool = False  # a joke or fact the bot added unasked: only "it" in a reaction ("That was funny")
    short: bool = False  # the bot's own answer: only meant by "it" on the next turn
    made: bool = False  # a bare object someone made, bought or ate ("made me soup"): "the soup" later
    # Describes or belongs to another thing ("the picture is a unicorn", "the unicorn has a mane"):
    # "it" means the main thing (the picture) when there is one
    detail: bool = False


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
    last_plural: bool = False  # whether the last thing put in place of "it"/"that" was plural
    asked_favorite: Optional[str] = None  # "animal" after the bot asked "What's your favorite animal?"

    def tick(self) -> int:
        self.clock += 1
        return self.clock


class ReferenceTracker:
    """Per-user record of recent people, things and events, used to resolve pronouns"""

    def __init__(self, parser, relations: Iterable[str], common_capitalized: Iterable[str] = (),
                 foods: Iterable[str] = ()):
        self.parser = parser
        self.relations = set(relations)
        self.common_capitalized = set(common_capitalized)
        self.foods = set(foods)  # "we had pizza": something eaten, so "it" is "the pizza"
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
        asked_favorite, state.asked_favorite = state.asked_favorite, None

        # "What's your favorite animal?" - "a wolf" / "mine is a wolf"
        if asked_favorite and not pending:
            answer = self._favorite_answer(doc, asked_favorite)
            if answer:
                doc = self.parser.parse(answer)

        chosen = self._clarification_answer(doc, pending) if pending else None
        if chosen is not None:
            chosen.pronoun = pending.pronoun
            chosen.turn = state.turn  # ahead of anyone mentioned after them
            doc = self.parser.parse(pending.message)

        parts = []
        resolved_people = set()
        named = {t.lower_ for t in doc}  # words naming who is in this message, for events
        # One-word names the child already used ("Milo"), for "milo is orange"
        known_names = {p.name for p in state.people if p.name and p.name.isalpha() and p.name[:1].isupper()}
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
                replacement = "are" if state.last_plural else "is"
            if replacement is None and token.is_lower and (
                    self._is_relation_name(token) or token.text.capitalize() in known_names):
                replacement = token.text.capitalize()  # "my friend sam" -> "my friend Sam"
            parts.append((replacement if replacement is not None else token.text) + token.whitespace_)
            replaced_previous = replacement is not None
        resolved = "".join(parts)

        resolved_doc = self.parser.parse(resolved) if resolved != doc.text else doc
        self._record(resolved_doc, state)
        return resolved

    def preview(self, message: str, user_id: int) -> str:
        """The message with references resolved, without recording anything"""
        saved = copy.deepcopy(self._states.get(user_id))
        try:
            return self.resolve(message, user_id)
        finally:
            if saved is None:
                self._states.pop(user_id, None)
            else:
                self._states[user_id] = saved

    @staticmethod
    def _favorite_answer(doc, category: str) -> Optional[str]:
        """The child's answer to "What's your favorite <category>?" as a full sentence"""
        words = [t for t in doc if not t.is_punct]
        # "cool mine is green", "ok blue"
        while len(words) > 1 and words[0].lower_ in _ANSWER_OPENERS:
            words = words[1:]
        if not words or len(words) > 4:
            return None
        if words[0].lower_ == "mine" and len(words) > 2 and words[1].lemma_ == "be":
            return f"My favorite {category} is {doc[words[2].i:].text}"
        if any(t.pos_ in ("VERB", "AUX", "PRON", "INTJ") or t.lower_ in _NOT_ANSWERS for t in words):
            return None
        return f"My favorite {category} is {doc[words[0].i:].text}"

    def record_bot_reply(self, user_id: int, reply: str, told: Optional[str] = None,
                         mentions: Iterable[str] = (), told_was_added: bool = False) -> None:
        """
        Remember what the bot said so the child can refer to it ("That's so cool!").

        Args:
            user_id: User ID
            reply: The bot's reply text (without quirk additions like puns)
            told: "joke" or "fun fact" if the bot told one; it becomes the most recent thing
            mentions: Things the bot offered as its own answer (e.g. its favorite color)
            told_was_added: The joke or fact was added to the reply, not asked for; the bot's
                own answers stay the most recent things ("Mine is red pandas" + a joke, then
                "why do you like it"), and it is only meant by a reaction ("That was funny"),
                not by "my teacher put it on the wall"
        """
        doc = self.parser.parse(reply)
        state = self.state(user_id)
        # "What's your favorite animal?", or "My favorite game is chess! What's yours?"
        asked = re.search(r"\byour favorite (\w+)\?", reply, re.IGNORECASE) or \
            re.search(r"\bWhat (\w+) do you like\?", reply)
        if asked is None and re.search(r"\bWhat's yours\?", reply):
            asked = re.search(r"\bfavorite (\w+)\b", reply, re.IGNORECASE)
        state.asked_favorite = asked.group(1).lower() if asked else None
        # "Who do you mean, Luna or Milo?" names people, not things "it" could mean
        if doc is not None and state.ambiguity is None:
            for chunk in doc.noun_chunks:
                root = chunk.root
                # "Moving is a big change!": a word of the bot's reply, not a thing the child means by "it"
                if root.lemma_.lower() in _BOT_FILLER_NOUNS:
                    continue
                # Only new things the bot brought up, not echoes of the child's words or
                # anything with "my"/"your" (whose it is depends on who is speaking)
                # Not an exclamation at the start of a sentence ("Awesome! You built a castle")
                exclamation = len(chunk) == 1 and root.i == root.sent.start and root.i + 1 < len(doc) \
                    and doc[root.i + 1].text in ("!", ",")
                # "Have you told a grown-up?" names a person, not a thing
                if "grown" in chunk.text.lower() or root.lemma_.lower() in ("adult", "grownup"):
                    continue
                if (root.pos_ in ("NOUN", "PROPN") and root.ent_type_ != "PERSON" and not exclamation
                        and not any(t.dep_ == "det" and t.lower_ == "no" for t in chunk)
                        and not any(t.pos_ == "PRON" or t.tag_ in ("WDT", "WP") for t in chunk)
                        and root.lemma_.lower() not in self.relations
                        and root.lemma_.lower() not in _TIME_WORDS
                        and root.lemma_.lower() not in state.last_child_words
                        and not self._describes_bot(root)):
                    # Short: meant by a reaction ("That's so cool!"), not by the child's own next news
                    self._remember_thing(self._thing_text(chunk), state, plural=root.tag_ in ("NNS", "NNPS"),
                                         short=True)
        mentions = list(mentions)
        if told and told_was_added:
            self._remember_thing(f"your {told}", state, added=True)
            told = None
        for mention in mentions:
            mention_doc = self.parser.parse(mention)
            plural = mention_doc is not None and mention_doc[:].root.tag_ in ("NNS", "NNPS")
            self._remember_thing(mention, state, plural=plural, short=True)
        if told:
            self._remember_thing(f"your {told}", state)

    # ------------------------------------------------------------------
    # Resolution
    # ------------------------------------------------------------------

    def _recent(self, items, state: DiscourseState):
        # The bot's own answers ("your name", its favorite color) only on the next turn
        return [item for item in items if state.turn - item.turn <= (1 if getattr(item, "short", False) else MAX_AGE)]

    def _antecedent(self, token, state: DiscourseState, resolved_people: set, message: str,
                    named: set, drop: set) -> Optional[str]:
        lower = token.lower_
        # "name her Lily": the reply is about the name; "name the new baby Lily" parses badly
        if token.dep_ == "dobj" and token.head.lemma_ in ("name", "call") and any(
                c.dep_ == "oprd" for c in token.head.children):
            return None

        if lower in _PERSON_PRONOUNS and token.pos_ == "PRON":
            gender = _PERSON_PRONOUNS[lower]
            people = self._recent(state.people, state)
            if gender == "they":
                candidates = [p for p in people if p.plural]
                if not candidates and lower in ("they", "them"):
                    # "Do you like dinosaurs?" -> "Yes, I love them"
                    things = [t for t in self._recent(state.things, state) if t.plural]
                    # "They gave me a toothbrush": people (at the dentist), not "no cavities"
                    agent = token.dep_ == "nsubj" and token.head.lemma_ in _PERSON_ACTIONS
                    if things and self._is_thing_reference(token) and not agent:
                        return self._match_case(self._as_subject(things[0], token), token)
            else:
                candidates = [p for p in people if not p.plural and p.pronoun in (None, gender, "any")]
            if not candidates and gender in ("she", "he"):
                # "It's a unicorn. She has a rainbow mane": a creature the child drew or made up
                creature = next((t for t in self._recent(state.things, state)
                                 if not t.plural and not t.added and t.text.split()[-1].lower() in _CREATURES), None)
                if creature is not None and not (lower in ("his", "her") and token.head.lower_ == "name"):
                    creature.turn = state.turn
                    words = [w for w in creature.text.split() if w.lower() not in _DETERMINERS]
                    phrase = f"the {' '.join(words)}" + ("'s" if lower in _POSSESSIVE_FORMS or (
                        lower == "her" and token.dep_ == "poss") else "")
                    return self._match_case(phrase, token)
            if not candidates:
                # "We built a snowman. His name is Frosty": the thing the child made
                if lower in ("his", "her") and token.head.lower_ == "name":
                    things = [t for t in self._recent(state.things, state)
                              if not t.short and not t.added and not t.plural]
                    if things:
                        # "my favorite stuffed animal" -> "the stuffed animal's"
                        words = [w for w in things[0].text.split()
                                 if w.lower() not in _DETERMINERS and w.lower() not in ("favorite", "favourite")]
                        return self._match_case(f"the {' '.join(words)}'s", token)
                return None

            # "My brother broke his arm": "his" is the subject of its own clause
            if lower in ("his", "her") and token.dep_ == "poss" and self._clause_subject_owns(token, gender):
                return None

            # "She is so cute" after "we got a puppy ... my mom was mad": the puppy
            if token.dep_ == "nsubj" and any(c.dep_ == "acomp" and c.lower_ in _PET_WORDS
                                             for c in token.head.children):
                pets = [p for p in candidates if p.relation and p.relation.split()[-1] in _PETS]
                if pets:
                    candidates = pets

            # Most recent turn first; within a turn, someone known to be "she"/"he"
            # A new baby ("my aunt had a baby. She is so tiny") is "he" or "she" and comes first
            candidates.sort(key=lambda p: (-p.turn, p.pronoun not in (gender, "any"), p.pronoun != "any"))
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

        # "Mine was blue and green" after "we made clay pots": my clay pot
        if lower == "mine" and token.dep_ == "nsubj":
            things = [t for t in self._recent(state.things, state) if not t.short and not t.added]
            if things:
                words = things[0].text.split()
                noun = " ".join(w for w in words if w.lower() not in _DETERMINERS)
                if noun:
                    noun = noun[:-1] if things[0].plural and noun.endswith("s") else noun
                    return self._match_case(f"my {noun}", token)

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
            # "It stopped bleeding": a body part, not the bandaid
            if token.head.lemma_ in _BODY_VERBS:
                things = sorted(things, key=lambda t: t.text.split()[-1].lower() not in _BODY_PARTS)
            # An added joke or fact: "That was funny", not "my teacher put it on the wall"
            reaction = token.dep_ == "nsubj" and any(
                c.dep_ in ("acomp", "attr") and c.lower_ in _REACTION_WORDS for c in token.head.children)
            if not reaction:
                things = [t for t in things if not t.added]
            # The bot's own answer ("Mine is Jupiter") for a reaction or "I like it too", not
            # for something the child goes on to say about their own topic ("It has rings")
            if not (reaction or token.head.lemma_ in _ANSWER_VERBS):
                things = [t for t in things if not t.short] or things
            if lower == "it":
                # "it" is singular: prefer a singular thing ("that" can point at "cats")
                things = [t for t in things if not t.plural] or things
                things = [t for t in things if not t.detail] or things
            # Not an event done by someone this message names: "She started it" is not
            # "My sister started my sister and my brother fighting"
            events = [e for e in self._recent(state.events, state) if not e.actor & named]
            # Only the bot's own words left ("a nap"), and the child told of something happening:
            # "It wakes me up" is the baby crying
            if things and all(t.short for t in things) and events and not reaction:
                things = []
            thing = things[0] if things else None
            event = events[0] if events else None
            if lower in _EVENT_PRONOUNS:
                # "that"/"this": the latest of the child's event or something the bot said
                choice = max((c for c in (thing, event) if c is not None), key=lambda c: c.order, default=None)
            else:
                choice = thing or event
            if choice is not None:
                choice.turn = state.turn
                state.last_plural = getattr(choice, "plural", False)
                return self._match_case(self._as_subject(choice, token), token)

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
            # "It was far away", "it was over there"
            where = any(c.dep_ == "advmod" and c.lower_ in ("away", "far", "close", "there", "here", "everywhere")
                        for c in head.children)
            return head.lemma_ != "be" or bool(complements) or where
        if token.dep_ == "dobj":
            # "They do it every day": what they do, not a thing ("I want to do that" is)
            return head.lemma_ not in _IDIOM_OBJECT_VERBS and not (head.lemma_ == "do" and token.lower_ == "it")
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

    def _is_relation_name(self, token) -> bool:
        """ "sam" in "my friend sam", "jake" in "my cousin jake": a name written in lowercase """
        if not token.is_alpha or token.lemma_.lower() in self.relations:
            return False
        if token.dep_ == "appos" and token.pos_ == "PROPN" and token.head.lemma_.lower() in self.relations:
            return True
        # "my friends maya and zoe": the second name, joined to the first
        if token.dep_ == "conj" and token.head.pos_ == "PROPN" and token.pos_ in ("PROPN", "NOUN") and (
                self._is_relation_name(token.head) or token.head.text[:1].isupper()):
            return token.lower_ not in self.parser.known_words() or token.pos_ == "PROPN"
        relation = next((c for c in token.children
                         if c.dep_ == "compound" and c.lemma_.lower() in self.relations), None)
        # "my" on the name ("my cousin jake") or on the relation ("my friend lucas")
        return (token.pos_ in ("NOUN", "PROPN") and relation is not None
                and any(c.dep_ == "poss" and c.lower_ in ("my", "our")
                        for c in list(token.children) + list(relation.children))
                and (token.pos_ == "PROPN" or not {token.lower_, token.lemma_.lower()} & self.parser.known_words()))

    def _is_detail(self, noun) -> bool:
        """
        "a unicorn" in "the picture is a unicorn", "a mane" in "the unicorn has a mane":
        a description or part of another thing (the subject), not of the child or a person
        """
        verb = noun.head
        if not ((noun.dep_ == "attr" and verb.lemma_ == "be") or (noun.dep_ == "dobj" and verb.lemma_ == "have")):
            return False
        subject = next((c for c in verb.children if c.dep_ == "nsubj"), None)
        # "My favorite planet is Saturn": Saturn is what the child is talking about
        if subject is not None and any(c.lower_ in ("favorite", "favourite") for c in subject.children):
            return False
        return (subject is not None and subject.pos_ == "NOUN"
                and subject.lemma_.lower() not in self.relations and subject.lemma_.lower() not in _GROUPS)

    @staticmethod
    def _clause_subject_owns(token, gender: str) -> bool:
        """True if a "his"/"her" most likely refers to its clause's subject, a noun or name before it"""
        verb = next((a for a in token.ancestors if a.pos_ in ("VERB", "AUX")), None)
        if verb is None:
            return False
        subject = next((c for c in verb.children if c.dep_ == "nsubj"), None)
        if subject is None or subject.pos_ not in ("NOUN", "PROPN") or subject.i > token.i:
            return False
        return _GENDERED_RELATIONS.get(subject.lemma_.lower()) in (gender, None)

    @staticmethod
    def _acl_name(token):
        """The name in "a dog named Max" / "my cat called Luna", if any"""
        for clause in token.children:
            if clause.dep_ == "acl" and clause.lemma_ in ("name", "call"):
                return next((c for c in clause.children if c.dep_ in ("oprd", "dobj") and c.pos_ == "PROPN"), None)
        return None

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
                # "My teacher is Mrs Garcia"
                if name_token is None and token.dep_ == "nsubj" and token.head.lemma_ == "be":
                    name_token = next((c for c in token.head.children
                                       if c.dep_ == "attr" and c.pos_ == "PROPN"), None)
                if name_token is None:
                    name_token = self._acl_name(token)
                if name_token is not None:
                    named_tokens.add(name_token.i)
                mentioned.append(Person(
                    name=self._full_name(name_token) if name_token is not None else None,
                    relation=relation.lower(),
                    plural=token.tag_ == "NNS",
                    pronoun=_GENDERED_RELATIONS.get(token.lemma_.lower()),
                ))
            elif (token.lemma_.lower() == "baby" and token.dep_ == "dobj" and token.head.lemma_ == "have"
                  and any(c.dep_ == "nsubj" and c.lemma_.lower() in self.relations for c in token.head.children)):
                # "My aunt had a baby": a cousin; "My mom is having a baby": the new baby
                parent = next(c for c in token.head.children if c.dep_ == "nsubj")
                if parent.lemma_.lower() in ("aunt", "uncle"):
                    mentioned.append(Person(relation="baby cousin", pronoun="any"))
                else:
                    mentioned.append(Person(name="the new baby", pronoun="any"))
            elif token.lemma_.lower() in self.relations and self._is_new_relation(token):
                # "I got a new puppy", "We have two cats and a dog": the child's from now on
                name_token = self._acl_name(token)
                if name_token is not None:
                    named_tokens.add(name_token.i)
                mentioned.append(Person(
                    name=self._full_name(name_token) if name_token is not None else None,
                    relation=token.lemma_.lower(),
                    plural=token.tag_ == "NNS",
                    pronoun=_GENDERED_RELATIONS.get(token.lemma_.lower()),
                ))

        for token in doc:
            # "My dog's name is Roxie" / "The dog's name is Roxie" (the child's dog)
            head = token.head
            if (token.dep_ == "poss" and token.pos_ == "NOUN" and token.lemma_.lower() not in self.relations
                    and head.lower_ == "name" and head.dep_ == "nsubj"
                    and any(c.lower_ in ("my", "our", "the") for c in token.children)):
                # "The snowman's name is Frosty": Frosty, a he or she the child may talk about
                name_token = next((c for c in head.head.children if c.dep_ in ("attr", "acomp")), None)
                if name_token is not None and name_token.is_alpha and not any(c.dep_ == "det" for c in name_token.children):
                    named_tokens.add(name_token.i)
                    named_tokens.update(c.i for c in name_token.children if c.dep_ == "compound")
                    name = self._full_name(name_token)
                    mentioned.append(Person(name=name[:1].upper() + name[1:]))
            if (token.dep_ == "poss" and token.lemma_.lower() in self.relations
                    and head.lower_ == "name" and head.dep_ == "nsubj"
                    and any(c.lower_ in ("my", "our", "the") for c in token.children)):
                name_token = next((c for c in head.head.children
                                   if c.dep_ in ("attr", "acomp", "npadvmod")), None)
                if name_token is not None and name_token.is_alpha:
                    named_tokens.add(name_token.i)
                    mentioned.append(Person(
                        name=name_token.text[:1].upper() + name_token.text[1:],
                        # "my baby cousin's name" -> "baby cousin"
                        relation=" ".join([c.lower_ for c in token.children if c.dep_ == "compound"]
                                          + [token.lemma_.lower()]),
                        pronoun=_GENDERED_RELATIONS.get(token.lemma_.lower()),
                    ))

        for token in doc:
            # "My dog is named Buster" / "The dog is called Buster"
            if (token.dep_ == "nsubjpass" and token.lemma_.lower() in self.relations
                    and token.head.lemma_ in ("name", "call")
                    and any(c.lower_ in ("my", "our", "the") for c in token.children)):
                name_token = next((c for c in token.head.children
                                   if c.dep_ in ("oprd", "attr", "dobj") and c.is_alpha), None)
                if name_token is not None:
                    named_tokens.add(name_token.i)
                    mentioned.append(Person(
                        name=name_token.text[:1].upper() + name_token.text[1:],
                        # "my baby cousin's name" -> "baby cousin"
                        relation=" ".join([c.lower_ for c in token.children if c.dep_ == "compound"]
                                          + [token.lemma_.lower()]),
                        pronoun=_GENDERED_RELATIONS.get(token.lemma_.lower()),
                    ))

        for token in doc:
            # Names on their own: "I played with Maya", "Maya and Jake came over"
            if token.i in named_tokens or token.pos_ != "PROPN" or self._is_childs_own_name(token):
                continue
            if token.lower_.rstrip(".") in _TITLES or any(c.i in named_tokens for c in token.ancestors):
                continue  # "Mrs" in "Mrs Garcia", or part of a name already recorded
            if self._names_a_favorite(token):
                continue  # "My favorite game is Mario Kart"
            if not self._is_person_name(token):
                continue
            if token.lower_ in {t.text.split()[-1].lower() for t in state.things}:
                continue  # "Soup was yummy" after "it" became the soup: a thing, not a name
            mentioned.append(Person(name=self._full_name(token)))
            group = [c for c in token.conjuncts if c.pos_ == "PROPN"]
            if group and token.dep_ != "conj":
                names = [token.text, *(c.text for c in group)]
                mentioned.append(Person(name=" and ".join(names), plural=True))

        for token in doc:
            # "My favorite character is Hermione": a person the child may call "she"
            if (token.dep_ in ("attr", "acomp") and token.head.lemma_ == "be" and token.is_alpha
                    and token.i not in named_tokens
                    and any(c.dep_ == "nsubj" and c.lemma_.lower() in _PERSON_CATEGORIES
                            and any(g.lower_ in ("favorite", "favourite") for g in c.children)
                            for c in token.head.children)):
                named_tokens.add(token.i)
                mentioned.append(Person(name=token.text[:1].upper() + token.text[1:]))

        for token in doc:
            # "Kids at school push me" -> "they" is the kids at school
            if (token.dep_ == "nsubj" and token.tag_ == "NNS" and token.lemma_.lower() in _GROUPS
                    and not any(c.dep_ == "poss" for c in token.children)):
                words = [t for t in token.subtree if t.dep_ != "det" and t.i <= token.i + 3 and t.i >= token.i]
                mentioned.append(Person(name=" ".join(t.text for t in words).lower(), plural=True))

        for person in mentioned:
            self._remember_person(person, state)

        # Record details ("out of legos") before the main objects ("a tower"), so the main
        # object of the latest sentence is the most recent thing
        salience = {"pobj": 0, "attr": 1, "nsubj": 1, "dobj": 2}
        chunks = [c for c in doc.noun_chunks
                  if (c.root.pos_ == "NOUN" or (c.root.pos_ == "PROPN" and self._names_a_favorite(c.root)))
                  and c.root.dep_ in salience
                  and c.root.lemma_.lower() not in self.relations
                  and c.root.lemma_.lower() not in _TIME_WORDS
                  and c.root.lemma_.lower() != "name"  # "My name is Liam": not what "it" means later
                  and c.root.lemma_.lower() not in _GROUPS]  # "kids" are people, not "it"
        # "I built another one" after "I built a sandcastle": the new sandcastle
        previous = next((t for t in state.things if not t.short and not t.added), None)
        for token in doc:
            if (previous is not None and token.lower_ == "one" and token.dep_ in ("dobj", "attr", "pobj")
                    and any(c.lower_ in ("another", "new") for c in token.children)):
                noun = previous.text.split()[-1]
                self._remember_thing(f"the new {noun}", state, plural=previous.plural)

        for chunk in sorted(chunks, key=lambda c: (c.sent.start, salience[c.root.dep_], c.start)):
            made = (chunk.root.dep_ == "dobj" and len(chunk) == 1 and chunk.root.tag_ == "NN"
                    and (chunk.root.head.lemma_ in _MAKING_VERBS
                         or (chunk.root.head.lemma_ == "have" and chunk.root.lemma_.lower() in self.foods)))
            self._remember_thing(self._thing_text(chunk), state, plural=chunk.root.tag_ == "NNS", made=made,
                                 detail=self._is_detail(chunk.root))

        event = self._event_phrase(doc)
        if event:
            text, actor = event
            state.events = [e for e in state.events if e.text != text]
            state.events.insert(0, Event(text=text, turn=state.turn, order=state.tick(), actor=actor))
            del state.events[3:]

    @staticmethod
    def _as_subject(item, token) -> str:
        """ "They had sprinkles" -> "The cupcakes had sprinkles", not "Cupcakes had sprinkles" """
        text = item.text
        if (token.dep_ == "nsubj" and (getattr(item, "plural", False) or getattr(item, "made", False))
                and text.split()[0].lower() not in _DETERMINERS and not text[:1].isupper()):
            return f"the {text}"
        return text

    @staticmethod
    def _names_a_favorite(token) -> bool:
        """The token is in the answer of "My favorite <thing> is ..." """
        while token.dep_ in ("compound", "conj", "appos") and token.head != token:
            token = token.head
        if token.dep_ not in ("attr", "acomp") or token.head.lemma_ != "be":
            return False
        # "My favorite character is Hermione" names a person
        return any(c.dep_ == "nsubj" and c.lemma_.lower() not in _PERSON_CATEGORIES
                   and any(g.lower_ in ("favorite", "favourite") for g in c.children)
                   for c in token.head.children)

    @staticmethod
    def _full_name(token) -> str:
        """The name with its title: "Mr Kim", not "Kim" """
        title = next((c.text for c in token.children
                      if c.dep_ == "compound" and c.lower_.rstrip(".") in _TITLES), None)
        return f"{title} {token.text}" if title else token.text

    @staticmethod
    def _is_new_relation(token) -> bool:
        """The object (or a listed object) of "I have/got/adopted ..." """
        while token.dep_ in ("conj", "appos") and token.head.pos_ == "NOUN":
            token = token.head
        verb = token.head
        return (token.dep_ == "dobj" and verb.lemma_ in ("have", "get", "adopt")
                and any(c.dep_ == "nsubj" and c.lower_ in ("i", "we") for c in verb.children))

    @staticmethod
    def _thing_text(chunk) -> str:
        root = chunk.root
        # Keep determiners, possessives and compounds ("my math test", "the world's oxygen"),
        # not adjectives other than "favorite"/"best" ("the test", not "the hard test")
        words = [t.text for t in chunk
                 if t == root or t.dep_ in ("det", "poss", "compound", "nummod", "case")
                 or (t.dep_ == "amod" and t.lower_ in ("favorite", "favourite", "best"))
                 # "hot chocolate", "mashed potatoes": part of the food's name
                 or (t.dep_ == "amod" and t.lower_ in _FOOD_ADJECTIVES)]
        for index in range(len(words) - 1, 0, -1):
            if words[index] in ("'s", "'"):
                words[index - 1] += words.pop(index)
        # "a math test" is referred back to as "the math test"
        if words and words[0].lower() in ("a", "an"):
            words[0] = "the"
        elif chunk.start == chunk.sent.start and root.pos_ != "PROPN":
            words[0] = words[0][:1].lower() + words[0][1:]
        return " ".join(words)

    def _remember_thing(self, text: str, state: DiscourseState, plural: bool = False, added: bool = False,
                        short: bool = False, made: bool = False, detail: bool = False) -> None:
        same = [t for t in state.things if t.text.lower() == text.lower()]
        # Once a detail of something else ("a unicorn" the picture shows), still a detail when named again
        detail = detail or any(t.detail for t in same)
        # The bot repeating the child's own word ("Saturn? Mine too!") does not make it the bot's answer
        short = short and not any(not t.short and not t.added for t in same)
        state.things = [t for t in state.things if t.text.lower() != text.lower()]
        state.things.insert(0, Thing(text=text, turn=state.turn, plural=plural, order=state.tick(), added=added,
                                     short=short, made=made, detail=detail))
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
        # "at Mario Kart", "in Minecraft": you play with people, not at them; and you read
        # or watch a book or show ("I'm reading Harry Potter")
        place = token.head if token.dep_ == "compound" else token
        if place.dep_ == "pobj" and place.head.lower_ in ("at", "in", "on"):
            return False
        if place.dep_ == "dobj" and place.head.lemma_ in ("read", "watch", "play", "finish", "beat"):
            return False
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
