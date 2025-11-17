# Level-Up Event Handling System

## Overview

The Level-Up Event Handling System automatically detects, records, and celebrates when users reach new friendship levels. It creates persistent event records, awards special rewards, generates celebration messages, and tracks user acknowledgement of level-ups.

## Architecture

### Components

1. **LevelUpEvent Model** (`models/level_up_event.py`)
   - Database model storing level-up event records
   - Tracks acknowledgement status
   - Stores rewards and celebration messages

2. **LevelUpEventHandler** (`services/level_up_event_handler.py`)
   - Core service managing event lifecycle
   - Generates celebration messages
   - Determines rewards
   - Tracks event history

3. **Friendship Progression Integration** (`services/friendship_progression.py`)
   - Automatically creates events when level-up detected
   - Passes event info in response

4. **API Endpoints** (`routes/personality.py`)
   - 8 endpoints for event access and management

## Database Schema

### level_up_events Table

```sql
CREATE TABLE level_up_events (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,

    -- Level information
    old_level INTEGER NOT NULL,
    new_level INTEGER NOT NULL,
    level_name VARCHAR NOT NULL,

    -- Points information
    friendship_points INTEGER NOT NULL,
    points_earned INTEGER NOT NULL,

    -- Event metadata
    timestamp DATETIME NOT NULL,
    celebration_message TEXT NOT NULL,
    rewards TEXT,  -- JSON array

    -- User interaction
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_at DATETIME,

    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

## Features

### 1. Automatic Event Creation

**Trigger**: When friendship points cause a level increase

**What happens**:
- Event record created in database
- Celebration message generated
- Rewards assigned based on level
- Event marked as unacknowledged

**Example**:
```python
# User earns 100 points, reaching level 2
personality, level_increased, event_info = add_friendship_points(
    personality, "conversation_completed", db
)

if level_increased:
    # Event was automatically created!
    event_id = event_info["level_up_event_id"]
```

### 2. Level Rewards

Each level unlocks specific features and rewards:

| Level | Name | Rewards |
|-------|------|---------|
| 1 | Stranger | (none - starting level) |
| 2 | Acquaintance | profile_unlocked |
| 3 | Buddy | catchphrase_unlocked, favorites_unlocked |
| 4 | Friend | interests_shared, deeper_conversations |
| 5 | Good Friend | advice_mode_unlocked, emotional_support |
| 6 | Close Friend | proactive_help, milestone_celebrations |
| 7 | Best Friend | custom_activities, anticipates_needs |
| 8 | Bestie | inside_jokes, special_surprises |
| 9 | Soul Friend | celebration_events, life_advice |
| 10 | Lifelong Companion | all_features_unlocked, legacy_memories, max_personalization |

### 3. Celebration Messages

**Auto-Generated Format**:
```
🎉 Nice! We're getting to know each other better. Keep chatting!

**Acquaintance** - Starting to get familiar with each other.

