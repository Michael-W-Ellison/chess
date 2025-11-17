# shares_facts Quirk Implementation

## Overview
The `shares_facts` personality quirk adds educational facts to bot responses, making conversations more informative and engaging. Facts are contextually relevant and scale with friendship level.

**Task**: Task 71 - Implement shares_facts quirk
**Status**: ✅ Completed

## Files Created

### `services/fact_quirk_service.py`
Main service that handles fact selection and integration.

**Key Features**:
- 60+ educational facts across 9 categories
- Context-aware fact selection
- Friendship level-based probability scaling
- Natural transition phrases
- "Did you know?" format for all facts

**Fact Categories**:
1. **Science Facts** (7 facts) - Lightning, atoms, sound, planets, etc.
2. **Animal Facts** (10 facts) - Octopuses, butterflies, elephants, etc.
3. **Space Facts** (7 facts) - Moon, sun, galaxies, etc.
4. **Nature Facts** (7 facts) - Trees, rainforests, volcanoes, etc.
5. **History Facts** (7 facts) - Great Wall, pyramids, printing press, etc.
6. **Tech Facts** (6 facts) - Internet, first computer, email, etc.
7. **Body Facts** (7 facts) - Brain, bones, blood, etc.
8. **Geography Facts** (6 facts) - Continents, oceans, mountains, etc.
9. **General Facts** (6 facts) - Honey, popcorn, bananas, etc.

**Context Keywords**: 30+ keywords mapped to fact categories for contextual matching.

### `tests/test_fact_quirk.py`
Comprehensive test suite with 33 tests covering:
- Service initialization
- Fact addition with various probabilities
- Context-based fact selection
- Category-specific fact retrieval
- Transition phrase usage
- Content validation (all start with "Did you know?")
- Integration scenarios (homework, pets, space, nature)
- Edge cases (long responses, special characters, multiple keywords)

## Integration

### In `conversation_manager.py`

```python
from services.fact_quirk_service import fact_quirk_service

def _apply_personality_filter(
    self, response: str, personality: BotPersonality, context: str = ""
) -> str:
    """Apply personality quirks to response"""
    quirks = personality.get_quirks()

    # Apply shares_facts quirk
    if "shares_facts" in quirks:
        # Base probability is 20%, increases by 2% per friendship level
        # Max probability is 35% at level 10
        base_probability = 0.20
        level_bonus = (personality.friendship_level - 1) * 0.02
        probability = min(0.35, base_probability + level_bonus)

        response = fact_quirk_service.add_fact(
            response,
            context=context,
            probability=probability
        )

    # ... other quirks

    return response
```

## Friendship Level Scaling

The `shares_facts` quirk scales with friendship level:

| Level | Probability | Description |
|-------|-------------|-------------|
| 1     | 20%         | Occasional facts for new friends |
| 2-3   | 22-24%      | Slightly more frequent |
| 4-6   | 26-30%      | Regular fact sharing |
| 7-9   | 32-34%      | Frequent educational moments |
| 10    | 35%         | Maximum engagement |

## Examples

### Science Context
**User**: "I have a science test tomorrow"
**Bot**: "I can help you study! Did you know? A bolt of lightning is five times hotter than the surface of the sun!"

### Animal Context
**User**: "I love my cat"
**Bot**: "Cats are wonderful pets! Here's something cool: Did you know? Butterflies can taste with their feet!"

### General Conversation
**User**: "That's interesting!"
**Bot**: "Glad you think so! By the way, did you know? Honey never spoils - archaeologists found 3000-year-old honey in Egyptian tombs that was still edible!"

## Technical Details

### Service Methods

```python
class FactQuirkService:
    def add_fact(
        self,
        response: str,
        context: str = "",
        probability: float = 0.3
    ) -> str:
        """
        Add a fact to the response based on context and probability

        Args:
            response: Original bot response
            context: Conversation context for selecting relevant facts
            probability: Chance of adding a fact (0.0-1.0)

        Returns:
            Response with fact added (or original if no fact added)
        """
```

**Key Internal Methods**:
- `_get_contextual_fact(context)`: Selects fact based on keywords
- `_get_random_fact()`: Returns random fact from all categories
- `get_fact_by_category(category)`: Gets fact from specific category

### Transition Phrases

Facts are sometimes (40% chance) prefaced with transition phrases for natural flow:
- "Here's something cool:"
- "Fun fact:"
- "By the way,"
- "Also,"
- "Did you know?"

## Testing

Run tests with:
```bash
python -m pytest tests/test_fact_quirk.py -v
```

**Test Results**: ✅ 33/33 passed

## Design Principles

1. **Educational Value**: All facts are age-appropriate and educational
2. **Context Awareness**: Facts match conversation topics when possible
3. **Natural Integration**: Transition phrases and formatting feel conversational
4. **Progressive Engagement**: Frequency increases as friendship grows
5. **Variety**: 60+ facts across 9 categories prevent repetition
6. **Consistent Format**: All facts start with "Did you know?" for recognition

## Future Enhancements

Potential improvements:
- Add more fact categories (sports, arts, languages)
- Track which facts have been shared to avoid repetition
- Allow user to request facts on specific topics
- Add fact difficulty levels based on user age/grade
- Include follow-up questions to encourage discussion

## Related Files

- `services/emoji_quirk_service.py` - uses_emojis quirk
- `services/pun_quirk_service.py` - tells_puns quirk
- `services/conversation_manager.py` - Quirk orchestration
- `models/personality.py` - Personality model with quirks

## Notes

- Facts are designed to be kid-friendly (ages 6-12)
- All facts are scientifically accurate and age-appropriate
- Probability scaling ensures facts don't overwhelm conversations
- Context matching makes facts feel relevant and timely
- Works harmoniously with other quirks (emojis, puns)
