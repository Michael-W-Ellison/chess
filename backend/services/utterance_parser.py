"""
Utterance Parser
Turns a user message into a dependency parse tree with spaCy

The parse is the input analysis layer for the rule-based response engine:
each token carries its base form (lemma), part of speech, dependency relation
and head, so rules can match sentence structure instead of exact wording.

spaCy and its English model are optional. If they are not installed,
is_available() returns False and callers fall back to keyword handling.
"""

import logging
import re
from functools import lru_cache

logger = logging.getLogger("chatbot.utterance_parser")

MODEL_NAME = "en_core_web_sm"

# Common spellings in children's messages, mapped to standard forms the parser knows
NORMALIZATIONS = {
    "i": "I",
    "im": "I'm",
    "ive": "I've",
    "dont": "don't",
    "cant": "can't",
    "wont": "won't",
    "didnt": "didn't",
    "doesnt": "doesn't",
    "isnt": "isn't",
    "wasnt": "wasn't",
    "luv": "love",
    "u": "you",
    "ur": "your",
    "r": "are",
    "becuz": "because",
    "becoz": "because",
    "cuz": "because",
    "bc": "because",
    "wanna": "want to",
    "gonna": "going to",
    "gotta": "got to",
    "fav": "favorite",
    "fave": "favorite",
    "favourite": "favorite",
    "colour": "color",
    "pls": "please",
    "plz": "please",
    "bday": "birthday",
    "bro": "brother",
    "sis": "sister",
    "shes": "she's",
    "hes": "he's",
    "theyre": "they're",
    "youre": "you're",
    "arent": "aren't",
    "werent": "weren't",
    "couldnt": "couldn't",
    "wouldnt": "wouldn't",
    "shouldnt": "shouldn't",
    "havent": "haven't",
    "hasnt": "hasn't",
    "whos": "who's",
    "lotsa": "lots of",
    "kinda": "kind of",
    "sorta": "sort of",
    "outta": "out of",
    "gimme": "give me",
    "lemme": "let me",
    "dunno": "don't know",
    "yall": "you all",
    "y'all": "you all",
    "wheres": "where's",
    # Past tenses children make regular: "I goed", "we runned"
    "goed": "went", "runned": "ran", "eated": "ate", "hitted": "hit", "drawed": "drew", "throwed": "threw",
    "losted": "lost", "beated": "beat", "builded": "built", "swimmed": "swam", "catched": "caught",
    "buyed": "bought", "bringed": "brought", "brang": "brought", "brung": "brought", "teached": "taught",
    "thinked": "thought", "falled": "fell", "feeled": "felt", "sleeped": "slept", "maked": "made",
    "taked": "took", "gived": "gave", "comed": "came", "sayed": "said", "telled": "told", "finded": "found",
    "rided": "rode", "writed": "wrote", "drinked": "drank", "blowed": "blew", "growed": "grew",
    "knowed": "knew", "hided": "hid", "bited": "bit", "breaked": "broke", "choosed": "chose",
    "forgetted": "forgot", "getted": "got", "digged": "dug", "standed": "stood", "sitted": "sat",
    "stealed": "stole", "sticked": "stuck", "weared": "wore", "winned": "won", "leaved": "left",
    "meeted": "met", "keeped": "kept", "speaked": "spoke", "waked": "woke", "shaked": "shook",
    "spinned": "spun", "drived": "drove", "feeded": "fed", "hurted": "hurt", "cutted": "cut",
    "shutted": "shut", "spended": "spent", "sended": "sent", "haved": "had", "doed": "did",
    "flyed": "flew", "fighted": "fought", "freezed": "froze", "readed": "read",
    "ringed": "rang", "shooted": "shot", "slided": "slid", "swinged": "swung", "throwded": "threw",
    "thats": "that's",
    "theres": "there's",
    "heres": "here's",
    "whats": "what's",
    "idk": "I don't know",
    "nm": "not much",
    "rn": "right now",
    "gtg": "got to go",
    "g2g": "got to go",
    "ttyl": "talk to you later",
    "brb": "be right back",
    "jk": "just kidding",
    # Common misspellings and texting shortcuts
    "lik": "like",
    "liek": "like",
    "alot": "a lot",
    "bilt": "built",
    "hous": "house",
    "rlly": "really",
    "rly": "really",
    "realy": "really",
    "wierd": "weird",
    "tomorow": "tomorrow",
    "tmrw": "tomorrow",
    "favrite": "favorite",
    "awsome": "awesome",
    "beutiful": "beautiful",
    "togther": "together",
    "becuase": "because",
    "beacuse": "because",
    "frend": "friend",
    "freind": "friend",
    "frends": "friends",
    "freinds": "friends",
    "skool": "school",
    "wat": "what",
    "wut": "what",
    "sumthing": "something",
    "somthing": "something",
    "gud": "good",
    "kool": "cool",
    "prolly": "probably",
    "probly": "probably",
    "tmrw": "tomorrow",
    "tmr": "tomorrow",
    "tomorow": "tomorrow",
    "tommorow": "tomorrow",
    "2day": "today",
    "2morrow": "tomorrow",
    "b4": "before",
    "gr8": "great",
    "nvm": "never mind",
    "ppl": "people",
    "cya": "bye",
    "thx": "thanks",
    "ty": "thank you",
    "favrite": "favorite",
    "favorit": "favorite",
    "pizzza": "pizza",
    "sooo": "so",
    "soo": "so",
    "verry": "very",
    "vary": "very",
    "dinosour": "dinosaur",
    "dinosours": "dinosaurs",
    "minecraf": "minecraft",
    "helo": "hello",
    "hellow": "hello",
    "nme": "name",
    "naem": "name",
    "calld": "called",
    "caled": "called",
    "relly": "really",
    "reely": "really",
    "dogz": "dogs",
    "catz": "cats",
    "k": "ok",
    "kk": "ok",
    "okk": "ok",
    "okey": "okay",
    "sed": "said",
    "becaus": "because",
    "scool": "school",
    "favirite": "favorite",
    "pritty": "pretty",
}

_EMOJI_WORDS = {
    **dict.fromkeys("😂🤣😆😄😁😹", "haha"),
    **dict.fromkeys("😊🙂😀😃☺", "I am happy"),
    **dict.fromkeys("👍👌✅", "ok"),
    **dict.fromkeys("❤💕💖💗💙💜🥰😍😻", "aww"),
    **dict.fromkeys("😢😭😞😔☹🙁😿💔", "I am sad"),
    **dict.fromkeys("😡😠🤬", "I am mad"),
    **dict.fromkeys("😱😨😰", "I am scared"),
    **dict.fromkeys("😴🥱", "I am sleepy"),
    **dict.fromkeys("🤔", "hmm"),
    **dict.fromkeys("👋", "hi"),
    **dict.fromkeys("😮😲🤯", "wow"),
    **dict.fromkeys("🎉🥳🙌👏", "yay"),
}

# "hiii", "heyyy", "hellooo": a greeting, not a name
_STRETCHED_GREETINGS = [
    (re.compile(r"^h+i+$", re.IGNORECASE), "hi"),
    (re.compile(r"^h+e+y+$", re.IGNORECASE), "hey"),
    (re.compile(r"^h+e+l+o+$", re.IGNORECASE), "hello"),
    (re.compile(r"^b+y+e+$", re.IGNORECASE), "bye"),
    (re.compile(r"^y+o+$", re.IGNORECASE), "yo"),
]
# Emoji and other pictographs: not words, so they are not echoed back ("Your cat is fluffy 😻?")
_EMOJI_RE = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F\u200D\u2B50\u2764]")

# Spellings that are also words, replaced only where the next word shows which is meant:
# "its so fun" (it's), "ill try" (I'll); "its wings" and "I feel ill" stay
_GOING_VERBS = r"(go|goes|going|went|gone|come|came|coming|walk|walked|drive|drove|ran|run|moved?|travel|flew|fly|"\
               r"trip|visit|back|way|road|welcome|next|due|according|close|up|down|out|over|on|from)$"
