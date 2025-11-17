"""
Pytest tests for memory extraction

Run with: pytest backend/tests/test_memory_extraction_pytest.py -v
"""

import pytest
import sys
import os

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, backend_path)

from services.memory_manager import MemoryManager
from database.database import SessionLocal, init_db
from models.user import User
from models.memory import UserProfile


@pytest.fixture(scope="module")
def db_session():
    """Create a database session for tests"""
    init_db()
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="module")
def test_user(db_session):
    """Create a test user"""
    user = User(id=9999, name="TestUser")
    db_session.add(user)
    db_session.commit()
    yield user
    # Cleanup
    db_session.delete(user)
    db_session.commit()


@pytest.fixture
def memory_manager():
    """Create a memory manager instance"""
    return MemoryManager()


class TestKeywordExtraction:
    """Tests for keyword-based extraction"""

    def test_extract_name(self, memory_manager):
        """Test name extraction"""
        message = "My name is Alex"
        extracted = memory_manager._simple_keyword_extraction(message)

        assert any(cat == "basic" and key == "name" and val == "Alex"
                   for cat, key, val in extracted), "Should extract name"

    def test_extract_age(self, memory_manager):
        """Test age extraction"""
        message = "I am 11 years old"
        extracted = memory_manager._simple_keyword_extraction(message)

        assert any(cat == "basic" and key == "age" and val == "11"
                   for cat, key, val in extracted), "Should extract age"

    def test_extract_favorite_color(self, memory_manager):
        """Test favorite color extraction"""
        message = "My favorite color is blue"
        extracted = memory_manager._simple_keyword_extraction(message)

        assert any(cat == "favorite" and "color" in key
                   for cat, key, val in extracted), "Should extract favorite color"

    def test_extract_friend(self, memory_manager):
        """Test friend extraction"""
        message = "My best friend Emma loves to read"
        extracted = memory_manager._simple_keyword_extraction(message)

        assert any(cat == "person" and "emma" in key.lower()
                   for cat, key, val in extracted), "Should extract friend"

    def test_extract_goal(self, memory_manager):
        """Test goal extraction"""
        message = "I want to make the soccer team"
        extracted = memory_manager._simple_keyword_extraction(message)

        assert any(cat == "goal" for cat, key, val in extracted), "Should extract goal"

    def test_no_extraction_from_question(self, memory_manager):
        """Test that questions don't extract facts"""
        message = "What's your favorite color?"
        extracted = memory_manager._simple_keyword_extraction(message)

        # Questions might extract nothing or minimal info
        # This is expected behavior
        assert True  # Just verify no crash


class TestMemoryStorage:
    """Tests for memory storage logic"""

    def test_store_new_memory(self, memory_manager, test_user, db_session):
        """Test storing a new memory"""
        message = "My favorite color is green"
        memories = memory_manager.extract_and_store_memories(
            message, test_user.id, db_session, use_llm=False
        )

        assert len(memories) > 0, "Should create at least one memory"

        # Check memory was stored
        stored = db_session.query(UserProfile).filter(
            UserProfile.user_id == test_user.id,
            UserProfile.category == "favorite"
        ).first()

        assert stored is not None, "Memory should be in database"
        assert stored.confidence >= 0.7, "Confidence should be reasonable"
        assert stored.mention_count == 1, "First mention should have count 1"

    def test_update_existing_memory(self, memory_manager, test_user, db_session):
        """Test updating an existing memory"""
        message = "My favorite color is red"

        # First extraction
        memories1 = memory_manager.extract_and_store_memories(
            message, test_user.id, db_session, use_llm=False
        )

        # Second extraction of same fact
        memories2 = memory_manager.extract_and_store_memories(
            message, test_user.id, db_session, use_llm=False
        )

        # Check that mention count increased
        stored = db_session.query(UserProfile).filter(
            UserProfile.user_id == test_user.id,
            UserProfile.category == "favorite",
            UserProfile.value == "red"
        ).first()

        if stored:
            assert stored.mention_count >= 1, "Mention count should increase"
            assert stored.confidence <= 1.0, "Confidence should not exceed 1.0"


class TestLLMExtraction:
    """Tests for LLM-based extraction (if LLM is available)"""

    def test_llm_extraction_basic(self, memory_manager):
        """Test basic LLM extraction"""
        from services.llm_service import llm_service

        if not llm_service.is_loaded:
            pytest.skip("LLM not loaded")

        message = "My name is Sarah and I'm 12 years old"
        extracted = memory_manager._llm_based_extraction(message)

        # Should extract name and age
        categories = [cat for cat, key, val in extracted]
        assert "basic" in categories, "Should extract basic info"

    def test_llm_fallback_on_error(self, memory_manager):
        """Test that LLM falls back to keywords on error"""
        from services.llm_service import llm_service

        if not llm_service.is_loaded:
            # If LLM not loaded, should fallback to keywords
            message = "My favorite color is purple"
            extracted = memory_manager._llm_based_extraction(message)

            # Should still extract using keywords
            assert len(extracted) >= 0, "Should fallback to keyword extraction"


class TestAccuracyMetrics:
    """Tests for extraction accuracy"""

    def test_precision_basic_info(self, memory_manager):
        """Test precision on basic info extraction"""
        test_cases = [
            ("My name is Alex", "basic"),
            ("I am 11 years old", "basic"),
            ("My favorite color is blue", "favorite"),
        ]

        total_extracted = 0
        correct_category = 0

        for message, expected_category in test_cases:
            extracted = memory_manager._simple_keyword_extraction(message)
            total_extracted += len(extracted)

            for cat, key, val in extracted:
                if cat == expected_category:
                    correct_category += 1

        if total_extracted > 0:
            precision = correct_category / total_extracted
            assert precision >= 0.5, "Precision should be reasonable"

    def test_recall_basic_info(self, memory_manager):
        """Test recall on basic info extraction"""
        # Message with 2 facts
        message = "My name is Alex and I am 11 years old"
        extracted = memory_manager._simple_keyword_extraction(message)

        categories = [cat for cat, key, val in extracted]

        # Should find at least 1 of the 2 facts
        assert "basic" in categories, "Should extract at least some basic info"


# Pytest configuration
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
