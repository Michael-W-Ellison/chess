# Uses Emojis Quirk Implementation

## Overview

The `uses_emojis` quirk is a personality trait that makes the bot add emojis to its responses, making conversations more expressive and engaging. When enabled, the bot will intelligently inject emojis based on:

- **Current mood** (happy, excited, concerned, playful, calm)
- **Message context** (detected keywords and topics)
- **Friendship level** (higher levels = more frequent emojis)

**Task 69 Complete**: Implement uses_emojis quirk

## Architecture

### Components

1. **EmojiQuirkService** (`services/emoji_quirk_service.py`)
   - Core service handling emoji selection and injection
   - Singleton pattern for efficient access
   - Configurable intensity and mood-based selection

2. **ConversationManager Integration** (`services/conversation_manager.py`)
   - Applies emoji quirk during response generation
   - Adjusts intensity based on friendship level
   - Integrated with existing personality filter

3. **Test Suite** (`tests/test_emoji_quirk.py`)
   - 28 comprehensive tests covering all functionality
   - Tests for mood-based, contextual, and edge cases

## Features

### 1. Mood-Based Emojis

The service selects emojis based on the bot's current mood:

| Mood | Emojis |
|------|--------|
| Happy | 😊 🙂 😄 ☺️ 🌟 |
| Excited | 🎉 😃 🤩 ✨ 🌈 |
| Concerned | 💙 🫂 💭 🤔 |
| Playful | 😄 😆 🎮 🎨 🎵 |
| Calm | 😌 ✨ 🌸 ☁️ |
| Thoughtful | 🤔 💭 📚 🧠 |

### 2. Context-Aware Emoji Selection

The service detects keywords and adds relevant emojis:

#### Activities
- **Games/Play**: 🎮 🎯 🏆 🎲 🎨
- **Reading**: 📚 📖 📝
- **Music**: 🎵 🎶 🎸
- **Art**: 🎨 🖌️ ✏️
- **Sports**: ⚽ 🏀 🎾
- **Learning**: 📚 ✏️ 💡

#### Emotions
- **Love/Friendship**: 💙 💜 💕 👥 🤝
- **Happy**: 😊 😄 🌟
- **Encouragement**: 💪 🎯 👍

#### School
- **School**: 🎒 📚 ✏️
- **Tests**: 📝 💪 🎯
- **Homework**: 📚 ✏️

#### Achievements
- **Winning**: 🏆 🎉 👏
- **Success**: 🌟 💪 🎯
- **Positivity**: 👍 😊 ✨

### 3. Friendship Level Scaling

Emoji frequency increases with friendship level:

```
Intensity = base_intensity + (friendship_level - 1) × 0.05
Max intensity = 0.7
```

| Friendship Level | Base Intensity | Effective Intensity |
|-----------------|----------------|---------------------|
| 1 | 0.40 | 0.40 |
| 3 | 0.40 | 0.50 |
| 5 | 0.40 | 0.60 |
| 10 | 0.40 | 0.70 (capped) |

### 4. Smart Placement

Emojis are placed intelligently:
- **Within sentences**: Before punctuation marks (., !, ?)
- **At sentence end**: Based on intensity probability
- **Final emoji**: Sometimes added at very end of message
- **Avoids duplication**: Won't add emoji if one already present

## Implementation Details

### Service API

```python
from services.emoji_quirk_service import emoji_quirk_service

# Apply emojis to text
result = emoji_quirk_service.apply_emojis(
    text="That's really cool!",
    mood="happy",
    intensity=0.5
)
# Result: "That's really cool 🌟!"
```

### Integration Flow

```
User Message
    ↓
Safety Check
    ↓
Build Context
    ↓
Generate Response (LLM)
    ↓
Apply Personality Filter
    ├─→ [uses_emojis quirk?]
    │   ├─→ Calculate intensity (based on friendship)
    │   ├─→ Detect mood and context
    │   ├─→ Select appropriate emojis
    │   └─→ Inject emojis
    └─→ [catchphrase quirk?]
    ↓
Final Response
```

## Usage Examples

### Example 1: Happy Mood, Gaming Context

**Input:**
```
Bot response: "Want to play a game? I know a fun one!"
Mood: happy
Intensity: 0.5
```

**Output:**
```
"Want to play a game 🎮? I know a fun one 😊!"
```

### Example 2: Excited Mood, Achievement

**Input:**
```
Bot response: "You did great on your test! I'm so proud of you."
Mood: excited
Intensity: 0.6
```

**Output:**
```
"You did great on your test 🎉! I'm so proud of you 🌟."
```

### Example 3: Calm Mood, Helpful Advice