_CONTEXT_NORMALIZATIONS = [
    # "to much homework", "it's to hot"
    # (not after a verb of going: "we went to Big Bear")
    (re.compile(r"\b(\w+) to(?= (much|hot|cold|big|small|hard|scary|loud|late|early|tired|full|long|fast|slow|"
                r"short|high|heavy|far|young|old|spicy|sweet|bright|dark)\b)", re.IGNORECASE),
     lambda m: m.group(0) if re.match(_GOING_VERBS, m.group(1), re.IGNORECASE) else f"{m.group(1)} too"),
    (re.compile(r"\bits(?= (so|really|very|not|too|just|a|an|the|my|ok|okay|fine|fun|boring|hard|easy|cool|"
                r"great|good|bad|true|time|going|gonna|like|always|never|raining|snowing|gross|yummy|awesome|"
                r"amazing|weird|scary|funny|cute|about|mine|yours|over|super|kind|pretty|beautiful|ugly|big|bigger|"
                r"small|smaller|huge|tiny|heavy|soft|red|orange|yellow|green|blue|purple|pink|brown|black|white|"
                r"gray|grey|sticky|shiny|sparkly|broken|done|finished|lost|gone|made|called|still|almost|my)\b)",
     re.IGNORECASE),
     "it's"),
    (re.compile(r"\bur(?= (so|really|very|not|the|a|an|my|weird|cool|funny|nice|mean|smart|awesome|silly|dumb|"
                r"stupid|annoying|best|worst|welcome|right|wrong|crazy|lying|kidding|joking|amazing|great|good|"
                r"bad|too)\b)", re.IGNORECASE),
     "you're"),
    # "your so funny", "your the best"; an adjective only at the end ("your funny face" stays)
    (re.compile(r"\byour(?= (so|really|very|not|the|a|an|too|being|going|gonna|welcome|always|never|my|such|"
                r"kidding|joking|lying)\b|(?= (funny|silly|cool|nice|mean|smart|awesome|weird|dumb|cute|amazing|"
                r"annoying|right|wrong|crazy|great|best|the best)\s*[.!?]*$))", re.IGNORECASE),
     "you're"),
    # "I could of won"
    (re.compile(r"\b(could|would|should|must|might) of\b", re.IGNORECASE), r"\1 have"),
    (re.compile(r"\blets(?= (play|go|do|make|watch|build|talk|be|see|try|have|pretend|sing|draw|read)\b)",
                re.IGNORECASE), "let's"),
    (re.compile(r"\bill(?= (try|do|be|go|ask|tell|practice|study|see|talk|play|have|get|make|show|let|just|never|"
                r"always|probably|draw|read|call|text|come|help|work|remember|eat|drink|wait|clean|finish|sleep|bring|"
                r"buy|use|build|write|stop|take|give|send|keep|think|put|pick|sit|stay|watch|listen|look|fix|"
                r"share|win|beat|check|miss|need|wear|sing|dance|run|swim|ride)\b)", re.IGNORECASE),
     "I'll"),
]
# "my moms room" -> "my mom's room"
_POSSESSIVE_RE = re.compile(
    r"\b(mom|dad|mommy|daddy|sister|brother|grandma|grandpa|friend|cousin|aunt|uncle|cat|dog|puppy|kitten|"
    r"hamster|fish|bunny|horse)s (?=(room|house|car|bed|phone|office|work|birthday|friend|dog|cat|toys?|lap|side|"
    r"name|bowl|food|tail|collar|cage|leash)\b)", re.IGNORECASE
)
_QUESTION_START_RE = re.compile(r"^(what|how|where|when|why|who|do|does|are|is|can|will)\b", re.IGNORECASE)
_JOINED_QUESTION_RE = re.compile(
    r",?\s+and\s+(?=(how|what|where|when|why|who|do you|are you|can you|will you)\b)", re.IGNORECASE
)
# "a snowman named frosty" -> "a snowman named Frosty"
_NAMED_RE = re.compile(r"\b(named|called) (?!(after|it|him|her|them|me|you|us|that|this|what|a|an|the|my)\b)([a-z])")
# "his name was nemo" -> "his name was Nemo"
_NAME_IS_RE = re.compile(
    r"\b(name (?:is|was|'s)) (?!(not|a|an|the|my|so|really|very|too|kind|cool|weird|nice|funny|silly|pretty|great|"
    r"awesome|beautiful|long|short|hard|easy|dumb|stupid|ugly|cute|good|bad|special|unique|strange|boring|perfect|"
    r"fine|ok|okay|lovely|fancy|same|different|tricky|interesting)\b)([a-z])")
# "their names are luna and milo" -> "their names are Luna and Milo"
_NAMES_ARE_RE = re.compile(r"\b(names are) ([a-z]+) and ([a-z]+)\b")
# Places a child may name in lowercase
_PLACES = ["alabama", "alaska", "arizona", "arkansas", "california", "colorado", "connecticut", "delaware",
           "florida", "georgia", "hawaii", "idaho", "illinois", "indiana", "iowa", "kansas", "kentucky",
           "louisiana", "maine", "maryland", "massachusetts", "michigan", "minnesota", "mississippi", "missouri",
           "montana", "nebraska", "nevada", "ohio", "oklahoma", "oregon", "pennsylvania", "tennessee", "texas",
           "utah", "vermont", "virginia", "washington", "wisconsin", "wyoming", "canada", "mexico", "england",
           "france", "spain", "italy", "germany", "china", "japan", "india", "australia", "brazil", "africa",
           "europe", "disneyland", "disney world", "new york", "chicago", "paris", "london", "hawaii"]
_PLACES_RE = re.compile(r"\b(" + "|".join(sorted(set(_PLACES), key=len, reverse=True)) + r")\b")
# Songs, books, games and shows children name in lowercase
_TITLES = {
    "fur elise": "Für Elise", "twinkle twinkle little star": "Twinkle Twinkle Little Star",
    "jingle bells": "Jingle Bells", "happy birthday": "Happy Birthday", "harry potter": "Harry Potter",
    "minecraft": "Minecraft", "roblox": "Roblox", "fortnite": "Fortnite", "pokemon": "Pokémon",
    "mario kart": "Mario Kart", "mario": "Mario", "zelda": "Zelda", "spiderman": "Spider-Man",
    "spider-man": "Spider-Man", "batman": "Batman", "superman": "Superman",
    "moana": "Moana", "encanto": "Encanto", "bluey": "Bluey", "paw patrol": "Paw Patrol",
    "peppa pig": "Peppa Pig", "lego": "LEGO", "legos": "LEGOs", "star wars": "Star Wars",
    "dog man": "Dog Man", "captain underpants": "Captain Underpants", "among us": "Among Us",
    "animal crossing": "Animal Crossing", "toy story": "Toy Story", "sonic": "Sonic",
    "youtube": "YouTube", "tiktok": "TikTok", "nintendo": "Nintendo", "xbox": "Xbox",
    "saturn": "Saturn", "jupiter": "Jupiter", "mars": "Mars", "venus": "Venus", "neptune": "Neptune",
    "uranus": "Uranus", "pluto": "Pluto", "halloween": "Halloween", "christmas": "Christmas",
    "easter": "Easter", "thanksgiving": "Thanksgiving", "hanukkah": "Hanukkah", "diwali": "Diwali",
    "mickey": "Mickey", "minnie": "Minnie", "elsa": "Elsa", "space mountain": "Space Mountain",
    "disney": "Disney", "legoland": "LEGOLAND", "kit kat": "Kit Kat", "kitkat": "KitKat", "skittles": "Skittles", "m&ms": "M&Ms", "reeses": "Reese's",
}
_TITLES_RE = re.compile(r"\b(" + "|".join(re.escape(t) for t in sorted(_TITLES, key=len, reverse=True)) + r")\b")
_NOT_SUBJECT_WORDS = {"then", "now", "so", "yes", "no", "well", "okay", "ok", "also", "today", "yesterday",
                      "tonight", "later", "after", "first", "next", "finally", "there", "here", "just"}
_ME_AND_RE = re.compile(r"(^|[.!?] )me and ((?:my |our )?(?!my\b|our\b)[a-z]+)(?= [a-z])", re.IGNORECASE)
_WEEKDAY_RE = re.compile(r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|january|february|april|"
                         r"june|july|august|september|october|november|december)\b")
# "its math" (a whole message): "it's math"
_ITS_ALONE_RE = re.compile(r"^its (?=[a-z]*[a-rt-z][.!]*$)", re.IGNORECASE)  # not "its wings"
# "mr kim" -> "Mr Kim", so the parser reads a name
_TITLE_RE = re.compile(r"\b(mr|mrs|ms|dr)\.? ([a-z])", re.IGNORECASE)

_WORD_RE = re.compile(r"[^\W\d_]+")  # letters, including accented ones ("Für")


