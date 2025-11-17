"""
Memory Manager Service
Extracts and manages user memories and profile information
"""

from typing import List, Dict, Optional
import logging
from datetime import datetime
import json

from sqlalchemy.orm import Session
from models.user import User
from models.memory import UserProfile
from models.conversation import Message
from services.prompts import MemoryExtractionPrompt

logger = logging.getLogger("chatbot.memory_manager")


class MemoryManager:
    """
    Memory Manager - handles user memory extraction and retrieval

    Responsibilities:
    - Extract facts from user messages
    - Store memories in UserProfile table
    - Retrieve relevant memories for conversation context
    - Update memory confidence and mention counts
    """

    def __init__(self):
        self.extraction_enabled = True
        self.use_llm_extraction = True  # Enable LLM-based extraction by default

    def extract_and_store_memories(
        self, user_message: str, user_id: int, db: Session, use_llm: bool = None
    ) -> List[UserProfile]:
        """
        Extract memories from a user message and store them

        Args:
            user_message: The user's message
            user_id: User ID
            db: Database session
            use_llm: Whether to use LLM for extraction (None = use instance setting)

        Returns:
            List of created/updated UserProfile objects
        """
        if not self.extraction_enabled:
            return []

        memories = []

        # Use instance setting if not specified
        if use_llm is None:
            use_llm = self.use_llm_extraction

        # Choose extraction method
        if use_llm:
            extracted = self._llm_based_extraction(user_message)
        else:
            # Fallback to simple keyword-based extraction
            extracted = self._simple_keyword_extraction(user_message)

        for category, key, value in extracted:
            # Check if this memory already exists
            existing = (
                db.query(UserProfile)
                .filter(
                    UserProfile.user_id == user_id,
                    UserProfile.category == category,
                    UserProfile.key == key,
                )
                .first()
            )

            if existing:
                # Update existing memory
                existing.value = value
                existing.last_mentioned = datetime.now()
                existing.mention_count += 1
                existing.confidence = min(1.0, existing.confidence + 0.1)  # Increase confidence
                memories.append(existing)
                logger.debug(f"Updated memory: {category}/{key}")
            else:
                # Create new memory
                memory = UserProfile(
                    user_id=user_id,
                    category=category,
                    key=key,
                    value=value,
                    confidence=0.8,  # Initial confidence
                    first_mentioned=datetime.now(),
                    last_mentioned=datetime.now(),
                    mention_count=1,
                )
                db.add(memory)
                memories.append(memory)
                logger.debug(f"Created memory: {category}/{key}")

        if memories:
            db.commit()
            logger.info(f"Stored {len(memories)} memories for user {user_id}")

        return memories

    def _simple_keyword_extraction(self, message: str) -> List[tuple]:
        """
        Simple keyword-based memory extraction

        Args:
            message: User message

        Returns:
            List of tuples: (category, key, value)
        """
        extracted = []
        message_lower = message.lower()

        # Favorite detection patterns
        favorite_patterns = [
            ("favorite color is", "favorite_color"),
            ("favorite colour is", "favorite_color"),
            ("love", "favorite_activity"),
            ("my favorite", "favorite_item"),
        ]

        for pattern, key in favorite_patterns:
            if pattern in message_lower:
                # Extract the value (simple approach)
                idx = message_lower.find(pattern)
                value_part = message[idx + len(pattern) :].strip().split()[0:3]
                value = " ".join(value_part).rstrip(".,!?")
                if value:
                    extracted.append(("favorite", key, value))

        # Name detection
        if "my name is" in message_lower:
            idx = message_lower.find("my name is")
            name = message[idx + 11 :].strip().split()[0].rstrip(".,!?")
            if name and len(name) > 1:
                extracted.append(("basic", "name", name.capitalize()))

        # Age detection
        if "i am" in message_lower and "years old" in message_lower:
            words = message_lower.split()
            for i, word in enumerate(words):
                if word == "i" and i + 1 < len(words) and words[i + 1] == "am":
                    if i + 2 < len(words) and words[i + 2].isdigit():
                        age = words[i + 2]
                        extracted.append(("basic", "age", age))

        # Friend detection
        if "my friend" in message_lower or "best friend" in message_lower:
            # Try to extract friend name
            words = message.split()
            for i, word in enumerate(words):
                if word.lower() in ["friend", "friend's"] and i > 0:
                    if i + 1 < len(words):
                        friend_name = words[i + 1].rstrip(".,!?")
                        if friend_name and len(friend_name) > 1:
                            extracted.append(
                                ("person", f"friend_{friend_name.lower()}", friend_name)
                            )

        # Goal detection
        if "want to" in message_lower or "goal" in message_lower or "hoping to" in message_lower:
            # Extract goal (simplified)
            for phrase in ["want to", "hoping to", "my goal is to"]:
                if phrase in message_lower:
                    idx = message_lower.find(phrase)
                    goal_text = message[idx + len(phrase) :].strip().split(".")[0]
                    if goal_text and len(goal_text) > 5:
                        key = f"goal_{datetime.now().strftime('%Y%m%d')}"
                        extracted.append(("goal", key, goal_text[:100]))

        return extracted

    def _llm_based_extraction(self, message: str) -> List[tuple]:
        """
        LLM-based memory extraction using structured prompts

        Args:
            message: User message

        Returns:
            List of tuples: (category, key, value)
        """
        from services.llm_service import llm_service

        # Check if LLM is available
        if not llm_service.is_loaded:
            logger.warning("LLM not loaded, falling back to keyword extraction")
            return self._simple_keyword_extraction(message)

        try:
            # Format the extraction prompt
            prompt = MemoryExtractionPrompt.format_prompt(message)

            # Generate extraction using LLM
            response = llm_service.generate(
                prompt,
                max_tokens=300,
                temperature=0.3,  # Low temperature for more consistent extraction
                stop=None,
            )

            # Parse JSON response
            response_clean = response.strip()

            # Handle potential markdown code blocks
            if response_clean.startswith("```json"):
                response_clean = response_clean[7:]
            if response_clean.startswith("```"):
                response_clean = response_clean[3:]
            if response_clean.endswith("```"):
                response_clean = response_clean[:-3]

            response_clean = response_clean.strip()

            # Parse JSON
            try:
                extractions = json.loads(response_clean)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM extraction response: {response_clean}")
                logger.error(f"JSON error: {e}")
                # Fallback to keyword extraction
                return self._simple_keyword_extraction(message)

            # Validate and convert to tuple format
            extracted = []
            for item in extractions:
                if not isinstance(item, dict):
                    continue

                category = item.get("category")
                key = item.get("key")
                value = item.get("value")
                confidence = item.get("confidence", 0.8)

                # Validate required fields
                if not all([category, key, value]):
                    logger.debug(f"Skipping incomplete extraction: {item}")
                    continue

                # Validate category
                valid_categories = ["favorite", "dislike", "person", "goal", "achievement", "basic"]
                if category not in valid_categories:
                    logger.debug(f"Skipping invalid category: {category}")
                    continue

                # Only include high-confidence extractions
                if confidence >= 0.7:
                    extracted.append((category, key, str(value)))
                    logger.debug(f"Extracted: {category}/{key} = {value} (confidence: {confidence})")

            logger.info(f"LLM extracted {len(extracted)} memories from message")
            return extracted

        except Exception as e:
            logger.error(f"Error in LLM-based extraction: {e}", exc_info=True)
            # Fallback to keyword extraction
            return self._simple_keyword_extraction(message)

    def get_relevant_memories(
        self, user_id: int, keywords: List[str], db: Session, limit: int = 5
    ) -> List[UserProfile]:
        """
        Retrieve relevant memories based on keywords

        Args:
            user_id: User ID
            keywords: List of keywords to search for
            db: Database session
            limit: Maximum number of memories to return

        Returns:
            List of relevant UserProfile objects
        """
        if not keywords:
            # Return most recently mentioned memories
            return (
                db.query(UserProfile)
                .filter(UserProfile.user_id == user_id)
                .order_by(UserProfile.last_mentioned.desc())
                .limit(limit)
                .all()
            )

        # Search for memories matching keywords
        memories = []
        for keyword in keywords:
            keyword_lower = keyword.lower()

            # Search in key and value fields
            results = (
                db.query(UserProfile)
                .filter(
                    UserProfile.user_id == user_id,
                    (
                        UserProfile.key.like(f"%{keyword_lower}%")
                        | UserProfile.value.like(f"%{keyword_lower}%")
                    ),
                )
                .all()
            )

            memories.extend(results)

        # Remove duplicates and sort by confidence and recency
        unique_memories = list({m.id: m for m in memories}.values())
        unique_memories.sort(
            key=lambda m: (m.confidence * m.mention_count, m.last_mentioned), reverse=True
        )

        return unique_memories[:limit]

    def get_user_profile_summary(self, user_id: int, db: Session) -> Dict:
        """
        Get a summary of the user's profile for context building

        Args:
            user_id: User ID
            db: Database session

        Returns:
            Dictionary with categorized profile information
        """
        profile = {
            "favorites": {},
            "dislikes": {},
            "important_people": [],
            "goals": [],
            "achievements": [],
            "basic_info": {},
        }

        # Get all profile items
        items = db.query(UserProfile).filter(UserProfile.user_id == user_id).all()

        for item in items:
            if item.category == "favorite":
                profile["favorites"][item.key] = item.value
            elif item.category == "dislike":
                profile["dislikes"][item.key] = item.value
            elif item.category == "person":
                profile["important_people"].append({"name": item.key, "notes": item.value})
            elif item.category == "goal":
                profile["goals"].append(item.value)
            elif item.category == "achievement":
                profile["achievements"].append(item.value)
            elif item.category == "basic":
                profile["basic_info"][item.key] = item.value

        return profile

    def extract_keywords(self, text: str) -> List[str]:
        """
        Extract keywords from text for memory search

        Args:
            text: Text to extract keywords from

        Returns:
            List of keywords
        """
        # Simple keyword extraction (remove stop words)
        stopwords = {
            "i",
            "me",
            "my",
            "we",
            "you",
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "is",
            "am",
            "are",
            "was",
            "were",
        }

        words = text.lower().split()
        keywords = [
            w.strip(".,!?") for w in words if w not in stopwords and len(w) > 3
        ]

        # Return top 5 keywords
        return keywords[:5]

    def format_memories_for_prompt(self, memories: List[UserProfile]) -> str:
        """
        Format memories for inclusion in LLM prompt

        Args:
            memories: List of UserProfile objects

        Returns:
            Formatted string for prompt
        """
        if not memories:
            return ""

        formatted = []
        for memory in memories:
            if memory.category == "favorite":
                formatted.append(f"- Likes {memory.key.replace('favorite_', '')}: {memory.value}")
            elif memory.category == "person":
                formatted.append(f"- Friend/person: {memory.value}")
            elif memory.category == "goal":
                formatted.append(f"- Goal: {memory.value}")
            elif memory.category == "achievement":
                formatted.append(f"- Achievement: {memory.value}")
            else:
                formatted.append(f"- {memory.key}: {memory.value}")

        return "\n".join(formatted)

    # Favorites Category Management Methods

    def add_favorite(self, user_id: int, key: str, value: str, db: Session) -> UserProfile:
        """
        Add a new favorite for a user

        Args:
            user_id: User ID
            key: Favorite key (e.g., 'color', 'food', 'game')
            value: Favorite value
            db: Database session

        Returns:
            Created or updated UserProfile object

        Raises:
            ValueError: If key or value is empty
        """
        if not key or not value:
            raise ValueError("Key and value cannot be empty")

        # Check if favorite already exists
        existing = (
            db.query(UserProfile)
            .filter(
                UserProfile.user_id == user_id,
                UserProfile.category == "favorite",
                UserProfile.key == key,
            )
            .first()
        )

        if existing:
            # Update existing favorite
            existing.value = value
            existing.last_mentioned = datetime.now()
            existing.mention_count += 1
            existing.confidence = min(1.0, existing.confidence + 0.1)
            db.commit()
            db.refresh(existing)
            logger.info(f"Updated favorite {key} for user {user_id}")
            return existing
        else:
            # Create new favorite
            favorite = UserProfile(
                user_id=user_id,
                category="favorite",
                key=key,
                value=value,
                confidence=1.0,  # User-added favorites have full confidence
                first_mentioned=datetime.now(),
                last_mentioned=datetime.now(),
                mention_count=1,
            )
            db.add(favorite)
            db.commit()
            db.refresh(favorite)
            logger.info(f"Added favorite {key} for user {user_id}")
            return favorite

    def get_favorites(self, user_id: int, db: Session) -> List[UserProfile]:
        """
        Get all favorites for a user

        Args:
            user_id: User ID
            db: Database session

        Returns:
            List of UserProfile objects with category='favorite'
        """
        favorites = (
            db.query(UserProfile)
            .filter(
                UserProfile.user_id == user_id,
                UserProfile.category == "favorite"
            )
            .order_by(UserProfile.last_mentioned.desc())
            .all()
        )

        logger.debug(f"Retrieved {len(favorites)} favorites for user {user_id}")
        return favorites

    def get_favorite_by_id(self, favorite_id: int, user_id: int, db: Session) -> Optional[UserProfile]:
        """
        Get a specific favorite by ID

        Args:
            favorite_id: Favorite ID
            user_id: User ID (for authorization)
            db: Database session

        Returns:
            UserProfile object or None if not found
        """
        favorite = (
            db.query(UserProfile)
            .filter(
                UserProfile.id == favorite_id,
                UserProfile.user_id == user_id,
                UserProfile.category == "favorite"
            )
            .first()
        )

        return favorite

    def update_favorite(
        self, favorite_id: int, user_id: int, key: Optional[str], value: Optional[str], db: Session
    ) -> Optional[UserProfile]:
        """
        Update an existing favorite

        Args:
            favorite_id: Favorite ID
            user_id: User ID (for authorization)
            key: New key (optional)
            value: New value (optional)
            db: Database session

        Returns:
            Updated UserProfile object or None if not found

        Raises:
            ValueError: If neither key nor value is provided
        """
        if key is None and value is None:
            raise ValueError("Must provide at least one of key or value to update")

        favorite = self.get_favorite_by_id(favorite_id, user_id, db)

        if not favorite:
            logger.warning(f"Favorite {favorite_id} not found for user {user_id}")
            return None

        # Update fields
        if key is not None:
            favorite.key = key
        if value is not None:
            favorite.value = value

        favorite.last_mentioned = datetime.now()
        db.commit()
        db.refresh(favorite)

        logger.info(f"Updated favorite {favorite_id} for user {user_id}")
        return favorite

    def delete_favorite(self, favorite_id: int, user_id: int, db: Session) -> bool:
        """
        Delete a favorite

        Args:
            favorite_id: Favorite ID
            user_id: User ID (for authorization)
            db: Database session

        Returns:
            True if deleted, False if not found
        """
        favorite = self.get_favorite_by_id(favorite_id, user_id, db)

        if not favorite:
            logger.warning(f"Favorite {favorite_id} not found for user {user_id}")
            return False

        db.delete(favorite)
        db.commit()

        logger.info(f"Deleted favorite {favorite_id} for user {user_id}")
        return True

    # Dislikes Category Management Methods

    def add_dislike(self, user_id: int, key: str, value: str, db: Session) -> UserProfile:
        """
        Add a new dislike for a user

        Args:
            user_id: User ID
            key: Dislike key (e.g., 'food', 'activity', 'subject')
            value: Dislike value
            db: Database session

        Returns:
            Created or updated UserProfile object

        Raises:
            ValueError: If key or value is empty
        """
        if not key or not value:
            raise ValueError("Key and value cannot be empty")

        # Check if dislike already exists
        existing = (
            db.query(UserProfile)
            .filter(
                UserProfile.user_id == user_id,
                UserProfile.category == "dislike",
                UserProfile.key == key,
            )
            .first()
        )

        if existing:
            # Update existing dislike
            existing.value = value
            existing.last_mentioned = datetime.now()
            existing.mention_count += 1
            existing.confidence = min(1.0, existing.confidence + 0.1)
            db.commit()
            db.refresh(existing)
            logger.info(f"Updated dislike {key} for user {user_id}")
            return existing
        else:
            # Create new dislike
            dislike = UserProfile(
                user_id=user_id,
                category="dislike",
                key=key,
                value=value,
                confidence=1.0,  # User-added dislikes have full confidence
                first_mentioned=datetime.now(),
                last_mentioned=datetime.now(),
                mention_count=1,
            )
            db.add(dislike)
            db.commit()
            db.refresh(dislike)
            logger.info(f"Added dislike {key} for user {user_id}")
            return dislike

    def get_dislikes(self, user_id: int, db: Session) -> List[UserProfile]:
        """
        Get all dislikes for a user

        Args:
            user_id: User ID
            db: Database session

        Returns:
            List of UserProfile objects with category='dislike'
        """
        dislikes = (
            db.query(UserProfile)
            .filter(
                UserProfile.user_id == user_id,
                UserProfile.category == "dislike"
            )
            .order_by(UserProfile.last_mentioned.desc())
            .all()
        )

        logger.debug(f"Retrieved {len(dislikes)} dislikes for user {user_id}")
        return dislikes

    def get_dislike_by_id(self, dislike_id: int, user_id: int, db: Session) -> Optional[UserProfile]:
        """
        Get a specific dislike by ID

        Args:
            dislike_id: Dislike ID
            user_id: User ID (for authorization)
            db: Database session

        Returns:
            UserProfile object or None if not found
        """
        dislike = (
            db.query(UserProfile)
            .filter(
                UserProfile.id == dislike_id,
                UserProfile.user_id == user_id,
                UserProfile.category == "dislike"
            )
            .first()
        )

        return dislike

    def update_dislike(
        self, dislike_id: int, user_id: int, key: Optional[str], value: Optional[str], db: Session
    ) -> Optional[UserProfile]:
        """
        Update an existing dislike

        Args:
            dislike_id: Dislike ID
            user_id: User ID (for authorization)
            key: New key (optional)
            value: New value (optional)
            db: Database session

        Returns:
            Updated UserProfile object or None if not found

        Raises:
            ValueError: If neither key nor value is provided
        """
        if key is None and value is None:
            raise ValueError("Must provide at least one of key or value to update")

        dislike = self.get_dislike_by_id(dislike_id, user_id, db)

        if not dislike:
            logger.warning(f"Dislike {dislike_id} not found for user {user_id}")
            return None

        # Update fields
        if key is not None:
            dislike.key = key
        if value is not None:
            dislike.value = value

        dislike.last_mentioned = datetime.now()
        db.commit()
        db.refresh(dislike)

        logger.info(f"Updated dislike {dislike_id} for user {user_id}")
        return dislike

    def delete_dislike(self, dislike_id: int, user_id: int, db: Session) -> bool:
        """
        Delete a dislike

        Args:
            dislike_id: Dislike ID
            user_id: User ID (for authorization)
            db: Database session

        Returns:
            True if deleted, False if not found
        """
        dislike = self.get_dislike_by_id(dislike_id, user_id, db)

        if not dislike:
            logger.warning(f"Dislike {dislike_id} not found for user {user_id}")
            return False

        db.delete(dislike)
        db.commit()

        logger.info(f"Deleted dislike {dislike_id} for user {user_id}")
        return True


# Global instance
memory_manager = MemoryManager()


# Convenience functions
def extract_and_store_memories(
    user_message: str, user_id: int, db: Session
) -> List[UserProfile]:
    """Extract and store memories from user message"""
    return memory_manager.extract_and_store_memories(user_message, user_id, db)


def get_relevant_memories(
    user_id: int, keywords: List[str], db: Session, limit: int = 5
) -> List[UserProfile]:
    """Get relevant memories for context"""
    return memory_manager.get_relevant_memories(user_id, keywords, db, limit)


def get_user_profile_summary(user_id: int, db: Session) -> Dict:
    """Get user profile summary"""
    return memory_manager.get_user_profile_summary(user_id, db)
