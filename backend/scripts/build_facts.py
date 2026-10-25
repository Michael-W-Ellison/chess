"""
Build the "generated" facts in knowledge/facts.json from the tables below. Most are science:
animals (class, legs, flying, diet, blood, backbone, eggs, feathers, fur, scales, gills, lungs,
babies), space, matter, magnets and electricity, light and sound, plants, the human body, the
Earth and dinosaurs. The rest are geography (capitals, continents), measurements, and the
numbers 0 to 20. The hand-written "facts" in the file are kept as they
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
    "annelid": (["annelids", "an annelid", "annelid"], "Annelids are worms with bodies made of rings."),
    "cnidarian": (["cnidarians", "a cnidarian", "cnidarian"], "Cnidarians have soft bodies and no bones."),
    "echinoderm": (["echinoderms", "an echinoderm", "echinoderm"], "Echinoderms live in the sea and have no bones."),
}
VERTEBRATES = {"mammal", "bird", "fish", "reptile", "amphibian"}
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
    # More mammals
    ("whale", "whales", "mammal", 0, False, None), ("dolphin", "dolphins", "mammal", 0, False, "carnivore"),
    ("bat", "bats", "mammal", None, None, None),
    ("aardvark", "aardvarks", "mammal", 4, False, None), ("alpaca", "alpacas", "mammal", 4, False, "herbivore"),
    ("antelope", "antelopes", "mammal", 4, False, "herbivore"), ("bobcat", "bobcats", "mammal", 4, False, "carnivore"),
    ("boar", "boars", "mammal", 4, False, "omnivore"), ("coyote", "coyotes", "mammal", 4, False, None),
    ("cougar", "cougars", "mammal", 4, False, "carnivore"), ("dingo", "dingoes", "mammal", 4, False, None),
    ("echidna", "echidnas", "mammal", 4, False, None), ("elk", "elk", "mammal", 4, False, "herbivore"),
    ("gazelle", "gazelles", "mammal", 4, False, "herbivore"), ("gerbil", "gerbils", "mammal", 4, False, None),
    ("gibbon", "gibbons", "mammal", None, False, None), ("wildebeest", "wildebeest", "mammal", 4, False, "herbivore"),
    ("hare", "hares", "mammal", 4, False, "herbivore"), ("ibex", "ibex", "mammal", 4, False, "herbivore"),
    ("impala", "impalas", "mammal", 4, False, "herbivore"), ("jackal", "jackals", "mammal", 4, False, None),
    ("lynx", "lynxes", "mammal", 4, False, "carnivore"), ("mink", "minks", "mammal", 4, False, "carnivore"),
    ("mongoose", "mongooses", "mammal", 4, False, None), ("narwhal", "narwhals", "mammal", 0, False, "carnivore"),
    ("okapi", "okapis", "mammal", 4, False, "herbivore"), ("ocelot", "ocelots", "mammal", 4, False, "carnivore"),
    ("orca", "orcas", "mammal", 0, False, "carnivore"), ("pangolin", "pangolins", "mammal", 4, False, None),
    ("puma", "pumas", "mammal", 4, False, "carnivore"), ("red panda", "red pandas", "mammal", 4, False, None),
    ("shrew", "shrews", "mammal", 4, False, None), ("tapir", "tapirs", "mammal", 4, False, "herbivore"),
    ("vole", "voles", "mammal", 4, False, None), ("warthog", "warthogs", "mammal", 4, False, None),
    ("weasel", "weasels", "mammal", 4, False, "carnivore"), ("wombat", "wombats", "mammal", 4, False, "herbivore"),
    ("yak", "yaks", "mammal", 4, False, "herbivore"), ("gopher", "gophers", "mammal", 4, False, None),
    # More birds
    ("blackbird", "blackbirds", "bird", 2, True, None), ("bluebird", "bluebirds", "bird", 2, True, None),
    ("budgie", "budgies", "bird", 2, True, None), ("condor", "condors", "bird", 2, True, None),
    ("cuckoo", "cuckoos", "bird", 2, True, None), ("dove", "doves", "bird", 2, True, None),
    ("finch", "finches", "bird", 2, True, None), ("goldfinch", "goldfinches", "bird", 2, True, None),
    ("lark", "larks", "bird", 2, True, None), ("mockingbird", "mockingbirds", "bird", 2, True, None),
    ("nightingale", "nightingales", "bird", 2, True, None), ("oriole", "orioles", "bird", 2, True, None),
    ("partridge", "partridges", "bird", 2, None, None), ("pheasant", "pheasants", "bird", 2, None, None),
    ("quail", "quail", "bird", 2, None, None), ("roadrunner", "roadrunners", "bird", 2, None, None),
    ("sandpiper", "sandpipers", "bird", 2, True, None), ("starling", "starlings", "bird", 2, True, None),
    ("swift", "swifts", "bird", 2, True, None), ("tern", "terns", "bird", 2, True, None),
    ("thrush", "thrushes", "bird", 2, True, None), ("wren", "wrens", "bird", 2, True, None),
    ("egret", "egrets", "bird", 2, True, None), ("ibis", "ibises", "bird", 2, True, None),
    ("kookaburra", "kookaburras", "bird", 2, True, None), ("lovebird", "lovebirds", "bird", 2, True, None),
    ("hornbill", "hornbills", "bird", 2, True, None), ("osprey", "ospreys", "bird", 2, True, "carnivore"),
    ("kestrel", "kestrels", "bird", 2, True, "carnivore"), ("buzzard", "buzzards", "bird", 2, True, None),
    ("bald eagle", "bald eagles", "bird", 2, True, "carnivore"), ("barn owl", "barn owls", "bird", 2, True, "carnivore"),
    # More fish
    ("anchovy", "anchovies", "fish", 0, None, None), ("bass", "bass", "fish", 0, None, None),
    ("barracuda", "barracudas", "fish", 0, None, "carnivore"), ("flounder", "flounder", "fish", 0, None, None),
    ("halibut", "halibut", "fish", 0, None, None), ("herring", "herring", "fish", 0, None, None),
    ("mackerel", "mackerel", "fish", 0, None, None), ("minnow", "minnows", "fish", 0, None, None),
    ("perch", "perch", "fish", 0, None, None), ("pike", "pike", "fish", 0, None, "carnivore"),
    ("sardine", "sardines", "fish", 0, None, None), ("snapper", "snapper", "fish", 0, None, None),
    ("sunfish", "sunfish", "fish", 0, None, None), ("tilapia", "tilapia", "fish", 0, None, None),
    ("grouper", "groupers", "fish", 0, None, None), ("koi", "koi", "fish", 0, None, None),
    ("lionfish", "lionfish", "fish", 0, None, "carnivore"), ("marlin", "marlin", "fish", 0, None, "carnivore"),
    ("blowfish", "blowfish", "fish", 0, None, None),
    # More reptiles and amphibians
    ("anaconda", "anacondas", "reptile", 0, False, "carnivore"), ("boa", "boas", "reptile", 0, False, "carnivore"),
    ("garter snake", "garter snakes", "reptile", 0, False, "carnivore"),
    ("viper", "vipers", "reptile", 0, False, "carnivore"), ("sea snake", "sea snakes", "reptile", 0, False, "carnivore"),
    ("monitor lizard", "monitor lizards", "reptile", 4, False, None), ("skink", "skinks", "reptile", 4, False, None),
    ("bearded dragon", "bearded dragons", "reptile", 4, False, None),
    ("gila monster", "gila monsters", "reptile", 4, False, "carnivore"),
    ("box turtle", "box turtles", "reptile", 4, False, None),
    ("snapping turtle", "snapping turtles", "reptile", 4, False, None),
    ("sea turtle", "sea turtles", "reptile", None, False, None),
    ("tree frog", "tree frogs", "amphibian", 4, None, None), ("bullfrog", "bullfrogs", "amphibian", 4, False, None),
    ("poison dart frog", "poison dart frogs", "amphibian", 4, False, None),
    ("caecilian", "caecilians", "amphibian", 0, False, None),
    # More invertebrates
    ("aphid", "aphids", "insect", 6, None, None), ("bumblebee", "bumblebees", "insect", 6, True, None),
    ("cicada", "cicadas", "insect", 6, True, None), ("earwig", "earwigs", "insect", 6, None, None),
    ("gnat", "gnats", "insect", 6, True, None), ("katydid", "katydids", "insect", 6, None, None),
    ("locust", "locusts", "insect", 6, True, None), ("louse", "lice", "insect", 6, False, None),
    ("mayfly", "mayflies", "insect", 6, True, None), ("weevil", "weevils", "insect", 6, None, None),
    ("honeybee", "honeybees", "insect", 6, True, None), ("monarch butterfly", "monarch butterflies", "insect", 6, True, None),
    ("horsefly", "horseflies", "insect", 6, True, None), ("housefly", "houseflies", "insect", 6, True, None),
    ("black widow", "black widows", "arachnid", 8, False, None), ("wolf spider", "wolf spiders", "arachnid", 8, False, None),
    ("jumping spider", "jumping spiders", "arachnid", 8, False, None),
    ("oyster", "oysters", "mollusk", None, False, None), ("mussel", "mussels", "mollusk", None, False, None),
    ("scallop", "scallops", "mollusk", None, False, None), ("cuttlefish", "cuttlefish", "mollusk", None, False, None),
    ("nautilus", "nautiluses", "mollusk", None, False, None),
    ("barnacle", "barnacles", "crustacean", None, False, None), ("crayfish", "crayfish", "crustacean", None, False, None),
    ("krill", "krill", "crustacean", None, False, None), ("hermit crab", "hermit crabs", "crustacean", None, False, None),
    ("prawn", "prawns", "crustacean", None, False, None),
    ("earthworm", "earthworms", "annelid", 0, False, None), ("leech", "leeches", "annelid", 0, False, None),
    ("jellyfish", "jellyfish", "cnidarian", 0, False, None), ("sea anemone", "sea anemones", "cnidarian", 0, False, None),
    ("starfish", "starfish", "echinoderm", None, False, None), ("sea star", "sea stars", "echinoderm", None, False, None),
    ("sea urchin", "sea urchins", "echinoderm", None, False, None),
    ("sand dollar", "sand dollars", "echinoderm", None, False, None),
]

# Exceptions to what a class usually has (see biology())
WARM_BLOOD_UNSURE = {"tuna", "swordfish", "marlin", "shark", "sea turtle"}  # some keep parts of their body warm
LIVE_BIRTH = {"guppy", "stingray", "scorpion", "rattlesnake", "anaconda", "boa", "garter snake"}
LAY_EGGS_MAMMALS = {"platypus", "echidna"}
EGGS_UNSURE = {"viper", "sea snake", "skink", "chameleon", "lizard", "snake", "salamander", "caecilian", "shark",
               "seahorse", "aphid", "sea anemone", "starfish", "sea star", "sea urchin", "sand dollar", "jellyfish"}
NO_FUR_MAMMALS = {"whale", "dolphin", "orca", "narwhal", "manatee", "walrus", "armadillo", "pangolin", "elephant",
                  "rhino", "rhinoceros", "hippo", "hippopotamus", "pig", "boar", "warthog", "seal", "sea lion"}
# No scales, scales on only part of the body (a rat's tail), or plates instead
SCALES_UNSURE = {"catfish", "eel", "shark", "stingray", "armadillo", "swordfish", "seahorse", "sunfish", "pufferfish",
                 "blowfish", "koi", "caecilian", "rat", "mouse", "beaver", "opossum"}
GILLS_UNSURE = {"barnacle", "mayfly", "dragonfly"}  # no gills, or gills only when young
LUNGS_UNSURE = {"barnacle", "hermit crab"}
GILLS_MOLLUSKS = {"octopus", "squid", "clam", "oyster", "mussel", "scallop", "cuttlefish", "nautilus"}
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


def can_fact(fact_id: str, names: str, shown: str, verb: str, verb_text: str, value: bool, yes: str, no: str) -> dict:
    """A "can"-type fact for "<animals> <verb>" ("birds lay eggs"), with its examples"""
    return {"id": fact_id, "type": "can", "subject": names, "verb": verb, "value": value, "correct": yes if value else no,
            "examples": [[f"{shown} {'dont ' if value else ''}{verb_text}", "wrong"],
                         [f"{shown} {'' if value else 'dont '}{verb_text}", "right"]]}


def biology(sets: dict) -> list:
    """Warm or cold blood, backbone, eggs, feathers, fur, scales, gills and lungs of each animal"""
    facts = []
    warm, cold = ["warm blooded", "warmblooded"], ["cold blooded", "coldblooded"]
    sets["blood"] = warm + cold
    vertebrate = ["vertebrates", "a vertebrate", "vertebrate"]
    invertebrate = ["invertebrates", "an invertebrate", "invertebrate"]
    sets["backbone"] = vertebrate + invertebrate
    for one, many, cls, *_ in ANIMALS:
        names = subject(one, many)
        shown = many[:1].upper() + many[1:]
        key = slug(one)
        backboned = cls in VERTEBRATES
        if backboned and one not in WARM_BLOOD_UNSURE:
            is_warm = cls in ("mammal", "bird")
            facts.append({
                "id": f"blood_{key}", "type": "is", "subject": names, "true": warm if is_warm else cold,
                "false_from": ["blood"],
                "correct": f"{shown} are warm-blooded: their bodies make their own heat!" if is_warm
                else f"{shown} are cold-blooded: their bodies stay about as warm as the air or water around them!",
                "examples": [[f"{many} are {(cold if is_warm else warm)[0]}", "wrong"],
                             [f"{many} are {(warm if is_warm else cold)[0]}", "right"]]})
        facts.append({
            "id": f"backbone_{key}", "type": "is", "subject": names, "true": vertebrate if backboned else invertebrate,
            "false_from": ["backbone"],
            "correct": f"{shown} are vertebrates: they have a backbone!" if backboned
            else f"{shown} are invertebrates: they don't have a backbone!",
            "examples": [[f"{many} are {(invertebrate if backboned else vertebrate)[0]}", "wrong"],
                         [f"{many} are {(vertebrate if backboned else invertebrate)[0]}", "right"]]})
        facts.append(can_fact(f"spine_{key}", names, many, r"(?:have|has) (?:a )?(?:backbones?|spines?)",
                              "have a backbone", backboned, f"{shown} have a backbone!",
                              f"{shown} don't have a backbone. They're invertebrates!"))
        if one not in EGGS_UNSURE:
            lays = (one in LAY_EGGS_MAMMALS) if cls == "mammal" else one not in LIVE_BIRTH
            extra = " They're one of the only mammals that do!" if one in LAY_EGGS_MAMMALS else ""
            facts.append(can_fact(f"eggs_{key}", names, many, r"(?:lay|lays) eggs", "lay eggs", lays,
                                  f"{shown} lay eggs!{extra}",
                                  f"{shown} don't lay eggs. Their babies are born alive!"))
        if backboned or cls in ("mollusk", "crustacean", "annelid", "cnidarian", "echinoderm", "arachnid", "insect"):
            facts.append(can_fact(f"feathers_{key}", names, many, r"(?:have|has) feathers", "have feathers",
                                  cls == "bird", f"{shown} have feathers!",
                                  f"{shown} don't have feathers. Only birds have feathers!"))
        if backboned and not (cls == "mammal" and one in NO_FUR_MAMMALS):
            facts.append(can_fact(f"fur_{key}", names, many, r"(?:have|has) (?:fur|hair)", "have fur", cls == "mammal",
                                  f"{shown} have fur!", f"{shown} don't have fur. Fur is something mammals have!"))
        if (cls in ("reptile", "fish", "amphibian") or cls == "mammal" and one not in ("armadillo",)) \
                and one not in SCALES_UNSURE:
            has_scales = cls in ("reptile", "fish") or one == "pangolin"
            facts.append(can_fact(f"scales_{key}", names, many, r"(?:have|has) scales", "have scales", has_scales,
                                  f"{shown} have scales!" if one != "pangolin"
                                  else "Pangolins have scales! They're the only mammals covered in them.",
                                  f"{shown} don't have scales!"))
        gills_verb = r"(?:breathe (?:with|through|using) gills|(?:have|has) gills)"
        lungs_verb = r"(?:breathe (?:with|through|using) lungs|(?:have|has) lungs)"
        air = cls in ("mammal", "bird", "reptile")
        if (air or cls in ("fish", "insect", "arachnid", "crustacean") or one in GILLS_MOLLUSKS) \
                and one not in GILLS_UNSURE:
            has_gills = cls in ("fish", "crustacean") or one in GILLS_MOLLUSKS
            how = " They breathe air with lungs!" if air else (
                " They breathe through tiny holes in their bodies!" if cls == "insect" else " They breathe air!")
            facts.append(can_fact(f"gills_{key}", names, many, gills_verb, "have gills", has_gills,
                                  f"{shown} breathe with gills!", f"{shown} don't have gills.{how}"))
        if (air or cls in ("fish", "insect", "crustacean")) and one not in LUNGS_UNSURE:
            how = " They breathe with gills!" if cls in ("fish", "crustacean") else \
                " They breathe through tiny holes in their bodies!"
            facts.append(can_fact(f"lungs_{key}", names, many, lungs_verb, "have lungs", air,
                                  f"{shown} breathe air with lungs!", f"{shown} don't have lungs.{how}"))
    return facts


# ----------------------------------------------------------------------------------------------
# Other sciences: space, matter, forces, light and sound, plants, the body, Earth, dinosaurs
# ----------------------------------------------------------------------------------------------

def _is(fact_id, names, true, false, correct, articles="(?:the )?"):
    """An "is" fact; the first name, true and false values make its examples"""
    return {"id": fact_id, "type": "is", "subject": subject(*names, articles=articles), "true": true, "false": false,
            "correct": correct,
            "examples": [[f"{names[0]} is {false[0]}", "wrong"], [f"{names[0]} is {true[0]}", "right"]]}


def _does(fact_id, names, verb, verb_text, value, correct, articles="(?:the )?", plural=False, past=None):
    """
    A "can" fact for "<subject> <verb>" ("the earth goes around the sun"); past is (the past
    form, the base form after "didn't") for one about the past ("ate meat", "eat meat")
    """
    if past:
        said, denied = past
        return {"id": fact_id, "type": "can", "subject": subject(*names, articles=articles), "verb": verb,
                "value": value, "correct": correct,
                "examples": [[f"{names[0]} {f'didnt {denied}' if value else said}", "wrong"],
                             [f"{names[0]} {said if value else f'didnt {denied}'}", "right"]]}
    return {"id": fact_id, "type": "can", "subject": subject(*names, articles=articles), "verb": verb, "value": value,
            "correct": correct,
            "examples": [[f"{names[0]} {'dont' if plural else 'doesnt'} {verb_text}" if value
                          else f"{names[0]} {verb_text_s(verb_text, plural)}", "wrong"],
                         [f"{names[0]} {verb_text_s(verb_text, plural)}" if value
                          else f"{names[0]} {'dont' if plural else 'doesnt'} {verb_text}", "right"]]}


def verb_text_s(text: str, plural: bool) -> str:
    """ "go around the sun" -> "goes around the sun" for one subject"""
    if plural:
        return text
    first, _, rest = text.partition(" ")
    first = {"go": "goes", "do": "does", "have": "has"}.get(first) or (
        first + "es" if first.endswith(("s", "sh", "ch", "x")) else first + "s")
    return f"{first} {rest}".strip()


ORBIT = r"(?:go|goes|orbit|orbits|move|moves|travel|travels|spin|spins|circle|circles) around"
GAS_GIANT = ["a gas giant", "gas giant", "a giant planet"]
ICE_GIANT = ["an ice giant", "ice giant", "a gas giant", "gas giant", "a giant planet"]
ROCKY = ["a rocky planet", "rocky", "rocky planet", "a terrestrial planet"]
SOLID, LIQUID, GAS = ["a solid", "solid"], ["a liquid", "liquid"], ["a gas", "gas"]
MATTER = [("ice", SOLID), ("water", LIQUID), ("steam", GAS), ("water vapor", GAS), ("air", GAS), ("oxygen", GAS),
          ("helium", GAS), ("hydrogen", GAS), ("nitrogen", GAS), ("carbon dioxide", GAS), ("milk", LIQUID),
          ("juice", LIQUID), ("oil", LIQUID), ("honey", LIQUID), ("lava", LIQUID), ("rock", SOLID), ("a rock", SOLID),
          ("iron", SOLID), ("wood", SOLID), ("glass", SOLID), ("gold", SOLID), ("a brick", SOLID), ("sand", SOLID),
          ("salt", SOLID), ("sugar", SOLID), ("a pencil", SOLID), ("a crayon", SOLID), ("a coin", SOLID),
          ("orange juice", LIQUID), ("vinegar", LIQUID), ("soda", LIQUID), ("shampoo", LIQUID)]
MAGNETIC = {"iron": True, "steel": True, "nickel": True, "cobalt": True, "paper clips": True, "nails": True,
            "wood": False, "plastic": False, "paper": False, "glass": False, "rubber": False, "aluminum": False,
            "aluminium": False, "copper": False, "gold": False, "silver": False, "water": False, "cloth": False}
CONDUCTS = {"metal": True, "copper": True, "iron": True, "steel": True, "aluminum": True, "gold": True, "silver": True,
            "rubber": False, "plastic": False, "wood": False, "glass": False, "paper": False, "cloth": False}
DINOSAURS = [("t rex", ["tyrannosaurus rex", "tyrannosaurus", "a t rex", "the t rex"], "carnivore"),
             ("stegosaurus", ["a stegosaurus", "the stegosaurus"], "herbivore"),
             ("triceratops", ["a triceratops", "the triceratops"], "herbivore"),
             ("brachiosaurus", ["a brachiosaurus", "the brachiosaurus"], "herbivore"),
             ("velociraptor", ["a velociraptor", "the velociraptor", "velociraptors", "raptors"], "carnivore"),
             ("ankylosaurus", ["an ankylosaurus", "the ankylosaurus"], "herbivore"),
             ("diplodocus", ["a diplodocus", "the diplodocus"], "herbivore"),
             ("spinosaurus", ["a spinosaurus", "the spinosaurus"], "carnivore"),
             ("allosaurus", ["an allosaurus", "the allosaurus"], "carnivore"),
             ("parasaurolophus", ["a parasaurolophus", "the parasaurolophus"], "herbivore"),
             ("apatosaurus", ["an apatosaurus", "the apatosaurus", "brontosaurus", "a brontosaurus"], "herbivore"),
             ("iguanodon", ["an iguanodon", "the iguanodon"], "herbivore")]
EXTINCT_PLURAL = {"dinosaurs", "the dinosaurs", "dodos", "woolly mammoths", "mammoths", "saber tooth tigers",
                  "sabertooth tigers"}
EXTINCT = ["dinosaurs", "the dinosaurs", "dodos", "the dodo", "woolly mammoths", "mammoths", "the woolly mammoth",
           "saber tooth tigers", "sabertooth tigers", "the saber tooth tiger"] + [d for d, *_ in DINOSAURS]


def science(sets: dict) -> list:
    facts = []
    for name in PLANETS:
        names = [name] + (["the earth"] if name == "earth" else [])
        kind = GAS_GIANT if name in ("jupiter", "saturn") else ICE_GIANT if name in ("uranus", "neptune") else ROCKY
        other = ROCKY if kind is not ROCKY else GAS_GIANT
        shown = name.capitalize()
        facts.append({"id": f"planet_kind_{name}", "type": "is", "subject": alt(*names), "true": kind,
                      "false": [v for v in other if v not in kind],
                      "correct": f"{shown} is a rocky planet, like Earth!" if kind is ROCKY else
                      f"{shown} is a giant planet made mostly of gas!" if kind is GAS_GIANT else
                      f"{shown} is an ice giant, a giant planet made of gas and ice!",
                      "examples": [[f"{name} is {[v for v in other if v not in kind][0]}", "wrong"],
                                   [f"{name} is {kind[0]}", "right"]]})
        facts.append(_does(f"orbit_{name}", names, rf"{ORBIT} the sun", "go around the sun", True,
                           f"{shown} goes around the sun, like all the planets!", articles=""))
        if name in ("jupiter", "saturn", "uranus", "neptune"):
            facts.append(_does(f"rings_{name}", names, r"(?:have|has) rings", "have rings", True,
                               f"{shown} has rings! Saturn's are the easiest to see, but all four giant planets have them.",
                               articles=""))
    facts += [
        _does("orbit_sun_earth", ["the sun", "sun"], rf"{ORBIT} the earth", "go around the earth", False,
              "The sun doesn't go around the Earth. The Earth goes around the sun, once a year!", articles=""),
        _does("orbit_moon", ["the moon", "moon"], rf"{ORBIT} (?:the )?earth", "go around the earth", True,
              "The moon goes around the Earth, about once a month!", articles=""),
        _does("orbit_earth_moon", ["the earth", "earth"], rf"{ORBIT} the moon", "go around the moon", False,
              "The Earth doesn't go around the moon. The moon goes around the Earth!", articles=""),
        _does("earth_spins", ["the earth", "earth"], r"(?:spin|spins|turn|turns|rotate|rotates)", "spin", True,
              "The Earth spins around once every day. That's why we have day and night!", articles=""),
        _does("light_sun", ["the sun", "sun"], r"(?:make|makes) (?:its own )?light|(?:glow|glows|shine|shines) by itself",
              "make its own light", True, "The sun makes its own light. It's a star!", articles=""),
        _does("light_stars", ["stars", "a star"], r"(?:make|makes) (?:their|its) own light", "make their own light",
              True, "Stars make their own light!", articles="", plural=True),
        _does("light_moon", ["the moon", "moon"], r"(?:make|makes) (?:its own )?light|(?:glow|glows|shine|shines) by itself",
              "make its own light", False,
              "The moon doesn't make its own light. It shines because sunlight bounces off it!", articles=""),
        _does("sunrise_east", ["the sun", "sun"], r"(?:rise|rises|comes up|come up) in the east", "rise in the east",
              True, "The sun rises in the east and sets in the west!", articles=""),
        _does("sunrise_west", ["the sun", "sun"], r"(?:rise|rises|comes up|come up) in the west", "rise in the west",
              False, "The sun rises in the east, not the west!", articles=""),
        _does("sunset_west", ["the sun", "sun"], r"(?:set|sets|goes down|go down) in the west", "set in the west",
              True, "The sun sets in the west!", articles=""),
        _does("sunset_east", ["the sun", "sun"], r"(?:set|sets|goes down|go down) in the east", "set in the east",
              False, "The sun sets in the west, not the east!", articles=""),
        _does("breathe_space", ["people", "humans", "astronauts"], r"breathe in (?:outer )?space", "breathe in space",
              False, "People can't breathe in space, because there's no air. Astronauts wear space suits with air inside!",
              articles="", plural=True),
        _does("sound_space", ["sound"], r"(?:travel|travels|go|goes|move|moves) (?:in|through) (?:outer )?space",
              "travel in space", False, "Sound can't travel in space, because there's no air to carry it!",
              articles=""),
        _does("light_space", ["light"], r"(?:travel|travels|go|goes|move|moves) (?:in|through) (?:outer )?space",
              "travel through space", True, "Light can travel through space. That's how sunlight gets to us!",
              articles=""),
        _does("light_faster", ["light"], r"(?:is|travel|travels|go|goes|move|moves) faster than sound", "travel faster than sound",
              True, "Light is much faster than sound. That's why you see lightning before you hear thunder!",
              articles=""),
        _does("sound_faster", ["sound"], r"(?:is|travel|travels|go|goes|move|moves) faster than light", "travel faster than light",
              False, "Sound is much slower than light. That's why you see lightning before you hear thunder!",
              articles=""),
        _is("moon_rock", ["the moon"], ["a moon", "rock", "made of rock", "rocky"], ["a planet", "a star"],
            "The moon is a big ball of rock that goes around Earth!"),
        _is("sun_gas", ["the sun"], ["a star", "a ball of gas", "made of gas", "hot gas"], ["a planet", "made of fire"],
            "The sun is a star, a giant ball of hot gas!"),
    ]
    for thing, state in MATTER:
        others = [v for v in SOLID + LIQUID + GAS if v not in state]
        facts.append({"id": f"matter_{slug(thing)}", "type": "is", "subject": subject(thing, articles=""),
                      "true": state, "false": others,
                      "correct": f"{thing[:1].upper() + thing[1:]} is {state[0]}!",
                      "examples": [[f"{thing} is {others[0]}", "wrong"], [f"{thing} is {state[0]}", "right"]]})
    for material, value in MAGNETIC.items():
        facts.append(_does(f"magnet_{slug(material)}", ["magnets", "a magnet"],
                           rf"(?:attract|attracts|pick up|picks up|stick to|sticks to|pull|pulls) {re.escape(material)}",
                           f"attract {material}", value,
                           f"Magnets attract {material}!" if value else
                           f"Magnets don't attract {material}. They attract metals like iron and steel!",
                           articles="", plural=True))
    for material, value in CONDUCTS.items():
        facts.append(_does(f"conducts_{slug(material)}", [material], r"(?:conduct|conducts|carry|carries) electricity",
                           "conduct electricity", value,
                           f"{material.capitalize()} conducts electricity!" if value else
                           f"{material.capitalize()} doesn't conduct electricity. That's why it's used to keep "
                           f"people safe from it!", articles=""))
    facts += [
        _does("plants_sunlight", ["plants", "trees", "flowers"], r"(?:need|needs) (?:sunlight|light|the sun|sun)",
              "need sunlight", True, "Plants need sunlight to make their food!", articles="", plural=True),
        _does("plants_water", ["plants", "trees", "flowers"], r"(?:need|needs) water", "need water", True,
              "Plants need water to grow!", articles="", plural=True),
        _does("plants_food", ["plants", "trees"], r"(?:make|makes) (?:their|its) own food", "make their own food",
              True, "Plants make their own food from sunlight, water and air!", articles="", plural=True),
        _does("plants_oxygen", ["plants", "trees"], r"(?:make|makes|give off|gives off|release|releases) oxygen",
              "make oxygen", True, "Plants make oxygen, the air we need to breathe!", articles="", plural=True),
        _does("roots_water", ["roots"], r"(?:take|takes|soak|soaks|suck|sucks) up water", "take up water", True,
              "Roots take up water from the soil!", articles="", plural=True),
        _is("mushroom_fungus", ["mushrooms", "a mushroom"], ["fungi", "a fungus", "fungus", "funguses"],
            ["plants", "a plant", "vegetables", "a vegetable", "animals"],
            "Mushrooms aren't plants. They're fungi, and they can't make their own food from sunlight!",
            articles="(?:all )?"),
        _is("tree_plant", ["trees", "a tree"], ["plants", "a plant"], ["animals", "an animal"], "Trees are plants!",
            articles="(?:all )?"),
        _is("grass_plant", ["grass"], ["a plant", "plants"], ["an animal"], "Grass is a plant!", articles=""),
        _is("cactus_plant", ["cactuses", "cacti", "a cactus"], ["plants", "a plant"], ["animals", "an animal"],
            "Cactuses are plants that store water inside them!", articles=""),
        _is("coral_animal", ["coral", "corals"], ["animals", "an animal", "a cnidarian"],
            ["a plant", "plants", "a rock", "rocks"],
            "Coral is made of tiny animals! They build hard skeletons that become reefs.", articles=""),
        _is("sponge_animal", ["sea sponges", "a sea sponge"], ["animals", "an animal"], ["plants", "a plant"],
            "Sea sponges are animals, even though they don't move around!", articles=""),
        _is("blood_red", ["blood"], ["red"], ["blue", "green"],
            "Blood is always red! Veins can look blue through your skin, but the blood inside is red.", articles=""),
        _is("heart_muscle", ["the heart", "a heart"], ["a muscle", "muscle"], ["a bone", "a brain"],
            "The heart is a muscle that pumps blood around the body!", articles=""),
        _is("skin_organ", ["skin", "the skin"], ["an organ", "the biggest organ"], ["a bone", "a muscle"],
            "Skin is an organ, the biggest one in the body!", articles=""),
        _is("teeth_bones", ["teeth"], ["not bones"], ["bones", "a bone"],
            "Teeth aren't bones! They're even harder than bones, and they're covered in enamel.", articles=""),
        _does("heart_pumps", ["the heart", "a heart"], r"(?:pump|pumps|push|pushes) blood", "pump blood", True,
              "The heart pumps blood all around the body!", articles=""),
        _does("brain_controls", ["the brain", "a brain"], r"(?:control|controls) (?:the|your) body", "control the body",
              True, "The brain controls the body. It's like the body's boss!", articles=""),
        _does("stomach_digests", ["the stomach", "a stomach"], r"(?:digest|digests|break down|breaks down) food",
              "digest food", True, "The stomach helps break down food so the body can use it!", articles=""),
        _does("lungs_breathe", ["the lungs", "lungs"], r"(?:help|helps) (?:you|us|people) breathe", "help us breathe",
              True, "The lungs help you breathe in air!", articles="", plural=True),
        _is("earth_core_hot", ["the earths core", "the core of the earth", "the center of the earth"],
            ["hot", "very hot", "super hot"], ["cold", "freezing"],
            "The center of the Earth is super hot, about as hot as the surface of the sun!", articles=""),
        _is("ocean_salty", ["the ocean", "oceans", "the sea", "sea water", "seawater", "ocean water"],
            ["salty", "salt water", "saltwater"], ["fresh water", "freshwater", "not salty"],
            "Ocean water is salty! Rivers and most lakes have fresh water.", articles=""),
        _is("sahara_desert", ["the sahara", "sahara", "the sahara desert"], ["a desert", "desert"],
            ["a jungle", "a forest", "an ocean", "a country"], "The Sahara is a huge desert in Africa!", articles=""),
        _is("antarctica_cold", ["antarctica"], ["cold", "very cold", "freezing", "the coldest continent"],
            ["hot", "warm", "the hottest continent"], "Antarctica is the coldest place on Earth!", articles=""),
        _is("north_pole_cold", ["the north pole"], ["cold", "very cold", "freezing"], ["hot", "warm"],
            "The North Pole is very cold, and covered in sea ice!", articles=""),
        _does("rain_clouds", ["rain"], r"(?:come|comes|falls?) (?:from|out of) (?:the )?clouds", "come from clouds", True,
              "Rain comes from clouds! Tiny drops of water join together until they're heavy enough to fall.",
              articles=""),
        _does("volcano_lava", ["volcanoes", "volcanos", "a volcano"], r"(?:erupt|erupts|shoot|shoots|spew|spews) lava",
              "erupt lava", True, "Volcanoes erupt hot melted rock called lava!", articles="", plural=True),
        _does("ice_floats", ["ice"], r"(?:float|floats)(?: on water| in water)?", "float", True,
              "Ice floats on water! It's lighter than the same amount of liquid water.", articles=""),
        _does("wood_floats", ["wood"], r"(?:float|floats)(?: on water| in water)?", "float", True,
              "Most wood floats on water!", articles=""),
        _does("oil_floats", ["oil"], r"(?:float|floats) on water", "float on water", True,
              "Oil floats on water, because it's lighter!", articles=""),
        _does("water_freezes", ["water"], r"(?:freeze|freezes|turn|turns) (?:into|to) ice(?: when its cold)?",
              "freeze into ice", True, "Water freezes into ice at 0 degrees Celsius, which is 32 degrees Fahrenheit!",
              articles=""),
        _does("ice_melts", ["ice"], r"(?:melt|melts|turn|turns) (?:into|to) water", "melt into water", True,
              "Ice melts into water when it gets warm!", articles=""),
        _does("water_steam", ["water"], r"(?:turn|turns) (?:into|to) steam when (?:it boils|you boil it)",
              "turn into steam when it boils", True, "Boiling water turns into steam!", articles=""),
        _does("gravity_down", ["gravity"], r"(?:pull|pulls) (?:things|stuff|us|everything) down",
              "pull things down", True, "Gravity pulls things down toward the Earth!", articles=""),
        _does("dinosaurs_people", ["dinosaurs"],
              r"(?:lived|live) (?:with|at the same time as|when there were) (?:people|humans)",
              "lived with people", False,
              "Dinosaurs died out about 66 million years before the first people lived!", articles="",
              past=("lived with people", "live with people")),
        _is("pterodactyl_reptile", ["pterodactyls", "a pterodactyl", "pterosaurs"],
            ["flying reptiles", "a flying reptile", "pterosaurs", "reptiles", "a reptile"],
            ["dinosaurs", "a dinosaur", "birds", "a bird"],
            "Pterodactyls weren't dinosaurs or birds. They were flying reptiles called pterosaurs!", articles=""),
    ]
    sets["extinct"] = ["extinct", "alive", "still alive", "living"]
    for name in EXTINCT:
        plural_name = name in EXTINCT_PLURAL
        facts.append({"id": f"extinct_{slug(name)}", "type": "is", "subject": subject(name, articles=""),
                      "true": ["extinct"], "false": ["alive", "still alive", "not extinct", "living"],
                      "correct": f"{'T. rex' if name == 't rex' else title(name)} {'are' if plural_name else 'is'} extinct. "
                                 f"{'They' if plural_name else 'It'} died out long ago!",
                      "examples": [[f"{name} {'are' if plural_name else 'is'} still alive", "wrong"],
                                   [f"{name} {'are' if plural_name else 'is'} extinct", "right"]]})
    for name, others, diet in DINOSAURS:
        forms, eats = DIETS[diet]
        facts.append({"id": f"dino_diet_{slug(name)}", "type": "is", "subject": subject(name, *others, articles=""),
                      "true": forms, "false_from": ["diets"],
                      "correct": f"{'T. rex' if name == 't rex' else name.capitalize()} was {forms[1]}. "
                                 f"{eats.replace('They eat', 'It ate')}",
                      "examples": [[f"{name} is {_other(sets['diets'], forms)}", "wrong"], [f"{name} is {forms[1]}", "right"]]})
        ate = "meat" if diet == "carnivore" else "plants"
        facts.append(_does(f"dino_ate_{slug(name)}", [name] + others, rf"(?:ate|eats|eat) {ate}", f"ate {ate}", True,
                           f"{'T. rex' if name == 't rex' else name.capitalize()} ate {ate}!", articles="",
                           past=(f"ate {ate}", f"eat {ate}")))
        wrong = "plants" if ate == "meat" else "meat"
        facts.append(_does(f"dino_not_ate_{slug(name)}", [name] + others, rf"(?:ate|eats|eat) {wrong}",
                           f"ate {wrong}", False,
                           f"{'T. rex' if name == 't rex' else name.capitalize()} ate {ate}, not {wrong}!",
                           articles="", past=(f"ate {wrong}", f"eat {wrong}")))
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

NUMBERS_UP_TO = 20  # the numbers children state facts about
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
    generated = (animals(sets) + biology(sets) + science(sets) + space(sets) + counts(sets) + places(sets)
                 + numbers(data))
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