def repair_parse(doc):
    """
    Fix a parse error the small English model makes with "had"/"has" as the main verb:
    in "The cupcakes had sprinkles" and "The pizza had pepperoni" it reads "had" as a helper
    verb and the object as the root. The helper becomes the root and the object its object.
    """
    for sentence in list(doc.sents):
        root = sentence.root
        helper = next((c for c in root.children if c.dep_ == "aux" and c.lemma_ == "have"), None)
        # The subject on the noun ("the cupcakes had sprinkles") or on "had" ("they had sprinkles")
        subject = next((c for c in root.children if c.dep_ == "nsubj"), None) or (
            next((c for c in helper.children if c.dep_ == "nsubj"), None) if helper is not None else None)
        # "I had eaten" (a real helper) has a past participle; "had sprinkles" does not
        if helper is None or subject is None or root.tag_ in ("VBN", "VBG") or helper.i > root.i:
            continue
        if any(c.dep_ in ("dobj", "aux") and c.i != helper.i for c in root.children):
            continue
        movers = [c for c in root.children
                  if c.i < root.i and c.i != helper.i and c.dep_ in ("nsubj", "neg", "advmod", "aux", "cc")]
        movers += [c for c in root.children if c.dep_ == "punct" and c.i > root.i]
        helper.head = helper
        helper.dep_ = "ROOT"
        helper.pos_ = "VERB"
        for token in movers:
            token.head = helper
        root.head = helper
        root.dep_ = "dobj"
        if root.pos_ == "VERB":
            root.pos_ = "NOUN"
            root.tag_ = "NNS" if root.text.lower().endswith("s") else "NN"
    _repair_objects(doc)
    _extend_person_names(doc)
    _repair_tags(doc)
    return doc


# Words the model tags as names when written in lowercase, though they are not names
_INTERJECTIONS = {"lol", "haha", "hahaha", "hehe", "lmao", "omg", "sup", "yay", "wow", "ugh", "yikes", "oops", "hmm",
                  "ok", "okay", "yep", "nope", "yeah", "aww", "aw", "woohoo", "brb", "idk", "jk"}
_COMMON_NOUNS = {"heaven", "pizza", "taco", "tacos", "banana", "bananas", "cookie", "cookies", "candy", "cake",
                 "school", "home", "park", "zoo", "beach", "pool", "recess", "lunch", "dinner", "breakfast",
                 "homework", "math", "art", "science", "music", "soccer", "basketball", "football", "baseball",
                 "chess", "legos", "lego", "slime", "pancakes", "nuggets", "fries", "spaghetti", "dinosaurs"}
_WEEKDAYS_AND_MONTHS = {"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "january",
                        "february", "march", "april", "june", "july", "august", "september", "october",
                        "november", "december"}
# Base forms of verbs, and irregular verb forms with their base ("swam" -> "swim"), from the
# model's lemmatizer tables (set when the model loads)
_VERBS: set = set()
_IRREGULAR_VERBS: dict = {}
# People and animals a child names as the subject: "my dog snores", "the baby cries"
_ANIMATE = {"dog", "cat", "puppy", "kitten", "baby", "brother", "sister", "mom", "dad", "mommy", "daddy", "friend",
            "grandma", "grandpa", "teacher", "bird", "fish", "hamster", "bunny", "horse", "cousin", "uncle", "aunt",
            "coach", "neighbor", "dogs", "cats", "birds", "kids", "boy", "girl",
            # Body parts: "my knee tickles", "my tummy hurts"
            "tummy", "knee", "head", "arm", "leg", "foot", "tooth", "throat", "ear", "nose", "eye", "back", "hand",
            "finger", "toe", "stomach", "belly", "skin"}
# Words a child puts before a name: "my friend ava", "my dog coco"
_NAMED_KINDS = {"friend", "bff", "brother", "sister", "cousin", "teacher", "coach", "neighbor", "uncle", "aunt",
                "dog", "cat", "puppy", "kitten", "hamster", "bunny", "horse", "fish", "bird", "turtle", "pony",
                "guinea", "lizard", "snake", "parrot", "goldfish"}
_NOUNS: set = set()  # filled from the lemmatizer's tables
_DETERMINERS = {"the", "a", "an", "my", "your", "his", "her", "their", "our", "this", "that"}
_AMOUNT_NOUNS = {"lots", "lot", "ton", "tons", "bunch", "bunches", "pile", "piles", "couple", "load", "loads", "bit"}
# Verbs that take a receiver and a thing: "make me a card", "read us a story"
_GIVING_VERBS = {"make", "give", "get", "buy", "bake", "draw", "send", "bring", "write", "show", "build", "cook",
                 "paint", "sing", "read", "tell", "find", "save", "knit", "sew", "pick"}
_OBJECT_PRONOUNS = {"me", "him", "her", "us", "them"}
_QUESTION_AUX = {"do", "does", "did", "can", "could", "will", "would", "should"}
_COPULAS = {"is", "are", "was", "were", "am", "'s", "'re", "'m"}


def _verb_base(word: str):
    """ "snores" -> "snore", "swam" -> "swim", "chases" -> "chase"; None if not a verb form"""
    if word in _IRREGULAR_VERBS:
        return _IRREGULAR_VERBS[word]
    if word.endswith("s"):
        for base in (word[:-1], word[:-2], word[:-3] + "y" if word.endswith("ies") else None):
            if base and base in _VERBS:
                return base
    return None


def _is_participle(word: str) -> bool:
    """True if the word is the past form of a verb ("played", "stopped", "tried", "swum"; not "ted")"""
    if word in _IRREGULAR_VERBS:
        return True
    if word.endswith("d") and word[:-1] in _VERBS:
        return True  # "invited"
    if word.endswith("ed"):
        stem = word[:-2]
        if stem in _VERBS or (len(stem) > 2 and stem[-1] == stem[-2] and stem[:-1] in _VERBS) \
                or (stem.endswith("i") and stem[:-1] + "y" in _VERBS):
            return True
    return False


def _repair_compound_subject(sentence) -> None:
    """
    "my dog snores", "jake hugs", "the baby cries": the subject read as a compound on a plural
    "noun" that is really the verb
    """
    root = sentence.root
    if root.pos_ in ("ADV", "ADJ"):
        # "grandpa snores really loud": "loud" read as the root, "snores" as its subject
        noun = next((c for c in root.children if c.dep_ == "nsubj" and c.pos_ == "NOUN"
                     and _verb_base(c.lower_) and c.i < root.i), None)
        if noun is None:
            return
        for child in list(root.children):
            if child.i != noun.i:
                child.head = noun
        noun.head, noun.dep_ = noun, "ROOT"
        root.head, root.dep_ = noun, "advmod"
        root = noun
    if root.pos_ != "NOUN" or any(c.dep_ in ("nsubj", "nsubjpass") for c in root.children):
        return
    base = _verb_base(root.lower_)
    if base is None:
        return
    # "a spider bit me": an object pronoun after it shows the "noun" is a verb
    takes_object = any(c.dep_ in ("appos", "dobj") and c.lower_ in _OBJECT_PRONOUNS and c.i == root.i + 1
                       for c in root.children)
    subject = next((c for c in root.children if c.dep_ in ("compound", "amod") and c.i == root.i - 1
                    and (c.lower_ in _ANIMATE or c.pos_ == "PROPN" or (takes_object and c.pos_ in ("NOUN", "ADJ")))), None)
    if subject is None:
        return
    for child in root.children:
        if child.dep_ == "appos" and child.lower_ in _OBJECT_PRONOUNS:
            child.dep_ = "dobj"
    for child in list(root.children):
        # "my" and "the" belong to the subject
        if child.dep_ in ("poss", "det") and child.i < subject.i:
            child.head = subject
    subject.dep_, subject.pos_ = "nsubj", ("PROPN" if subject.pos_ == "PROPN" else "NOUN")
    for child in list(root.children):
        # "our new puppy cries": "new" belongs to the subject
        if child.dep_ == "amod" and child.i < subject.i:
            child.head = subject
    tag = "VBD" if root.lower_ in _IRREGULAR_VERBS and not root.lower_.endswith("s") else "VBZ"
    root.pos_, root.tag_, root.lemma_ = "VERB", tag, base