**Input:**
```
Bot response: "Take your time. Let's work through this together."
Mood: calm
Intensity: 0.4
```

**Output:**
```
"Take your time ✨. Let's work through this together 😌."
```

### Example 4: High Friendship Level

**Input:**
```
Bot response: "I love chatting with you! You're awesome. Thanks for being such a great friend."
Mood: happy
Friendship Level: 8
Calculated Intensity: 0.75 → 0.70 (capped)
```

**Output:**
```
"I love chatting with you 💙! You're awesome 🌟. Thanks for being such a great friend 😊!"
```

## Configuration

### Emoji Sets

Emoji sets can be customized in `EmojiQuirkService`:

```python
MOOD_EMOJIS = {
    "happy": ["😊", "🙂", "😄", "☺️", "🌟"],
    # Add more moods...
}

CONTEXT_EMOJIS = {
    "game": ["🎮", "🎯", "🏆"],
    # Add more contexts...
}
```

### Intensity Tuning

Adjust intensity calculation in `conversation_manager.py`:

```python
# Current formula
base_intensity = 0.4
level_bonus = (personality.friendship_level - 1) * 0.05
intensity = min(0.7, base_intensity + level_bonus)

# Modify base_intensity or level_bonus to tune behavior
```

## Testing

Run the emoji quirk test suite:

```bash
cd backend
python -m pytest tests/test_emoji_quirk.py -v
```

### Test Coverage

- ✅ Service initialization
- ✅ Basic emoji application
- ✅ Mood-based selection
- ✅ Contextual emoji selection
- ✅ Intensity scaling
- ✅ Emoji placement
- ✅ Multiple sentences
- ✅ Edge cases (empty text, special characters, numbers)
- ✅ Integration scenarios
- ✅ Individual service methods

**All 28 tests passing**

## API Endpoints

The `uses_emojis` quirk is automatically applied when the bot personality has this quirk enabled. No special API endpoints are required.

### Checking Quirks

```bash
GET /api/personality?user_id=1
```

Response includes:
```json
{
  "quirks": ["uses_emojis", "tells_puns"],
  ...
}
```

### Enabling the Quirk

Update the bot personality's quirks array to include `"uses_emojis"`:

```python
personality = db.query(BotPersonality).filter_by(user_id=1).first()
quirks = personality.get_quirks()
if "uses_emojis" not in quirks:
    quirks.append("uses_emojis")
    personality.set_quirks(quirks)
    db.commit()
```

## Performance Considerations

- **Lightweight**: Emoji injection adds minimal overhead (<1ms per message)
- **No external dependencies**: Uses only Python standard library
- **Singleton pattern**: Single instance shared across requests
- **Efficient regex**: Compiled patterns for sentence splitting

## Future Enhancements

Potential improvements:

- [ ] Machine learning-based emoji suggestion
- [ ] User-specific emoji preferences
- [ ] Seasonal/holiday-themed emojis
- [ ] Emoji reactions to user emotions
- [ ] Customizable emoji intensity per user
- [ ] A/B testing different emoji styles
- [ ] Emoji usage analytics and insights

## Troubleshooting

### Emojis Not Appearing

1. **Check quirk is enabled**: Verify `"uses_emojis"` in personality quirks
2. **Check intensity**: Low friendship levels = fewer emojis
3. **Random variation**: Emoji injection is probabilistic
4. **Empty response**: Very short responses may not get emojis

### Too Many Emojis

1. **Adjust base intensity**: Lower the base_intensity value
2. **Cap intensity**: Reduce the max intensity cap
3. **Reduce level bonus**: Lower the friendship level multiplier

### Wrong Emojis for Context

1. **Update CONTEXT_EMOJIS**: Add or modify keyword mappings
2. **Adjust mood mapping**: Update MOOD_EMOJIS for different moods
3. **Check bot mood**: Verify mood is set correctly in personality

## Related Files

- `backend/services/emoji_quirk_service.py` - Core emoji service
- `backend/services/conversation_manager.py` - Integration point
- `backend/tests/test_emoji_quirk.py` - Test suite
- `backend/models/personality.py` - Personality model with quirks
- `backend/USES_EMOJIS_QUIRK.md` - This documentation

## Conclusion

The `uses_emojis` quirk is **fully implemented and tested**, providing:

✅ Intelligent emoji selection based on mood and context
✅ Friendship level-based intensity scaling
✅ Smart placement within sentences
✅ Comprehensive test coverage (28 tests)
✅ Efficient, lightweight implementation
✅ Easy configuration and customization

This quirk enhances the bot's personality, making conversations more engaging and expressive for users.

**Task 69 Complete**: Implement uses_emojis quirk
