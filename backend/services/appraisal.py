"""
Appraisal
What a message says happened, in general terms, so replies can fit wordings no rule names

For the main clause of a message: who acted (the child, a person, a pet, a thing, the bot),
who or what it was done to, the kind of action (from the verb lexicon in the knowledge base:
"harm", "break", "kindness", "achieve", "setback", "loss", ...), whether it happened or is
only future, hoped for, wanted, possible, an obligation or a "what if", whether it is
negated, and how it feels for the child (positive, negative or neutral).

"My brother knocked over my tower"  -> actor person, action break, target child's thing, negative
"Next time we will win"             -> actor child, action achieve, future, positive
"I hope my dog gets better"         -> hope, positive
"What if nobody likes me"           -> hypothetical, negative
"I didn't get one"                  -> actor child, action receive, negated, negative
"""

from dataclasses import dataclass, field
from typing import Dict, Iterable, Optional

# Modalities, from most to least specific
REAL = "real"
FUTURE = "future"
HYPOTHETICAL = "hypothetical"
HOPE = "hope"
WANT = "want"
POSSIBLE = "possible"
OBLIGATION = "obligation"

_FUTURE_AUX = {"will", "'ll", "wo", "gonna", "shall"}
_POSSIBLE_AUX = {"can", "could", "might", "may", "ca"}
_HOPE_VERBS = {"hope", "pray"}
_WANT_VERBS = {"want", "wanna", "like", "love"}  # "like/love" only as "would like to"
_OBLIGATION_VERBS = {"have", "need", "must", "got"}
_CHILD = {"i", "we", "me", "us", "my", "our"}
_BOT = {"you", "your"}
# Person pronouns left after reference resolution (the tracker could not resolve them)
_PERSON_PRONOUNS = {"he", "she", "they", "him", "her", "them", "someone", "somebody", "everyone", "everybody",
                    "nobody", "anyone"}


@dataclass
class Appraisal:
    root: object                      # the clause's main verb (spaCy Token)
    action: Optional[str] = None      # lexicon class, e.g. "harm"
    actor: str = "unknown"            # child, person, pet, thing, bot, unknown
    target: Optional[str] = None      # child, child_thing, person, pet, thing
    modality: str = REAL
    negated: bool = False
    tense: str = "present"            # past, present, future
    question: bool = False
    valence: str = "neutral"          # how it feels for the child
    notes: Dict[str, str] = field(default_factory=dict)


