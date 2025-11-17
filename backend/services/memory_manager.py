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

    # Important People Category Management Methods

    def add_person(self, user_id: int, key: str, value: str, db: Session) -> UserProfile:
        """
        Add an important person for a user

        Args:
            user_id: User ID
            key: Person identifier (e.g., 'friend_emma', 'teacher_smith', 'mom')
            value: Person details/description
            db: Database session

        Returns:
            Created or updated UserProfile object

        Raises:
            ValueError: If key or value is empty
        """
        if not key or not value:
            raise ValueError("Key and value cannot be empty")

        # Check if person already exists
        existing = (
            db.query(UserProfile)
            .filter(
                UserProfile.user_id == user_id,
                UserProfile.category == "person",
                UserProfile.key == key,
            )
            .first()
        )

        if existing:
            # Update existing person
            existing.value = value
            existing.last_mentioned = datetime.now()
            existing.mention_count += 1
            existing.confidence = min(1.0, existing.confidence + 0.1)
            db.commit()
            db.refresh(existing)
            logger.info(f"Updated person {key} for user {user_id}")
            return existing
        else:
            # Create new person
            person = UserProfile(
                user_id=user_id,
                category="person",
                key=key,
                value=value,
                confidence=1.0,  # User-added people have full confidence
                first_mentioned=datetime.now(),
                last_mentioned=datetime.now(),
                mention_count=1,
            )
            db.add(person)
            db.commit()
            db.refresh(person)
            logger.info(f"Added person {key} for user {user_id}")
            return person

    def get_people(self, user_id: int, db: Session) -> List[UserProfile]:
        """
        Get all important people for a user

        Args:
            user_id: User ID
            db: Database session

        Returns:
            List of UserProfile objects with category='person'
        """
        people = (
            db.query(UserProfile)
            .filter(
                UserProfile.user_id == user_id,
                UserProfile.category == "person"
            )
            .order_by(UserProfile.last_mentioned.desc())
            .all()
        )

        logger.debug(f"Retrieved {len(people)} important people for user {user_id}")
        return people

    def get_person_by_id(self, person_id: int, user_id: int, db: Session) -> Optional[UserProfile]:
        """
        Get a specific person by ID

        Args:
            person_id: Person ID
            user_id: User ID (for authorization)
            db: Database session

        Returns:
            UserProfile object or None if not found
        """
        person = (
            db.query(UserProfile)
            .filter(
                UserProfile.id == person_id,
                UserProfile.user_id == user_id,
                UserProfile.category == "person"
            )
            .first()
        )

        return person

    def update_person(
        self, person_id: int, user_id: int, key: Optional[str], value: Optional[str], db: Session
    ) -> Optional[UserProfile]:
        """
        Update an existing person

        Args:
            person_id: Person ID
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

        person = self.get_person_by_id(person_id, user_id, db)

        if not person:
            logger.warning(f"Person {person_id} not found for user {user_id}")
            return None

        # Update fields
        if key is not None:
            person.key = key
        if value is not None:
            person.value = value

        person.last_mentioned = datetime.now()
        db.commit()
        db.refresh(person)

        logger.info(f"Updated person {person_id} for user {user_id}")
        return person

    def delete_person(self, person_id: int, user_id: int, db: Session) -> bool:
        """
        Delete a person

        Args:
            person_id: Person ID
            user_id: User ID (for authorization)
            db: Database session

        Returns:
            True if deleted, False if not found
        """
        person = self.get_person_by_id(person_id, user_id, db)

        if not person:
            logger.warning(f"Person {person_id} not found for user {user_id}")
            return False

        db.delete(person)
        db.commit()

        logger.info(f"Deleted person {person_id} for user {user_id}")
        return True

    # Goals Category Management Methods

    def add_goal(self, user_id: int, key: str, value: str, db: Session) -> UserProfile:
        """
        Add a goal for a user

        Args:
            user_id: User ID
            key: Goal identifier (e.g., 'make_soccer_team', 'learn_guitar', 'improve_grades')
            value: Goal description
            db: Database session

        Returns:
            Created or updated UserProfile object

        Raises:
            ValueError: If key or value is empty
        """
        if not key or not value:
            raise ValueError("Key and value cannot be empty")

        # Check if goal already exists
        existing = (
            db.query(UserProfile)
            .filter(
                UserProfile.user_id == user_id,
                UserProfile.category == "goal",
                UserProfile.key == key,
            )
            .first()
        )

        if existing:
            # Update existing goal
            existing.value = value
            existing.last_mentioned = datetime.now()
            existing.mention_count += 1
            existing.confidence = min(1.0, existing.confidence + 0.1)
            db.commit()
            db.refresh(existing)
            logger.info(f"Updated goal {key} for user {user_id}")
            return existing
        else:
            # Create new goal
            goal = UserProfile(
                user_id=user_id,
                category="goal",
                key=key,
                value=value,
                confidence=1.0,  # User-added goals have full confidence
                first_mentioned=datetime.now(),
                last_mentioned=datetime.now(),
                mention_count=1,
            )
            db.add(goal)
            db.commit()
            db.refresh(goal)
            logger.info(f"Added goal {key} for user {user_id}")
            return goal

    def get_goals(self, user_id: int, db: Session) -> List[UserProfile]:
        """
        Get all goals for a user

        Args:
            user_id: User ID
            db: Database session

        Returns:
            List of UserProfile objects with category='goal'
        """
        goals = (
            db.query(UserProfile)
            .filter(
                UserProfile.user_id == user_id,
                UserProfile.category == "goal"
            )
            .order_by(UserProfile.last_mentioned.desc())
            .all()
        )

        logger.debug(f"Retrieved {len(goals)} goals for user {user_id}")
        return goals

    def get_goal_by_id(self, goal_id: int, user_id: int, db: Session) -> Optional[UserProfile]:
        """
        Get a specific goal by ID

        Args:
            goal_id: Goal ID
            user_id: User ID (for authorization)
            db: Database session

        Returns:
            UserProfile object or None if not found
        """
        goal = (
            db.query(UserProfile)
            .filter(
                UserProfile.id == goal_id,
                UserProfile.user_id == user_id,
                UserProfile.category == "goal"
            )
            .first()
        )

        return goal

    def update_goal(
        self, goal_id: int, user_id: int, key: Optional[str], value: Optional[str], db: Session
    ) -> Optional[UserProfile]:
        """
        Update an existing goal

        Args:
            goal_id: Goal ID
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

        goal = self.get_goal_by_id(goal_id, user_id, db)

        if not goal:
            logger.warning(f"Goal {goal_id} not found for user {user_id}")
            return None

        # Update fields
        if key is not None:
            goal.key = key
        if value is not None:
            goal.value = value

        goal.last_mentioned = datetime.now()
        db.commit()
        db.refresh(goal)

        logger.info(f"Updated goal {goal_id} for user {user_id}")
        return goal

    def delete_goal(self, goal_id: int, user_id: int, db: Session) -> bool:
        """
        Delete a goal

        Args:
            goal_id: Goal ID
            user_id: User ID (for authorization)
            db: Database session

        Returns:
            True if deleted, False if not found
        """
        goal = self.get_goal_by_id(goal_id, user_id, db)

        if not goal:
            logger.warning(f"Goal {goal_id} not found for user {user_id}")
            return False

        db.delete(goal)
        db.commit()

        logger.info(f"Deleted goal {goal_id} for user {user_id}")
        return True

    # Achievements Category Management Methods

    def add_achievement(self, user_id: int, key: str, value: str, db: Session) -> UserProfile:
        """
        Add an achievement for a user

        Args:
            user_id: User ID
            key: Achievement identifier (e.g., 'academic', 'sports', 'personal')
            value: Achievement description
            db: Database session

        Returns:
            Created or updated UserProfile object

        Raises:
            ValueError: If key or value is empty
        """
        if not key or not value:
            raise ValueError("Key and value cannot be empty")

        # Check if achievement already exists
        existing = (
            db.query(UserProfile)
            .filter(
                UserProfile.user_id == user_id,
                UserProfile.category == "achievement",
                UserProfile.key == key,
            )
            .first()
        )

        if existing:
            # Update existing achievement
            existing.value = value
            existing.last_mentioned = datetime.now()
            existing.mention_count += 1
            existing.confidence = min(1.0, existing.confidence + 0.1)
            db.commit()
            db.refresh(existing)
            logger.info(f"Updated achievement {key} for user {user_id}")
            return existing
        else:
            # Create new achievement
            achievement = UserProfile(
                user_id=user_id,
                category="achievement",
                key=key,
                value=value,
                confidence=1.0,  # User-added achievements have full confidence
                first_mentioned=datetime.now(),
                last_mentioned=datetime.now(),
                mention_count=1,
            )
            db.add(achievement)
            db.commit()
            db.refresh(achievement)
            logger.info(f"Added achievement {key} for user {user_id}")
            return achievement

    def get_achievements(self, user_id: int, db: Session) -> List[UserProfile]:
        """
        Get all achievements for a user

        Args:
            user_id: User ID
            db: Database session

        Returns:
            List of UserProfile objects with category='achievement'
        """
        achievements = (
            db.query(UserProfile)
            .filter(
                UserProfile.user_id == user_id,
                UserProfile.category == "achievement"
            )
            .order_by(UserProfile.last_mentioned.desc())
            .all()
        )

        logger.debug(f"Retrieved {len(achievements)} achievements for user {user_id}")
        return achievements

    def get_achievement_by_id(self, achievement_id: int, user_id: int, db: Session) -> Optional[UserProfile]:
        """
        Get a specific achievement by ID

        Args:
            achievement_id: Achievement ID
            user_id: User ID (for authorization)
            db: Database session

        Returns:
            UserProfile object or None if not found
        """
        achievement = (
            db.query(UserProfile)
            .filter(
                UserProfile.id == achievement_id,
                UserProfile.user_id == user_id,
                UserProfile.category == "achievement"
            )
            .first()
        )

        return achievement

    def update_achievement(
        self, achievement_id: int, user_id: int, key: Optional[str], value: Optional[str], db: Session
    ) -> Optional[UserProfile]:
        """
        Update an existing achievement

        Args:
            achievement_id: Achievement ID
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

        achievement = self.get_achievement_by_id(achievement_id, user_id, db)

        if not achievement:
            logger.warning(f"Achievement {achievement_id} not found for user {user_id}")
            return None

        # Update fields
        if key is not None:
            achievement.key = key
        if value is not None:
            achievement.value = value

        achievement.last_mentioned = datetime.now()
        db.commit()
        db.refresh(achievement)

        logger.info(f"Updated achievement {achievement_id} for user {user_id}")
        return achievement

    def delete_achievement(self, achievement_id: int, user_id: int, db: Session) -> bool:
        """
        Delete an achievement

        Args:
            achievement_id: Achievement ID
            user_id: User ID (for authorization)
            db: Database session

        Returns:
            True if deleted, False if not found
        """
        achievement = self.get_achievement_by_id(achievement_id, user_id, db)

        if not achievement:
            logger.warning(f"Achievement {achievement_id} not found for user {user_id}")
            return False

        db.delete(achievement)
        db.commit()

        logger.info(f"Deleted achievement {achievement_id} for user {user_id}")
        return True

    # Memory Search Methods

    def search_memories(
        self,
        user_id: int,
        keywords: str,
        db: Session,
        category: Optional[str] = None,
        limit: Optional[int] = 20
    ) -> List[UserProfile]:
        """
        Search memories by keywords

        Args:
            user_id: User ID
            keywords: Search keywords (space-separated)
            db: Database session
            category: Optional category filter (e.g., 'favorite', 'goal', 'person')
            limit: Maximum number of results (default 20)

        Returns:
            List of UserProfile objects ranked by relevance
        """
        if not keywords or not keywords.strip():
            logger.warning("Empty search keywords provided")
            return []

        # Parse keywords
        keyword_list = [k.lower().strip() for k in keywords.split() if k.strip()]

        if not keyword_list:
            return []

        # Build base query
        query = db.query(UserProfile).filter(UserProfile.user_id == user_id)

        # Apply category filter if provided
        if category:
            query = query.filter(UserProfile.category == category)

        # Get all memories for this user (with category filter if applicable)
        all_memories = query.all()

        # Score each memory based on keyword matches
        scored_memories = []
        for memory in all_memories:
            score = self._calculate_relevance_score(memory, keyword_list)
            if score > 0:
                scored_memories.append((memory, score))

        # Sort by score (descending) and limit results
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        results = [memory for memory, score in scored_memories[:limit]]

        logger.info(f"Search for '{keywords}' returned {len(results)} results for user {user_id}")
        return results

    def _calculate_relevance_score(self, memory: UserProfile, keywords: List[str]) -> int:
        """
        Calculate relevance score for a memory based on keyword matches

        Args:
            memory: UserProfile object
            keywords: List of lowercase keywords

        Returns:
            Relevance score (higher is more relevant)
        """
        score = 0

        # Convert memory fields to lowercase for case-insensitive matching
        key_lower = (memory.key or "").lower()
        value_lower = (memory.value or "").lower()
        category_lower = (memory.category or "").lower()

        for keyword in keywords:
            # Exact match in key gets high score
            if keyword == key_lower:
                score += 10
            # Partial match in key
            elif keyword in key_lower:
                score += 5

            # Exact word match in value gets high score
            value_words = value_lower.split()
            if keyword in value_words:
                score += 8
            # Partial match in value
            elif keyword in value_lower:
                score += 3

            # Category match
            if keyword == category_lower:
                score += 7
            elif keyword in category_lower:
                score += 2

        return score

    # Memory Relevance Ranking Methods

    def calculate_memory_relevance(
        self,
        memory: UserProfile,
        strategy: str = "combined"
    ) -> float:
        """
        Calculate overall relevance score for a memory

        Args:
            memory: UserProfile object
            strategy: Ranking strategy - "recency", "frequency", "confidence", or "combined"

        Returns:
            Relevance score (0.0 to 100.0)
        """
        from datetime import datetime, timedelta

        if strategy == "recency":
            # Score based on how recently the memory was mentioned
            if memory.last_mentioned:
                days_ago = (datetime.now() - memory.last_mentioned).days
                # Exponential decay: 100 for today, 50 for 7 days ago, etc.
                score = 100 * (0.9 ** days_ago)
                return min(100.0, max(0.0, score))
            return 0.0

        elif strategy == "frequency":
            # Score based on mention count
            # Log scale to prevent very high counts from dominating
            import math
            score = 20 * math.log(memory.mention_count + 1)
            return min(100.0, max(0.0, score))

        elif strategy == "confidence":
            # Score based on confidence (already 0.0 to 1.0)
            return memory.confidence * 100

        elif strategy == "combined":
            # Weighted combination of all factors
            recency_score = self.calculate_memory_relevance(memory, "recency")
            frequency_score = self.calculate_memory_relevance(memory, "frequency")
            confidence_score = self.calculate_memory_relevance(memory, "confidence")

            # Weights: recency 40%, frequency 30%, confidence 30%
            combined_score = (
                recency_score * 0.4 +
                frequency_score * 0.3 +
                confidence_score * 0.3
            )
            return combined_score

        else:
            raise ValueError(f"Unknown ranking strategy: {strategy}")

    def get_top_memories(
        self,
        user_id: int,
        db: Session,
        limit: int = 10,
        category: Optional[str] = None,
        strategy: str = "combined"
    ) -> List[UserProfile]:
        """
        Get top most relevant memories for a user

        Args:
            user_id: User ID
            db: Database session
            limit: Maximum number of memories to return (default 10)
            category: Optional category filter
            strategy: Ranking strategy - "recency", "frequency", "confidence", or "combined"

        Returns:
            List of UserProfile objects ranked by relevance
        """
        # Build query
        query = db.query(UserProfile).filter(UserProfile.user_id == user_id)

        if category:
            query = query.filter(UserProfile.category == category)

        # Get all memories
        all_memories = query.all()

        # Score and rank
        scored_memories = []
        for memory in all_memories:
            score = self.calculate_memory_relevance(memory, strategy)
            scored_memories.append((memory, score))

        # Sort by score (descending) and limit
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        results = [memory for memory, score in scored_memories[:limit]]

        logger.info(
            f"Retrieved {len(results)} top memories for user {user_id} "
            f"using strategy '{strategy}'"
        )
        return results

    def get_memory_importance_breakdown(
        self,
        user_id: int,
        db: Session,
        category: Optional[str] = None
    ) -> Dict:
        """
        Get breakdown of memory importance metrics

        Args:
            user_id: User ID
            db: Database session
            category: Optional category filter

        Returns:
            Dictionary with importance metrics and top memories by different criteria
        """
        # Build query
        query = db.query(UserProfile).filter(UserProfile.user_id == user_id)

        if category:
            query = query.filter(UserProfile.category == category)

        memories = query.all()

        if not memories:
            return {
                "total_memories": 0,
                "top_by_recency": [],
                "top_by_frequency": [],
                "top_by_confidence": [],
                "top_combined": []
            }

        # Get top 5 by each strategy
        top_recency = self.get_top_memories(
            user_id, db, limit=5, category=category, strategy="recency"
        )
        top_frequency = self.get_top_memories(
            user_id, db, limit=5, category=category, strategy="frequency"
        )
        top_confidence = self.get_top_memories(
            user_id, db, limit=5, category=category, strategy="confidence"
        )
        top_combined = self.get_top_memories(
            user_id, db, limit=5, category=category, strategy="combined"
        )

        # Calculate average scores
        avg_recency = sum(
            self.calculate_memory_relevance(m, "recency") for m in memories
        ) / len(memories)
        avg_frequency = sum(
            self.calculate_memory_relevance(m, "frequency") for m in memories
        ) / len(memories)
        avg_confidence = sum(
            self.calculate_memory_relevance(m, "confidence") for m in memories
        ) / len(memories)

        return {
            "total_memories": len(memories),
            "average_scores": {
                "recency": round(avg_recency, 2),
                "frequency": round(avg_frequency, 2),
                "confidence": round(avg_confidence, 2)
            },
            "top_by_recency": [
                {
                    "memory": m.to_dict(),
                    "score": round(self.calculate_memory_relevance(m, "recency"), 2)
                }
                for m in top_recency
            ],
            "top_by_frequency": [
                {
                    "memory": m.to_dict(),
                    "score": round(self.calculate_memory_relevance(m, "frequency"), 2)
                }
                for m in top_frequency
            ],
            "top_by_confidence": [
                {
                    "memory": m.to_dict(),
                    "score": round(self.calculate_memory_relevance(m, "confidence"), 2)
                }
                for m in top_confidence
            ],
            "top_combined": [
                {
                    "memory": m.to_dict(),
                    "score": round(self.calculate_memory_relevance(m, "combined"), 2)
                }
                for m in top_combined
            ]
        }


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