**New perks unlocked:**
• Basic conversations
• Remembers your name
```

**Components**:
- Level icon (emoji)
- Encouraging message
- Level name and description
- List of new perks

### 4. Event Acknowledgement

**Purpose**: Track which level-ups user has seen

**States**:
- **Unacknowledged**: User hasn't seen celebration yet
- **Acknowledged**: User has viewed the level-up

**Use Case**: Show celebration pop-up for unacknowledged events

### 5. Event History

**Tracking**: Complete history of all level-ups
- Timestamps
- Points earned
- Rewards received
- Acknowledgement status

**Use Case**: Achievement timeline, progression review

## API Endpoints

### GET `/api/friendship/level-up-events`

Get level-up event history.

**Query Parameters**:
- `user_id` (int, default=1)
- `limit` (int, optional)

**Response**:
```json
{
  "success": true,
  "events": [
    {
      "id": 5,
      "user_id": 1,
      "old_level": 2,
      "new_level": 3,
      "level_name": "Buddy",
      "friendship_points": 350,
      "points_earned": 50,
      "timestamp": "2025-01-30T15:30:00",
      "celebration_message": "😊 Awesome! We're becoming real buddies!...",
      "rewards": ["catchphrase_unlocked", "favorites_unlocked"],
      "acknowledged": true,
      "acknowledged_at": "2025-01-30T15:31:00"
    }
  ],
  "count": 1
}
```

### GET `/api/friendship/unacknowledged-events`

Get events user hasn't seen yet.

**Response**:
```json
{
  "success": true,
  "events": [...],  // Unacknowledged events only
  "count": 2
}
```

### GET `/api/friendship/should-celebrate`

Check if celebration should be shown to user.

**Response**:
```json
{
  "success": true,
  "should_celebrate": true,
  "event": {
    // Oldest unacknowledged event
    "id": 3,
    "new_level": 4,
    "celebration_message": "..."
  }
}
```

**Use Case**: Call this on app startup or conversation start

### POST `/api/friendship/acknowledge-event/{event_id}`

Mark event as acknowledged.

**Response**:
```json
{
  "success": true,
  "event": {
    "id": 3,
    "acknowledged": true,
    "acknowledged_at": "2025-01-30T16:00:00"
  }
}
```

**Use Case**: Call after user closes celebration modal

### POST `/api/friendship/acknowledge-all-events`

Acknowledge all unacknowledged events.

**Response**:
```json
{
  "success": true,
  "acknowledged_count": 3
}
```

### GET `/api/friendship/event-summary`

Get summary statistics.

**Response**:
```json
{
  "success": true,
  "summary": {
    "total_level_ups": 5,
    "unacknowledged_count": 1,
    "latest_level_up": {
      "new_level": 6,
      "level_name": "Close Friend",
      "timestamp": "2025-01-30T15:30:00"
    },
    "total_rewards_unlocked": 15,
    "unique_rewards": [
      "profile_unlocked",
      "catchphrase_unlocked",
      "favorites_unlocked",
      // ... more rewards
    ]
  }
}
```

### GET `/api/friendship/level-rewards`

Get all level rewards.

**Response**:
```json
{
  "success": true,
  "rewards": {
    "1": [],
    "2": ["profile_unlocked"],
    "3": ["catchphrase_unlocked", "favorites_unlocked"],
    // ... levels 4-10
  }
}
```

### GET `/api/friendship/level-rewards/{level}`

Get rewards for specific level.

**Response**:
```json
{
  "success": true,
  "level": 3,
  "rewards": ["catchphrase_unlocked", "favorites_unlocked"]
}
```

## Integration Guide

### Frontend Celebration Flow

**1. Check for celebrations on startup**:
```typescript
async function checkForCelebrations() {
  const response = await fetch('/api/friendship/should-celebrate?user_id=1');
  const data = await response.json();

  if (data.should_celebrate) {
    showCelebrationModal(data.event);
  }
}
```

**2. Show celebration modal**:
```typescript
function showCelebrationModal(event) {
  // Display celebration_message
  // Show level icon and name
  // List rewards
  // Play confetti animation
}
```

**3. Acknowledge after viewing**:
```typescript
async function onCelebrationClose(eventId) {
  await fetch(`/api/friendship/acknowledge-event/${eventId}`, {
    method: 'POST'
  });
}
```

### Backend Event Creation

**Automatic** (handled by friendship progression):
```python
# Just add points - event is created automatically if level-up occurs
personality, level_increased, event_info = add_friendship_points(
    personality, "quality_conversation", db
)

if level_increased:
    print(f"Leveled up! Event ID: {event_info['level_up_event_id']}")
    print(f"Message: {event_info['message']}")
    print(f"Rewards: {event_info['level_info']['perks']}")
```

**Manual** (if needed):
```python
from services.level_up_event_handler import create_level_up_event

