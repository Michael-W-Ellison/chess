# Personality Drift System

## Overview

The Personality Drift System enables the chatbot's personality traits to evolve gradually based on conversation patterns and user interactions. Instead of having a static personality, the bot adapts its behavior over time, creating a more dynamic and realistic relationship experience.

## Core Concept

**Personality Drift** is the gradual change in personality traits based on conversation metrics. The bot's personality traits (humor, energy, curiosity, formality) shift in response to:
- User behavior patterns
- Conversation quality and length
- Topics discussed
- User emotional state
- Interaction style

All drift is:
- **Gradual**: Small incremental changes (0.01-0.05 per conversation)
- **Bounded**: Traits stay within valid range [0.0, 1.0]
- **Reversible**: Traits can drift back if patterns change
- **Transparent**: All changes are logged with reasons

## Architecture

### Components

1. **PersonalityDrift Model** (`models/personality_drift.py`)
   - Database model tracking all personality changes
   - Records what changed, why, when, and by how much
   - Links to user, conversation, and friendship level

2. **PersonalityDriftCalculator** (`services/personality_drift_calculator.py`)
   - Core service calculating drift based on conversation analysis
   - Analyzes conversation patterns and triggers
   - Applies bounded trait adjustments
   - Provides drift history and analytics

3. **Integration** (`services/conversation_manager.py`)
   - Automatically calculates drift when conversation ends
   - Integrated into conversation flow
   - No manual intervention required

4. **API Endpoints** (`routes/personality.py`)
   - 6 endpoints for drift querying and management
   - History, summary, timeline, stats
   - Manual adjustment capability

## Personality Traits

### The Four Traits

| Trait | Range | Description | High Value Means | Low Value Means |
|-------|-------|-------------|------------------|-----------------|
| **Humor** | 0.0-1.0 | Frequency and intensity of jokes | Very playful, lots of jokes | Serious, minimal humor |
| **Energy** | 0.0-1.0 | Enthusiasm and liveliness | Highly enthusiastic, energetic | Calm, subdued, relaxed |
| **Curiosity** | 0.0-1.0 | How often bot asks questions | Very inquisitive, engaged | More passive, less questioning |
| **Formality** | 0.0-1.0 | Casual vs formal language | Very formal, proper language | Very casual, informal |

### Default Values

All traits start at **0.5** (neutral middle ground) and drift based on interactions.

## Drift Rules

### Humor Drift

**Increases When**:
- User laughs frequently (lol, haha, funny, 😂)
- User shows appreciation for jokes
- Positive, playful interactions

**Decreases When**:
- Deep/serious topics discussed (life, death, meaning, philosophy)
- User shares heavy feelings (worried, anxious, scared)
- Formal or somber conversations

**Drift Amounts**:
- 3+ laughs: +0.03 (medium increase)
- 1-2 laughs: +0.01 (small increase)
- 3+ deep topics: -0.01 (small decrease)
- 3+ feelings shared: -0.01 (small decrease)

### Energy Drift

**Increases When**:
- Long conversations (20+ messages = quality)
- Active engagement (10+ messages = long)
- User shows enthusiasm (laughter, exclamation marks)

**Decreases When**:
- Many short messages (70%+ very brief responses)
- Low engagement
- One-word answers

**Drift Amounts**:
- 20+ messages: +0.03 (medium increase)
- 10-19 messages: +0.01 (small increase)
- User enthusiasm: +0.01 (small increase)
- 70%+ short messages: -0.01 (small decrease)

### Curiosity Drift

**Increases When**:
- User asks questions (encourages engagement)
- User shares feelings (shows trust)
- User opens up and shares

**Decreases When**:
- User gives mostly brief responses
- Low engagement
- Minimal interaction

**Drift Amounts**:
- 3+ questions: +0.03 (medium increase)
- 1-2 questions: +0.01 (small increase)
- 2+ feelings shared: +0.01 (small increase)
- 70%+ short messages: -0.01 (small decrease)

### Formality Drift

**Increases When**:
- User uses formal language (however, therefore, regarding)
- Structured, proper conversations
- Academic or professional topics

**Decreases When**:
- User uses casual language (yeah, nah, lol, btw, idk)
- Deep personal topics (more intimate = less formal)
- User shares feelings (personal connection)
- Informal, friendly interactions