def _repair_question_verb(sentence) -> None:
    """
    "can fish swim", "do dogs dance", "how do dogs bark": the subject read as the verb and the
    verb as its object. The verb becomes the root, the subject its subject.
    """
    words = [t for t in sentence if not t.is_punct]
    start = 1 if words and words[0].tag_ in ("WRB", "WP") else 0
    if len(words) < start + 3 or words[start].lower_ not in _QUESTION_AUX:
        return
    aux = words[start]
    # "does your dog bark": skip the subject's determiner
    determiners = [w for w in words[start + 1:start + 3] if w.lower_ in _DETERMINERS]
    if len(words) < start + 3 + len(determiners):
        return
    subject, verb = words[start + 1 + len(determiners)], words[start + 2 + len(determiners)]
    if verb.lower_ not in _VERBS or verb.pos_ == "VERB" and verb.dep_ == "ROOT":
        return
    if subject.lower_ in ("you", "i", "we", "they", "he", "she", "it"):
        return  # pronoun subjects parse fine
    if subject.dep_ not in ("ROOT", "dobj", "compound", "nsubj") or verb.dep_ not in ("dobj", "ROOT", "npadvmod", "nsubj",
                                                                                   "compound", "conj", "xcomp"):
        return
    rest = [t for t in sentence if t.i != verb.i]
    verb.head, verb.dep_, verb.pos_, verb.tag_, verb.lemma_ = verb, "ROOT", "VERB", "VB", verb.lower_
    for token in rest:
        if token in determiners:
            token.head, token.dep_ = subject, "poss" if token.tag_ == "PRP$" else "det"
        elif token.i == subject.i:
            token.head, token.dep_ = verb, "nsubj"
            token.pos_ = "PROPN" if token.pos_ == "PROPN" else "NOUN"
            token.tag_ = "NNS" if token.lower_.endswith("s") else "NN"
        elif token.i == aux.i:
            token.head, token.dep_, token.pos_ = verb, "aux", "AUX"
        elif token.i < aux.i:
            token.head, token.dep_ = verb, "advmod"  # "how"
        elif token.head.i in (subject.i, aux.i) or token.dep_ == "ROOT":
            token.head = verb


def _extend_person_names(doc) -> None:
    """ "taylor swift": the person tag covers "taylor" only; the surname is part of the name"""
    ents = list(doc.ents)
    changed = False
    for k, ent in enumerate(ents):
        last = ent[-1]
        if ent.label_ == "PERSON" and last.i + 1 < len(doc):
            following = doc[last.i + 1]
            if last.dep_ == "compound" and last.head.i == following.i and following.is_alpha and following.pos_ in ("NOUN", "PROPN"):
                ents[k] = doc[ent.start:following.i + 1]
                ents[k].label_ = "PERSON"
                changed = True
    if changed:
        try:
            from spacy.tokens import Span
            doc.ents = [Span(doc, e.start, e.end, label="PERSON") if e.label_ == "PERSON" else e for e in ents]
            for e in doc.ents:
                if e.label_ == "PERSON":
                    for t in e:
                        t.pos_, t.tag_ = "PROPN", "NNP"
        except Exception as e:  # overlapping entities: keep the model's
            logger.debug(f"Could not extend name: {e}")


