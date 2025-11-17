"""
Fact Quirk Service
Handles the shares_facts personality quirk
"""

import random
from typing import List, Optional


class FactQuirkService:
    """
    Service for applying the shares_facts quirk to bot responses

    This service adds interesting, educational facts to responses based on:
    - Context keywords in the conversation
    - Current mood for fact tone
    - Random selection from curated fact collection
    """

    # Science facts
    SCIENCE_FACTS = [
        "Did you know? A bolt of lightning is five times hotter than the surface of the sun!",
        "Did you know? Sound travels about 4 times faster through water than air!",
        "Did you know? A single bolt of lightning contains enough energy to toast 100,000 slices of bread!",
        "Did you know? Water can boil and freeze at the same time in a phenomenon called the triple point!",
        "Did you know? Hot water freezes faster than cold water, which is called the Mpemba effect!",
        "Did you know? Bananas are naturally radioactive because they contain potassium-40!",
        "Did you know? A rubber ball bounces higher when it's warmer because heat increases energy!",
    ]

    # Animal facts
    ANIMAL_FACTS = [
        "Did you know? Octopuses have three hearts and blue blood!",
        "Did you know? A group of flamingos is called a 'flamboyance'!",
        "Did you know? Cats have over 100 vocal sounds, while dogs only have about 10!",
        "Did you know? A snail can sleep for three years straight!",
        "Did you know? Butterflies taste with their feet!",
        "Did you know? Dolphins have names for each other and can call each other specifically!",
        "Did you know? Hummingbirds are the only birds that can fly backwards!",
        "Did you know? A group of pugs is called a 'grumble'!",
        "Did you know? Elephants can recognize themselves in mirrors, showing self-awareness!",
        "Did you know? Sea otters hold hands while sleeping so they don't drift apart!",
    ]

    # Space facts
    SPACE_FACTS = [
        "Did you know? A day on Venus is longer than a year on Venus!",
        "Did you know? There are more stars in the universe than grains of sand on all Earth's beaches!",
        "Did you know? The footprints on the Moon will last millions of years because there's no wind!",
        "Did you know? Jupiter has the shortest day of all planets - just 10 hours!",
        "Did you know? The Sun is 400 times larger than the Moon but 400 times farther away!",
        "Did you know? A teaspoon of neutron star would weigh about 6 billion tons!",
        "Did you know? Mars appears red because its surface is covered in rusty iron!",
    ]

    # Nature facts
    NATURE_FACTS = [
        "Did you know? Bamboo is the fastest-growing plant - it can grow 3 feet in just 24 hours!",
        "Did you know? A single tree can absorb up to 48 pounds of CO2 per year!",
        "Did you know? Rainbows are actually full circles, but we usually only see half from the ground!",
        "Did you know? The oldest tree in the world is over 5,000 years old!",
        "Did you know? Mushrooms are more closely related to humans than they are to plants!",
        "Did you know? Some plants can 'hear' running water and grow their roots toward it!",
        "Did you know? A bolt of lightning can reach temperatures of 30,000°C (54,000°F)!",
    ]

    # History facts
    HISTORY_FACTS = [
        "Did you know? The ancient Egyptians used sleds to move the heavy stones that built the pyramids!",
        "Did you know? The first computer programmer was Ada Lovelace, a woman who lived in the 1800s!",
        "Did you know? Ancient Romans used crushed mouse brains as toothpaste!",
        "Did you know? The Great Wall of China is not visible from space with the naked eye!",
        "Did you know? Cleopatra lived closer to the invention of the iPhone than to the building of the pyramids!",
        "Did you know? Before alarm clocks, there were 'knocker-uppers' who tapped on windows to wake people!",
    ]

    # Technology facts
    TECH_FACTS = [
        "Did you know? The first computer mouse was made of wood!",
        "Did you know? The first 1GB hard drive weighed over 500 pounds!",
        "Did you know? More computing power went into sending a man to the moon than your smartphone has!",
        "Did you know? The first computer bug was an actual bug - a moth stuck in a computer!",
        "Did you know? WiFi doesn't actually stand for 'Wireless Fidelity' - it's just a made-up name!",
        "Did you know? The first email was sent in 1971 by Ray Tomlinson to himself!",
    ]

    # Human body facts
    BODY_FACTS = [
        "Did you know? Your brain uses 20% of your body's energy despite being only 2% of your weight!",
        "Did you know? You have about 100,000 hairs on your head!",
        "Did you know? Your heart beats about 100,000 times a day!",
        "Did you know? Humans are the only animals that blush!",
        "Did you know? Your nose can remember 50,000 different scents!",
        "Did you know? You can't tickle yourself because your brain predicts your own movements!",
        "Did you know? Your bones are about 5 times stronger than steel of the same weight!",
    ]

    # Geography facts
    GEOGRAPHY_FACTS = [
        "Did you know? The Earth's core is as hot as the surface of the Sun!",
        "Did you know? Mount Everest grows about 4 millimeters every year!",
        "Did you know? The Pacific Ocean is bigger than all the land on Earth combined!",
        "Did you know? Antarctica is the world's largest desert because it gets very little rain!",
        "Did you know? The Amazon rainforest produces 20% of the world's oxygen!",
        "Did you know? Russia is bigger than Pluto!",
    ]

    # General amazing facts
    GENERAL_FACTS = [
        "Did you know? A cloud can weigh more than a million pounds!",
        "Did you know? Honey never spoils - archaeologists found 3,000-year-old honey that's still edible!",
        "Did you know? The shortest war in history lasted only 38 minutes!",
        "Did you know? The world's quietest room is so quiet you can hear your heartbeat!",
        "Did you know? It would take 1,200,000 mosquitoes to drain all your blood!",
        "Did you know? The inventor of the Pringles can is now buried in one!",
    ]

    # Keyword-to-fact-category mapping
    CONTEXT_KEYWORDS = {
        "science": SCIENCE_FACTS,
        "experiment": SCIENCE_FACTS,
        "chemistry": SCIENCE_FACTS,
        "physics": SCIENCE_FACTS,
        "learn": SCIENCE_FACTS,

        "animal": ANIMAL_FACTS,
        "dog": ANIMAL_FACTS,
        "cat": ANIMAL_FACTS,
        "pet": ANIMAL_FACTS,
        "bird": ANIMAL_FACTS,
        "fish": ANIMAL_FACTS,
        "zoo": ANIMAL_FACTS,

        "space": SPACE_FACTS,
        "planet": SPACE_FACTS,
        "star": SPACE_FACTS,
        "moon": SPACE_FACTS,
        "sun": SPACE_FACTS,
        "astronaut": SPACE_FACTS,
        "universe": SPACE_FACTS,

        "nature": NATURE_FACTS,
        "tree": NATURE_FACTS,
        "plant": NATURE_FACTS,
        "forest": NATURE_FACTS,
        "rain": NATURE_FACTS,
        "weather": NATURE_FACTS,

        "history": HISTORY_FACTS,
        "ancient": HISTORY_FACTS,
        "historical": HISTORY_FACTS,

        "computer": TECH_FACTS,
        "tech": TECH_FACTS,
        "technology": TECH_FACTS,
        "phone": TECH_FACTS,
        "robot": TECH_FACTS,

        "body": BODY_FACTS,
        "brain": BODY_FACTS,
        "heart": BODY_FACTS,
        "human": BODY_FACTS,

        "earth": GEOGRAPHY_FACTS,
        "geography": GEOGRAPHY_FACTS,
        "ocean": GEOGRAPHY_FACTS,
        "mountain": GEOGRAPHY_FACTS,
        "country": GEOGRAPHY_FACTS,
    }

    def add_fact(self, response: str, context: str = "", probability: float = 0.3) -> str:
        """
        Add a fact to the response based on context

        Args:
            response: Original bot response
            context: User message or conversation context for contextual facts
            probability: Chance of adding a fact (0.0-1.0)

        Returns:
            Response with fact appended (if selected)
        """
        # Random chance to add fact
        if random.random() > probability:
            return response

        # Get contextual fact if possible
        fact = self._get_contextual_fact(context)

        # Fall back to general fact if no context match
        if not fact:
            fact = self._get_random_fact()

        # Add fact with appropriate punctuation
        response = response.rstrip()

        # Add fact as separate sentence or with transition
        if response:
            # Add fact with transition phrase
            if random.random() < 0.5:
                # Direct append
                return f"{response} {fact}"
            else:
                # With transition phrase
                transitions = [
                    f"{response} Here's something cool: {fact}",
                    f"{response} Fun fact: {fact}",
                    f"{response} By the way, {fact}",
                    f"{response} Also, {fact}",
                ]
                return random.choice(transitions)
        else:
            return fact

    def _get_contextual_fact(self, context: str) -> Optional[str]:
        """Get a fact based on context keywords"""
        if not context:
            return None

        context_lower = context.lower()

        # Find matching keyword
        for keyword, fact_list in self.CONTEXT_KEYWORDS.items():
            if keyword in context_lower:
                return random.choice(fact_list)

        return None

    def _get_random_fact(self) -> str:
        """Get a random fact from all categories"""
        all_facts = (
            self.GENERAL_FACTS +
            self.SCIENCE_FACTS +
            self.ANIMAL_FACTS +
            self.SPACE_FACTS +
            self.NATURE_FACTS +
            self.HISTORY_FACTS +
            self.TECH_FACTS +
            self.BODY_FACTS +
            self.GEOGRAPHY_FACTS
        )
        return random.choice(all_facts)

    def get_fact_by_category(self, category: str) -> str:
        """Get a random fact from a specific category"""
        category_map = {
            "general": self.GENERAL_FACTS,
            "science": self.SCIENCE_FACTS,
            "animal": self.ANIMAL_FACTS,
            "space": self.SPACE_FACTS,
            "nature": self.NATURE_FACTS,
            "history": self.HISTORY_FACTS,
            "tech": self.TECH_FACTS,
            "body": self.BODY_FACTS,
            "geography": self.GEOGRAPHY_FACTS,
        }

        facts = category_map.get(category, self.GENERAL_FACTS)
        return random.choice(facts)


# Global singleton instance
fact_quirk_service = FactQuirkService()