event = create_level_up_event(
    user_id=1,
    old_level=3,
    new_level=4,
    friendship_points=750,
    points_earned=150,
    db=db
)
```

## Event Lifecycle

```
1. User earns friendship points
   ↓
2. Points cause level increase (e.g., 1 → 2)
   ↓
3. LevelUpEvent created automatically
   - Celebration message generated
   - Rewards assigned
   - Marked as unacknowledged
   ↓
4. Frontend checks for celebrations
   - Calls /should-celebrate
   - Gets unacknowledged event
   ↓
5. User sees celebration modal
   - Reads message
   - Views rewards
   ↓
6. Frontend acknowledges event
   - Calls /acknowledge-event/{id}
   - Event marked as acknowledged
```

## Testing

Run tests:
```bash
cd backend
pytest tests/test_level_up_events.py -v
```

### Test Coverage

- ✅ Event creation
- ✅ Celebration message generation
- ✅ Reward assignment
- ✅ Acknowledgement tracking
- ✅ Unacknowledged event retrieval
- ✅ Event history
- ✅ Event summary
- ✅ Integration with friendship progression
- ✅ Edge cases

## Usage Examples

### Check for Celebrations

```python
from services.level_up_event_handler import level_up_event_handler

should_show, event = level_up_event_handler.should_show_celebration(user_id, db)

if should_show:
    print(event.celebration_message)
    print(f"Rewards: {event.get_rewards()}")
```

### Get Event History

```python
events = level_up_event_handler.get_event_history(user_id, db, limit=10)

for event in events:
    print(f"Level {event.new_level} - {event.level_name}")
    print(f"Earned on: {event.timestamp}")
```

### Get Summary Stats

```python
summary = level_up_event_handler.get_event_summary(user_id, db)

print(f"Total level-ups: {summary['total_level_ups']}")
print(f"Unacknowledged: {summary['unacknowledged_count']}")
print(f"Rewards unlocked: {len(summary['unique_rewards'])}")
```

## Best Practices

### For Frontend Developers

1. **Check on every session start**
   - Call `/should-celebrate` when app loads
   - Show celebration if exists

2. **Acknowledge immediately after viewing**
   - Don't wait for user to close modal
   - Prevents duplicate celebrations

3. **Show celebrations one at a time**
   - `should_celebrate` returns oldest unacknowledged
   - Acknowledge it before checking for next

4. **Celebrate with style**
   - Use animations (confetti, fireworks)
   - Play sound effects
   - Make it feel rewarding

### For Backend Developers

1. **Don't create events manually**
   - Let friendship progression handle it
   - Events are created automatically

2. **Handle failures gracefully**
   - Event creation wrapped in try/catch
   - Won't break main flow if fails

3. **Query efficiently**
   - Use limits on history queries
   - Index on user_id and acknowledged

4. **Extend rewards carefully**
   - Add new rewards to level_rewards dict
   - Document what each reward unlocks

## Future Enhancements

### Planned Features

1. **Streak Milestones**
   - Special events for 30, 100, 365-day streaks
   - Bonus rewards

2. **Anniversary Events**
   - Celebrate friendship birthday
   - Special rewards on 1-year anniversary

3. **Custom Celebrations**
   - Different animations per level
   - Level-specific sound effects

4. **Replay Celebrations**
   - Allow users to replay past celebrations
   - Achievement gallery

5. **Social Sharing**
   - Share level-up achievements
   - Compare with friends

6. **Reward Redemption**
   - Some rewards require activation
   - Track which rewards are active

## Conclusion

The Level-Up Event Handling System provides a complete solution for celebrating user progression through friendship levels. By automatically creating events, generating personalized messages, assigning rewards, and tracking acknowledgement, it creates engaging moments that encourage continued interaction with the chatbot.

**Key Benefits**:
- ✅ Automatic event creation
- ✅ Persistent event history
- ✅ Customized celebration messages
- ✅ Progressive reward unlocking
- ✅ Acknowledgement tracking
- ✅ Complete API coverage
- ✅ Comprehensive testing