def _repair_tags(doc) -> None:
    """
    Part-of-speech errors of the small model on children's messages:
    "lol", "haha" read as names; "tacos", "heaven" read as names when lowercase;
    "do you like pizza" with "like" as a preposition; "how do fish sleep" and "my tummy
    hurts" with the verb read as a noun; "why is the sky blue" with "is" as a helper verb
    """
    for token in doc:
        lower = token.lower_
        if token.pos_ == "PROPN" and token.is_lower and lower in _INTERJECTIONS:
            token.pos_, token.tag_ = "INTJ", "UH"
        elif token.pos_ == "PROPN" and ((token.is_lower and lower in _COMMON_NOUNS) or any(
                c.dep_ == "det" and c.lower_ in ("a", "an") for c in token.children)):
            # "a bee stung me": a name does not take "a"
            token.pos_ = "NOUN"
            token.tag_ = "NNS" if lower.endswith("s") else "NN"
        # "can fish go to heaven": a subject is not a finite verb ("swimming is fun" is a gerund, VBG)
        if token.dep_ in ("nsubj", "nsubjpass") and token.pos_ == "VERB" and token.tag_ != "VBG" and not any(
                c.dep_ in ("nsubj", "aux", "dobj") for c in token.children):
            token.pos_ = "NOUN"
            token.tag_ = "NNS" if lower.endswith("s") else "NN"
        # "they're so mean": a complement of "be" is an adjective
        if token.dep_ == "acomp" and token.pos_ == "VERB" and token.tag_ not in ("VBN", "VBG"):
            token.pos_, token.tag_ = "ADJ", "JJ"
        # "lol just kidding": an interjection, not the subject
        if token.pos_ == "INTJ" and token.dep_ == "nsubj":
            token.dep_ = "intj"
        # "do you like pizza": "like" with a subject is the verb
        if token.lemma_ in ("like", "love") and token.pos_ == "ADP" and any(
                c.dep_ == "nsubj" for c in token.children):
            token.pos_, token.tag_ = "VERB", "VBP"
    for token in doc:
        # "I'm happy and excited": the second feeling joins the first, not the verb
        if token.dep_ == "conj" and token.head.lemma_ == "be" and (token.tag_ == "JJ" or token.lower_ in _FEELING_WORDS) \
                and not any(c.dep_ in ("nsubj", "nsubjpass", "aux", "dobj") for c in token.children):
            first = next((c for c in token.head.children if c.dep_ == "acomp" and c.i < token.i), None)
            if first is not None:
                cc = next((c for c in token.head.children if c.dep_ == "cc" and first.i < c.i < token.i), None)
                token.head, token.pos_, token.tag_ = first, "ADJ", "JJ"
                if cc is not None:
                    cc.head = first
        if token.dep_ == "conj" and token.lower_ in _FEELING_WORDS and token.head.dep_ == "acomp" and token.pos_ == "VERB":
            token.pos_, token.tag_ = "ADJ", "JJ"  # "sad and scared"
        # "which is better, pizza or tacos": the choices hang on the verb, not on "better"
        if token.dep_ == "conj" and token.pos_ in ("NOUN", "PROPN") and token.head.pos_ == "ADJ" \
                and token.head.dep_ == "acomp":
            token.head = token.head.head
        # "maya, jake and zoe": the last name in a list read as a verb
        if token.dep_ == "conj" and token.pos_ == "VERB" and token.head.pos_ in ("PROPN", "NOUN") \
                and not any(c.dep_ not in ("punct", "cc") for c in token.children) \
                and token.lower_ not in _VERBS and not _verb_base(token.lower_):
            token.pos_, token.tag_ = token.head.pos_, token.head.tag_
        # "my mom said yes": the answer is what was said
        if token.lower_ in ("yes", "no", "okay", "ok", "sure", "maybe") and token.dep_ == "intj" \
                and token.head.lemma_ in ("say", "tell", "answer") and token.i > token.head.i:
            token.dep_ = "dobj"
        # "I don't want to": the "to" of a verb left unsaid, not punctuation
        if token.lower_ == "to" and token.dep_ == "punct" and token.head.pos_ in ("VERB", "AUX"):
            token.dep_, token.pos_ = "aux", "PART"
        # "our new puppy cries": "new" describes the noun after it, not the verb
        if token.dep_ == "amod" and token.head.pos_ in ("VERB", "AUX") and token.i + 1 < len(doc) \
                and doc[token.i + 1].pos_ in ("NOUN", "PROPN"):
            token.head = doc[token.i + 1]
        # "I have lots of homework", "a lot of friends": the thing is the object, the amount describes it
        if token.lower_ in _AMOUNT_NOUNS and token.dep_ in ("dobj", "nsubj", "attr", "pobj"):
            of = next((c for c in token.children if c.dep_ == "prep" and c.lower_ == "of"), None)
            thing = next((g for g in of.children if g.dep_ == "pobj"), None) if of is not None else None
            if thing is not None and thing.pos_ in ("NOUN", "PROPN"):
                thing.head, thing.dep_ = token.head, token.dep_
                token.head, token.dep_ = thing, "nmod"
                for child in list(token.children):
                    if child.dep_ == "det":
                        child.head = thing
        # "do you like pizza?": a verb's object read as the object of a preposition
        if token.dep_ == "pobj" and token.head.pos_ == "VERB" and token.head.i < token.i:
            token.dep_ = "dobj"
        # "tag you're it": a second subject after "be" is what the first one is
        if token.dep_ == "nsubj" and token.head.lemma_ == "be" and token.i > token.head.i and any(
                c.dep_ == "nsubj" and c.i < token.head.i for c in token.head.children):
            token.dep_ = "attr"
        # "I made you a card": "you" read as the subject of "card" instead of who it was made for
        if (token.lower_ in _OBJECT_PRONOUNS | {"you"} and token.dep_ == "nsubj" and token.head.pos_ == "NOUN"
                and token.head.dep_ in ("ccomp", "dobj", "xcomp") and token.head.head.lemma_ in _GIVING_VERBS
                and token.i == token.head.head.i + 1):
            noun, verb = token.head, token.head.head
            token.head, token.dep_ = verb, "dative"
            noun.dep_ = "dobj"
        # "I'm Sofia": a capitalized word the dictionary does not know, mid-sentence, is a name
        if (token.pos_ == "NOUN" and token.text[:1].isupper() and not token.is_sent_start and token.is_alpha
                and not _verb_base(token.lower_) and token.text != "I"
                and not any(c.dep_ == "det" and c.lower_ in ("a", "an") for c in token.children)
                and not any(t.text[:1].isupper() for t in token.sent if t.i != token.i and not t.is_sent_start
                            and t.text not in ("I", "I'm", "I've", "I'll", "I'd"))):
            token.pos_, token.tag_ = "PROPN", "NNP"
        # "I'm ted": a "participle" that is no verb's form is what the subject is (a name)
        if token.dep_ == "ROOT" and token.tag_ == "VBN" and token.is_alpha and not _is_participle(token.lower_):
            be = next((c for c in token.children if c.dep_ == "auxpass" and c.lemma_ == "be"), None)
            if be is not None:
                for child in list(token.children):
                    if child.i != be.i:
                        child.head = be
                        if child.dep_ == "nsubjpass":
                            child.dep_ = "nsubj"
                be.head, be.dep_ = be, "ROOT"
                token.head, token.dep_ = be, "attr"
                token.pos_, token.tag_, token.lemma_ = "PROPN", "NNP", token.lower_
        # "a dog bit me": the pronoun after the verb is its object
        if token.dep_ == "appos" and token.lower_ in _OBJECT_PRONOUNS and token.head.pos_ == "VERB":
            token.dep_ = "dobj"
        # "my friend ava came over": the name after "my friend" read as a common noun
        if token.pos_ in ("NOUN", "ADJ") and token.is_alpha and token.lower_ not in _NAMED_KINDS and (
                (token.dep_ == "appos" and token.head.lower_ in _NAMED_KINDS and token.i == token.head.i + 1)
                or (token.lower_ not in _NOUNS and not _verb_base(token.lower_) and token.i > 0 and doc[token.i - 1].lower_ in _NAMED_KINDS
                    and doc[token.i - 1].head.i == token.i and doc[token.i - 1].dep_ == "compound")):
            token.pos_, token.tag_ = "PROPN", "NNP"
        # "my cat whiskers is sleeping": a plural word taking "is" is one thing's name
        elif (token.tag_ == "NNS" and token.dep_ == "nsubj" and token.i > 0 and doc[token.i - 1].lower_ in _NAMED_KINDS
              and doc[token.i - 1].head.i == token.i and any(
                  c.dep_ in ("aux", "auxpass") and c.lower_ in ("is", "was", "'s") for c in token.head.children)
              or (token.tag_ == "NNS" and token.dep_ == "nsubj" and token.i > 0 and doc[token.i - 1].lower_ in _NAMED_KINDS
                  and doc[token.i - 1].head.i == token.i and token.head.lower_ in ("is", "was", "'s"))):
            token.pos_, token.tag_ = "PROPN", "NNP"
        # "I like jumping": "like" read as a helper of the gerund
        if token.lemma_ in ("like", "love", "hate", "enjoy") and token.dep_ == "aux" and token.head.tag_ in ("VBG", "VB"):
            verb = token.head
            subject = next((c for c in verb.children if c.dep_ == "nsubj"), None)
            head = verb.head if verb.dep_ != "ROOT" else token
            token.head, token.dep_ = head, verb.dep_ if verb.dep_ != "ROOT" else "ROOT"
            token.pos_, token.tag_ = "VERB", "VBP"
            verb.head, verb.dep_ = token, "xcomp"
            if subject is not None:
                subject.head = token
        # "I love to camp", "I have to camp": the verb after "to" read as a noun
        if token.pos_ == "NOUN" and token.lower_ in _VERBS and not any(c.dep_ in ("det", "poss", "amod") for c in token.children):
            to = None
            if token.dep_ == "xcomp" and any(c.lower_ == "to" for c in token.children):
                to = next(c for c in token.children if c.lower_ == "to")
            elif token.dep_ == "pobj" and token.head.lower_ == "to" and token.head.head.lemma_ in (
                    "love", "like", "want", "need", "try", "hate", "have", "get", "learn", "wanna"):
                to = token.head
                token.head, token.dep_ = to.head, "xcomp"
                to.head, to.dep_ = token, "aux"
            if to is not None or (token.dep_ == "ccomp" and token.head.lemma_ == "let"):
                # also "let's race": the suggested activity is a verb
                token.pos_, token.tag_, token.lemma_ = "VERB", "VB", token.lower_
    for sentence in doc.sents:
        # "maya and I went": the name is a subject too, not a modifier
        words = [t for t in sentence]
        if (len(words) > 3 and words[0].dep_ in ("npadvmod", "compound", "nmod", "advmod")
                and words[0].pos_ in ("PROPN", "NOUN", "ADV") and words[0].lower_ not in _NOT_SUBJECT_WORDS
                and words[1].lower_ == "and" and words[2].lower_ in ("i", "we") and words[2].dep_ == "nsubj"):
            name, conj, me = words[0], words[1], words[2]
            verb = me.head
            name.head, name.dep_ = verb, "nsubj"
            if name.pos_ == "ADV":
                name.pos_, name.tag_ = "PROPN", "NNP"
            conj.head, conj.dep_ = name, "cc"
            me.head, me.dep_ = name, "conj"
        _repair_question_verb(sentence)
        _repair_compound_subject(sentence)
        root = sentence.root
        subjects = [c for c in root.children if c.dep_ in ("nsubj", "nsubjpass")]
        # "how do fish sleep", "can dogs swim": a helper verb on a "noun" root makes it a verb
        if root.pos_ == "NOUN" and any(c.dep_ == "aux" and c.lower_ in ("do", "does", "did", "can", "could", "will",
                                                                        "would", "should") for c in root.children):
            root.pos_, root.tag_ = "VERB", "VB"
            for subject in subjects:
                if subject.pos_ == "VERB":
                    subject.pos_ = "NOUN"
                    subject.tag_ = "NNS" if subject.lower_.endswith("s") else "NN"
        # "my tummy hurts", "my mom swam": a verb read as a noun
        elif (root.pos_ in ("NOUN", "ADJ") and subjects and _verb_base(root.lower_)
              and not any(c.dep_ in ("det", "poss", "amod", "compound") for c in root.children)):
            base = _verb_base(root.lower_)
            if base:
                tag = "VBD" if root.lower_ in _IRREGULAR_VERBS and not root.lower_.endswith("s") else "VBZ"
                root.pos_, root.tag_, root.lemma_ = "VERB", tag, base
                for subject in subjects:
                    if subject.pos_ == "ADJ":
                        subject.pos_, subject.tag_ = "NOUN", "NN"
        # "why is the sky blue": "is" as a helper of "blue"; make it the verb, "blue" its complement
        elif root.pos_ == "ADJ" and subjects:
            copula = next((c for c in root.children if c.dep_ == "aux" and c.lower_ in _COPULAS), None)
            if copula is not None:
                copula.head, copula.dep_, copula.pos_ = copula, "ROOT", "AUX"
                for child in list(root.children):
                    if child.i != copula.i and child.dep_ in ("nsubj", "advmod", "neg", "punct", "aux", "mark"):
                        child.head = child.head if child.i == copula.i else copula
                root.head, root.dep_ = copula, "acomp"


# Past forms the parser sometimes reads as nouns
_IRREGULAR_PAST = {"bit": "bite", "hit": "hit", "fell": "fall", "broke": "break", "tore": "tear", "threw": "throw",
                   "left": "leave", "lost": "lose", "won": "win", "found": "find", "made": "make", "drew": "draw"}
# Verbs after "help/watch/let someone": "helped my mom bake cookies"
_BARE_VERBS = {"bake", "cook", "make", "clean", "build", "fix", "wash", "paint", "plant", "fold", "carry", "find",
               "pick", "set", "feed", "walk", "decorate", "wrap", "dig", "draw", "play", "read", "write"}