**Drift Amounts**:
- 5+ casual phrases: -0.03 (medium decrease)
- 2-4 casual phrases: -0.01 (small decrease)
- 3+ formal indicators: +0.01 (small increase)
- 2+ deep topics: -0.01 (small decrease)
- 3+ feelings shared: -0.01 (small decrease)

## Database Schema

### PersonalityDrift Table

```sql
CREATE TABLE personality_drift (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,

    -- What changed
    trait_name VARCHAR NOT NULL,  -- humor, energy, curiosity, formality
    old_value FLOAT NOT NULL,
    new_value FLOAT NOT NULL,
    change_amount FLOAT NOT NULL,  -- Can be positive or negative

    -- Why it changed
    trigger_type VARCHAR NOT NULL,  -- conversation_pattern, user_feedback, level_up, manual
    trigger_details TEXT,  -- JSON with specific reasons

    -- Context
    conversation_id INTEGER,
    friendship_level INTEGER NOT NULL,

    -- When
    timestamp DATETIME NOT NULL,

    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);
```

### Trigger Types

| Type | Description | Example |
|------|-------------|---------|
| `conversation_pattern` | Automatic drift from conversation analysis | User laughed 3 times |
| `user_feedback` | User explicitly requests personality change | User says "be more funny" |
| `level_up` | Friendship level milestone triggers trait change | Reaching level 5 |
| `manual` | Admin/user manually adjusts trait | User slider adjustment |

### Trigger Details JSON

```json
{
    "reasons": [
        "User laughed 3 times",
        "User showed enthusiasm"
    ],
    "requested_change": 0.03,
    "actual_change": 0.03,
    "bounded": false
}
```

## API Endpoints

### GET `/api/friendship/drift/history`

Get drift history for a user.

**Query Parameters**:
- `user_id` (int, default=1)
- `trait_name` (str, optional) - Filter by specific trait
- `limit` (int, default=50)

**Response**:
```json
{
    "success": true,
    "user_id": 1,
    "trait_name": "humor",
    "drift_events": [
        {
            "id": 1,
            "user_id": 1,
            "trait_name": "humor",
            "old_value": 0.5,
            "new_value": 0.53,
            "change_amount": 0.03,
            "trigger_type": "conversation_pattern",
            "trigger_details": {
                "reasons": ["User laughed 3 times"],
                "requested_change": 0.03,
                "actual_change": 0.03,
                "bounded": false
            },
            "conversation_id": 42,
            "friendship_level": 5,
            "timestamp": "2024-01-15T14:30:00"
        }
    ],
    "count": 1
}
```

### GET `/api/friendship/drift/summary`

Get comprehensive drift summary.

**Query Parameters**:
- `user_id` (int, default=1)

**Response**:
```json
{
    "success": true,
    "user_id": 1,
    "summary": {
        "total_drifts": 45,
        "by_trait": {
            "humor": {
                "drift_count": 12,
                "total_change": 0.15,
                "average_change": 0.0125,
                "current_value": 0.65,
                "original_value": 0.5
            },
            "energy": {
                "drift_count": 10,
                "total_change": 0.08,
                "average_change": 0.008,
                "current_value": 0.58,
                "original_value": 0.5
            }
        },
        "by_trigger": {
            "conversation_pattern": 40,
            "manual": 5
        },
        "recent_drifts": [...]
    }
}
```

### GET `/api/friendship/drift/timeline/{trait_name}`

Get timeline of changes for a specific trait.

**Path Parameters**:
- `trait_name` (str) - humor, energy, curiosity, or formality

**Query Parameters**:
- `user_id` (int, default=1)

**Response**:
```json
{
    "success": true,
    "user_id": 1,
    "trait_name": "humor",
    "current_value": 0.65,
    "timeline": [
        {
            "timestamp": "2024-01-15T10:00:00",
            "value": 0.53,
            "change": 0.03,
            "trigger": "conversation_pattern",
            "reasons": ["User laughed 3 times"]
        },
        {
            "timestamp": "2024-01-15T15:00:00",
            "value": 0.65,
            "change": 0.12,
            "trigger": "conversation_pattern",
            "reasons": ["User laughed 5 times", "User showed enthusiasm"]
        }
    ],
    "total_changes": 2
}
```

### POST `/api/friendship/drift/manual-adjust`

Manually adjust a personality trait.

**Request Body**:
```json
{
    "user_id": 1,
    "trait_name": "humor",
    "new_value": 0.8
}
```

