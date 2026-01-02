"""
Manual Test Script for SafetyFilter - Task 159
Tests various input categories to demonstrate SafetyFilter functionality

Run with: python test_safety_filter_manual.py
"""

import sys
import json
from services.safety_filter import SafetyFilter


def print_result(test_name, message, result):
    """Pretty print test results"""
    print(f"\n{'='*80}")
    print(f"TEST: {test_name}")
    print(f"{'='*80}")
    print(f"Input Message: {message}")
    print(f"\nResult:")
    print(f"  Safe: {result['safe']}")
    print(f"  Flags: {result['flags']}")
    print(f"  Severity: {result['severity']}")
    print(f"  Action: {result['action']}")
    print(f"  Notify Parent: {result['notify_parent']}")
    if result.get('response_message'):
        print(f"  Response Message: {result['response_message'][:200]}...")
    print(f"\nDetails:")
    for key, value in result['details'].items():
        if isinstance(value, dict):
            print(f"  {key}:")
            for k, v in value.items():
                if isinstance(v, list) and len(v) > 3:
                    print(f"    {k}: {v[:3]}... ({len(v)} items)")
                else:
                    print(f"    {k}: {v}")
        else:
            print(f"  {key}: {value}")


def run_tests():
    """Run comprehensive tests with various input categories"""
    filter = SafetyFilter()

    print("\n" + "="*80)
    print("SAFETY FILTER MANUAL TESTING - TASK 159")
    print("="*80)

    # Category 1: Safe Messages
    print("\n\n" + "#"*80)
    print("# CATEGORY 1: SAFE MESSAGES (Should Pass)")
    print("#"*80)

    safe_messages = [
        ("Normal Homework Help", "Can you help me with my algebra homework?"),
        ("General Question", "What's the capital of France?"),
        ("Essay Writing Help", "How do I write a good essay introduction?"),
        ("Math Problem", "What is the quadratic formula?"),
        ("Science Question", "How does photosynthesis work?"),
    ]

    for test_name, message in safe_messages:
        result = filter.check_message(message)
        print_result(test_name, message, result)


    # Category 2: Crisis Messages (Critical Priority)
    print("\n\n" + "#"*80)
    print("# CATEGORY 2: CRISIS DETECTION (Critical Severity)")
    print("#"*80)

    crisis_messages = [
        ("Suicide - Direct", "I want to kill myself"),
        ("Suicide - Indirect", "I'm thinking about ending it all"),
        ("Self-Harm", "I cut myself last night"),
        ("Physical Abuse", "My dad hits me every day"),
        ("Emotional Abuse", "My mom threatens me all the time"),
        ("Sexual Abuse", "Someone touched me inappropriately"),
        ("Multiple Crisis Indicators", "I want to die and I cut myself"),
    ]

    for test_name, message in crisis_messages:
        result = filter.check_message(message)
        print_result(test_name, message, result)


    # Category 3: Bullying Messages (Medium Severity)
    print("\n\n" + "#"*80)
    print("# CATEGORY 3: BULLYING DETECTION (Medium Severity)")
    print("#"*80)

    bullying_messages = [
        ("Physical Bullying", "Kids at school keep bullying me"),
        ("Verbal Bullying", "Everyone makes fun of me at school"),
        ("Social Exclusion", "Nobody will talk to me, they exclude me from everything"),
        ("Cyberbullying", "People are spreading rumors about me online"),
    ]

    for test_name, message in bullying_messages:
        result = filter.check_message(message)
        print_result(test_name, message, result)


    # Category 4: Profanity (Low to High Severity)
    print("\n\n" + "#"*80)
    print("# CATEGORY 4: PROFANITY DETECTION (Low to High Severity)")
    print("#"*80)

    profanity_messages = [
        ("Mild Profanity - 'stupid'", "This homework is so stupid", 1),
        ("Mild Profanity - 'dumb'", "This test is dumb", 2),
        ("Moderate Profanity - 'damn'", "damn it, I forgot my homework", 3),
        ("Moderate Profanity - 'crap'", "this is crap", 4),
        ("Severe Profanity - 'f-word'", "This is fucking difficult", 5),
        ("Severe Profanity - 'sh-word'", "This is shit", 6),
    ]

    for test_name, message, user_id in profanity_messages:
        result = filter.check_message(message, user_id=user_id)
        print_result(test_name, message, result)


    # Category 5: Inappropriate Requests
    print("\n\n" + "#"*80)
    print("# CATEGORY 5: INAPPROPRIATE REQUEST DETECTION")
    print("#"*80)

    inappropriate_messages = [
        ("Cheating Request", "How can I cheat on my test?"),
        ("Violence Request", "How to hurt someone?"),
        ("Theft Request", "How to steal from a store?"),
        ("Hacking Request", "How do I hack into someone's account?"),
    ]

    for test_name, message in inappropriate_messages:
        try:
            result = filter.check_message(message)
            print_result(test_name, message, result)
        except Exception as e:
            print(f"\nERROR in test '{test_name}': {str(e)}")


    # Category 6: Edge Cases
    print("\n\n" + "#"*80)
    print("# CATEGORY 6: EDGE CASES")
    print("#"*80)

    edge_cases = [
        ("Empty Message", ""),
        ("Whitespace Only", "   \n\t  "),
        ("Very Long Message", "This is a safe message. " * 100),
        ("Mixed Case Crisis", "I WANT TO KILL MYSELF"),
        ("Unicode Characters", "Hello 你好 مرحبا"),
        ("Special Characters", "Hello!!! How are you??? :) :D <3"),
        ("Crisis in Context", "Sometimes I feel like I want to hurt myself but I know I shouldn't"),
    ]

    for test_name, message in edge_cases:
        result = filter.check_message(message)
        print_result(test_name, message, result)


    # Category 7: Priority Testing
    print("\n\n" + "#"*80)
    print("# CATEGORY 7: PRIORITY ORDER TESTING")
    print("#"*80)

    priority_messages = [
        ("Crisis + Profanity", "I want to kill myself, this is shit"),
        ("Abuse + Inappropriate", "My teacher hits me and how to steal"),
        ("Bullying + Profanity", "Everyone bullies me and this is damn annoying", 7),
    ]

    for test_name, *args in priority_messages:
        if len(args) == 2:
            message, user_id = args
            result = filter.check_message(message, user_id=user_id)
        else:
            message = args[0]
            result = filter.check_message(message)
        print_result(test_name, message, result)


    # Category 8: Realistic Student Scenarios
    print("\n\n" + "#"*80)
    print("# CATEGORY 8: REALISTIC STUDENT SCENARIOS")
    print("#"*80)

    student_scenarios = [
        ("Frustrated Student", "This math homework is so hard and stupid!", 10),
        ("Stressed Student", "I have so much homework and I'm really stressed"),
        ("Student in Crisis", "I failed my test and now I feel like I want to hurt myself"),
        ("Student Reporting Bullying", "The kids at school keep making fun of me"),
        ("Student Seeking Help", "I don't understand this assignment, can you help?"),
    ]

    for test_name, message, *user_id in student_scenarios:
        uid = user_id[0] if user_id else None
        result = filter.check_message(message, user_id=uid)
        print_result(test_name, message, result)


    # Summary Statistics
    print("\n\n" + "#"*80)
    print("# SERVICE STATISTICS")
    print("#"*80)

    stats = filter.get_service_stats()
    print(json.dumps(stats, indent=2))


    print("\n\n" + "="*80)
    print("TESTING COMPLETE")
    print("="*80)


if __name__ == "__main__":
    try:
        run_tests()
    except KeyboardInterrupt:
        print("\n\nTesting interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