def _repair_objects(doc) -> None:
    """
    Three more errors of the small model:
    "My dad made me soup": "soup" a clause with "me" its subject -> "me" the dative, "soup" the object
    "I want to name her Lily": "her" Lily's possessive -> "her" the object, "Lily" the name (oprd)
    "What game do you like": "you" the object of "do" -> the subject of "like"
    """
    for token in doc:
        # "knitted me a scarf": two objects, the first (a person) is who it was for
        objects = [c for c in token.children if c.dep_ == "dobj"]
        if len(objects) == 2 and objects[0].lower_ in ("me", "us", "him", "her", "them") and objects[0].i < objects[1].i:
            objects[0].dep_ = "dative"
        # "The dog bit my sister": "bit" read as a noun with a subject and an object
        if (token.dep_ == "ROOT" and token.pos_ == "NOUN" and any(c.dep_ == "nsubj" for c in token.children)
                and any(c.dep_ == "dobj" for c in token.children)):
            token.pos_, token.tag_ = "VERB", "VBD"
            token.lemma_ = _IRREGULAR_PAST.get(token.lower_, token.lemma_)
            continue
        # "knocked over my tower": "my tower" the object of "knocked", not of the particle "over"
        if token.dep_ == "pobj" and token.head.dep_ == "prt":
            token.head, token.dep_ = token.head.head, "dobj"
            continue
        # "My favorite food is tacos": "tacos" read as punctuation
        if (token.dep_ == "punct" and token.is_alpha and token.head.lemma_ == "be"
                and not any(c.dep_ in ("attr", "acomp") for c in token.head.children)):
            token.dep_, token.pos_ = "attr", "NOUN"
            token.tag_ = "NNS" if token.lower_.endswith("s") else "NN"
            continue
        # "let's go swimming": the activity after the verb read as punctuation
        if (token.dep_ == "punct" and token.is_alpha and token.lower_.endswith("ing") and token.i > 0
                and doc[token.i - 1].pos_ in ("VERB", "AUX")):
            token.head, token.dep_ = doc[token.i - 1], "xcomp"
            token.pos_, token.tag_ = "VERB", "VBG"
            continue
        # "Do you like pancakes": "like" read as an interjection on "pancakes"
        if (token.dep_ == "intj" and token.lemma_ in ("like", "love", "want", "hate") and token.head.dep_ == "ROOT"
                and token.head.pos_ == "NOUN" and token.i < token.head.i
                and any(c.dep_ == "nsubj" for c in token.children)):
            noun = token.head
            for c in list(noun.children):
                if c.i < token.i and c.dep_ in ("aux", "nsubj"):
                    c.head = token
            token.head, token.dep_, token.pos_ = token, "ROOT", "VERB"
            noun.head, noun.dep_ = token, "dobj"
            for c in list(noun.children):
                if c.dep_ == "punct":
                    c.head = token
            continue
        # "I helped my grandma bake cookies": "grandma" read as the subject of a noun "bake"
        if (token.dep_ == "ccomp" and token.head.lemma_ in ("help", "watch", "see", "let", "make", "hear")
                and token.pos_ == "NOUN" and token.lower_ in _BARE_VERBS):
            person = next((c for c in token.children if c.dep_ == "nsubj" and c.i < token.i
                           and c.lower_ not in ("'s", "us", "s")), None)
            # "made you a card": "a card" is a thing, not a verb
            if person is not None and not any(c.dep_ == "det" for c in token.children):
                person.head, person.dep_ = token.head, "dobj"
                token.pos_, token.tag_, token.lemma_ = "VERB", "VB", token.lower_
                continue
        # "I helped my mom bake cookies": "my mom bake cookies" read as one noun
        if (token.dep_ == "dobj" and token.head.lemma_ in ("help", "watch", "see", "let", "make", "hear")
                and token.pos_ == "NOUN"):
            compounds = [c for c in token.children if c.dep_ == "compound"]
            if len(compounds) == 2 and compounds[1].lower_ in _BARE_VERBS:
                person, verb = compounds
                main = token.head
                person.head, person.dep_ = main, "dobj"
                verb.head, verb.dep_, verb.pos_, verb.tag_ = main, "ccomp", "VERB", "VB"
                verb.lemma_ = verb.lower_
                token.head, token.dep_ = verb, "dobj"
                for c in list(token.children):
                    if c.dep_ == "poss" and c.i < person.i:
                        c.head = person
                continue
        # "brought me a present": "present" read as an adjective
        if token.dep_ == "dobj" and token.pos_ == "ADJ" and any(c.dep_ == "det" for c in token.children):
            token.pos_ = "NOUN"
            token.tag_ = "NN"
        if (token.dep_ == "ccomp" and token.pos_ == "NOUN" and token.head.lemma_ in _GIVING_VERBS
                and token.head.i < token.i):
            pronoun = next((c for c in token.children if c.dep_ == "nsubj"
                            and c.lower_ in ("me", "him", "her", "us", "them")), None)
            if pronoun is not None:
                pronoun.head = token.head
                pronoun.dep_ = "dative"
                token.dep_ = "dobj"
        elif (token.dep_ == "dobj" and token.head.lemma_ in ("name", "call") and token.head.pos_ == "VERB"
              and token.i == max(t.i for t in doc if not t.is_punct)):
            pronoun = next((c for c in token.children if c.dep_ == "poss" and c.lower_ == "her"), None)
            if pronoun is not None:
                pronoun.head = token.head
                pronoun.dep_ = "dobj"
                token.dep_ = "oprd"
        elif (token.lower_ in ("you", "i") and token.dep_ == "dobj" and token.head.lemma_ == "do"
              and token.head.dep_ == "aux"):
            verb = token.head.head
            if not any(c.dep_ == "nsubj" for c in verb.children):
                token.head = verb
                token.dep_ = "nsubj"


_TAG_QUESTION_RE = re.compile(r"^(.*?),? (?:right|huh|(?:aren't|isn't|don't|doesn't|didn't|wasn't|weren't|can't|won't) "
                              r"(?:they|it|you|we|he|she|i))\s*\?*$", re.IGNORECASE)
_NOT_BEFORE_TAG = {"that's", "turn", "turned", "go", "went", "on", "the", "to", "all", "you're", "i'm", "is", "was",
                   "are", "just", "yeah", "yes", "it's", "exactly", "alright", "left", "be", "it", "right", "anything",
                   "everything", "something", "nothing", "this", "that", "them", "him", "her", "me", "you", "us", "not",
                   "so", "very", "too", "quite", "really", "never", "always"}


def _tag_question(match) -> str:
    """ "you like pizza right" -> "you like pizza?"; "that's right" and "turn right" stay"""
    words = match.group(1).split()
    if len(words) < 3 or words[-1].lower() in _NOT_BEFORE_TAG:
        return match.group(0)
    # "you like pizza right" asks "do you like pizza?"; "dogs are cute aren't they" says they are
    if words[0].lower() == "you" and words[1].lower() not in ("are", "were", "can", "will", "would", "could", "should",
                                                              "have", "had", "did", "do", "don't", "didn't", "can't"):
        return f"do {match.group(1)}?"
    return match.group(1)


_DIGIT_SHORTHAND = {"b4": "before", "2day": "today", "2morrow": "tomorrow", "2moro": "tomorrow", "2nite": "tonight",
                    "l8r": "later", "l8": "late", "gr8": "great", "h8": "hate", "m8": "mate", "w8": "wait",
                    "any1": "anyone", "some1": "someone", "every1": "everyone", "no1": "no one"}
_DIGIT_SHORTHAND_RE = re.compile(r"(?<![\w'])(" + "|".join(_DIGIT_SHORTHAND) + r")(?![\w'])", re.IGNORECASE)
_STRETCH_RE = re.compile(r"([a-z])\1{2,}", re.IGNORECASE)
_SAYING_VERBS = {"say", "think", "know", "hope", "wish", "guess", "bet", "feel", "believe", "mean", "remember",
                 "forget", "tell", "hear", "see", "notice", "pretend", "dream", "promise", "bet", "swear"}


_FEELING_WORDS = {"scared", "afraid", "worried", "sure", "glad", "happy", "sad", "sorry", "mad", "nervous",
                  "excited", "upset", "proud", "surprised", "angry", "certain", "lucky", "thankful", "jealous",
                  "embarrassed", "disappointed", "frustrated", "confused", "shocked", "positive", "bored", "tired",
                  "annoyed", "amazed", "terrified", "stressed", "relieved", "thrilled", "pleased", "grossed"}


_TITLE_KINDS = {"book", "movie", "show", "song", "series", "cartoon", "film"}
_TIME_NOUNS = {"today", "tonight", "yesterday", "tomorrow", "now", "again", "later", "once", "twice", "everyday",
               "sometimes", "morning", "night", "week", "weekend", "year"}
_PLACE_VERBS = {"go", "come", "be", "live", "stay", "sit", "put", "leave", "get", "run", "walk", "drive", "move",
                "stand", "play", "wait", "keep", "hide", "sleep", "fly", "swim", "travel", "visit", "meet", "find"}


def _verb_base_ing(word: str) -> bool:
    """True if the -ing word is a verb's form ("cooking", "running", "making")"""
    stem = word[:-3]
    return stem in _VERBS or stem + "e" in _VERBS or (len(stem) > 2 and stem[-1] == stem[-2] and stem[:-1] in _VERBS)