class Appraiser:
    """Classifies clauses with the knowledge base's action lexicon"""

    def __init__(self, kb: Dict):
        appraisal = kb.get("appraisal", {})
        self.action_of: Dict[str, str] = {}
        for action, lemmas in appraisal.get("actions", {}).items():
            for lemma in lemmas:
                self.action_of.setdefault(lemma, action)
        self.phrasal: Dict[str, str] = appraisal.get("phrasal", {})  # "knock over" -> break
        self.valence: Dict[str, Dict[str, str]] = appraisal.get("valence", {})
        lexicons = kb.get("lexicons", {})
        self.relations = set(lexicons.get("relations", []))
        self.pets = set(appraisal.get("pets", []))
        self.chore_places = set(appraisal.get("chore_places", []))
        self.foods = set(kb.get("lexicons", {}).get("foods", []))
        self.positive_words = {w for w, v in kb.get("evaluations", {}).items() if v == "positive"}
        self.negative_words = {w for w, v in kb.get("evaluations", {}).items() if v == "negative"}
        self._pet_names = set()  # set per message (see appraise)
        self._source = "verb"

    # ------------------------------------------------------------------

    def appraise(self, doc, pet_names: Iterable[str] = ()) -> Optional[Appraisal]:
        """
        Appraisal of the last sentence with a verb, or None

        pet_names: names of the child's pets ("Milo"), so "Milo scratched me" is a pet
        """
        self._pet_names = {n.lower() for n in pet_names}
        for sentence in reversed(list(doc.sents)):
            root = self._main_verb(sentence)
            if root is not None:
                return self._appraise_clause(root, sentence)
        return None

    def appraise_tokens(self, root, pet_names: Iterable[str] = ()) -> Appraisal:
        """Appraisal of the clause of a given verb"""
        self._pet_names = {n.lower() for n in pet_names}
        return self._appraise_clause(root, root.sent)

    def subject(self, verb):
        """The verb's subject, or its governing verb's ("I want to win" -> "I")"""
        return self._subject(verb)

    # ------------------------------------------------------------------

    @staticmethod
    def _main_verb(sentence):
        root = sentence.root
        if root.pos_ in ("VERB", "AUX"):
            return root
        # "What if nobody likes me": "what" is the root, the clause hangs off it
        clause = next((c for c in root.children if c.dep_ in ("advcl", "ccomp") and c.pos_ in ("VERB", "AUX")), None)
        return clause

    def _appraise_clause(self, root, sentence) -> Appraisal:
        event = self._event_verb(root)
        appraisal = Appraisal(root=event)
        appraisal.question = sentence.text.strip().endswith("?") or (
            len(sentence) > 0 and sentence[0].lower_ in ("do", "does", "did", "can", "could", "will", "would", "is",
                                                         "are", "was", "were", "should", "why", "how", "what",
                                                         "when", "where", "who"))
        self._source = "verb"
        appraisal.action = self._action(event)
        # "phrasal" when a verb with its particle or object decided the kind ("make fun of")
        appraisal.notes["source"] = self._source
        subject = self._subject(event)
        appraisal.actor = self._role(subject)
        appraisal.target = self._target(event)
        if subject is not None and subject.dep_ == "nsubjpass":
            # "I got invited", "my bike got broken": done to the subject by someone
            appraisal.target = "child" if appraisal.actor == "child" else appraisal.actor
            appraisal.actor = "unknown"
        if any(c.lower_ == "never" for c in event.children):
            appraisal.notes["habit"] = "yes"  # "I never finish my homework on time"
        if any(t.lower_ in ("accidentally", "accident", "oops") for t in event.subtree) or \
                any(t.lower_ == "accident" for t in sentence):
            appraisal.notes["accident"] = "yes"
        self._counterfactual = False
        appraisal.modality = self._modality(event, root, sentence)
        if self._counterfactual:
            appraisal.notes["counterfactual"] = "yes"
        if appraisal.modality in (WANT, HOPE):
            # "my mom wants to talk about my grades": someone else's wish, not the child's
            chain = [event] + [a for a in event.ancestors if a.sent == sentence][:3]
            wish = next((v for v in chain if v.lemma_ in _HOPE_VERBS | _WANT_VERBS | {"wish"}), None)
            wisher = next((c for c in wish.children if c.dep_ == "nsubj"), None) if wish is not None else None
            if wisher is not None and wisher.lower_ not in ("i", "we", "me"):
                appraisal.notes["wanter"] = "other"
            # "I don't want to go": not wanting something, rather than a sad wish
            if wish is not None and wish.lemma_ in ("want", "wanna") and wish.i != event.i and self._negated(wish):
                appraisal.notes["refuse"] = "yes"
        appraisal.negated = self._negated(event) or (event.i != root.i and self._negated(root))
        appraisal.tense = self._tense(event, appraisal.modality)
        appraisal.valence = self._valence(appraisal)
        return appraisal

    @staticmethod
    def _event_verb(root):
        """ "I want to win" -> "win"; "I hope he gets better" -> "gets"; "I have to get a shot" -> "get" """
        token = root
        for _ in range(3):
            nxt = next((c for c in token.children if c.dep_ in ("xcomp", "ccomp") and c.pos_ in ("VERB", "AUX")
                        and token.lemma_ in _HOPE_VERBS | _WANT_VERBS | _OBLIGATION_VERBS | {"go", "try", "get",
                                                                                            "think", "bet", "wish"}),
                       None)
            if nxt is None:
                break
            token = nxt
        return token

    def _action(self, verb) -> Optional[str]:
        lemma = verb.lemma_.lower()
        particle = next((c.lower_ for c in verb.children if c.dep_ == "prt" or (
            c.dep_ == "advmod" and c.lower_ in ("away", "over", "down", "up", "out", "off"))), None)
        if particle and f"{lemma} {particle}" in self.phrasal:
            self._source = "phrasal"
            return self.phrasal[f"{lemma} {particle}"] or None
        # "laughed at my shoes", "picked on me": a verb with its preposition
        for prep in (c for c in verb.children if c.dep_ == "prep"):
            if f"{lemma} {prep.lower_}" in self.phrasal:
                self._source = "phrasal"
                return self.phrasal[f"{lemma} {prep.lower_}"] or None
        # "get lost", "got hurt": "get" with a past participle
        passive = next((c.lemma_ for c in verb.children if c.dep_ == "auxpass"), None)
        if passive and f"{passive} {verb.lower_}" in self.phrasal:
            self._source = "phrasal"
            return self.phrasal[f"{passive} {verb.lower_}"]
        obj = next((c for c in verb.children if c.dep_ == "dobj"), None)
        if obj is not None and f"{lemma} {obj.lemma_.lower()}" in self.phrasal:
            self._source = "phrasal"
            return self.phrasal[f"{lemma} {obj.lemma_.lower()}"] or None
        # "We had hot chocolate", "I had pizza": eating
        if lemma == "have" and obj is not None and obj.lemma_.lower() in self.foods:
            return "eat"
        if lemma in ("be", "get", "feel") and any(c.dep_ == "acomp" for c in verb.children):
            word = next(c for c in verb.children if c.dep_ == "acomp")
            if word.lower_ in ("sick", "hurt", "injured", "ill"):
                return "loss"
            if word.lower_ in ("better", "well"):
                return "recover"
            return None
        action = self.action_of.get(lemma)
        # "My grandma knitted me a scarf": something made or given for the child, whatever the verb
        if action is None and obj is not None and any(c.dep_ == "dative" and c.lower_ in ("me", "us")
                                                      for c in verb.children):
            return "kindness"
        # "I miss my grandpa", "I will miss her": missing a person is sad, not a missed bus
        if lemma == "miss" and obj is not None and (obj.lower_ in ("her", "him", "them", "you")
                                                    or self._role(obj) in ("person", "pet")):
            return "loss"
        # "We went to the dentist": going somewhere is not always fun
        if action == "fun" and lemma in ("go", "visit"):
            place = next((g for c in verb.children if c.dep_ == "prep" for g in c.children if g.dep_ == "pobj"), None)
            if place is not None and place.lemma_.lower() in self.chore_places:
                return None
        # "the power went out", "the plane flew": things moving are not an outing
        if action == "fun" and self._role(self._subject(verb)) == "thing":
            return None
        # "My mom made me soup", "I made him a card": made for someone
        if action == "achieve" and any(c.dep_ == "dative" for c in verb.children):
            return "kindness"
        return action

    @staticmethod
    def _subject(verb):
        token = verb
        for _ in range(4):
            subject = next((c for c in token.children if c.dep_ in ("nsubj", "nsubjpass")), None)
            if subject is not None:
                return subject
            if token.dep_ in ("xcomp", "conj", "ccomp", "advcl") and token.head.i != token.i:
                token = token.head
            else:
                break
        return None

    def _role(self, token) -> str:
        if token is None:
            return "unknown"
        lower = token.lower_
        if lower in _CHILD:
            return "child"
        if lower in _BOT:
            return "bot"
        if lower in _PERSON_PRONOUNS:
            return "person"
        lemma = token.lemma_.lower()
        # "my dog Max" is a pet; "my dog food" is not
        if lower in self._pet_names or lemma in self.pets or (token.pos_ == "PROPN" and any(
                c.lemma_.lower() in self.pets for c in token.children if c.dep_ in ("compound", "amod"))):
            return "pet"
        if lemma in self.relations or token.ent_type_ == "PERSON" or token.pos_ == "PROPN":
            return "person"
        if lemma in ("kid", "kids", "boy", "girl", "man", "woman", "lady", "guy", "teacher", "coach", "stranger",
                     "people", "friend", "classmate"):
            return "person"
        return "thing"

    def _target(self, verb) -> Optional[str]:
        # "threw sand at me": the child is the one it was done to, whatever was thrown
        for child in verb.children:
            if child.dep_ == "prep" and child.lower_ in ("at", "on", "to", "into"):
                if any(g.dep_ == "pobj" and g.lower_ in ("me", "us") for g in child.children):
                    return "child"
        for child in verb.children:
            if child.dep_ in ("dobj", "dative", "attr") or (child.dep_ == "pobj"):
                if child.lower_ in ("me", "us"):
                    return "child"
                if any(c.dep_ == "poss" and c.lower_ in ("my", "our") for c in child.children):
                    return "child_thing" if self._role(child) == "thing" else self._role(child)
                return self._role(child)
            if child.dep_ == "prep":
                obj = next((c for c in child.children if c.dep_ == "pobj"), None)
                if obj is not None and obj.lower_ in ("me", "us"):
                    return "child"
        return None

    @staticmethod
    def _negated(verb) -> bool:
        # "I didn't get invited": the "not" can sit on the helper "get"
        if any(c.dep_ in ("auxpass", "aux") and any(g.dep_ == "neg" for g in c.children) for c in verb.children):
            return True
        return any(c.dep_ == "neg" for c in verb.children) or any(
            c.lower_ in ("never", "nobody", "nothing", "no") and c.dep_ in ("neg", "nsubj", "dobj", "det", "advmod")
            for c in verb.children)

    def _modality(self, event, root, sentence) -> str:
        words = [t.lower_ for t in sentence]
        if "if" in words and words[:1] == ["what"]:
            return HYPOTHETICAL
        if any(t.dep_ == "mark" and t.lower_ == "if" for t in event.children):
            return HYPOTHETICAL
        chain = [event] + [a for a in event.ancestors if a.sent == sentence][:3]
        for verb in chain:
            if verb.lemma_ in _HOPE_VERBS:
                return HOPE
            if verb.lemma_ == "wish":
                return WANT  # "I wish I had a puppy"
            if verb.lemma_ in ("want", "wanna") or (verb.lemma_ in ("like", "love") and any(
                    c.lower_ in ("would", "'d") for c in verb.children)):
                if verb.i != event.i or any(c.dep_ in ("xcomp", "dobj") for c in verb.children):
                    return WANT
            if verb.lemma_ in ("have", "need", "got") and verb.i != event.i and \
                    any(c.dep_ == "aux" and c.lower_ == "to" for c in event.children):
                return OBLIGATION
        # "I would've won", "I should've studied": what did not happen
        own = {c.lower_ for c in event.children if c.dep_ == "aux"}
        if own & {"would", "could", "should", "might", "'d"} and own & {"have", "'ve", "of"}:
            self._counterfactual = True
            return HYPOTHETICAL
        for verb in chain[:2]:
            auxes = {c.lower_ for c in verb.children if c.dep_ == "aux"}
            if auxes & _FUTURE_AUX and not self._negated(verb):
                return FUTURE
            # "We're going to Disneyland", "I'm going to be a ninja"
            if verb.lemma_ == "go" and verb.tag_ == "VBG" and (
                    any(c.dep_ == "xcomp" for c in verb.children) or any(c.dep_ == "aux" for c in verb.children)):
                return FUTURE
            if verb.dep_ == "xcomp" and verb.head.lemma_ == "go" and verb.head.tag_ == "VBG":
                return FUTURE
            # "We can't go": not able to, which is real (and negated), not a possibility
            if auxes & _POSSIBLE_AUX and not sentence.text.strip().endswith("?") and not self._negated(verb):
                return POSSIBLE
        return REAL

    @staticmethod
    def _tense(verb, modality: str) -> str:
        if modality == FUTURE:
            return "future"
        if verb.tag_ in ("VBD", "VBN") or any(c.dep_ in ("aux", "auxpass") and c.tag_ == "VBD" for c in verb.children):
            return "past"
        return "present"

    def _valence(self, a: Appraisal) -> str:
        """How the event feels for the child"""
        table = self.valence.get(a.action or "", {})
        valence = table.get(f"{a.actor}>{a.target}") or table.get(f"{a.actor}>") or table.get(f">{a.target}") \
            or table.get("default", "neutral")
        if a.action is None:
            # Evaluative words in the clause: "it was scary", "the movie was awesome"
            words = {t.lower_ for t in a.root.subtree}
            if words & self.negative_words:
                valence = "negative"
            elif words & self.positive_words:
                valence = "positive"
        if a.negated and valence in ("positive", "negative"):
            # "I didn't win", "he didn't hit me" (a relief), "I don't want her to die"
            valence = {"positive": "negative", "negative": "positive"}[valence]
            if a.modality in (WANT, HOPE) and table.get("default") == "negative":
                valence = "negative"  # not wanting something bad: still a sad topic
        return valence
