"""
Pun Quirk Service
Handles the tells_puns personality quirk
"""

import random
from typing import List, Optional


class PunQuirkService:
    """
    Service for applying the tells_puns quirk to bot responses

    This service adds appropriate puns to responses based on:
    - Context keywords in the conversation
    - Current mood for pun tone
    - Random selection from curated pun collection
    """

    # General puns for any conversation
    GENERAL_PUNS = [
        "Why don't scientists trust atoms? Because they make up everything!",
        "What do you call a bear with no teeth? A gummy bear!",
        "Why did the scarecrow win an award? Because he was outstanding in his field!",
        "What do you call a fake noodle? An impasta!",
        "Why can't you hear a pterodactyl using the bathroom? Because the 'P' is silent!",
        "What did one wall say to the other wall? I'll meet you at the corner!",
        "Why did the bicycle fall over? Because it was two-tired!",
        "What do you call a sleeping bull? A bulldozer!",
        "Why don't eggs tell jokes? They'd crack each other up!",
        "What do you call a belt made of watches? A waist of time!",
    ]

    # School-related puns
    SCHOOL_PUNS = [
        "Why did the student eat his homework? Because the teacher said it was a piece of cake!",
        "What did the pencil say to the paper? Write on!",
        "Why was the math book sad? It had too many problems!",
        "What's a math teacher's favorite place? Times Square!",
        "Why did the teacher wear sunglasses? Because her students were so bright!",
        "What do you call a knight who is afraid to fight? Sir Render!",
        "Why didn't the skeleton go to school? He had no body to go with!",
    ]

    # Friend and social puns
    FRIEND_PUNS = [
        "What did one plate say to another plate? Dinner is on me!",
        "Why did the cookie go to the doctor? It felt crumbly!",
        "What do you call a group of musical whales? An orca-stra!",
        "Why don't teddy bears ever order dessert? They're always stuffed!",
        "What did the traffic light say to the car? Don't look, I'm changing!",
    ]

    # Game and play puns
    GAME_PUNS = [
        "Why did the golfer bring two pairs of pants? In case he got a hole in one!",
        "What do you call a dinosaur that crashes his car? Tyrannosaurus Wrecks!",
        "Why don't basketball players go on vacation? They're afraid they might get called for traveling!",
        "What do you call a pig that does karate? A pork chop!",
        "Why did the soccer player bring string to the game? So he could tie the score!",
    ]

    # Food puns
    FOOD_PUNS = [
        "What do you call cheese that isn't yours? Nacho cheese!",
        "Why did the tomato turn red? Because it saw the salad dressing!",
        "What did the grape say when it got stepped on? Nothing, it just let out a little wine!",
        "Why don't eggs tell jokes? They'd crack each other up!",
        "What do you call a sad strawberry? A blue-berry!",
    ]

    # Animal puns
    ANIMAL_PUNS = [
        "What do you call a fish wearing a bow tie? Sofishticated!",
        "Why don't cats play poker in the jungle? Too many cheetahs!",
        "What do you call a sleeping dinosaur? A dino-snore!",
        "Why do fish live in salt water? Because pepper makes them sneeze!",
        "What do you call a dog magician? A labracadabrador!",
        "Why did the chicken go to the séance? To talk to the other side!",
    ]

    # Weather and nature puns
    NATURE_PUNS = [
        "What did the tree say to the wind? Leaf me alone!",
        "Why did the sun go to school? To get brighter!",
        "What's a tornado's favorite game? Twister!",
        "Why don't mountains get cold in winter? They wear snow caps!",
    ]

    # Technology puns
    TECH_PUNS = [
        "Why was the computer cold? It left its Windows open!",
        "What do you call a computer that sings? A-Dell!",
        "Why did the PowerPoint presentation cross the road? To get to the other slide!",
    ]

    # Keyword-to-pun-category mapping
    CONTEXT_KEYWORDS = {
        "school": SCHOOL_PUNS,
        "homework": SCHOOL_PUNS,
        "test": SCHOOL_PUNS,
        "math": SCHOOL_PUNS,
        "teacher": SCHOOL_PUNS,
        "learn": SCHOOL_PUNS,
        "study": SCHOOL_PUNS,
        "class": SCHOOL_PUNS,

        "friend": FRIEND_PUNS,
        "play": GAME_PUNS,
        "game": GAME_PUNS,
        "sport": GAME_PUNS,
        "soccer": GAME_PUNS,
        "basketball": GAME_PUNS,
        "fun": GAME_PUNS,

        "food": FOOD_PUNS,
        "eat": FOOD_PUNS,
        "lunch": FOOD_PUNS,
        "dinner": FOOD_PUNS,
        "hungry": FOOD_PUNS,
        "snack": FOOD_PUNS,

        "animal": ANIMAL_PUNS,
        "cat": ANIMAL_PUNS,
        "dog": ANIMAL_PUNS,
        "pet": ANIMAL_PUNS,
        "fish": ANIMAL_PUNS,
        "bird": ANIMAL_PUNS,

        "weather": NATURE_PUNS,
        "sun": NATURE_PUNS,
        "rain": NATURE_PUNS,
        "tree": NATURE_PUNS,
        "nature": NATURE_PUNS,

        "computer": TECH_PUNS,
        "tech": TECH_PUNS,
        "phone": TECH_PUNS,
    }

    def add_pun(self, response: str, context: str = "", probability: float = 0.3) -> str:
        """
        Add a pun to the response based on context

        Args:
            response: Original bot response
            context: User message or conversation context for contextual puns
            probability: Chance of adding a pun (0.0-1.0)

        Returns:
            Response with pun appended (if selected)
        """
        # Random chance to add pun
        if random.random() > probability:
            return response

        # Get contextual pun if possible
        pun = self._get_contextual_pun(context)

        # Fall back to general pun if no context match
        if not pun:
            pun = self._get_random_pun()

        # Add pun with appropriate punctuation
        response = response.rstrip()

        # Add spacing and pun
        if response:
            # Add pun as separate sentence or with transition
            if random.random() < 0.5:
                # Direct append
                return f"{response} {pun}"
            else:
                # With transition phrase
                transitions = [
                    f"{response} Oh, and here's a fun one: {pun}",
                    f"{response} Speaking of which... {pun}",
                    f"{response} That reminds me: {pun}",
                    f"{response} By the way, {pun}",
                ]
                return random.choice(transitions)
        else:
            return pun

    def _get_contextual_pun(self, context: str) -> Optional[str]:
        """Get a pun based on context keywords"""
        if not context:
            return None

        context_lower = context.lower()

        # Find matching keyword
        for keyword, pun_list in self.CONTEXT_KEYWORDS.items():
            if keyword in context_lower:
                return random.choice(pun_list)

        return None

    def _get_random_pun(self) -> str:
        """Get a random pun from all categories"""
        all_puns = (
            self.GENERAL_PUNS +
            self.SCHOOL_PUNS +
            self.FRIEND_PUNS +
            self.GAME_PUNS +
            self.FOOD_PUNS +
            self.ANIMAL_PUNS +
            self.NATURE_PUNS +
            self.TECH_PUNS
        )
        return random.choice(all_puns)

    def get_pun_by_category(self, category: str) -> str:
        """Get a random pun from a specific category"""
        category_map = {
            "general": self.GENERAL_PUNS,
            "school": self.SCHOOL_PUNS,
            "friend": self.FRIEND_PUNS,
            "game": self.GAME_PUNS,
            "food": self.FOOD_PUNS,
            "animal": self.ANIMAL_PUNS,
            "nature": self.NATURE_PUNS,
            "tech": self.TECH_PUNS,
        }

        puns = category_map.get(category, self.GENERAL_PUNS)
        return random.choice(puns)


# Global singleton instance
pun_quirk_service = PunQuirkService()
