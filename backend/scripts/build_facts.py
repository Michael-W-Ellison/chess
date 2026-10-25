"""
Build the "generated" facts in knowledge/facts.json from the tables below (capitals, continents,
animals, planets, measurements, numbers). The hand-written "facts" in the file are kept as they
are; "sets" and "generated" are replaced.

Each generated fact gets one wrong and one right example. The build stops if a fact's examples
are not answered as listed, or if they are answered by another fact with the opposite verdict;
a generated fact whose examples an earlier fact already answers the same way is left out.

Usage (from backend/):
    python scripts/build_facts.py

Only put facts in the tables that are simply true for a child, without exceptions worth arguing
about: no disputed capitals, no countries on two continents, no "the longest river".
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from services.fact_base import FactBase  # noqa: E402

FACTS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "knowledge", "facts.json")


def alt(*names: str) -> str:
    """A regex alternation of plain phrases"""
    return "(?:" + "|".join(re.escape(n) for n in sorted(set(names), key=lambda n: (-len(n), n))) + ")"


def subject(*names: str, articles: str = "(?:a |an |the |all )?") -> str:
    return articles + alt(*names)


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def title(text: str) -> str:
    small = {"of", "and", "the", "la", "de", "es", "au"}
    words = text.split()
    return " ".join(w if (i and w in small) else w[:1].upper() + w[1:] for i, w in enumerate(words))


def a_or_an(word: str) -> str:
    return ("an " if word[:1] in "aeiou" else "a ") + word


# ----------------------------------------------------------------------------------------------
# Places
# ----------------------------------------------------------------------------------------------

# (country, other names, capital, other capital spellings, continent or None for two continents)
COUNTRIES = [
    ("albania", [], "tirana", [], "europe"), ("austria", [], "vienna", [], "europe"),
    ("belarus", [], "minsk", [], "europe"), ("belgium", [], "brussels", [], "europe"),
    ("bosnia and herzegovina", ["bosnia"], "sarajevo", [], "europe"), ("bulgaria", [], "sofia", [], "europe"),
    ("croatia", [], "zagreb", [], "europe"), ("czechia", ["the czech republic", "czech republic"], "prague", [], "europe"),
    ("denmark", [], "copenhagen", [], "europe"), ("estonia", [], "tallinn", [], "europe"),
    ("finland", [], "helsinki", [], "europe"), ("france", [], "paris", [], "europe"),
    ("germany", [], "berlin", [], "europe"), ("greece", [], "athens", [], "europe"),
    ("hungary", [], "budapest", [], "europe"), ("iceland", [], "reykjavik", [], "europe"),
    ("ireland", [], "dublin", [], "europe"), ("italy", [], "rome", [], "europe"),
    ("latvia", [], "riga", [], "europe"), ("liechtenstein", [], "vaduz", [], "europe"),
    ("lithuania", [], "vilnius", [], "europe"), ("malta", [], "valletta", [], "europe"),
    ("moldova", [], "chisinau", [], "europe"), ("montenegro", [], "podgorica", [], "europe"),
    ("the netherlands", ["netherlands", "holland"], "amsterdam", [], "europe"),
    ("north macedonia", ["macedonia"], "skopje", [], "europe"), ("norway", [], "oslo", [], "europe"),
    ("poland", [], "warsaw", [], "europe"), ("portugal", [], "lisbon", [], "europe"),
    ("romania", [], "bucharest", [], "europe"), ("serbia", [], "belgrade", [], "europe"),
    ("slovakia", [], "bratislava", [], "europe"), ("slovenia", [], "ljubljana", [], "europe"),
    ("spain", [], "madrid", [], "europe"), ("sweden", [], "stockholm", [], "europe"),
    ("switzerland", [], "bern", ["berne"], "europe"), ("ukraine", [], "kyiv", ["kiev"], "europe"),
    ("the united kingdom", ["the uk", "uk", "united kingdom", "britain", "great britain"], "london", [], "europe"),
    ("england", [], "london", [], "europe"), ("scotland", [], "edinburgh", [], "europe"),
    ("wales", [], "cardiff", [], "europe"), ("russia", [], "moscow", [], None), ("turkey", [], "ankara", [], None),
    ("afghanistan", [], "kabul", [], "asia"), ("bangladesh", [], "dhaka", [], "asia"),
    ("bhutan", [], "thimphu", [], "asia"), ("cambodia", [], "phnom penh", [], "asia"),
    ("china", [], "beijing", [], "asia"), ("india", [], "new delhi", ["delhi"], "asia"),
    ("iran", [], "tehran", [], "asia"), ("iraq", [], "baghdad", [], "asia"), ("japan", [], "tokyo", [], "asia"),
    ("jordan", [], "amman", [], "asia"), ("north korea", [], "pyongyang", [], "asia"),
    ("south korea", [], "seoul", [], "asia"), ("laos", [], "vientiane", [], "asia"),
    ("lebanon", [], "beirut", [], "asia"), ("malaysia", [], "kuala lumpur", [], "asia"),
    ("mongolia", [], "ulaanbaatar", ["ulan bator"], "asia"), ("nepal", [], "kathmandu", [], "asia"),
    ("oman", [], "muscat", [], "asia"), ("pakistan", [], "islamabad", [], "asia"),
    ("the philippines", ["philippines"], "manila", [], "asia"), ("qatar", [], "doha", [], "asia"),
    ("saudi arabia", [], "riyadh", [], "asia"), ("syria", [], "damascus", [], "asia"),
    ("thailand", [], "bangkok", [], "asia"),
    ("the united arab emirates", ["the uae", "uae", "united arab emirates"], "abu dhabi", [], "asia"),
    ("vietnam", [], "hanoi", [], "asia"), ("uzbekistan", [], "tashkent", [], "asia"),
    ("kyrgyzstan", [], "bishkek", [], "asia"), ("tajikistan", [], "dushanbe", [], "asia"),
    ("turkmenistan", [], "ashgabat", [], "asia"), ("bahrain", [], "manama", [], "asia"),
    ("algeria", [], "algiers", [], "africa"), ("angola", [], "luanda", [], "africa"),
    ("botswana", [], "gaborone", [], "africa"), ("burkina faso", [], "ouagadougou", [], "africa"),
    ("cameroon", [], "yaounde", [], "africa"), ("chad", [], "ndjamena", [], "africa"),
    ("egypt", [], "cairo", [], None), ("ethiopia", [], "addis ababa", [], "africa"),
    ("ghana", [], "accra", [], "africa"), ("kenya", [], "nairobi", [], "africa"),
    ("libya", [], "tripoli", [], "africa"), ("madagascar", [], "antananarivo", [], "africa"),
    ("malawi", [], "lilongwe", [], "africa"), ("mali", [], "bamako", [], "africa"),
    ("mauritania", [], "nouakchott", [], "africa"), ("morocco", [], "rabat", [], "africa"),
    ("mozambique", [], "maputo", [], "africa"), ("namibia", [], "windhoek", [], "africa"),
    ("niger", [], "niamey", [], "africa"), ("nigeria", [], "abuja", [], "africa"),
    ("rwanda", [], "kigali", [], "africa"), ("senegal", [], "dakar", [], "africa"),
    ("sierra leone", [], "freetown", [], "africa"), ("somalia", [], "mogadishu", [], "africa"),
    ("south sudan", [], "juba", [], "africa"), ("sudan", [], "khartoum", [], "africa"),
    ("tanzania", [], "dodoma", [], "africa"), ("togo", [], "lome", [], "africa"),
    ("tunisia", [], "tunis", [], "africa"), ("uganda", [], "kampala", [], "africa"),
    ("zambia", [], "lusaka", [], "africa"), ("zimbabwe", [], "harare", [], "africa"),
    ("gabon", [], "libreville", [], "africa"), ("liberia", [], "monrovia", [], "africa"),
    ("eritrea", [], "asmara", [], "africa"), ("guinea", [], "conakry", [], "africa"),
    ("the gambia", ["gambia"], "banjul", [], "africa"),
    ("canada", [], "ottawa", [], "north america"),
    ("the united states", ["the usa", "usa", "the us", "america", "the united states of america", "united states"],
     "washington dc", ["washington d c", "washington", "dc"], "north america"),
    ("mexico", [], "mexico city", [], "north america"), ("cuba", [], "havana", [], "north america"),
    ("jamaica", [], "kingston", [], "north america"), ("haiti", [], "port au prince", [], "north america"),
    ("the dominican republic", ["dominican republic"], "santo domingo", [], "north america"),
    ("the bahamas", ["bahamas"], "nassau", [], "north america"),
    ("guatemala", [], "guatemala city", [], "north america"), ("honduras", [], "tegucigalpa", [], "north america"),
    ("el salvador", [], "san salvador", [], "north america"), ("nicaragua", [], "managua", [], "north america"),
    ("costa rica", [], "san jose", [], "north america"), ("panama", [], "panama city", [], "north america"),
    ("belize", [], "belmopan", [], "north america"), ("barbados", [], "bridgetown", [], "north america"),
    ("trinidad and tobago", [], "port of spain", [], None),
    ("argentina", [], "buenos aires", [], "south america"), ("brazil", [], "brasilia", [], "south america"),
    ("chile", [], "santiago", [], "south america"), ("colombia", [], "bogota", [], "south america"),
    ("ecuador", [], "quito", [], "south america"), ("guyana", [], "georgetown", [], "south america"),
    ("paraguay", [], "asuncion", [], "south america"), ("peru", [], "lima", [], "south america"),
    ("suriname", [], "paramaribo", [], "south america"), ("uruguay", [], "montevideo", [], "south america"),
    ("venezuela", [], "caracas", [], "south america"),
    ("australia", [], "canberra", [], "oceania"), ("new zealand", [], "wellington", [], "oceania"),
    ("fiji", [], "suva", [], "oceania"), ("papua new guinea", [], "port moresby", [], "oceania"),
    ("samoa", [], "apia", [], "oceania"),
]

US_STATES = [
    ("alabama", "montgomery"), ("alaska", "juneau"), ("arizona", "phoenix"), ("arkansas", "little rock"),
    ("california", "sacramento"), ("colorado", "denver"), ("connecticut", "hartford"), ("delaware", "dover"),
    ("florida", "tallahassee"), ("georgia", "atlanta"), ("hawaii", "honolulu"), ("idaho", "boise"),
    ("illinois", "springfield"), ("indiana", "indianapolis"), ("iowa", "des moines"), ("kansas", "topeka"),
    ("kentucky", "frankfort"), ("louisiana", "baton rouge"), ("maine", "augusta"), ("maryland", "annapolis"),
    ("massachusetts", "boston"), ("michigan", "lansing"), ("minnesota", "saint paul"), ("mississippi", "jackson"),
    ("missouri", "jefferson city"), ("montana", "helena"), ("nebraska", "lincoln"), ("nevada", "carson city"),
    ("new hampshire", "concord"), ("new jersey", "trenton"), ("new mexico", "santa fe"), ("new york", "albany"),
    ("north carolina", "raleigh"), ("north dakota", "bismarck"), ("ohio", "columbus"),
    ("oklahoma", "oklahoma city"), ("oregon", "salem"), ("pennsylvania", "harrisburg"),
    ("rhode island", "providence"), ("south carolina", "columbia"), ("south dakota", "pierre"),
    ("tennessee", "nashville"), ("texas", "austin"), ("utah", "salt lake city"), ("vermont", "montpelier"),
    ("virginia", "richmond"), ("washington", "olympia"), ("west virginia", "charleston"),
    ("wisconsin", "madison"), ("wyoming", "cheyenne"),
]
CAPITAL_SPELLINGS = {"saint paul": ["st paul"]}
STATE_NAMES = {"washington": ["washington state"]}

PROVINCES = [
    ("ontario", "toronto"), ("quebec", "quebec city"), ("british columbia", "victoria"), ("alberta", "edmonton"),
    ("manitoba", "winnipeg"), ("saskatchewan", "regina"), ("nova scotia", "halifax"),
    ("new brunswick", "fredericton"), ("newfoundland and labrador", "st johns"),
    ("prince edward island", "charlottetown"), ("yukon", "whitehorse"),
    ("the northwest territories", "yellowknife"), ("nunavut", "iqaluit"),
]
TERRITORIES = {"yukon", "the northwest territories", "nunavut"}

# Big cities that are not capitals, and the place they are often taken for the capital of
NOT_CAPITALS = {
    "sydney": "australia", "melbourne": "australia", "toronto": None, "vancouver": "canada",
    "montreal": "canada", "rio de janeiro": "brazil", "rio": "brazil", "sao paulo": "brazil",
    "new york": "the united states", "new york city": "the united states", "los angeles": "california",
    "san francisco": "california", "chicago": "illinois", "istanbul": "turkey", "lagos": "nigeria",
    "dar es salaam": "tanzania", "karachi": "pakistan", "mumbai": "india", "shanghai": "china",
    "hong kong": "china", "osaka": "japan", "barcelona": "spain", "milan": "italy", "munich": "germany",
    "zurich": "switzerland", "geneva": "switzerland", "auckland": "new zealand", "casablanca": "morocco",
    "dubai": "the united arab emirates", "houston": "texas", "dallas": "texas", "miami": "florida",
    "orlando": "florida", "seattle": "washington", "philadelphia": "pennsylvania", "detroit": "michigan",
    "las vegas": "nevada", "new orleans": "louisiana", "portland": "oregon", "louisville": "kentucky",
    "kansas city": "missouri", "st louis": "missouri", "anchorage": "alaska", "baltimore": "maryland",
    "milwaukee": "wisconsin", "minneapolis": "minnesota", "cleveland": "ohio", "cincinnati": "ohio",
    "birmingham": "alabama", "memphis": "tennessee", "san diego": "california", "pittsburgh": "pennsylvania",
    "savannah": "georgia", "manchester": "the united kingdom", "venice": "italy", "florence": "italy",
    "st petersburg": "russia", "almaty": "kazakhstan", "alexandria": "egypt",
}
# Names that are a country and a city, or a state and a country: no "is a country" facts. Victoria is
# also a state in Australia; "columbia" is how children often spell Colombia
AMBIGUOUS_KINDS = {"australia", "georgia", "washington", "new york", "mexico", "panama", "guatemala",
                   "quebec", "turkey", "jordan", "chad", "niger", "guinea", "the gambia", "gambia", "victoria",
                   "columbia"}

CONTINENTS = ["africa", "antarctica", "asia", "australia", "europe", "north america", "south america"]


def capital_forms(place: str) -> list:
    bare = place[4:] if place.startswith("the ") else place
    return list(dict.fromkeys([f"the capital of {place}", f"the capital city of {place}", f"the capital of {bare}",
                               f"the capital city of {bare}"]))


def places(sets: dict) -> list:
    facts = []
    capital_of = {}  # capital -> [places]
    capitals = {}  # place -> (names, capital, spellings, kind)
    for country, others, capital, spellings, _ in COUNTRIES:
        capitals[country] = ([country] + others, capital, spellings, "country")
    for state, capital in US_STATES:
        capitals[state] = ([state] + STATE_NAMES.get(state, []), capital, CAPITAL_SPELLINGS.get(capital, []), "state")
    for province, capital in PROVINCES:
        capitals[province] = ([province], capital, [], "territory" if province in TERRITORIES else "province")
    for place, (names, capital, spellings, kind) in capitals.items():
        capital_of.setdefault(capital, []).append(place)

    sets["capitals"] = sorted({c for _, c, s, _ in capitals.values() for c in [c] + s} | set(NOT_CAPITALS))
    sets["capital_of"] = sorted({f for names, _, _, _ in capitals.values() for n in names for f in capital_forms(n)})
    sets["continent_in"] = [f"in {c}" for c in CONTINENTS] + ["in oceania"]
    sets["kinds"] = ["a country", "a state", "a continent", "a city", "a province", "a territory"]

    for place, (names, capital, spellings, kind) in capitals.items():
        shown = title(place[4:] if place.startswith("the ") else place)
        if place in ("the united states",):
            shown = "the United States"
        elif place.startswith("the "):
            shown = "the " + title(place[4:])
        city = title(capital).replace("Dc", "DC").replace("St ", "St. ")
        subjects = [f"the capital of {n}" for n in names] + [f"the capital city of {n}" for n in names]
        facts.append({
            "id": f"capital_{slug(place)}", "type": "is", "subject": alt(*subjects),
            "true": [capital] + spellings, "false_from": ["capitals"],
            "correct": f"The capital of {shown} is {city}!",
            "examples": [[f"the capital of {names[0]} is {_other(sets['capitals'], [capital] + spellings)}", "wrong"],
                         [f"the capital of {names[0]} is {capital}", "right"]]})
        if capital == "washington dc":
            continue  # "washington is the capital of ..." is also the state
        places_with_it = capital_of[capital]
        if places_with_it[0] != place:
            continue  # one fact for a capital of two places (London)
        true = list(dict.fromkeys(f for p in places_with_it for n in capitals[p][0] for f in capital_forms(n)))
        facts.append({
            "id": f"capital_city_{slug(capital)}", "type": "is", "subject": subject(capital, *spellings, articles=""),
            "true": true, "false_from": ["capital_of"],
            "correct": f"{city} is the capital of {shown}!",
            "examples": [[f"{capital} is {_other(sets['capital_of'], true)}", "wrong"],
                         [f"{capital} is the capital of {names[0]}", "right"]]})

    for city, place in NOT_CAPITALS.items():
        if place not in capitals:  # no capital listed for it (Kazakhstan)
            continue
        names, capital, _, _ = capitals[place]
        shown = "the United States" if place == "the united states" else title(place).replace("The ", "the ")
        facts.append({
            "id": f"not_capital_{slug(city)}", "type": "is", "subject": subject(city, articles=""),
            "true": [], "false_from": ["capital_of"],
            "correct": f"{title(city).replace('St ', 'St. ')} is a big city, but the capital of {shown} is "
                       f"{title(capital).replace('Dc', 'DC')}!",
            "examples": [[f"{city} is the capital of {names[0]}", "wrong"]]})

    kinds = sets["kinds"]
    for place, (names, capital, _, kind) in capitals.items():
        if place in AMBIGUOUS_KINDS:
            continue
        shown = title(place).replace("The ", "the ")
        shown = shown[:1].upper() + shown[1:]
        noun = {"country": "a country", "state": "a state", "province": "a province", "territory": "a territory"}[kind]
        extra = {"state": " in the United States", "province": " in Canada", "territory": " in Canada",
                 "country": ""}[kind]
        facts.append({
            "id": f"kind_{slug(place)}", "type": "is", "subject": subject(*names, articles=""),
            "true": [noun] + ([f"a us state", "an american state"] if kind == "state" else []),
            "false_from": ["kinds"], "correct": f"{shown} is {noun}{extra}!",
            "examples": [[f"{names[0]} is {_other(kinds, [noun])}", "wrong"], [f"{names[0]} is {noun}", "right"]]})
    for place, (names, capital, spellings, kind) in capitals.items():
        if capital in AMBIGUOUS_KINDS or capital in ("washington dc",) or capital_of[capital][0] != place:
            continue
        facts.append({
            "id": f"kind_city_{slug(capital)}", "type": "is", "subject": subject(capital, *spellings, articles=""),
            "true": ["a city", "a capital", "a capital city", "a big city"], "false": ["a country", "a continent"],
            "correct": f"{title(capital)} is a city!",
            "examples": [[f"{capital} is a country", "wrong"], [f"{capital} is a city", "right"]]})
    for continent in CONTINENTS:
        if continent in AMBIGUOUS_KINDS:
            continue
        facts.append({
            "id": f"kind_{slug(continent)}", "type": "is", "subject": subject(continent, articles="(?:the )?"),
            "true": ["a continent"], "false": ["a country", "a state", "a city"],
            "correct": f"{title(continent)} is a continent, with lots of countries in it!"
            if continent != "antarctica" else "Antarctica is a continent. It's covered in ice, and no country owns it!",
            "examples": [[f"{continent} is a country", "wrong"], [f"{continent} is a continent", "right"]]})

    for country, others, capital, _, continent in COUNTRIES:
        if continent is None or country in ("england", "scotland", "wales"):
            continue
        shown = title(country).replace("The ", "the ")
        shown = shown[:1].upper() + shown[1:]
        if continent == "oceania":
            true = ["in oceania", "in australia"] if country == "australia" else ["in oceania"]
            false = [v for v in sets["continent_in"] if v not in ("in oceania", "in australia")]
            correct = f"{shown} is in Oceania!" if country != "australia" else "Australia is a country and a continent!"
        else:
            true = [f"in {continent}"]
            false = [v for v in sets["continent_in"] if v not in true]
            correct = f"{shown} is in {title(continent)}!"
        facts.append({
            "id": f"continent_{slug(country)}", "type": "is", "subject": subject(country, *others, articles=""),
            "true": true, "false": false, "correct": correct,
            "examples": [[f"{country} is {false[0]}", "wrong"], [f"{country} is {true[0]}", "right"]]})
    usa = ["in the usa", "in the us", "in america", "in the united states"]
    for state, _ in US_STATES:
        names = [state] + STATE_NAMES.get(state, [])
        true = usa + ([] if state == "hawaii" else ["in north america"])
        skip = {"in oceania", "in australia", "in north america"} if state == "hawaii" else set()
        false = [v for v in sets["continent_in"] if v not in true and v not in skip] + ["in canada", "in mexico"]
        if state in ("georgia", "washington", "new york"):
            continue
        facts.append({
            "id": f"in_usa_{slug(state)}", "type": "is", "subject": subject(*names, articles=""),
            "true": true, "false": false, "correct": f"{title(state)} is a state in the United States!",
            "examples": [[f"{state} is in canada", "wrong"], [f"{state} is in america", "right"]]})
    for province, _ in PROVINCES:
        true = ["in canada", "in north america"]
        false = [v for v in sets["continent_in"] if v not in true] + usa
        if province == "quebec":
            continue
        shown = title(province).replace("The ", "the ")
        facts.append({
            "id": f"in_canada_{slug(province)}", "type": "is", "subject": subject(province, articles=""),
            "true": true, "false": false, "correct": f"{shown[:1].upper() + shown[1:]} is in Canada!",
            "examples": [[f"{province} is in america", "wrong"], [f"{province} is in canada", "right"]]})
    return facts


def wrong_number(accepted: list) -> int:
    """A number near the right one that is not accepted, for a wrong example"""
    return next(n for n in (accepted[0] + 1, accepted[0] + 2, accepted[0] - 1, accepted[0] + 10) if n not in accepted)


def _other(values, true):
    """A value from a set that is not one of the right ones, for a wrong example"""
    return next(v for v in values if v not in true)


# ----------------------------------------------------------------------------------------------
# Animals
# ----------------------------------------------------------------------------------------------

CLASSES = {
    "mammal": (["mammals", "a mammal", "mammal"], "Mammals feed their babies milk."),
    "bird": (["birds", "a bird", "bird"], "Birds have feathers and lay eggs."),
    "fish": (["fish", "a fish", "fishes"], "Fish live in water and breathe with gills."),
    "reptile": (["reptiles", "a reptile", "reptile"], "Reptiles have dry, scaly skin."),
    "amphibian": (["amphibians", "an amphibian", "amphibian"], "Amphibians usually start their lives in water."),
    "insect": (["insects", "an insect", "insect"], "Insects have 6 legs."),
    "arachnid": (["arachnids", "an arachnid", "arachnid"], "Arachnids have 8 legs."),
    "mollusk": (["mollusks", "a mollusk", "mollusk", "molluscs", "a mollusc", "mollusc"],
                "Mollusks have soft bodies."),
    "crustacean": (["crustaceans", "a crustacean", "crustacean"], "Crustaceans have a hard shell outside."),
}
DIETS = {
    "carnivore": (["carnivores", "a carnivore", "carnivore", "meat eaters", "a meat eater"], "They eat meat!"),
    "herbivore": (["herbivores", "a herbivore", "an herbivore", "herbivore", "plant eaters", "a plant eater"],
                  "They eat plants!"),
    "omnivore": (["omnivores", "an omnivore", "omnivore"], "They eat both plants and meat!"),
}

# (singular, plural, class, legs, can fly, diet). None: not stated.
ANIMALS = [
    ("dog", "dogs", "mammal", 4, False, None), ("cat", "cats", "mammal", 4, False, "carnivore"),
    ("cow", "cows", "mammal", 4, False, "herbivore"), ("horse", "horses", "mammal", 4, False, "herbivore"),
    ("pig", "pigs", "mammal", 4, False, "omnivore"), ("sheep", "sheep", "mammal", 4, False, "herbivore"),
    ("goat", "goats", "mammal", 4, False, "herbivore"), ("lion", "lions", "mammal", 4, False, "carnivore"),
    ("tiger", "tigers", "mammal", 4, False, "carnivore"), ("bear", "bears", "mammal", 4, False, "omnivore"),
    ("elephant", "elephants", "mammal", 4, False, "herbivore"),
    ("giraffe", "giraffes", "mammal", 4, False, "herbivore"), ("zebra", "zebras", "mammal", 4, False, "herbivore"),
    ("monkey", "monkeys", "mammal", None, False, None), ("gorilla", "gorillas", "mammal", None, False, None),
    ("chimpanzee", "chimpanzees", "mammal", None, False, "omnivore"),
    ("kangaroo", "kangaroos", "mammal", None, False, "herbivore"),
    ("koala", "koalas", "mammal", 4, False, "herbivore"), ("panda", "pandas", "mammal", 4, False, None),
    ("rabbit", "rabbits", "mammal", 4, False, "herbivore"), ("mouse", "mice", "mammal", 4, False, None),
    ("rat", "rats", "mammal", 4, False, None), ("hamster", "hamsters", "mammal", 4, False, None),
    ("guinea pig", "guinea pigs", "mammal", 4, False, "herbivore"),
    ("squirrel", "squirrels", "mammal", 4, None, None), ("deer", "deer", "mammal", 4, False, "herbivore"),
    ("fox", "foxes", "mammal", 4, False, "omnivore"), ("wolf", "wolves", "mammal", 4, False, "carnivore"),
    ("cheetah", "cheetahs", "mammal", 4, False, "carnivore"),
    ("leopard", "leopards", "mammal", 4, False, "carnivore"), ("jaguar", "jaguars", "mammal", 4, False, "carnivore"),
    ("hippo", "hippos", "mammal", 4, False, "herbivore"),
    ("hippopotamus", "hippopotamuses", "mammal", 4, False, "herbivore"),
    ("rhino", "rhinos", "mammal", 4, False, "herbivore"), ("rhinoceros", "rhinoceroses", "mammal", 4, False, "herbivore"),
    ("camel", "camels", "mammal", 4, False, "herbivore"),
    ("polar bear", "polar bears", "mammal", 4, False, "carnivore"),
    ("seal", "seals", "mammal", None, False, "carnivore"), ("sea lion", "sea lions", "mammal", None, False, "carnivore"),
    ("walrus", "walruses", "mammal", None, False, None), ("otter", "otters", "mammal", 4, False, None),
    ("beaver", "beavers", "mammal", 4, False, "herbivore"), ("raccoon", "raccoons", "mammal", 4, False, "omnivore"),
    ("skunk", "skunks", "mammal", 4, False, "omnivore"), ("hedgehog", "hedgehogs", "mammal", 4, False, None),
    ("porcupine", "porcupines", "mammal", 4, False, "herbivore"), ("sloth", "sloths", "mammal", None, False, None),
    ("platypus", "platypuses", "mammal", 4, False, None), ("donkey", "donkeys", "mammal", 4, False, "herbivore"),
    ("llama", "llamas", "mammal", 4, False, "herbivore"), ("moose", "moose", "mammal", 4, False, "herbivore"),
    ("reindeer", "reindeer", "mammal", 4, False, "herbivore"), ("bison", "bison", "mammal", 4, False, "herbivore"),
    ("manatee", "manatees", "mammal", None, False, "herbivore"), ("mole", "moles", "mammal", 4, False, None),
    ("chipmunk", "chipmunks", "mammal", 4, False, None), ("armadillo", "armadillos", "mammal", 4, False, None),
    ("anteater", "anteaters", "mammal", 4, False, None), ("opossum", "opossums", "mammal", 4, False, "omnivore"),
    ("hyena", "hyenas", "mammal", 4, False, "carnivore"), ("meerkat", "meerkats", "mammal", 4, False, None),
    ("lemur", "lemurs", "mammal", None, False, None), ("orangutan", "orangutans", "mammal", None, False, None),
    ("ferret", "ferrets", "mammal", 4, False, "carnivore"), ("badger", "badgers", "mammal", 4, False, None),
    ("penguin", "penguins", "bird", 2, None, None), ("ostrich", "ostriches", "bird", 2, None, None),
    ("emu", "emus", "bird", 2, False, None), ("kiwi", "kiwis", "bird", 2, False, None),
    ("cassowary", "cassowaries", "bird", 2, False, None), ("dodo", "dodos", "bird", 2, False, None),
    ("eagle", "eagles", "bird", 2, True, "carnivore"), ("owl", "owls", "bird", 2, True, "carnivore"),
    ("parrot", "parrots", "bird", 2, True, None), ("pigeon", "pigeons", "bird", 2, True, None),
    ("crow", "crows", "bird", 2, True, None), ("robin", "robins", "bird", 2, True, None),
    ("sparrow", "sparrows", "bird", 2, True, None), ("seagull", "seagulls", "bird", 2, True, None),
    ("hummingbird", "hummingbirds", "bird", 2, True, None), ("flamingo", "flamingos", "bird", 2, True, None),
    ("peacock", "peacocks", "bird", 2, None, None), ("chicken", "chickens", "bird", 2, None, "omnivore"),
    ("duck", "ducks", "bird", 2, True, None), ("goose", "geese", "bird", 2, True, None),
    ("swan", "swans", "bird", 2, True, None), ("turkey", "turkeys", "bird", 2, None, None),
    ("pelican", "pelicans", "bird", 2, True, None), ("stork", "storks", "bird", 2, True, None),
    ("heron", "herons", "bird", 2, True, None), ("woodpecker", "woodpeckers", "bird", 2, True, None),
    ("vulture", "vultures", "bird", 2, True, None), ("falcon", "falcons", "bird", 2, True, "carnivore"),
    ("hawk", "hawks", "bird", 2, True, "carnivore"), ("toucan", "toucans", "bird", 2, True, None),
    ("cardinal", "cardinals", "bird", 2, True, None), ("blue jay", "blue jays", "bird", 2, True, None),
    ("puffin", "puffins", "bird", 2, True, None), ("canary", "canaries", "bird", 2, True, None),
    ("parakeet", "parakeets", "bird", 2, True, None), ("macaw", "macaws", "bird", 2, True, None),
    ("cockatoo", "cockatoos", "bird", 2, True, None), ("raven", "ravens", "bird", 2, True, None),
    ("magpie", "magpies", "bird", 2, True, None), ("swallow", "swallows", "bird", 2, True, None),
    ("kingfisher", "kingfishers", "bird", 2, True, None), ("albatross", "albatrosses", "bird", 2, True, None),
    ("goldfish", "goldfish", "fish", 0, None, None), ("salmon", "salmon", "fish", 0, None, None),
    ("tuna", "tuna", "fish", 0, None, None), ("trout", "trout", "fish", 0, None, None),
    ("clownfish", "clownfish", "fish", 0, None, None), ("catfish", "catfish", "fish", 0, None, None),
    ("swordfish", "swordfish", "fish", 0, None, None), ("piranha", "piranhas", "fish", 0, None, None),
    ("eel", "eels", "fish", 0, None, None), ("seahorse", "seahorses", "fish", 0, None, None),
    ("stingray", "stingrays", "fish", 0, None, None), ("carp", "carp", "fish", 0, None, None),
    ("cod", "cod", "fish", 0, None, None), ("guppy", "guppies", "fish", 0, None, None),
    ("pufferfish", "pufferfish", "fish", 0, None, None), ("angelfish", "angelfish", "fish", 0, None, None),
    ("shark", "sharks", "fish", 0, False, "carnivore"),
    ("tortoise", "tortoises", "reptile", 4, False, "herbivore"), ("iguana", "iguanas", "reptile", 4, False, None),
    ("gecko", "geckos", "reptile", 4, None, None), ("chameleon", "chameleons", "reptile", 4, False, None),
    ("komodo dragon", "komodo dragons", "reptile", 4, False, "carnivore"),
    ("cobra", "cobras", "reptile", 0, False, "carnivore"), ("python", "pythons", "reptile", 0, False, "carnivore"),
    ("rattlesnake", "rattlesnakes", "reptile", 0, False, "carnivore"), ("snake", "snakes", "reptile", 0, False, "carnivore"),
    ("turtle", "turtles", "reptile", 4, False, None), ("lizard", "lizards", "reptile", 4, None, None),
    ("crocodile", "crocodiles", "reptile", 4, False, "carnivore"),
    ("alligator", "alligators", "reptile", 4, False, "carnivore"),
    ("frog", "frogs", "amphibian", 4, False, None), ("toad", "toads", "amphibian", 4, False, None),
    ("salamander", "salamanders", "amphibian", 4, False, None), ("newt", "newts", "amphibian", 4, False, None),
    ("axolotl", "axolotls", "amphibian", 4, False, None),
    ("beetle", "beetles", "insect", 6, None, None), ("moth", "moths", "insect", 6, True, None),
    ("grasshopper", "grasshoppers", "insect", 6, None, None), ("cricket", "crickets", "insect", 6, None, None),
    ("fly", "flies", "insect", 6, True, None), ("mosquito", "mosquitoes", "insect", 6, True, None),
    ("dragonfly", "dragonflies", "insect", 6, True, None), ("wasp", "wasps", "insect", 6, True, None),
    ("hornet", "hornets", "insect", 6, True, None), ("cockroach", "cockroaches", "insect", 6, None, None),
    ("termite", "termites", "insect", 6, None, None), ("flea", "fleas", "insect", 6, False, None),
    ("firefly", "fireflies", "insect", 6, True, None), ("praying mantis", "praying mantises", "insect", 6, None, None),
    ("stick insect", "stick insects", "insect", 6, None, None), ("bee", "bees", "insect", 6, True, None),
    ("butterfly", "butterflies", "insect", 6, True, None), ("ladybug", "ladybugs", "insect", 6, True, None),
    ("ant", "ants", "insect", 6, None, None),
    ("scorpion", "scorpions", "arachnid", 8, False, None), ("tick", "ticks", "arachnid", 8, False, None),
    ("tarantula", "tarantulas", "arachnid", 8, False, None), ("mite", "mites", "arachnid", 8, False, None),
    ("octopus", "octopuses", "mollusk", None, False, None), ("squid", "squid", "mollusk", None, False, None),
    ("snail", "snails", "mollusk", 0, False, None), ("slug", "slugs", "mollusk", 0, False, None),
    ("clam", "clams", "mollusk", None, False, None),
    ("crab", "crabs", "crustacean", None, False, None), ("lobster", "lobsters", "crustacean", None, False, None),
    ("shrimp", "shrimp", "crustacean", None, False, None),
]
# Animals in the sea that breathe air, and ones that breathe underwater
BREATHE_AIR = ["whale", "dolphin", "seal", "sea lion", "walrus", "otter", "manatee", "penguin", "sea turtle",
               "crocodile", "alligator", "polar bear"]
BREATHE_WATER = ["goldfish", "salmon", "tuna", "trout", "clownfish", "shark", "stingray", "octopus", "squid",
                 "lobster", "seahorse"]
PLURALS = {a[0]: a[1] for a in ANIMALS}
PLURALS.update({"whale": "whales", "dolphin": "dolphins", "sea turtle": "sea turtles"})

# (animal, baby names); "a baby dog is a puppy". Reverse facts only for names used for one kind
BABIES = [
    ("dog", ["puppy", "pup"]), ("cat", ["kitten", "kitty"]), ("cow", ["calf"]), ("horse", ["foal", "colt", "filly"]),
    ("sheep", ["lamb"]), ("goat", ["kid"]), ("pig", ["piglet"]), ("chicken", ["chick"]),
    ("duck", ["duckling", "chick"]), ("goose", ["gosling"]), ("swan", ["cygnet"]),
    ("frog", ["tadpole", "froglet", "polliwog"]), ("kangaroo", ["joey"]), ("koala", ["joey"]), ("bear", ["cub"]),
    ("lion", ["cub"]), ("tiger", ["cub"]), ("fox", ["kit", "cub", "pup"]), ("wolf", ["pup", "cub"]),
    ("deer", ["fawn", "calf"]), ("owl", ["owlet", "chick"]), ("eagle", ["eaglet", "chick"]), ("elephant", ["calf"]),
    ("giraffe", ["calf"]), ("whale", ["calf"]), ("dolphin", ["calf"]), ("rabbit", ["kit", "kitten", "bunny"]),
    ("seal", ["pup"]), ("butterfly", ["caterpillar", "larva"]), ("hippo", ["calf"]), ("zebra", ["foal"]),
    ("donkey", ["foal"]), ("penguin", ["chick"]), ("turkey", ["poult", "chick"]), ("mouse", ["pup", "pinky"]),
]
BABY_ONLY_OF = {"puppy": ["dog"], "duckling": ["duck"], "gosling": ["goose"], "cygnet": ["swan"],
                "piglet": ["pig"], "lamb": ["sheep"], "owlet": ["owl"], "eaglet": ["eagle"], "fawn": ["deer"],
                "tadpole": ["frog", "toad"]}
IRREGULAR = {"puppy": "puppies", "kitty": "kitties", "calf": "calves", "filly": "fillies", "pinky": "pinkies",
             "larva": "larvae", "polliwog": "polliwogs", "butterfly": "butterflies", "mouse": "mice",
             "sheep": "sheep", "deer": "deer", "goose": "geese", "wolf": "wolves", "fox": "foxes"}


def plural(word: str) -> str:
    return IRREGULAR.get(word) or PLURALS.get(word) or (word + "es" if word.endswith(("s", "x", "ch")) else word + "s")


def animals(sets: dict) -> list:
    facts = []
    sets["animal_classes"] = sorted({f for forms, _ in CLASSES.values() for f in forms})
    sets["diets"] = sorted({f for forms, _ in DIETS.values() for f in forms})
    for one, many, cls, legs, flies, diet in ANIMALS:
        names = subject(one, many)
        shown = many[:1].upper() + many[1:]
        forms, about = CLASSES[cls]
        facts.append({
            "id": f"class_{slug(one)}", "type": "is", "subject": names, "true": forms, "false_from": ["animal_classes"],
            "correct": f"{shown} are {forms[0]}! {about}",
            "examples": [[f"{many} are {_other(sets['animal_classes'], forms)}", "wrong"], [f"{many} are {forms[0]}", "right"]]})
        if legs is not None:
            facts.append({
                "id": f"legs_{slug(one)}", "type": "count", "subject": names, "noun": "legs?", "value": legs,
                "correct": f"{shown} have {legs} legs!" if legs else f"{shown} don't have any legs!",
                "examples": [[f"{many} have {legs + 2} legs", "wrong"], [f"{many} have {legs or 'no'} legs", "right"]]})
        if flies is not None:
            facts.append({
                "id": f"fly_{slug(one)}", "type": "can", "subject": names, "verb": "fly", "value": flies,
                "correct": f"{shown} can fly!" if flies else f"{shown} can't fly!",
                "examples": [[f"{many} {'cant' if flies else 'can'} fly", "wrong"],
                             [f"{many} {'can' if flies else 'cant'} fly", "right"]]})
        if diet is not None:
            diet_forms, eats = DIETS[diet]
            facts.append({
                "id": f"diet_{slug(one)}", "type": "is", "subject": names, "true": diet_forms, "false_from": ["diets"],
                "correct": f"{shown} are {diet_forms[0]}. {eats}",
                "examples": [[f"{many} are {_other(sets['diets'], diet_forms)}", "wrong"],
                             [f"{many} are {diet_forms[0]}", "right"]]})
    for one in BREATHE_AIR + BREATHE_WATER:
        many = PLURALS[one]
        water = one in BREATHE_WATER
        shown = many[:1].upper() + many[1:]
        facts.append({
            "id": f"breathe_{slug(one)}", "type": "can", "subject": subject(one, many), "verb": "breathe underwater",
            "value": water,
            "correct": f"{shown} can breathe underwater. They breathe with gills!" if water
            else f"{shown} can't breathe underwater. They come up to the surface to breathe air!",
            "examples": [[f"{many} {'cant' if water else 'can'} breathe underwater", "wrong"],
                         [f"{many} {'can' if water else 'cant'} breathe underwater", "right"]]})
    birds = [(a[0], a[1]) for a in ANIMALS if a[2] == "bird"]
    facts.append({"id": "wings_birds", "type": "count", "subject": subject("birds", "a bird", *[n for b in birds for n in b]),
                  "noun": "wings?", "value": 2, "correct": "Birds have 2 wings!",
                  "examples": [["birds have 4 wings", "wrong"], ["birds have 2 wings", "right"]]})
    sets["baby_names"] = sorted({w for _, words in BABIES for n in words for w in (a_or_an(n), plural(n), n)})
    for animal, words in BABIES:
        true = [w for n in words for w in (a_or_an(n), plural(n), n)]
        many = plural(animal)
        facts.append({
            "id": f"baby_{slug(animal)}", "type": "is",
            "subject": rf"(?:(?:a |the )?baby {re.escape(animal)}|baby {re.escape(many)})",
            "true": true, "false_from": ["baby_names"],
            "correct": f"A baby {animal} is called {a_or_an(words[0])}!",
            "examples": [[f"a baby {animal} is {_other(sets['baby_names'], true)}", "wrong"],
                         [f"a baby {animal} is {a_or_an(words[0])}", "right"]]})
    sets["baby_of"] = sorted({w for animal, _ in BABIES + [("toad", [])] for w in (f"a baby {animal}", f"baby {plural(animal)}")})
    for name, kinds in BABY_ONLY_OF.items():
        true = [w for k in kinds for w in (f"a baby {k}", f"baby {plural(k)}")]
        facts.append({
            "id": f"baby_name_{slug(name)}", "type": "is", "subject": subject(name, plural(name), articles="(?:a |an )?"),
            "true": true, "false_from": ["baby_of"],
            "correct": f"{a_or_an(name).capitalize()} is a baby {kinds[0]}!" if len(kinds) == 1
            else f"{a_or_an(name).capitalize()} is a baby {kinds[0]} or {kinds[1]}!",
            "examples": [[f"{a_or_an(name)} is {_other(sets['baby_of'], true)}", "wrong"],
                         [f"{a_or_an(name)} is {true[0]}", "right"]]})
    return facts


# ----------------------------------------------------------------------------------------------
# Space, superlatives
# ----------------------------------------------------------------------------------------------

PLANETS = ["mercury", "venus", "earth", "mars", "jupiter", "saturn", "uranus", "neptune"]
ORDINALS = ["first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth"]
SHORT_ORDINALS = ["1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th"]

# (id, superlative phrases, right answers, set of other answers, correct text)
SUPERLATIVES = [
    ("biggest_planet", ["the biggest planet", "the largest planet"], ["jupiter"], "planets",
     "Jupiter is the biggest planet in our solar system!"),
    ("smallest_planet", ["the smallest planet"], ["mercury"], "planets",
     "Mercury is the smallest planet in our solar system!"),
    ("closest_planet", ["the closest planet to the sun", "the nearest planet to the sun"], ["mercury"], "planets",
     "Mercury is the closest planet to the sun!"),
    ("farthest_planet", ["the farthest planet from the sun", "the furthest planet from the sun"], ["neptune"],
     "planets", "Neptune is the farthest planet from the sun!"),
    ("hottest_planet", ["the hottest planet"], ["venus"], "planets",
     "Venus is the hottest planet. Its thick clouds trap the heat, so it's even hotter than Mercury!"),
    ("red_planet", ["the red planet"], ["mars"], "planets", "Mars is called the red planet!"),
    ("biggest_ocean", ["the biggest ocean", "the largest ocean"], ["the pacific", "the pacific ocean", "pacific"],
     "oceans", "The Pacific Ocean is the biggest ocean!"),
    ("smallest_ocean", ["the smallest ocean"], ["the arctic", "the arctic ocean", "arctic"], "oceans",
     "The Arctic Ocean is the smallest ocean!"),
    ("biggest_continent", ["the biggest continent", "the largest continent"], ["asia"], "continents",
     "Asia is the biggest continent!"),
    ("smallest_continent", ["the smallest continent"], ["australia", "oceania"], "continents",
     "Australia is the smallest continent!"),
    ("tallest_mountain", ["the tallest mountain", "the highest mountain", "the tallest mountain in the world",
                          "the highest mountain in the world"],
     ["mount everest", "mt everest", "everest"], "mountains", "Mount Everest is the tallest mountain in the world!"),
    ("biggest_country", ["the biggest country", "the largest country", "the biggest country in the world"],
     ["russia"], "countries", "Russia is the biggest country in the world!"),
    ("biggest_animal", ["the biggest animal", "the largest animal", "the biggest animal in the world",
                        "the biggest animal ever"],
     ["the blue whale", "a blue whale", "blue whales", "the whale", "a whale", "whales"], "big_animals",
     "The blue whale is the biggest animal ever, even bigger than the dinosaurs!"),
    ("biggest_land_animal", ["the biggest land animal", "the largest land animal"],
     ["the elephant", "an elephant", "elephants", "the african elephant", "african elephants"], "big_animals",
     "The African elephant is the biggest animal on land!"),
    ("tallest_animal", ["the tallest animal", "the tallest animal in the world"],
     ["the giraffe", "a giraffe", "giraffes"], "big_animals", "The giraffe is the tallest animal!"),
    ("fastest_land_animal", ["the fastest land animal", "the fastest animal on land"],
     ["the cheetah", "a cheetah", "cheetahs"], "fast_animals", "The cheetah is the fastest animal on land!"),
    ("fastest_animal", ["the fastest animal", "the fastest animal in the world"],
     ["the peregrine falcon", "a peregrine falcon", "peregrine falcons", "the falcon", "falcons"], "fast_animals",
     "Cheetahs are the fastest on land, but the peregrine falcon is the fastest animal of all when it dives!"),
    ("biggest_bird", ["the biggest bird", "the largest bird"], ["the ostrich", "an ostrich", "ostriches"], "birds",
     "The ostrich is the biggest bird!"),
    ("smallest_bird", ["the smallest bird"], ["the hummingbird", "a hummingbird", "hummingbirds",
                                              "the bee hummingbird"], "birds",
     "The bee hummingbird is the smallest bird!"),
    ("biggest_fish", ["the biggest fish", "the largest fish"], ["the whale shark", "a whale shark", "whale sharks"],
     "big_animals", "The whale shark is the biggest fish! Blue whales are bigger, but they're mammals."),
    ("biggest_cat", ["the biggest cat", "the largest cat"], ["the tiger", "a tiger", "tigers"], "cats",
     "The tiger is the biggest cat!"),
    ("closest_star", ["the closest star to earth", "the nearest star to earth", "the closest star"],
     ["the sun", "sun"], "stars", "The sun is the closest star to Earth!"),
    ("biggest_organ", ["the biggest organ", "the largest organ", "the biggest organ in the body",
                       "the largest organ in the body"], ["the skin", "skin"], "organs",
     "Your skin is your biggest organ!"),
]
SUPERLATIVE_SETS = {
    "planets": PLANETS + ["the earth", "pluto", "the sun", "the moon"],
    "oceans": [f for o in ("pacific", "atlantic", "indian", "arctic", "southern")
               for f in (o, f"the {o}", f"the {o} ocean")],
    "continents": CONTINENTS + ["oceania"],
    "mountains": ["mount everest", "mt everest", "everest", "k2", "kilimanjaro", "mount kilimanjaro", "denali",
                  "mont blanc", "mount fuji", "mt fuji", "the matterhorn", "matterhorn"],
    "countries": [c for c, *_ in COUNTRIES if c not in ("england", "scotland", "wales")] + ["the usa", "america"],
    "big_animals": ["the elephant", "an elephant", "elephants", "the african elephant", "african elephants",
                    "the giraffe", "a giraffe", "giraffes", "the dinosaur", "dinosaurs", "the t rex", "t rex",
                    "the shark", "sharks", "a shark", "the whale shark", "a whale shark", "whale sharks",
                    "the blue whale", "a blue whale", "blue whales", "the whale", "a whale", "whales",
                    "the hippo", "hippos", "the rhino", "rhinos", "the great white shark", "great white sharks"],
    "fast_animals": ["the cheetah", "a cheetah", "cheetahs", "the lion", "lions", "the horse", "horses",
                     "the peregrine falcon", "a peregrine falcon", "peregrine falcons", "the falcon", "falcons",
                     "the eagle", "eagles", "the tiger", "tigers", "the leopard", "leopards"],
    "birds": ["the ostrich", "an ostrich", "ostriches", "the eagle", "eagles", "the emu", "emus", "the penguin",
              "penguins", "the hummingbird", "a hummingbird", "hummingbirds", "the bee hummingbird",
              "the albatross", "albatrosses", "the condor", "condors", "the sparrow", "sparrows"],
    "cats": ["the tiger", "a tiger", "tigers", "the lion", "a lion", "lions", "the cheetah", "cheetahs",
             "the leopard", "leopards", "the jaguar", "jaguars"],
    "stars": ["the sun", "sun", "the moon", "polaris", "the north star", "sirius", "proxima centauri",
              "alpha centauri"],
    "organs": ["the skin", "skin", "the heart", "the brain", "the liver", "the lungs", "the stomach"],
}


def space(sets: dict) -> list:
    facts = []
    for name in PLANETS:
        names = [name] + (["the earth"] if name == "earth" else [])
        facts.append({
            "id": f"planet_{name}", "type": "is", "subject": alt(*names), "true": ["a planet"],
            "false": ["a star", "a moon", "a dwarf planet"],
            "correct": f"{name.capitalize()} is a planet!",
            "examples": [[f"{name} is a star", "wrong"], [f"{name} is a planet", "right"]]})
    facts.append({"id": "planet_pluto", "type": "is", "subject": "pluto", "true": ["a dwarf planet"],
                  "false": ["a planet", "a star", "a moon"],
                  "correct": "Pluto is called a dwarf planet now. It used to count as the ninth planet!",
                  "examples": [["pluto is a planet", "wrong"], ["pluto is a dwarf planet", "right"]]})
    order_forms = lambda i: [f"the {o} planet{s}" for o in (ORDINALS[i], SHORT_ORDINALS[i])  # noqa: E731
                             for s in ("", " from the sun")]
    sets["planet_order"] = sorted({f for i in range(8) for f in order_forms(i)})
    for i, name in enumerate(PLANETS):
        names = [name] + (["the earth"] if name == "earth" else [])
        facts.append({
            "id": f"planet_order_{name}", "type": "is", "subject": alt(*names), "true": order_forms(i),
            "false_from": ["planet_order"],
            "correct": f"{name.capitalize()} is the {ORDINALS[i]} planet from the sun!",
            "examples": [[f"{name} is the {ORDINALS[(i + 1) % 8]} planet from the sun", "wrong"],
                         [f"{name} is the {ORDINALS[i]} planet from the sun", "right"]]})
    facts.append({"id": "mars_moons", "type": "count", "subject": "mars", "noun": "moons?", "value": 2,
                  "correct": "Mars has 2 tiny moons, Phobos and Deimos!",
                  "examples": [["mars has 3 moons", "wrong"], ["mars has 2 moons", "right"]]})

    sets.update(SUPERLATIVE_SETS)
    for fact_id, phrases, answers, others, correct in SUPERLATIVES:
        facts.append({
            "id": f"most_{fact_id}", "type": "is", "subject": alt(*phrases), "true": answers, "false_from": [others],
            "correct": correct,
            "examples": [[f"{phrases[0]} is {_other(sets[others], answers)}", "wrong"],
                         [f"{phrases[0]} is {answers[0]}", "right"]]})
    return facts


# ----------------------------------------------------------------------------------------------
# Counts: calendar, shapes, body, games, measurements
# ----------------------------------------------------------------------------------------------

MONTHS = [("january", 31), ("february", [28, 29]), ("march", 31), ("april", 30), ("may", 31), ("june", 30),
          ("july", 31), ("august", 31), ("september", 30), ("october", 31), ("november", 30), ("december", 31)]

# (id, subject names, example subject, noun forms, example noun, value, correct)
COUNTS = [
    ("decade_years", ["a decade", "one decade"], "a decade", ["years?"], "years", 10, "A decade is 10 years!"),
    ("century_years", ["a century", "one century"], "a century", ["years?"], "years", 100, "A century is 100 years!"),
    ("millennium_years", ["a millennium", "one millennium"], "a millennium", ["years?"], "years", 1000,
     "A millennium is 1,000 years!"),
    ("year_weeks", ["a year", "one year"], "a year", ["weeks?"], "weeks", 52, "A year has 52 weeks!"),
    ("year_seasons", ["a year", "one year"], "a year", ["seasons?"], "seasons", 4,
     "A year has 4 seasons: spring, summer, fall and winter!"),
    ("leap_year_days", ["a leap year", "leap years"], "a leap year", ["days?"], "days", 366,
     "A leap year has 366 days, one more than other years, because February gets a 29th day!"),
    ("heptagon_sides", ["a heptagon", "heptagons"], "a heptagon", ["sides?", "corners?"], "sides", 7,
     "A heptagon has 7 sides!"),
    ("nonagon_sides", ["a nonagon", "nonagons"], "a nonagon", ["sides?", "corners?"], "sides", 9, "A nonagon has 9 sides!"),
    ("decagon_sides", ["a decagon", "decagons"], "a decagon", ["sides?", "corners?"], "sides", 10,
     "A decagon has 10 sides!"),
    ("dodecagon_sides", ["a dodecagon", "dodecagons"], "a dodecagon", ["sides?", "corners?"], "sides", 12,
     "A dodecagon has 12 sides!"),
    ("triangle_angles", ["a triangle", "triangles"], "a triangle", ["angles?"], "angles", 3, "A triangle has 3 angles!"),
    ("square_angles", ["a square", "squares", "a rectangle", "rectangles"], "a square", ["angles?"], "angles", 4,
     "Squares and rectangles have 4 angles!"),
    ("cube_edges", ["a cube", "cubes"], "a cube", ["edges?"], "edges", 12, "A cube has 12 edges!"),
    ("cube_corners", ["a cube", "cubes"], "a cube", ["corners?", "vertices", "vertexes"], "corners", 8,
     "A cube has 8 corners!"),
    ("people_eyes", ["people", "humans", "a person", "a human"], "people", ["eyes?"], "eyes", 2, "People have 2 eyes!"),
    ("people_ears", ["people", "humans", "a person", "a human"], "people", ["ears?"], "ears", 2, "People have 2 ears!"),
    ("people_noses", ["people", "humans", "a person", "a human"], "people", ["noses?"], "noses", 1,
     "People have 1 nose!"),
    ("people_hands", ["people", "humans", "a person", "a human"], "people", ["hands?"], "hands", 2,
     "People have 2 hands!"),
    ("people_feet", ["people", "humans", "a person", "a human"], "people", ["feet", "foots?"], "feet", 2,
     "People have 2 feet!"),
    ("people_legs", ["people", "humans", "a person", "a human"], "people", ["legs?"], "legs", 2, "People have 2 legs!"),
    ("people_hearts", ["people", "humans", "a person", "a human"], "people", ["hearts?"], "hearts", 1,
     "People have 1 heart!"),
    ("people_lungs", ["people", "humans", "a person", "a human"], "people", ["lungs?"], "lungs", 2,
     "People have 2 lungs!"),
    ("people_kidneys", ["people", "humans", "a person", "a human"], "people", ["kidneys?"], "kidneys", 2,
     "People have 2 kidneys!"),
    ("people_bones", ["people", "humans", "adults", "grown ups", "grownups", "an adult", "a grown up"], "people",
     ["bones?"], "bones", 206,
     "Grown-ups have 206 bones. Babies are born with about 300, and some of them join together as they grow!"),
    ("heart_chambers", ["the heart", "a heart", "the human heart", "a human heart"], "the heart", ["chambers?"],
     "chambers", 4, "The human heart has 4 chambers!"),
    ("insect_body_parts", ["insects", "an insect", "all insects"], "insects", ["body parts?", "parts?"], "body parts",
     3, "Insects have 3 body parts: a head, a thorax and an abdomen!"),
    ("spider_body_parts", ["spiders", "a spider"], "spiders", ["body parts?", "parts?"], "body parts", 2,
     "Spiders have 2 main body parts!"),
    ("insect_antennae", ["insects", "an insect"], "insects", ["antennae", "antennas", "antenna"], "antennae", 2,
     "Insects have 2 antennae!"),
    ("chessboard_squares", ["a chessboard", "a chess board", "chessboards", "chess boards", "a checkerboard",
                            "a checkers board"], "a chessboard", ["squares?"], "squares", 64,
     "A chessboard has 64 squares: 8 rows of 8!"),
    ("chess_pieces", ["chess", "a chess set", "a chess game"], "chess", ["pieces?"], "pieces", 32,
     "A chess game starts with 32 pieces, 16 for each player!"),
    ("checkers_pieces", ["checkers", "a checkers game"], "checkers", ["pieces?"], "pieces", 24,
     "Checkers starts with 24 pieces, 12 for each player!"),
    ("deck_cards", ["a deck of cards", "a deck", "a card deck"], "a deck of cards", ["cards?"], "cards", [52, 54],
     "A deck of cards has 52 cards, plus jokers in some decks!"),
    ("piano_keys", ["a piano", "pianos"], "a piano", ["keys?"], "keys", 88, "A piano has 88 keys!"),
    ("violin_strings", ["a violin", "violins"], "a violin", ["strings?"], "strings", 4, "A violin has 4 strings!"),
    ("guitar_strings", ["a guitar", "guitars"], "a guitar", ["strings?"], "strings", [6, 12],
     "A guitar usually has 6 strings!"),
    ("ukulele_strings", ["a ukulele", "ukuleles"], "a ukulele", ["strings?"], "strings", 4, "A ukulele has 4 strings!"),
    ("bike_wheels", ["a bike", "a bicycle", "bikes", "bicycles"], "a bike", ["wheels?"], "wheels", 2,
     "A bike has 2 wheels!"),
    ("tricycle_wheels", ["a tricycle", "tricycles", "a trike"], "a tricycle", ["wheels?"], "wheels", 3,
     "A tricycle has 3 wheels. \"Tri\" means three!"),
    ("unicycle_wheels", ["a unicycle", "unicycles"], "a unicycle", ["wheels?"], "wheels", 1, "A unicycle has 1 wheel!"),
    ("soccer_team", ["a soccer team", "soccer teams"], "a soccer team", ["players?"], "players", 11,
     "A soccer team has 11 players on the field!"),
    ("basketball_team", ["a basketball team", "basketball teams"], "a basketball team", ["players?"], "players", 5,
     "A basketball team has 5 players on the court!"),
    ("baseball_team", ["a baseball team", "baseball teams"], "a baseball team", ["players?"], "players", 9,
     "A baseball team has 9 players on the field!"),
    ("volleyball_team", ["a volleyball team", "volleyball teams"], "a volleyball team", ["players?"], "players", 6,
     "A volleyball team has 6 players on the court!"),
    ("clock_numbers", ["a clock", "clocks"], "a clock", ["numbers?"], "numbers", 12, "A clock has 12 numbers!"),
    ("alphabet_letters", ["the alphabet", "the english alphabet", "the abc"], "the alphabet", ["letters?"], "letters",
     26, "The alphabet has 26 letters, from A to Z!"),
    ("us_flag_stars", ["the american flag", "the us flag", "the usa flag", "the flag of the usa",
                       "the united states flag"], "the american flag", ["stars?"], "stars", 50,
     "The American flag has 50 stars, one for each state!"),
    ("us_flag_stripes", ["the american flag", "the us flag", "the usa flag", "the flag of the usa",
                         "the united states flag"], "the american flag", ["stripes?"], "stripes", 13,
     "The American flag has 13 stripes, for the first 13 colonies!"),
    ("usa_states", ["the usa", "the us", "america", "the united states"], "america", ["states?"], "states", 50,
     "The United States has 50 states!"),
    ("dozen", ["a dozen"], "a dozen", ["things?", "eggs?", "donuts?", "cookies?"], "eggs", 12, "A dozen is 12!"),
    ("foot_inches", ["a foot", "one foot"], "a foot", ["inches?"], "inches", 12, "A foot is 12 inches!"),
    ("yard_feet", ["a yard", "one yard"], "a yard", ["feet", "foot"], "feet", 3, "A yard is 3 feet!"),
    ("mile_feet", ["a mile", "one mile"], "a mile", ["feet", "foot"], "feet", 5280, "A mile is 5,280 feet!"),
    ("meter_centimeters", ["a meter", "one meter", "a metre"], "a meter", ["centimeters?", "centimetres?", "cm"],
     "centimeters", 100, "A meter is 100 centimeters!"),
    ("kilometer_meters", ["a kilometer", "one kilometer", "a kilometre"], "a kilometer", ["meters?", "metres?"],
     "meters", 1000, "A kilometer is 1,000 meters!"),
    ("centimeter_millimeters", ["a centimeter", "one centimeter"], "a centimeter", ["millimeters?", "mm"],
     "millimeters", 10, "A centimeter is 10 millimeters!"),
    ("kilogram_grams", ["a kilogram", "one kilogram", "a kilo"], "a kilogram", ["grams?"], "grams", 1000,
     "A kilogram is 1,000 grams!"),
    ("pound_ounces", ["a pound", "one pound"], "a pound", ["ounces?"], "ounces", 16, "A pound is 16 ounces!"),
    ("gallon_quarts", ["a gallon", "one gallon"], "a gallon", ["quarts?"], "quarts", 4, "A gallon is 4 quarts!"),
    ("dollar_cents", ["a dollar", "one dollar"], "a dollar", ["cents?", "pennies"], "cents", 100,
     "A dollar is 100 cents!"),
    ("dollar_quarters", ["a dollar", "one dollar"], "a dollar", ["quarters?"], "quarters", 4,
     "A dollar is 4 quarters!"),
    ("dollar_dimes", ["a dollar", "one dollar"], "a dollar", ["dimes?"], "dimes", 10, "A dollar is 10 dimes!"),
    ("nickel_cents", ["a nickel", "one nickel"], "a nickel", ["cents?", "pennies"], "cents", 5, "A nickel is 5 cents!"),
    ("dime_cents", ["a dime", "one dime"], "a dime", ["cents?", "pennies"], "cents", 10, "A dime is 10 cents!"),
    ("quarter_cents", ["a quarter", "one quarter"], "a quarter", ["cents?", "pennies"], "cents", 25,
     "A quarter is 25 cents!"),
]
# (id, noun forms, example noun, value, correct): "there are 50 states in the usa"
THERE_ARE = [
    ("there_states", ["states? in (?:the usa|the us|america|the united states)"], "states in america", 50,
     "There are 50 states in the United States!"),
    ("there_letters", ["letters? in the (?:english )?alphabet"], "letters in the alphabet", 26,
     "There are 26 letters in the alphabet!"),
    ("there_oceans", ["oceans?(?: in the world| on earth)?"], "oceans", 5,
     "There are 5 oceans: the Pacific, Atlantic, Indian, Arctic and Southern Oceans!"),
    ("there_days_year", ["days? in a year"], "days in a year", [365, 366], "There are 365 days in a year, and 366 in a leap year!"),
    ("there_hours_day", ["hours? in a day"], "hours in a day", 24, "There are 24 hours in a day!"),
    ("there_minutes_hour", ["minutes? in an hour"], "minutes in an hour", 60, "There are 60 minutes in an hour!"),
    ("there_seconds_minute", ["seconds? in a minute"], "seconds in a minute", 60, "There are 60 seconds in a minute!"),
    ("there_weeks_year", ["weeks? in a year"], "weeks in a year", 52, "There are 52 weeks in a year!"),
    ("there_years_decade", ["years? in a decade"], "years in a decade", 10, "There are 10 years in a decade!"),
    ("there_years_century", ["years? in a century"], "years in a century", 100, "There are 100 years in a century!"),
    ("there_squares_chessboard", ["squares? on a (?:chessboard|chess board)"], "squares on a chessboard", 64,
     "There are 64 squares on a chessboard!"),
    ("there_cards_deck", ["cards? in a deck(?: of cards)?"], "cards in a deck", [52, 54],
     "There are 52 cards in a deck, plus jokers in some decks!"),
    ("there_keys_piano", ["keys? on a piano"], "keys on a piano", 88, "There are 88 keys on a piano!"),
    ("there_colors_rainbow", ["colou?rs? in (?:a|the) rainbow"], "colors in a rainbow", 7,
     "There are 7 colors in a rainbow: red, orange, yellow, green, blue, indigo and violet!"),
    ("there_bones", ["bones? in (?:the|a) (?:human )?body"], "bones in the human body", 206,
     "Grown-ups have 206 bones. Babies are born with about 300, and some of them join together as they grow!"),
    ("there_seasons", ["seasons?(?: in a year)?"], "seasons", 4,
     "There are 4 seasons: spring, summer, fall and winter!"),
    ("there_players_soccer", ["players? on a soccer team"], "players on a soccer team", 11,
     "There are 11 players on a soccer team on the field!"),
    ("there_inches_foot", ["inches? in a foot"], "inches in a foot", 12, "There are 12 inches in a foot!"),
    ("there_cents_dollar", ["cents? in a dollar"], "cents in a dollar", 100, "There are 100 cents in a dollar!"),
    ("there_stars_flag", ["stars? on the (?:american|us|usa) flag"], "stars on the american flag", 50,
     "There are 50 stars on the American flag, one for each state!"),
    ("there_planets_dwarf", ["planets? in (?:the|our) solar system"], "planets in the solar system", 8,
     "There are 8 planets in our solar system!"),
]


def counts(sets: dict) -> list:
    facts = []
    for month, days in MONTHS:
        accepted = days if isinstance(days, list) else [days]
        facts.append({
            "id": f"month_days_{month}", "type": "count", "subject": rf"(?:the month of )?{month}", "noun": "days?",
            "value": days,
            "correct": "February has 28 days, and 29 in a leap year!" if month == "february"
            else f"{month.capitalize()} has {days} days!",
            "examples": [[f"{month} has {wrong_number(accepted)} days", "wrong"], [f"{month} has {accepted[0]} days", "right"]]})
    for fact_id, names, example, nouns, noun, value, correct in COUNTS:
        accepted = value if isinstance(value, list) else [value]
        facts.append({
            "id": f"count_{fact_id}", "type": "count", "subject": subject(*names, articles=""),
            "noun": "(?:" + "|".join(nouns) + ")", "value": value, "correct": correct,
            "examples": [[f"{example} {'have' if not example.startswith(('a ', 'an ', 'the ', 'one ')) else 'has'} "
                          f"{wrong_number(accepted)} {noun}", "wrong"],
                         [f"{example} {'have' if not example.startswith(('a ', 'an ', 'the ', 'one ')) else 'has'} "
                          f"{accepted[0]} {noun}", "right"]]})
    for fact_id, nouns, noun, value, correct in THERE_ARE:
        accepted = value if isinstance(value, list) else [value]
        facts.append({
            "id": fact_id, "type": "there_are", "noun": "(?:" + "|".join(nouns) + ")", "value": value,
            "correct": correct,
            "examples": [[f"there are {wrong_number(accepted)} {noun}", "wrong"], [f"there are {accepted[0]} {noun}", "right"]]})
    return facts


# ----------------------------------------------------------------------------------------------
# Numbers: even, odd, prime
# ----------------------------------------------------------------------------------------------

NUMBERS_UP_TO = 1000
ODD = ["odd", "an odd number", "odd number"]
EVEN = ["even", "an even number", "even number"]
PRIME = ["prime", "a prime number", "a prime", "prime number"]


def numbers(data: dict) -> list:
    words = {v: k for k, v in data["numbers"].items() if k not in ("no", "none", "a", "an")}
    facts = []
    for n in range(NUMBERS_UP_TO + 1):
        factor = next((p for p in range(2, int(n ** 0.5) + 1) if n % p == 0), None)
        prime = n >= 2 and factor is None
        parity, other = (ODD, EVEN) if n % 2 else (EVEN, ODD)
        true = parity + (PRIME if prime else [])
        false = other + ([] if prime else PRIME)
        if n == 2:
            correct = "2 is an even number, and it's the only even prime number!"
        elif prime:
            correct = f"{n} is an odd number, and it's a prime number: only 1 and {n} divide it evenly!"
        elif n < 2:
            correct = f"{n} is {'an odd' if n % 2 else 'an even'} number. It isn't a prime number: a prime number " \
                      f"has exactly two numbers that divide it evenly!"
        else:
            correct = f"{n} is {'an odd' if n % 2 else 'an even'} number. It isn't a prime number, because " \
                      f"{factor} times {n // factor} is {n}."
        names = [str(n)] + ([words[n]] if n in words else [])
        facts.append({
            "id": f"number_{n}", "type": "is", "subject": rf"(?:the number )?{alt(*names)}", "true": true,
            "false": false, "correct": correct,
            "examples": [[f"{n} is {false[0] if false[0] != 'prime' else 'a prime number'}", "wrong"],
                         [f"{n} is {true[0]}", "right"]]})
    return facts


# ----------------------------------------------------------------------------------------------
# Build
# ----------------------------------------------------------------------------------------------

def verify(data: dict) -> list:
    """(fact id, example, problem) for examples not answered as listed"""
    base = FactBase(data)
    problems = []
    for fact in base.facts:
        for message, verdict in fact.get("examples", []):
            checked = base.check_message(message) if verdict is not None else None
            if verdict is None:
                continue
            if checked is None:
                problems.append((fact["id"], message, "not checked"))
            elif checked[1] != (verdict == "right"):
                problems.append((fact["id"], message, f"answered {checked[1]} by {checked[0]['id']}"))
            elif checked[0]["id"] != fact["id"]:
                problems.append((fact["id"], message, f"answered by {checked[0]['id']}"))
    return problems


def generate(data: dict):
    """
    (sets, generated facts, ids left out as already covered, problems) for the file's data;
    problems are (fact id, example, problem) for examples not answered as listed
    """
    sets: dict = {}
    generated = places(sets) + animals(sets) + space(sets) + counts(sets) + numbers(data)
    ids = [f["id"] for f in data["facts"] + generated]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    if duplicates:
        return sets, generated, set(), [(i, "", "duplicate id") for i in duplicates]

    # Leave out generated facts whose examples an earlier fact already answers the same way
    data = {**data, "sets": sets, "generated": generated}
    generated_ids = {f["id"] for f in generated}
    dropped = {fact_id for fact_id, _, problem in verify(data)
               if problem.startswith("answered by ") and fact_id in generated_ids}
    data["generated"] = [f for f in generated if f["id"] not in dropped]
    return sets, data["generated"], dropped, verify(data)


def main() -> int:
    with open(FACTS_PATH, encoding="utf-8") as f:
        text = f.read()
    data = json.loads(text)
    sets, generated, dropped, problems = generate(data)
    if problems:
        for problem in problems:
            print(*problem, sep=" | ")
        return 1
    data = {**data, "sets": sets, "generated": generated}

    head = text[: text.index(',\n  "sets":')] if ',\n  "sets":' in text else text[: text.rstrip().rindex("}")].rstrip()
    lines = [head + ",", '  "sets": {']
    lines.append(",\n".join(f"    {json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}" for k, v in sets.items()))
    lines.append("  },")
    lines.append('  "generated": [')
    lines.append(",\n".join("    " + json.dumps(f, ensure_ascii=False) for f in data["generated"]))
    lines.append("  ]")
    lines.append("}")
    with open(FACTS_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"{len(data['generated'])} generated facts ({len(dropped)} left out as already covered), "
          f"{len(data['facts'])} hand-written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