**Response**:
```json
{
    "success": true,
    "message": "Trait humor adjusted successfully",
    "drift_event": {
        "id": 46,
        "trait_name": "humor",
        "old_value": 0.65,
        "new_value": 0.8,
        "change_amount": 0.15,
        "trigger_type": "manual",
        "timestamp": "2024-01-15T16:00:00"
    },
    "new_personality": {
        "name": "Buddy",
        "traits": {
            "humor": 0.8,
            "energy": 0.58,
            "curiosity": 0.55,
            "formality": 0.35
        }
    }
}
```

**Validation**:
- trait_name must be one of: humor, energy, curiosity, formality
- new_value must be between 0.0 and 1.0

### GET `/api/friendship/drift/stats`

Get drift statistics for all traits.

**Query Parameters**:
- `user_id` (int, default=1)

**Response**:
```json
{
    "success": true,
    "user_id": 1,
    "current_traits": {
        "humor": 0.65,
        "energy": 0.58,
        "curiosity": 0.55,
        "formality": 0.35
    },
    "drift_stats": {
        "humor": {
            "drift_count": 12,
            "total_change": 0.15,
            "average_change": 0.0125
        }
    },
    "total_drift_events": 45,
    "drift_by_trigger": {
        "conversation_pattern": 40,
        "manual": 5
    }
}
```

### GET `/api/friendship/drift/recent`

Get recent drift events.

**Query Parameters**:
- `user_id` (int, default=1)
- `limit` (int, default=10)

**Response**:
```json
{
    "success": true,
    "user_id": 1,
    "recent_drifts": [
        {
            "trait_name": "humor",
            "change_amount": 0.03,
            "trigger_type": "conversation_pattern",
            "timestamp": "2024-01-15T16:00:00"
        }
    ],
    "count": 1
}
```

## Integration Guide

### Automatic Integration

Drift is automatically calculated when conversations end. No manual intervention required.

**Flow**:
1. User starts conversation
2. User and bot exchange messages
3. User ends conversation
4. `conversation_manager.end_conversation()` is called
5. Drift calculator analyzes the conversation
6. Traits are adjusted based on patterns
7. Drift events are saved to database

### In Conversation Manager

```python
from services.personality_drift_calculator import personality_drift_calculator

def end_conversation(self, conversation_id: int, db: Session):
    # ... existing code ...

    # Calculate and apply personality drift
    drift_events = personality_drift_calculator.calculate_drift_after_conversation(
        personality, conversation, db
    )

    logger.info(f"Applied {len(drift_events)} personality drifts")
```

### Manual Adjustment

For user customization features (e.g., personality sliders in UI):

```python
from services.personality_drift_calculator import manual_trait_adjustment

# User adjusts humor slider to 0.8
drift_event = manual_trait_adjustment(
    personality,
    "humor",
    0.8,
    db
)
```

## Usage Examples

### Example 1: Tracking Humor Evolution

```python
from services.personality_drift_calculator import personality_drift_calculator

# Get humor timeline
timeline = personality_drift_calculator.get_trait_timeline(
    user_id=1,
    trait_name="humor",
    db=db
)

# Visualize how humor changed over time
for point in timeline:
    print(f"{point['timestamp']}: {point['value']:.2f} ({point['change']:+.2f})")
    print(f"  Reason: {', '.join(point['reasons'])}")
```

**Output**:
```
2024-01-10T10:00:00: 0.53 (+0.03)
  Reason: User laughed 3 times
2024-01-12T14:00:00: 0.56 (+0.03)
  Reason: User laughed 3 times, User showed enthusiasm
2024-01-13T16:00:00: 0.55 (-0.01)
  Reason: Discussed 3 deep topics
```

### Example 2: Drift Summary Dashboard

```python
# Get complete drift summary
summary = personality_drift_calculator.get_drift_summary(user_id=1, db=db)

print(f"Total personality changes: {summary['total_drifts']}")

for trait, stats in summary['by_trait'].items():
    print(f"\n{trait.capitalize()}:")
    print(f"  Current: {stats['current_value']:.2f}")
    print(f"  Original: {stats['original_value']:.2f}")
    print(f"  Total change: {stats['total_change']:+.2f}")
    print(f"  Changes: {stats['drift_count']}")
```

**Output**:
```
Total personality changes: 45

Humor:
  Current: 0.65
  Original: 0.50
  Total change: +0.15
  Changes: 12

Energy:
  Current: 0.58
  Original: 0.50
  Total change: +0.08
  Changes: 10
```

### Example 3: Conversation Analysis