def _resplit(doc) -> str:
    """
    Text for a second parse when the first shows a misreading only the text can fix:
    "bigger then you" -> "bigger than you"; "we went to the zoo we saw a lion" -> two sentences
    """
    text = doc.text
    edits = []
    for token in doc:
        # "there dog is so cute": "their"; "there going to the park": "they're"
        if token.lower_ == "there" and token.i + 1 < len(doc):
            following = doc[token.i + 1]
            before = doc[token.i - 1] if token.i > 0 else None
            if following.pos_ == "NOUN" and following.dep_ != "attr" and token.dep_ in ("expl", "advmod", "poss", "det") \
                    and following.lower_ not in _TIME_NOUNS and (before is None or before.pos_ not in ("AUX", "ADP")) \
                    and (before is None or before.pos_ != "VERB" or before.lemma_ not in _PLACE_VERBS):
                edits.append((token.idx, token.idx + 5, "their" if token.text.islower() else "Their"))
            elif following.tag_ == "VBG" and (token.i == 0 or doc[token.i - 1].pos_ != "AUX"):
                edits.append((token.idx, token.idx + 5, "they're" if token.text.islower() else "They're"))
        # "the book wings of fire": a title after "the book", "the song", "the show"
        if token.lower_ in _TITLE_KINDS and token.i + 1 < len(doc):
            words = []
            for t in doc[token.i + 1:]:
                if t.is_punct or t.pos_ in ("VERB", "AUX", "PRON", "SCONJ", "CCONJ", "DET") or t.lower_ in _TIME_NOUNS \
                        or (t.pos_ == "ADP" and t.lower_ != "of"):
                    break
                words.append(t)
            while words and words[-1].lower_ == "of":
                words.pop()
            head = words[-1] if words else None
            attached = head is not None and (
                (token.dep_ == "compound" and token.head.i in {w.i for w in words})
                or any(w.dep_ == "appos" and w.head.i == token.i for w in words)
                or (head.dep_ == "pobj" and any(w.head.i == token.i or token.head.i == w.i for w in words)))
            if attached and len(words) <= 5 and any(w.text.islower() for w in words):
                start, end = words[0].idx, words[-1].idx + len(words[-1].text)
                title = " ".join(w.capitalize() if k == 0 or w.lower() not in ("of", "the", "and", "a", "an", "in", "on")
                                 else w.lower() for k, w in enumerate(doc.text[start:end].split()))
                edits.append((start, end, title))
        # "dad's cooking dinner": "is", not a possessive
        if token.tag_ == "POS" and token.lower_ == "'s" and token.i + 1 < len(doc) and token.i > 0:
            following = doc[token.i + 1]
            if (following.lower_.endswith("ing") and _verb_base_ing(following.lower_)) or \
                    following.lower_ in ("not", "so", "really", "very", "going", "gonna", "here", "home", "sick", "mad", "sad"):
                edits.append((token.idx, token.idx + 2, " is"))
        # "my dog is bigger then your dog"
        if token.lower_ == "then" and token.i > 0 and (doc[token.i - 1].tag_ in ("JJR", "RBR")
                                                         or doc[token.i - 1].lower_ in ("more", "less")):
            edits.append((token.idx, token.idx + 4, "than" if token.text.islower() else "Than"))
        # A run-on: a second clause with its own subject and object read as a relative clause
        # ("the zoo we saw a lion") or hung off a verb that does not take a clause
        if (token.pos_ in ("VERB", "AUX") and token.dep_ in ("relcl", "ccomp", "parataxis")
                and (token.head.lemma_ not in _SAYING_VERBS
                     or (token.head.lemma_ in ("see", "hear", "notice")  # "I saw a dog it was big"
                         and any(c.dep_ == "dobj" and c.pos_ in ("NOUN", "PROPN") for c in token.head.children)))
                and token.head.pos_ in ("VERB", "AUX", "NOUN", "PROPN")
                # "I'm scared it will hurt", "I'm glad you came": the feeling's reason
                and not any(c.dep_ == "acomp" and c.lower_ in _FEELING_WORDS for c in token.head.children)
                and any(c.dep_ == "nsubj" and c.lower_ in ("i", "we", "he", "she", "they", "it", "you") for c in token.children)
                and not any(c.dep_ in ("mark", "advmod") and c.tag_ in ("IN", "WRB", "WDT") for c in token.children)
                and not any(t.tag_ in ("WDT", "WP", "WRB") or t.lower_ == "that" for t in token.subtree if t.i < token.i)
                and (token.dep_ != "relcl" or any(c.dep_ in ("dobj", "attr", "acomp") and c.pos_ in ("NOUN", "PROPN", "ADJ")
                                             and c.lower_ not in ("most", "best", "least", "more") for c in token.children))):
            start = token.left_edge
            if start.i > 0 and not doc[start.i - 1].is_punct and doc[start.i - 1].lower_ not in ("and", "but", "so", "then"):
                edits.append((doc[start.i - 1].idx + len(doc[start.i - 1].text), doc[start.i - 1].idx + len(doc[start.i - 1].text), "."))
    for begin, end, new in sorted(edits, reverse=True):
        text = text[:begin] + new + text[end:]
    return text


def _load_verbs(nlp) -> None:
    """Base forms of verbs from the lemmatizer's tables, for _repair_tags"""
    try:
        if "lemmatizer" in nlp.pipe_names:
            lookups = nlp.get_pipe("lemmatizer").lookups
            if lookups.has_table("lemma_index"):
                _VERBS.update(lookups.get_table("lemma_index")["verb"])
                _NOUNS.update(lookups.get_table("lemma_index")["noun"])
            if lookups.has_table("lemma_exc"):
                for form, lemmas in lookups.get_table("lemma_exc")["verb"].items():
                    if lemmas:
                        _IRREGULAR_VERBS[form] = lemmas[0]
    except Exception as e:  # tables differ between model versions
        logger.warning(f"Could not read verb forms: {e}")


