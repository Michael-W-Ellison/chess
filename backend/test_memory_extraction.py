"""
Memory Extraction Accuracy Tests

Tests the accuracy of both keyword-based and LLM-based memory extraction.
Validates extraction against expected results and calculates accuracy metrics.

Run with: python backend/test_memory_extraction.py
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from services.memory_manager import MemoryManager
from database.database import SessionLocal, init_db
from models.user import User
from models.memory import UserProfile
from datetime import datetime
import json
from typing import List, Dict, Tuple

# Test cases with expected extractions
TEST_CASES = [
    # Basic info extraction
    {
        "message": "My name is Alex and I'm 11 years old",
        "expected": [
            {"category": "basic", "key": "name", "value": "Alex"},
            {"category": "basic", "key": "age", "value": "11"},
        ],
        "description": "Basic info (name and age)",
    },
    {
        "message": "I'm Sarah, I'm 12 years old and in 7th grade",
        "expected": [
            {"category": "basic", "key": "name", "value": "Sarah"},
            {"category": "basic", "key": "age", "value": "12"},
            {"category": "basic", "key": "grade", "value": "7"},
        ],
        "description": "Complete basic info",
    },
    # Favorites extraction
    {
        "message": "My favorite color is blue",
        "expected": [
            {"category": "favorite", "key": "color", "value": "blue"},
        ],
        "description": "Single favorite (color)",
    },
    {
        "message": "I love playing basketball and my favorite food is pizza",
        "expected": [
            {"category": "favorite", "key": "sport", "value": "basketball"},
            {"category": "favorite", "key": "food", "value": "pizza"},
        ],
        "description": "Multiple favorites",
    },
    {
        "message": "I really love soccer",
        "expected": [
            {"category": "favorite", "key_contains": "soccer"},
        ],
        "description": "Favorite activity (love keyword)",
    },
    # People extraction
    {
        "message": "My best friend Emma loves to read",
        "expected": [
            {"category": "person", "key_contains": "emma"},
        ],
        "description": "Best friend mention",
    },
    {
        "message": "My friend Jake and I play video games",
        "expected": [
            {"category": "person", "key_contains": "jake"},
        ],
        "description": "Friend mention",
    },
    # Goals extraction
    {
        "message": "I want to make the soccer team this year",
        "expected": [
            {"category": "goal", "value_contains": "soccer team"},
        ],
        "description": "Goal (want to)",
    },
    {
        "message": "I'm hoping to get better at math",
        "expected": [
            {"category": "goal", "value_contains": "math"},
        ],
        "description": "Goal (hoping to)",
    },
    {
        "message": "My goal is to learn piano",
        "expected": [
            {"category": "goal", "value_contains": "piano"},
        ],
        "description": "Explicit goal",
    },
    # Achievements
    {
        "message": "I just won the spelling bee at school!",
        "expected": [
            {"category": "achievement", "value_contains": "spelling bee"},
        ],
        "description": "Achievement",
    },
    # Dislikes
    {
        "message": "I hate broccoli, it's so gross",
        "expected": [
            {"category": "dislike", "value_contains": "broccoli"},
        ],
        "description": "Dislike (hate keyword)",
    },
    # Edge cases - should NOT extract
    {
        "message": "What's your favorite color?",
        "expected": [],
        "description": "Question (no extraction)",
    },
    {
        "message": "I'm feeling happy today",
        "expected": [],
        "description": "Temporary mood (no extraction)",
    },
    {
        "message": "Maybe I like pizza",
        "expected": [],
        "description": "Hypothetical (no extraction)",
    },
    # Complex sentences
    {
        "message": "Hi! I'm Tom and I'm 10. I love playing Minecraft and my best friend is Sam. We want to build a treehouse together!",
        "expected": [
            {"category": "basic", "key": "name", "value": "Tom"},
            {"category": "basic", "key": "age", "value": "10"},
            {"category": "favorite", "value_contains": "Minecraft"},
            {"category": "person", "key_contains": "sam"},
            {"category": "goal", "value_contains": "treehouse"},
        ],
        "description": "Complex multi-fact sentence",
    },
]


class MemoryExtractionTester:
    """Test memory extraction accuracy"""

    def __init__(self):
        self.memory_manager = MemoryManager()
        self.db = None
        self.test_user_id = 999  # Test user ID

    def setup_database(self):
        """Initialize database for testing"""
        print("Setting up test database...")
        init_db()
        self.db = SessionLocal()

        # Create test user
        existing_user = self.db.query(User).filter(User.id == self.test_user_id).first()
        if existing_user:
            self.db.delete(existing_user)
            self.db.commit()

        test_user = User(id=self.test_user_id, name="TestUser")
        self.db.add(test_user)
        self.db.commit()

    def cleanup_database(self):
        """Clean up test data"""
        if self.db:
            # Delete test user and all associated data
            test_user = self.db.query(User).filter(User.id == self.test_user_id).first()
            if test_user:
                self.db.delete(test_user)
                self.db.commit()
            self.db.close()

    def check_extraction(self, extracted: List[Tuple], expected: List[Dict]) -> Tuple[int, int, List[str]]:
        """
        Check if extraction matches expected results

        Returns:
            (matches, total_expected, errors)
        """
        matches = 0
        errors = []

        for exp in expected:
            category = exp.get("category")
            key = exp.get("key")
            value = exp.get("value")
            key_contains = exp.get("key_contains")
            value_contains = exp.get("value_contains")

            found = False
            for ext_cat, ext_key, ext_val in extracted:
                # Check category match
                if ext_cat != category:
                    continue

                # Check key match
                if key and ext_key != key:
                    continue
                if key_contains and key_contains.lower() not in ext_key.lower():
                    continue

                # Check value match
                if value and ext_val != value:
                    continue
                if value_contains and value_contains.lower() not in ext_val.lower():
                    continue

                # All checks passed
                found = True
                break

            if found:
                matches += 1
            else:
                error_msg = f"Expected {category}"
                if key:
                    error_msg += f"/{key}"
                elif key_contains:
                    error_msg += f"/*{key_contains}*"
                if value:
                    error_msg += f"={value}"
                elif value_contains:
                    error_msg += f"=*{value_contains}*"
                errors.append(error_msg + " (not found)")

        return matches, len(expected), errors

    def test_keyword_extraction(self) -> Dict:
        """Test keyword-based extraction"""
        print("\n" + "=" * 60)
        print("TESTING KEYWORD-BASED EXTRACTION")
        print("=" * 60)

        total_cases = 0
        passed_cases = 0
        total_expected = 0
        total_matched = 0

        results = []

        for test_case in TEST_CASES:
            message = test_case["message"]
            expected = test_case["expected"]
            description = test_case["description"]

            # Extract using keywords
            extracted = self.memory_manager._simple_keyword_extraction(message)

            # Check accuracy
            matches, total, errors = self.check_extraction(extracted, expected)

            total_cases += 1
            total_expected += total
            total_matched += matches

            passed = matches == total
            if passed:
                passed_cases += 1

            # Print result
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"\n{status}: {description}")
            print(f"  Message: \"{message}\"")
            print(f"  Expected: {total} facts, Found: {len(extracted)}, Matched: {matches}")

            if extracted:
                print(f"  Extracted:")
                for cat, key, val in extracted:
                    print(f"    - {cat}/{key} = {val}")

            if errors:
                print(f"  Errors:")
                for error in errors:
                    print(f"    - {error}")

            results.append({
                "description": description,
                "passed": passed,
                "matches": matches,
                "total": total,
                "extracted_count": len(extracted),
            })

        # Calculate metrics
        precision = total_matched / max(sum(r["extracted_count"] for r in results), 1)
        recall = total_matched / max(total_expected, 1)
        f1_score = 2 * (precision * recall) / max((precision + recall), 0.0001)

        print("\n" + "=" * 60)
        print("KEYWORD EXTRACTION SUMMARY")
        print("=" * 60)
        print(f"Total Test Cases: {total_cases}")
        print(f"Passed: {passed_cases}")
        print(f"Failed: {total_cases - passed_cases}")
        print(f"Pass Rate: {(passed_cases / total_cases * 100):.1f}%")
        print(f"\nAccuracy Metrics:")
        print(f"  Precision: {precision:.3f} ({total_matched} correct / {sum(r['extracted_count'] for r in results)} extracted)")
        print(f"  Recall: {recall:.3f} ({total_matched} found / {total_expected} expected)")
        print(f"  F1 Score: {f1_score:.3f}")

        return {
            "method": "keyword",
            "total_cases": total_cases,
            "passed_cases": passed_cases,
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
        }

    def test_llm_extraction(self) -> Dict:
        """Test LLM-based extraction"""
        print("\n" + "=" * 60)
        print("TESTING LLM-BASED EXTRACTION")
        print("=" * 60)

        from services.llm_service import llm_service

        if not llm_service.is_loaded:
            print("\n⚠️  LLM not loaded. Skipping LLM extraction tests.")
            print("To test LLM extraction:")
            print("  1. Download a GGUF model (./backend/scripts/download_model.sh)")
            print("  2. Set MODEL_PATH in .env")
            print("  3. Run tests again")
            return {
                "method": "llm",
                "skipped": True,
                "reason": "LLM not loaded",
            }

        total_cases = 0
        passed_cases = 0
        total_expected = 0
        total_matched = 0

        results = []

        for test_case in TEST_CASES:
            message = test_case["message"]
            expected = test_case["expected"]
            description = test_case["description"]

            # Extract using LLM
            try:
                extracted = self.memory_manager._llm_based_extraction(message)
            except Exception as e:
                print(f"\n✗ ERROR: {description}")
                print(f"  Message: \"{message}\"")
                print(f"  Error: {e}")
                continue

            # Check accuracy
            matches, total, errors = self.check_extraction(extracted, expected)

            total_cases += 1
            total_expected += total
            total_matched += matches

            passed = matches == total
            if passed:
                passed_cases += 1

            # Print result
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"\n{status}: {description}")
            print(f"  Message: \"{message}\"")
            print(f"  Expected: {total} facts, Found: {len(extracted)}, Matched: {matches}")

            if extracted:
                print(f"  Extracted:")
                for cat, key, val in extracted:
                    print(f"    - {cat}/{key} = {val}")

            if errors:
                print(f"  Errors:")
                for error in errors:
                    print(f"    - {error}")

            results.append({
                "description": description,
                "passed": passed,
                "matches": matches,
                "total": total,
                "extracted_count": len(extracted),
            })

        # Calculate metrics
        if results:
            precision = total_matched / max(sum(r["extracted_count"] for r in results), 1)
            recall = total_matched / max(total_expected, 1)
            f1_score = 2 * (precision * recall) / max((precision + recall), 0.0001)
        else:
            precision = recall = f1_score = 0.0

        print("\n" + "=" * 60)
        print("LLM EXTRACTION SUMMARY")
        print("=" * 60)
        print(f"Total Test Cases: {total_cases}")
        print(f"Passed: {passed_cases}")
        print(f"Failed: {total_cases - passed_cases}")
        if total_cases > 0:
            print(f"Pass Rate: {(passed_cases / total_cases * 100):.1f}%")
            print(f"\nAccuracy Metrics:")
            print(f"  Precision: {precision:.3f} ({total_matched} correct / {sum(r['extracted_count'] for r in results)} extracted)")
            print(f"  Recall: {recall:.3f} ({total_matched} found / {total_expected} expected)")
            print(f"  F1 Score: {f1_score:.3f}")

        return {
            "method": "llm",
            "total_cases": total_cases,
            "passed_cases": passed_cases,
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
        }

    def run_all_tests(self):
        """Run all memory extraction tests"""
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║         Memory Extraction Accuracy Test Suite               ║")
        print("╚══════════════════════════════════════════════════════════════╝")

        try:
            self.setup_database()

            # Test keyword extraction
            keyword_results = self.test_keyword_extraction()

            # Test LLM extraction
            llm_results = self.test_llm_extraction()

            # Compare results
            print("\n" + "=" * 60)
            print("COMPARISON")
            print("=" * 60)

            if not llm_results.get("skipped"):
                print(f"\n{'Metric':<15} {'Keyword':<15} {'LLM':<15} {'Winner':<10}")
                print("-" * 60)

                metrics = ["precision", "recall", "f1_score"]
                for metric in metrics:
                    kw_val = keyword_results.get(metric, 0)
                    llm_val = llm_results.get(metric, 0)
                    winner = "LLM" if llm_val > kw_val else "Keyword" if kw_val > llm_val else "Tie"
                    print(f"{metric.capitalize():<15} {kw_val:<15.3f} {llm_val:<15.3f} {winner:<10}")

                print(f"\n{'Pass Rate':<15} {keyword_results['passed_cases']}/{keyword_results['total_cases']:<15} {llm_results['passed_cases']}/{llm_results['total_cases']:<15}")
            else:
                print(f"\nKeyword Extraction:")
                print(f"  Pass Rate: {keyword_results['passed_cases']}/{keyword_results['total_cases']}")
                print(f"  Precision: {keyword_results['precision']:.3f}")
                print(f"  Recall: {keyword_results['recall']:.3f}")
                print(f"  F1 Score: {keyword_results['f1_score']:.3f}")
                print(f"\nLLM Extraction: Skipped ({llm_results['reason']})")

            print("\n" + "=" * 60)
            print("✅ All tests completed!")
            print("=" * 60)

        finally:
            self.cleanup_database()


if __name__ == "__main__":
    tester = MemoryExtractionTester()
    tester.run_all_tests()
