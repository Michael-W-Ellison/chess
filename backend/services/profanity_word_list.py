"""
Profanity Word List Service
Comprehensive age-appropriate profanity filtering for kid-friendly chatbot

This list is designed for children ages 8-14 and focuses on:
- Common mild profanity
- Age-appropriate filtering
- Educational context (teaching appropriate language)
- Variations and common misspellings
"""

from typing import Dict, List, Set
import logging

logger = logging.getLogger("chatbot.profanity_word_list")


class ProfanityWordList:
    """
    Profanity Word List - Comprehensive age-appropriate word filtering

    Categories:
    - MILD: Minor profanity (damn, hell, crap)
    - MODERATE: More serious profanity
    - SEVERE: Strong profanity (filtered strictly)

    Note: This list is designed for educational contexts with children.
    It focuses on teaching appropriate language rather than adult censorship.
    """

    def __init__(self):
        # MILD profanity - minor words often used by kids
        self.mild_words = {
            # Common mild profanity
            "damn",
            "darn",
            "dang",
            "hell",
            "heck",
            "crap",
            "crud",

            # Name-calling (age-appropriate filter)
            "stupid",
            "dumb",
            "idiot",
            "moron",
            "dork",
            "loser",
            "dummy",
            "jerk",
            "creep",

            # Commands/insults
            "shut up",
            "shutup",
            "shut-up",
            "shut it",

            # Variations
            "dammit",
            "damn it",
            "what the hell",
            "wth",
            "wtf",
        }

        # MODERATE profanity - more serious words
        self.moderate_words = {
            # Common moderate profanity
            "ass",
            "butt",
            "butthole",
            "jackass",
            "badass",
            "smartass",
            "dumbass",
            "asshole",

            # Body parts (crude)
            "boob",
            "boobs",
            "tit",
            "tits",

            # Excretory
            "piss",
            "pissed",
            "pee",
            "poop",
            "crapola",

            # Religious
            "goddamn",
            "god damn",
            "jesus christ",
            "christ",
            "holy hell",

            # Insults
            "bastard",
            "bitch",
            "douche",
            "douchebag",
            "scumbag",

            # Slang
            "suck",
            "sucks",
            "sucked",
            "screwed",
        }

        # SEVERE profanity - strong words (strictly filtered)
        # Note: Keeping this minimal and age-focused
        self.severe_words = {
            # Strong profanity (f-word family)
            "fuck",
            "fucked",
            "fucking",
            "fucker",
            "fck",
            "f***",
            "f**k",

            # Strong profanity (s-word)
            "shit",
            "shitty",
            "bullshit",
            "bs",
            "sh*t",
            "s**t",

            # Body parts (explicit)
            "dick",
            "cock",
            "penis",
            "vagina",
            "pussy",
            "balls",

            # Strong insults
            "whore",
            "slut",
            "fag",
            "faggot",
            "retard",
            "retarded",

            # Racial slurs (important to filter)
            "n-word",
            "n***a",

            # Sexual content
            "sex",
            "sexy",
            "porn",
            "pornography",
        }

        # Common variations and leetspeak
        self.variations = {
            # Leetspeak and censored versions
            "d4mn",
            "h3ll",
            "cr4p",
            "@ss",
            "a$$",
            "b1tch",
            "b!tch",
            "fvck",
            "fuk",
            "sh1t",
            "sh!t",

            # Spacing tricks
            "d a m n",
            "h e l l",
            "s h i t",
            "f u c k",

            # Asterisk censoring (original form)
            "d*mn",
            "h*ll",
            "cr*p",
            "s**t",
            "f**k",
            "a**",
            "b***h",

            # Asterisk censoring (stripped form - what users actually type)
            "dmn",  # d*mn becomes dmn
            "hll",  # h*ll becomes hll
            "crp",  # cr*p becomes crp
            "fk",   # f**k becomes fk
            "st",   # s**t becomes st
            "btch", # b***h becomes btch

            # Common misspellings kids use
            "dam",
            "damm",
            "shiat",
            "shiit",
            "fuk",
            "fack",
        }

        # Combine all words into comprehensive set
        self.all_words = (
            self.mild_words
            | self.moderate_words
            | self.severe_words
            | self.variations
        )

        # Exceptions - words that look like profanity but aren't
        # (to prevent false positives)
        self.exceptions = {
            "class",  # contains "ass"
            "classic",
            "bassist",
            "assemble",
            "assassin",
            "compass",
            "grass",
            "glass",
            "bass",
            "pass",
            "mass",
            "hassle",
            "assist",
            "assignment",
            "assume",
            "massachusetts",
            "cassette",
            "passive",

            # Other false positives
            "Essex",
            "Sussex",
            "Wessex",
            "assess",
            "assessment",
        }

        logger.info(
            f"Profanity word list initialized: "
            f"{len(self.mild_words)} mild, "
            f"{len(self.moderate_words)} moderate, "
            f"{len(self.severe_words)} severe words"
        )

    def get_all_words(self) -> Set[str]:
        """
        Get all profanity words

        Returns:
            Set of all profanity words
        """
        return self.all_words.copy()

    def get_words_by_severity(self, severity: str) -> Set[str]:
        """
        Get words by severity level

        Args:
            severity: 'mild', 'moderate', or 'severe'

        Returns:
            Set of words for that severity level
        """
        if severity == "mild":
            return self.mild_words.copy()
        elif severity == "moderate":
            return self.moderate_words.copy()
        elif severity == "severe":
            return self.severe_words.copy()
        else:
            return set()

    def is_profanity(self, word: str) -> bool:
        """
        Check if a word is profanity

        Args:
            word: Word to check (will be lowercased)

        Returns:
            True if word is profanity
        """
        word_lower = word.lower().strip()

        # Check exceptions first
        if word_lower in self.exceptions:
            return False

        # Check if it's in any profanity list
        return word_lower in self.all_words

    def get_severity(self, word: str) -> str:
        """
        Get severity level of a profanity word

        Args:
            word: Word to check

        Returns:
            'mild', 'moderate', 'severe', or 'none' if not profanity
        """
        word_lower = word.lower().strip()

        if word_lower in self.exceptions:
            return "none"

        if word_lower in self.severe_words or word_lower in self.variations:
            return "severe"
        elif word_lower in self.moderate_words:
            return "moderate"
        elif word_lower in self.mild_words:
            return "mild"
        else:
            return "none"

    def contains_profanity(self, text: str) -> bool:
        """
        Check if text contains any profanity

        Args:
            text: Text to check

        Returns:
            True if text contains profanity
        """
        text_lower = text.lower()

        # Check for whole-word matches
        words = text_lower.split()
        for word in words:
            # Remove punctuation from word
            cleaned_word = "".join(c for c in word if c.isalnum() or c in ["-", "'"])

            if self.is_profanity(cleaned_word):
                return True

        # Check for multi-word phrases (like "shut up")
        for phrase in self.all_words:
            if " " in phrase and phrase in text_lower:
                return True

        return False

    def find_profanity_words(self, text: str) -> List[Dict[str, str]]:
        """
        Find all profanity words in text with severity

        Args:
            text: Text to analyze

        Returns:
            List of dicts with word and severity
        """
        found = []
        text_lower = text.lower()

        # Check whole words
        words = text_lower.split()
        for word in words:
            # Remove punctuation
            cleaned_word = "".join(c for c in word if c.isalnum() or c in ["-", "'"])

            if self.is_profanity(cleaned_word):
                severity = self.get_severity(cleaned_word)
                found.append({"word": cleaned_word, "severity": severity})

        # Check multi-word phrases
        for phrase in self.all_words:
            if " " in phrase and phrase in text_lower:
                severity = self.get_severity(phrase)
                found.append({"word": phrase, "severity": severity})

        return found

    def censor_text(self, text: str, replacement: str = "***") -> str:
        """
        Censor profanity in text

        Args:
            text: Text to censor
            replacement: Replacement string (default: ***)

        Returns:
            Censored text
        """
        result = text

        # Find all profanity
        profanity_found = self.find_profanity_words(text)

        # Replace each occurrence (case-insensitive)
        for item in profanity_found:
            word = item["word"]
            # Use case-insensitive replacement
            import re

            pattern = re.compile(re.escape(word), re.IGNORECASE)
            result = pattern.sub(replacement, result)

        return result

    def get_stats(self) -> Dict[str, int]:
        """
        Get statistics about the word list

        Returns:
            Dictionary with counts by category
        """
        return {
            "total": len(self.all_words),
            "mild": len(self.mild_words),
            "moderate": len(self.moderate_words),
            "severe": len(self.severe_words),
            "variations": len(self.variations),
            "exceptions": len(self.exceptions),
        }


# Global instance
profanity_word_list = ProfanityWordList()


# Convenience functions
def is_profanity(word: str) -> bool:
    """Check if word is profanity"""
    return profanity_word_list.is_profanity(word)


def contains_profanity(text: str) -> bool:
    """Check if text contains profanity"""
    return profanity_word_list.contains_profanity(text)


def get_severity(word: str) -> str:
    """Get severity of profanity word"""
    return profanity_word_list.get_severity(word)


def find_profanity_words(text: str) -> List[Dict[str, str]]:
    """Find all profanity words in text"""
    return profanity_word_list.find_profanity_words(text)


def censor_text(text: str, replacement: str = "***") -> str:
    """Censor profanity in text"""
    return profanity_word_list.censor_text(text, replacement)


def get_stats() -> Dict[str, int]:
    """Get word list statistics"""
    return profanity_word_list.get_stats()