class UtteranceParser:
    """Lazily loads spaCy and parses normalized user messages"""

    def __init__(self, model_name: str = MODEL_NAME):
        self.model_name = model_name
        self._nlp = None
        self._load_failed = False
        self._known_words = None

    def is_available(self) -> bool:
        """Return True if spaCy and the language model can be loaded"""
        return self._get_nlp() is not None

    def _get_nlp(self):
        if self._nlp is None and not self._load_failed:
            try:
                import spacy

                self._nlp = spacy.load(self.model_name)
                _load_verbs(self._nlp)
                logger.info(f"Loaded spaCy model {self.model_name}")
            except Exception as e:  # ImportError or missing model (OSError)
                self._load_failed = True
                logger.warning(f"spaCy model {self.model_name} unavailable: {e}")
        return self._nlp

    @staticmethod
    def normalize(text: str) -> str:
        """Collapse whitespace and replace common child spellings word by word"""
        # A message of only emoji: the first one in words ("😂" -> "haha", "😢" -> "I am sad")
        if not any(c.isalnum() for c in text):
            for char in text:
                if char in _EMOJI_WORDS:
                    return _EMOJI_WORDS[char]
        text = " ".join(_EMOJI_RE.sub(" ", text).split())
        # ALL CAPS ("I GOT A PUPPY TODAY") parses badly; read it as lowercase
        letters = [c for c in text if c.isalpha()]
        if len(letters) >= 4 and sum(c.isupper() for c in letters) >= 0.8 * len(letters):
            text = re.sub(r"\bi\b", "I", text.lower())
        text = " ".join(next((r for p, r in _STRETCHED_GREETINGS if p.match(w)), w) for w in text.split())

        def replace(match):
            word = match.group(0)
            if word.lower() == "ur":
                return word  # "ur weird" (you're) or "ur dog" (your): decided below by the next word
            return NORMALIZATIONS.get(word.lower(), word)

        # Shorthand with digits ("b4", "2day", "l8r"), which the word pattern below does not see
        text = _DIGIT_SHORTHAND_RE.sub(lambda m: _DIGIT_SHORTHAND[m.group(0).lower()], text)
        # Spellings first, so "its rlly big" reads "its really big" before "its" -> "it's"
        text = _WORD_RE.sub(replace, text)
        for pattern, replacement in _CONTEXT_NORMALIZATIONS:
            text = pattern.sub(replacement, text)
        text = re.sub(r"\bur\b", "your", text, flags=re.IGNORECASE)
        text = _POSSESSIVE_RE.sub(r"\1's ", text)
        text = _NAMED_RE.sub(lambda m: f"{m.group(1)} {m.group(3).upper()}", text)
        text = _NAME_IS_RE.sub(lambda m: f"{m.group(1)} {m.group(3).upper()}", text)
        text = _NAMES_ARE_RE.sub(lambda m: f"{m.group(1)} {m.group(2).capitalize()} and {m.group(3).capitalize()}", text)
        text = _PLACES_RE.sub(lambda m: m.group(1).title(), text)
        text = _TITLES_RE.sub(lambda m: _TITLES[m.group(1)], text)
        # "on saturday" -> "on Saturday" ("may" and "march" are also words, so they stay)
        text = _WEEKDAY_RE.sub(lambda m: m.group(1).capitalize(), text)
        text = _ITS_ALONE_RE.sub("it's ", text)
        # "buddy do you like pizza": the bot's name is a greeting, set off by a comma
        text = re.sub(r"^buddy,? (?=(?:do|does|did|can|could|will|would|are|guess|what|why|how|where|who|when|i|you|look|listen|tell|let's|lets|wanna|want)\b)", "", text, flags=re.IGNORECASE)
        text = re.sub(r"^((?:hey|hi|hello) buddy)(?= (?:do|does|did|can|could|will|would|are|guess|what|why|how|where|who|when|i|you|look|listen|tell|let's|lets|wanna|want)\b)", r"\1,", text, flags=re.IGNORECASE)
        text = re.sub(r"\b(you|thanks|bye|goodnight|night),? buddy\s*([.!?]*)$", r"\1\2", text, flags=re.IGNORECASE)
        # "home.it was fun": a sentence run together after the period
        text = re.sub(r"(?<=[a-z])\.(?=(?:i|it|we|he|she|they|my|the|then|and|but|so|you|that|there|this)\b)", ". ", text)
        # "my mom n dad", "me & my sister", "w/ my grandma", "going 2 the store"
        text = re.sub(r"(?<=\w) (?:n|&|\+) (?=\w)", " and ", text)
        text = re.sub(r"\bw/(?=\s)", "with", text, flags=re.IGNORECASE)
        text = re.sub(r"\b(go|going|went|goes|come|came|want|wanna|have|need|got|talk|listen|back|up|next|way|time|to|due)"
                      r" 2 (?=(?:the|my|a|school|bed|sleep|play|go|eat|be|see|get|do|work|church|grandma's|grandpa's)\b)",
                      r"\1 to ", text, flags=re.IGNORECASE)
        # "you like pizza right", "dogs are cute aren't they": a question looking for "yes"
        text = _TAG_QUESTION_RE.sub(_tag_question, text)
        # "i dare you to say something funny": the dare is the request
        text = re.sub(r"^i (?:dare|double dare|triple dare) you to ", "", text, flags=re.IGNORECASE)
        # "I'm a dinosaur rawr": the growl is its own sentence
        text = re.sub(r"(?<=[a-z])\s+((?:rawr+|roa+r+|grr+|meow+|woof+|moo+|oink+)\W*)$", r"! \1", text, flags=re.IGNORECASE)
        text = re.sub(r"\by'?all\b", "you all", text, flags=re.IGNORECASE)
        # "which is better, pizza or tacos": the choice itself
        text = re.sub(r"^((?:which|what)(?: one)? (?:is|do you like|would you pick|do you pick|would you choose)"
                      r"(?: better| more| best)?),?\s+(\w+(?: \w+)?) or (\w+(?: \w+)?)\s*\??$", r"\1, \2 or \3?", text,
                      flags=re.IGNORECASE)
        # Quotes around what someone said: 'my mom said "no way"'
        text = re.sub(r"[\"“”]", "", text)
        # "what do i do": asking for advice
        text = re.sub(r"^what do i do\b", "what should I do", text, flags=re.IGNORECASE)
        # "what does gravity mean": the question the world answers know as "what is gravity"
        text = re.sub(r"^what does (?!(?:that|it|this|he|she|they|you|mine)\b)([\w ]+?) mean\b", r"what is \1", text,
                      flags=re.IGNORECASE)
        # "i watched frozen": a movie title after a word for watching
        text = re.sub(r"\b(watch|watched|watching|saw|seen|see|love|loved|like|liked)( the movie)? (frozen|moana|encanto|"
                      r"coco|elemental|luca|tangled|bluey|trolls|turning red|inside out|"
                      r"toy story|zootopia|minions|despicable me|shrek|wicked|lilo and stitch|the lion king)"
                      r"(?=\s*(?:[.!?,]|$)|\s+(?:and|with|today|yesterday|again|last|at|on|tonight|so|too|two|2)\b)",
                      lambda m: f"{m.group(1)}{m.group(2) or ''} {m.group(3).title().replace(' And ', ' and ')}", text,
                      flags=re.IGNORECASE)
        # "i wonder why the sky is blue": the question itself ("why is the sky blue?")
        text = re.sub(r"^i (?:wonder|want to know|wanna know|wish i knew) (why|how|where|what|when|if) "
                      r"((?:the |a |my |your )?\w+) (is|are|was|were|can|do|does) (.+?)[.!?]*$",
                      lambda m: f"{m.group(1) if m.group(1) != 'if' else ''} {m.group(3)} {m.group(2)} {m.group(4)}?".strip(),
                      text, flags=re.IGNORECASE)
        # "y is the sky blue", "y not": "why"
        text = re.sub(r"^y(?= (is|are|do|does|did|not|can|can't|would|wouldn't|should|won't|cant|dont|don't|was|were)\b)|^y(?=\W*$)",
                      "why", text, flags=re.IGNORECASE)
        # "lets fish" at the start: "let's fish"
        text = re.sub(r"^lets\b", "let's", text, flags=re.IGNORECASE)
        # "me and lily played tag" -> "lily and I played tag" (the parser reads "me and" badly)
        text = _ME_AND_RE.sub(lambda m: f"{m.group(1)}{m.group(2)} and I", text)
        text = _TITLE_RE.sub(lambda m: f"{m.group(1).capitalize()} {m.group(2).upper()}", text)
        # "what's your name and how old are you": two questions, answered one by one
        if _QUESTION_START_RE.match(text):
            text = _JOINED_QUESTION_RE.sub("? ", text)
        return text

    def parse(self, text: str):
        """
        Parse a message into a spaCy Doc

        Returns:
            spaCy Doc, or None if the parser is unavailable or the text is empty
        """
        if not text or not text.strip():
            return None
        if self._get_nlp() is None:
            return None
        return self._parse_cached(self._unstretch(self.normalize(text)))

    def _unstretch(self, text: str) -> str:
        """ "sooooo fun" -> "so fun", "yesss" -> "yes", "cooool" -> "cool": the spelling the model knows"""
        if not _STRETCH_RE.search(text):
            return text
        known = self.known_words()

        def fix(match):
            word = match.group(0)
            options = {re.sub(r"(\w)\1{2,}", r"\1" * n, word) for n in (1, 2)}
            # several stretched letters: try each run at one or two
            runs = list(re.finditer(r"(\w)\1{2,}", word))
            if len(runs) > 1:
                options = set()
                for counts in range(2 ** len(runs)):
                    out, last = [], 0
                    for k, run in enumerate(runs):
                        out.append(word[last:run.start()] + run.group(1) * (1 + (counts >> k & 1)))
                        last = run.end()
                    options.add("".join(out) + word[last:])
            # the longest known spelling: "cooool" is "cool", not "col"
            ordered = sorted(options, key=len, reverse=True)
            # a common short word first: "soooo" is "so", not "soo"
            stop = next((o for o in ordered if o.lower() in self._nlp.Defaults.stop_words), None)
            return stop or next((o for o in ordered if o.lower() in known), ordered[-1])

        return re.sub(r"\b\w*(\w)\1{2,}\w*\b", fix, text)

    @lru_cache(maxsize=256)
    def _parse_cached(self, normalized_text: str):
        doc = repair_parse(self._nlp(normalized_text))
        fixed = _resplit(doc)
        return repair_parse(self._nlp(fixed)) if fixed != normalized_text else doc

    @property
    def vocab(self):
        nlp = self._get_nlp()
        return nlp.vocab if nlp is not None else None

    def known_words(self) -> set:
        """
        Lowercase English words the model knows: the lemmatizer's word lists (base forms
        and irregular forms, from WordNet), its stop words and the child spellings in
        NORMALIZATIONS. Empty if the model is unavailable.
        """
        if self._known_words is not None:
            return self._known_words
        nlp = self._get_nlp()
        if nlp is None:
            return set()
        words = {w.lower() for w in nlp.Defaults.stop_words} | set(NORMALIZATIONS)
        if "lemmatizer" in nlp.pipe_names:
            lookups = nlp.get_pipe("lemmatizer").lookups
            for table_name in ("lemma_index", "lemma_exc"):
                if lookups.has_table(table_name):
                    table = lookups.get_table(table_name)
                    for pos in table.keys():
                        words.update(w.lower() for w in table[pos])
        self._known_words = words
        return words


# Global instance
utterance_parser = UtteranceParser()
