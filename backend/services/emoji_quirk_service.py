"""
Emoji Quirk Service
Handles the uses_emojis personality quirk
"""

import random
import re
from typing import List, Dict


class EmojiQuirkService:
    """
    Service for applying the uses_emojis quirk to bot responses

    This service adds appropriate emojis to responses based on:
    - Bot's current mood
    - Message sentiment and keywords
    - Natural placement within sentences
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

    # Punctuation marks where emojis can be inserted
    EMOJI_INSERTION_POINTS = ['.', '!', '?']

    def apply_emojis(self, text: str, mood: str = "happy", intensity: float = 0.5) -> str:
        """
        Apply emojis to text based on mood and intensity

        Args:
            text: Original response text
            mood: Bot's current mood
            intensity: How often to add emojis (0.0-1.0)

        Returns:
            Text with emojis added
        """
        if not text:
            return text

        # Split into sentences
        sentences = self._split_into_sentences(text)

        # Process each sentence
        modified_sentences = []
        for i, sentence in enumerate(sentences):
            # Skip very short sentences
            if len(sentence.strip()) < 5:
                modified_sentences.append(sentence)
                continue

            # Determine if we should add emoji to this sentence
            should_add = random.random() < intensity

            if should_add:
                # Try to add contextual emoji first
                emoji = self._get_contextual_emoji(sentence, mood)
                if not emoji:
                    # Fall back to mood-based emoji
                    emoji = self._get_mood_emoji(mood)

                # Add emoji at end of sentence
                sentence = self._add_emoji_to_sentence(sentence, emoji)

            modified_sentences.append(sentence)

        # Rejoin sentences
        result = " ".join(modified_sentences)

        # Sometimes add an emoji at the very end for extra personality
        if random.random() < (intensity * 0.6):
            result = self._add_final_emoji(result, mood)

        return result

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting on punctuation
        sentences = re.split(r'([.!?]+\s+)', text)

        # Recombine sentences with their punctuation
        result = []
        for i in range(0, len(sentences), 2):
            if i + 1 < len(sentences):
                result.append(sentences[i] + sentences[i + 1])
            else:
                result.append(sentences[i])

        return [s for s in result if s.strip()]

    def _get_contextual_emoji(self, text: str, mood: str) -> str:
        """Get emoji based on text content and keywords"""
        text_lower = text.lower()

        # Find matching keywords
        matches = []
        for keyword, emojis in self.CONTEXT_EMOJIS.items():
            if keyword in text_lower:
                matches.extend(emojis)

        if matches:
            return random.choice(matches)

        return ""

    def _get_mood_emoji(self, mood: str) -> str:
        """Get emoji based on mood"""
        emojis = self.MOOD_EMOJIS.get(mood, self.GENERIC_POSITIVE)
        return random.choice(emojis)

    def _add_emoji_to_sentence(self, sentence: str, emoji: str) -> str:
        """Add emoji to sentence (at the end, before punctuation if possible)"""
        sentence = sentence.rstrip()

        # Check if sentence ends with punctuation
        if sentence and sentence[-1] in self.EMOJI_INSERTION_POINTS:
            # Insert before the punctuation
            return sentence[:-1] + f" {emoji}" + sentence[-1]
        else:
            # Add at the end
            return sentence + f" {emoji}"

    def _add_final_emoji(self, text: str, mood: str) -> str:
        """Add a final emoji at the end of the entire message"""
        text = text.rstrip()
        emoji = self._get_mood_emoji(mood)

        # If already ends with an emoji, don't add another
        if text and text[-1] in ["😊", "🙂", "😄", "🎉", "😃", "🤩", "💙", "🫂", "😆", "😌", "✨", "🤔"]:
            return text

        return text + f" {emoji}"


# Global singleton instance
emoji_quirk_service = EmojiQuirkService()
