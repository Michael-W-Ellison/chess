"""
Emoji Quirk Service
Handles the uses_emojis personality quirk
"""

import random
import re
from typing import List


class EmojiQuirkService:
    """
    Service for applying the uses_emojis quirk to bot responses

    This service adds appropriate emojis to responses based on:
    - Bot's current mood
    - Message sentiment and keywords
    - Placement after a sentence's punctuation, at most one or two per reply
    """

    # Emoji sets organized by mood
    MOOD_EMOJIS = {
        "happy": ["😊", "🙂", "😄", "☺️", "🌟"],
        "excited": ["🎉", "😃", "🤩", "✨", "🌈"],
        "concerned": ["💙", "🫂", "💭", "🤔"],
        "playful": ["😄", "😆", "🎮", "🎨", "🎵"],
        "calm": ["😌", "✨", "🌸", "☁️"],
        "thoughtful": ["🤔", "💭", "📚", "🧠"],
    }

    # Context-based emojis for common topics
    CONTEXT_EMOJIS = {
        # Activities
        "game": ["🎮", "🎯", "🏆"],
        "play": ["🎮", "🎲", "🎨"],
        "read": ["📚", "📖", "📝"],
        "music": ["🎵", "🎶", "🎸"],
        "art": ["🎨", "🖌️", "✏️"],
        "sport": ["⚽", "🏀", "🎾"],
        "learn": ["📚", "✏️", "💡"],

        # Emotions
        "love": ["💙", "💜", "💕"],
        "friend": ["👥", "🤝", "💙"],
        "happy": ["😊", "😄", "🌟"],
        "sad": ["💙", "🫂"],
        "fun": ["🎉", "😄", "✨"],
        "cool": ["😎", "✨", "🌟"],

        # School/Learning
        "school": ["🎒", "📚", "✏️"],
        "test": ["📝", "💪", "🎯"],
        "homework": ["📚", "✏️"],

        # Achievements
        "win": ["🏆", "🎉", "👏"],
        "success": ["🌟", "💪", "🎯"],
        "good": ["👍", "😊", "✨"],
        "great": ["🌟", "🎉", "😄"],
        "awesome": ["🤩", "🎉", "✨"],

        # Questions/Thinking
        "think": ["🤔", "💭"],
        "know": ["💡", "🧠"],
        "wonder": ["🤔", "✨"],
    }

    # Generic positive emojis for variety
    GENERIC_POSITIVE = ["😊", "🙂", "✨", "💙", "🌟"]

    # Words that make a sentence sad or difficult: use a caring emoji, not a cheerful one
    NEGATIVE_WORDS = {
        "sorry", "sad", "hard", "tough", "frustrating", "upset", "worried", "worry", "sick",
        "hurt", "miss", "lonely", "scared", "angry", "mad", "wrong", "bad", "cry", "crying",
        "afraid", "nervous", "stressed", "awful", "terrible", "mean", "lost", "broke", "broken",
        "hospital", "died", "dead", "funeral", "divorce", "injured", "fight", "fighting",
        "buried", "lonely", "alone", "annoying", "stupid", "dumb", "ugly", "fever", "pain", "hurts",
        "ouch", "oof", "sting", "stings", "nightmare", "nightmares", "worst", "trouble", "cracked", "spilled", "ripped", "ruined",
    }
    COMFORT_EMOJIS = ["💙", "🫂"]
    PLAY_FIGHTS = {"pillow", "snowball", "water", "food", "nerf", "tickle", "play", "balloon"}

    def apply_emojis(self, text: str, mood: str = "happy", intensity: float = 0.5) -> str:
        """
        Apply emojis to text based on its words, the bot's mood, and intensity

        At most one emoji is added (two when intensity is 0.6 or more), after a sentence's
        closing punctuation. Sentences whose words match an emoji keyword are preferred,
        then the last sentence. Sad or difficult sentences get a caring emoji.

        Args:
            text: Original response text
            mood: Bot's current mood
            intensity: How likely emojis are (0.0-1.0)

        Returns:
            Text with emojis added
        """
        if not text:
            return text

        sentences = self._split_into_sentences(text)
        eligible = [i for i, sentence in enumerate(sentences) if len(sentence.strip()) >= 5]
        max_emojis = 2 if intensity >= 0.6 else 1

        # Sentences with a matching keyword first, then later sentences before earlier ones
        eligible.sort(key=lambda i: (not self._context_matches(sentences[i]), -i))
        chosen = []
        for index in eligible:
            if len(chosen) >= max_emojis:
                break
            if random.random() < intensity:
                chosen.append(index)

        for index in chosen:
            emoji = self._choose_emoji(sentences[index], mood)
            sentences[index] = self._add_emoji_to_sentence(sentences[index], emoji)

        return " ".join(sentences)

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences, each keeping its closing punctuation"""
        parts = re.split(r'(?<=[.!?])\s+', text.strip())
        return [part.strip() for part in parts if part.strip()]

    def _context_matches(self, text: str) -> List[str]:
        """Emojis for keywords that appear as whole words ("game", "games"; not "art" in "part")"""
        text_lower = text.lower()
        matches = []
        for keyword, emojis in self.CONTEXT_EMOJIS.items():
            if re.search(rf"\b{re.escape(keyword)}(s|es|ed|ing|er)?\b", text_lower):
                matches.extend(emojis)
        return matches

    def is_negative(self, text: str) -> bool:
        """
        True if the text is about something sad or difficult ("I wasn't scared" and "we were
        laughing so hard" are not)
        """
        words = re.findall(r"[a-z']+", text.lower())
        if any(re.match(r"(laugh|giggl|fun|happy|yay|haha|lol)", word) for word in words):
            return False
        for i, word in enumerate(words):
            if word in self.NEGATIVE_WORDS and not (i > 0 and (words[i - 1] in ("not", "no", "never")
                                                                 or words[i - 1].endswith(("n't", "nt")))):
                if word.startswith("fight") and i > 0 and words[i - 1] in self.PLAY_FIGHTS:
                    continue  # "a pillow fight"
                if word == "lost" and ("tooth" in words or "teeth" in words):
                    continue  # "I lost a tooth" is good news
                if word == "hospital" and i > 0 and words[i - 1] in ("the", "a") and i > 1 and words[i - 2] in ("from", "left", "of"):
                    continue  # "she came home from the hospital"
                if word == "hard" and any(w.startswith(("stud", "work", "tri", "try", "practic", "train"))
                                          for w in words[max(0, i - 3):i]):
                    continue  # "I studied really hard"
                return True
        return "oh no" in text.lower()

    def _choose_emoji(self, sentence: str, mood: str) -> str:
        """Caring emoji for sad/difficult sentences, else a keyword emoji, else a mood emoji"""
        if self.is_negative(sentence) or mood == "concerned":
            return random.choice(self.COMFORT_EMOJIS)
        return self._get_contextual_emoji(sentence, mood) or self._get_mood_emoji(mood)

    def _get_contextual_emoji(self, text: str, mood: str) -> str:
        """Get emoji based on text content and keywords"""
        matches = self._context_matches(text)
        return random.choice(matches) if matches else ""

    def _get_mood_emoji(self, mood: str) -> str:
        """Get emoji based on mood"""
        emojis = self.MOOD_EMOJIS.get(mood, self.GENERIC_POSITIVE)
        return random.choice(emojis)

    def _add_emoji_to_sentence(self, sentence: str, emoji: str) -> str:
        """Add emoji after the sentence, following its punctuation ("That's awesome! 🎉")"""
        return f"{sentence.rstrip()} {emoji}"


# Global singleton instance
emoji_quirk_service = EmojiQuirkService()