```python
# After a conversation ends, drift is automatically calculated
# But you can see what happened:

from services.personality_drift_calculator import personality_drift_calculator

# Get recent drifts
recent = personality_drift_calculator.get_drift_history(
    user_id=1,
    db=db,
    limit=5
)

for drift in recent:
    details = drift.get_trigger_details()
    print(f"{drift.trait_name}: {drift.change_amount:+.3f}")
    for reason in details.get('reasons', []):
        print(f"  - {reason}")
```

**Output**:
```
humor: +0.030
  - User laughed 3 times
energy: +0.010
  - Long conversation with 15 messages
curiosity: +0.030
  - User asked 4 questions
formality: -0.030
  - User used casual language 5 times
```

## Testing

### Run Tests

```bash
cd backend
pytest tests/test_personality_drift.py -v
```

### Test Coverage

The test suite includes 50+ test cases covering:

#### Drift Calculation
- ✅ Conversation analysis (laughter, feelings, questions, casual/formal language)
- ✅ Humor drift (increases with laughter, decreases with deep topics)
- ✅ Energy drift (increases with long conversations, decreases with short messages)
- ✅ Curiosity drift (increases with questions and feelings shared)
- ✅ Formality drift (decreases with casual language and personal topics)

#### Drift Bounding
- ✅ Traits cannot exceed maximum (1.0)
- ✅ Traits cannot go below minimum (0.0)

#### Manual Adjustment
- ✅ Manual trait adjustment works
- ✅ Validates trait name
- ✅ Validates value range

#### Drift Tracking
- ✅ Drift history retrieval
- ✅ Drift history filtering by trait
- ✅ Drift summary generation
- ✅ Trait timeline generation

#### Persistence
- ✅ Drift events saved to database
- ✅ Drift events contain correct data
- ✅ Drift reasons stored in trigger_details

#### Edge Cases
- ✅ Empty conversations
- ✅ Conversations with no triggers
- ✅ Extreme trait values

## Best Practices

### For Backend Developers

1. **Don't Bypass Drift System**
   ```python
   # Bad - directly modifying traits
   personality.humor = 0.8

   # Good - use manual adjustment
   manual_trait_adjustment(personality, "humor", 0.8, db)
   ```

2. **Check Drift History for Debugging**
   ```python
   # If personality seems off, check what happened
   history = get_drift_history(user_id, db, limit=20)
   for drift in history:
       print(f"{drift.trait_name}: {drift.change_amount:+.3f}")
   ```

3. **Monitor Drift Velocity**
   ```python
   # Check if traits are changing too fast
   summary = get_drift_summary(user_id, db)
   for trait, stats in summary['by_trait'].items():
       if abs(stats['average_change']) > 0.05:
           logger.warning(f"{trait} changing too quickly")
   ```

### For Frontend Developers

1. **Visualize Drift Timeline**
   - Show trait evolution over time
   - Line chart with trait values
   - Highlight major changes

2. **Show Recent Changes**
   - "Your bot became 10% funnier!"
   - Display reasons for changes
   - Make drift visible to user

3. **Personality Customization**
   - Allow manual adjustments via sliders
   - Show current vs original values
   - Preview personality changes

4. **Drift Notifications**
   ```javascript
   // Check for recent significant drifts
   const recentDrifts = await fetch('/api/friendship/drift/recent?limit=5');

   recentDrifts.forEach(drift => {
       if (Math.abs(drift.change_amount) >= 0.05) {
           showNotification(`Your bot's ${drift.trait_name} changed significantly!`);
       }
   });
   ```

### For System Designers

1. **Balance Drift Speed**
   - Too fast: Personality feels unstable
   - Too slow: No perceptible change
   - Current: 0.01-0.05 per conversation is reasonable

2. **Monitor Long-term Drift**
   - Traits shouldn't max out too quickly
   - Should take 20-30 conversations to move from 0.5 to 0.8
   - Check average drift per conversation

3. **Provide Reset Option**
   - Allow users to reset personality to defaults
   - Or reset individual traits
   - Keep drift history even after reset

4. **Test Edge Cases**
   - Users who never laugh
   - Users who only send short messages
   - Users with very long conversations
   - Ensure reasonable drift in all cases

## Drift Velocity Analysis

### Typical Drift Rates

| Scenario | Conversations | Expected Change | Result |
|----------|--------------|-----------------|--------|
| User laughs often | 10 | +0.01 to +0.03 per convo | Humor: 0.50 → 0.65 |
| User is very engaged | 15 | +0.01 per convo | Energy: 0.50 → 0.65 |
| User asks questions | 20 | +0.01 to +0.03 per convo | Curiosity: 0.50 → 0.70 |
| User is very casual | 10 | -0.01 to -0.03 per convo | Formality: 0.50 → 0.35 |

### Bounding Effects

When traits approach limits (0.0 or 1.0), further drift in that direction becomes impossible:

```python
# Example: Humor at 0.98
drift_requested = +0.05  # Would go to 1.03
drift_actual = +0.02     # Bounded at 1.0
```

The `trigger_details` JSON includes `bounded: true` when this happens.

## Troubleshooting

### Problem: Traits Not Changing

**Possible Causes**:
1. No conversations happening
2. Conversations too short or neutral
3. No drift triggers detected

**Debug**:
```python
# Check if drift calculator is running
from services.conversation_manager import conversation_manager

# Add debug logging in end_conversation
logger.info(f"Drift events created: {len(drift_events)}")
```

**Solution**:
- Ensure conversations are completing normally
- Check that messages contain drift triggers
- Verify drift calculator is called in conversation_manager

### Problem: Traits Changing Too Fast

**Possible Causes**:
1. Drift amounts too large
2. Multiple triggers in every conversation

**Debug**:
```python
# Check recent drifts
recent = get_drift_history(user_id, db, limit=10)
for drift in recent:
    print(f"{drift.trait_name}: {drift.change_amount:+.3f}")
```

**Solution**:
- Reduce drift amounts (DRIFT_AMOUNT_SMALL, MEDIUM, LARGE)
- Increase trigger thresholds
- Add cooldown period between drifts

### Problem: Drift Events Not Saving

**Possible Causes**:
1. Database session not committing
2. Relationship not configured
3. Model not imported in database.py

**Debug**:
```python
# Check database directly
drift_count = db.query(PersonalityDrift).count()
print(f"Total drifts in DB: {drift_count}")
```

**Solution**:
- Ensure database.py imports personality_drift model
- Check that drift events are added to session
- Verify db.commit() is called

### Problem: Trait Values Outside Range

**Possible Causes**:
1. Bounding logic not working
2. Manual adjustments bypassing validation

**Debug**:
```python
# Check current trait values
personality = db.query(BotPersonality).filter_by(user_id=1).first()
for trait in ["humor", "energy", "curiosity", "formality"]:
    value = getattr(personality, trait)
    if value < 0 or value > 1:
        print(f"ERROR: {trait} = {value}")
```

**Solution**:
- Always use drift calculator methods
- Don't modify traits directly
- Validate values before setting

## Future Enhancements

### Planned Features

1. **Mood-Based Drift Modulation**
   - Drift amounts vary based on bot's current mood
   - Playful mood = faster humor drift
   - Calm mood = slower energy drift

2. **Friendship Level Multipliers**
   - Higher friendship levels = more responsive drift
   - Level 1-3: 0.5x drift speed (bot still learning)
   - Level 4-7: 1.0x drift speed (normal)
   - Level 8-10: 1.5x drift speed (very attuned)

3. **Drift Decay**
   - Unused traits slowly drift toward neutral (0.5)
   - If user stops laughing, humor slowly decreases
   - Prevents traits from staying extreme forever

4. **Conversation Context Awareness**
   - Different drift rules for different conversation types
   - Homework help = increase formality
   - Play/games = increase humor and energy
   - Emotional support = decrease formality, increase empathy

5. **User Feedback Integration**
   - "Was I too formal?" prompts
   - User can give direct feedback
   - Feedback creates manual drift events

6. **Drift Reversal Protection**
   - Prevent rapid back-and-forth changes
   - If trait changed recently, reduce drift in opposite direction
   - Adds stability to personality

## Conclusion

The Personality Drift System creates a dynamic, evolving chatbot personality that adapts to each user's interaction style. By analyzing conversation patterns and gradually adjusting traits, the bot becomes more personalized over time while maintaining stability and transparency.

**Key Benefits**:
- ✅ Realistic personality evolution
- ✅ Automatic adaptation to user style
- ✅ Transparent and trackable changes
- ✅ Bounded and stable drift
- ✅ Complete drift history
- ✅ Manual adjustment capability
- ✅ Comprehensive API coverage
- ✅ 50+ test cases

The system strikes a balance between adaptability and stability, ensuring the bot's personality evolves meaningfully without becoming erratic or unpredictable.
