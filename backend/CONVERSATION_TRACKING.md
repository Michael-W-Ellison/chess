# Conversation Count Tracking System

## Overview

The Conversation Tracking System monitors user engagement, tracks conversation patterns, and automatically awards friendship points for various activities. It integrates seamlessly with the Friendship Progression System to reward quality interactions and consistent engagement.

## Architecture

### Components

1. **ConversationTracker** (`services/conversation_tracker.py`)
   - Core service handling conversation tracking logic
   - Monitors daily check-ins, streaks, and activity patterns
   - Awards friendship points automatically

2. **ConversationManager Integration** (`services/conversation_manager.py`)
   - Calls tracker on conversation start/message/end events
   - Integrates tracking into conversation flow

3. **API Endpoints** (`routes/conversation.py`)
   - `/api/conversation/stats` - Get conversation statistics
   - `/api/conversation/recent` - Get recent conversations
   - `/api/conversation/streak` - Get streak information

4. **Database Models**
   - `Conversation`: Stores conversation metadata
   - `Message`: Stores individual messages
   - `BotPersonality`: Tracks friendship points and total conversations

## Features

### 1. Daily Check-In Tracking

**Automatic Detection:**
- First conversation each day triggers a "daily check-in"
- Awards 15 friendship points
- Subsequent conversations same day don't trigger duplicate check-ins

**Implementation:**
```python
def on_conversation_start(user_id: int, personality: BotPersonality, db: Session):
    """
    Handle conversation start event
    Awards points for daily check-in and streaks
    """
    is_first_today = tracker.is_first_conversation_today(user_id, db)

    if is_first_today:
        add_friendship_points(personality, "daily_checkin", db)  # +15 points
```

**Example Response:**
```json
{
  "is_first_today": true,
  "streak_days": 5,
  "points_awarded": [
    {"activity": "daily_checkin", "points": 15}
  ],
  "streak_bonus": false
}
```

### 2. Streak Tracking

**Streak Definition:**
- Consecutive days with at least one conversation
- Calculated by checking for gaps in conversation dates
- Both current and longest streaks are tracked

**Streak Bonuses:**
- **3-day streak**: +50 friendship points
- **7-day streak**: +100 friendship points
- **30-day streak**: +300 friendship points

**Implementation:**
```python
def calculate_streak(user_id: int, db: Session) -> int:
    """
    Calculate consecutive days streak
    Returns: Number of consecutive days with conversations
    """
    # Get all conversation dates
    # Check for consecutive days backwards from today
    # Return streak count
```

**Streak Calculation Logic:**
1. Get all unique conversation dates
2. Start from today (or yesterday if no conversation today)
3. Count backwards while dates are consecutive
4. Break on first gap

### 3. Message Activity Detection

**Automatic Activity Detection:**

The system automatically detects and rewards these activities in user messages:

| Activity | Trigger Words | Points | Detected Flag |
|----------|--------------|--------|---------------|
| **Thanks Bot** | thank, thanks, thx, ty | 15 | thanked_bot |
| **Laughs at Joke** | lol, haha, hehe, funny, 😂 | 10 | laughed |
| **Shares Feelings** | feel, sad, happy, excited, worried, anxious, scared, nervous, proud, angry, upset | 30 | shared_feelings |
| **Asks for Advice** | what should i, should i, advice, what do you think, help me, can you help | 20 | asked_advice |
| **Positive Feedback** | you're great, you're awesome, you're the best, love talking to you, you're cool, you're nice, you're helpful | 40 | positive_feedback |

**Implementation:**
```python
def on_message_sent(user_id: int, personality: BotPersonality, message: str, db: Session):
    """
    Handle message sent event
    Awards points for message and detects special activities
    """
    # Always award base points for message
    add_friendship_points(personality, "message_sent", db)  # +5 points

    # Detect special activities
    if "thank" in message.lower():
        add_friendship_points(personality, "thanks_bot", db)

    if any(word in message.lower() for word in ["lol", "haha"]):
        add_friendship_points(personality, "laughs_at_joke", db)

    # ... additional detections
```

**Example Response:**
```json
{
  "points_awarded": [
    {"activity": "message_sent", "points": 5},
    {"activity": "thanks_bot", "points": 15},
    {"activity": "shares_feelings", "points": 30}
  ],
  "activities_detected": ["thanked_bot", "shared_feelings"]
}
```

### 4. Conversation Quality Tracking

**Quality Tiers:**

Conversations are categorized by message count:

| Quality | Message Count | Points | Additional Reward |
|---------|--------------|--------|-------------------|
| **Short** | < 10 messages | 20 | conversation_completed |
| **Long** | 10-19 messages | 50 | conversation_completed + long_conversation |
| **Quality** | 20+ messages | 60 | conversation_completed + quality_conversation |

**Implementation:**
```python
def on_conversation_end(conversation_id: int, personality: BotPersonality, db: Session):
    """
    Handle conversation end event
    Awards points based on conversation quality
    """
    message_count = conversation.message_count

    # Base points for completing conversation
    add_friendship_points(personality, "conversation_completed", db)  # +20

    # Quality bonuses
    if message_count >= 20:
        add_friendship_points(personality, "quality_conversation", db)  # +40
    elif message_count >= 10:
        add_friendship_points(personality, "long_conversation", db)  # +30
```

**Example Response:**
```json
{
  "conversation_quality": "quality",
  "message_count": 25,
  "points_awarded": [
    {"activity": "conversation_completed", "points": 20},
    {"activity": "quality_conversation", "points": 40}
  ]
}
```

### 5. Conversation Statistics

**Tracked Metrics:**

- **Total conversations**: Lifetime conversation count
- **Total messages**: Lifetime message count across all conversations
- **Average messages per conversation**: Mean messages per session
- **Average duration**: Mean conversation duration in seconds
- **Days active**: Days since first conversation
- **Current streak**: Current consecutive days streak
- **Longest streak**: Best streak ever achieved
- **Conversations this week**: Count in last 7 days
- **Conversations this month**: Count in last 30 days

**Example Stats Response:**
```json
{
  "success": true,
  "stats": {
    "total_conversations": 47,
    "total_messages": 523,
    "avg_messages_per_conversation": 11.1,
    "avg_duration_seconds": 245.3,
    "days_active": 30,
    "current_streak": 5,
    "longest_streak": 12,
    "conversations_this_week": 8,
    "conversations_this_month": 35,
    "first_conversation": "2025-01-01T10:00:00",
    "last_conversation": "2025-01-30T15:30:00"
  }
}
```

## API Endpoints

### GET `/api/conversation/stats`

Get comprehensive conversation statistics for a user.

**Query Parameters:**
- `user_id` (int, default=1): User ID

**Response:**
```json
{
  "success": true,
  "stats": {
    "total_conversations": 47,
    "total_messages": 523,
    "avg_messages_per_conversation": 11.1,
    "avg_duration_seconds": 245.3,
    "days_active": 30,
    "current_streak": 5,
    "conversations_this_week": 8,
    "conversations_this_month": 35,
    "first_conversation": "2025-01-01T10:00:00",
    "last_conversation": "2025-01-30T15:30:00"
  }
}
```

### GET `/api/conversation/recent`

Get recent conversations.

**Query Parameters:**
- `user_id` (int, default=1): User ID
- `limit` (int, default=10, max=50): Number of conversations to return

**Response:**
```json
{
  "success": true,
  "conversations": [
    {
      "id": 123,
      "user_id": 1,
      "timestamp": "2025-01-30T15:30:00",
      "conversation_summary": "Discussed: homework, soccer, friends",
      "mood_detected": "happy",
      "topics": ["homework", "soccer", "friends"],
      "duration_seconds": 300,
      "message_count": 15
    }
    // ... more conversations
  ],
  "count": 10
}
```

### GET `/api/conversation/streak`

Get current and longest streak information.

**Query Parameters:**
- `user_id` (int, default=1): User ID

**Response:**
```json
{
  "success": true,
  "current_streak": 5,
  "longest_streak": 12
}
```

## Integration with Friendship Progression

### Point Awards Flow

1. **Conversation Start** → Daily check-in points + Streak bonuses
2. **Each Message** → Base points + Activity detection bonuses
3. **Conversation End** → Completion points + Quality bonuses

### Example Session Points Breakdown

**Scenario**: User has 5-day streak, sends quality conversation with 22 messages

```
Conversation Start:
├─ daily_checkin: +15 points
└─ streak_3_days: +50 points

Messages (22 total):
├─ message_sent (×22): +110 points (5 each)
├─ thanks_bot (×2): +30 points (15 each)
├─ laughs_at_joke (×3): +30 points (10 each)
├─ shares_feelings (×1): +30 points
└─ positive_feedback (×1): +40 points

Conversation End:
├─ conversation_completed: +20 points
└─ quality_conversation: +40 points

TOTAL: 365 friendship points earned in one session!
```

## Usage Examples

### Basic Integration

```python
from services.conversation_tracker import (
    on_conversation_start,
    on_message_sent,
    on_conversation_end
)

# When starting conversation
checkin_info = on_conversation_start(user_id, personality, db)
if checkin_info["is_first_today"]:
    print(f"Welcome back! {checkin_info['streak_days']}-day streak!")

# When processing message
message_tracking = on_message_sent(user_id, personality, user_message, db)
for activity in message_tracking["activities_detected"]:
    print(f"Detected: {activity}")

# When ending conversation
end_info = on_conversation_end(conversation_id, personality, db)
print(f"Conversation quality: {end_info['conversation_quality']}")
```

### Getting Statistics

```python
from services.conversation_tracker import get_conversation_stats

stats = get_conversation_stats(user_id, db)

print(f"Total conversations: {stats['total_conversations']}")
print(f"Current streak: {stats['current_streak']} days")
print(f"Average messages: {stats['avg_messages_per_conversation']}")
```

## Database Schema

### Conversations Table

```sql
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    timestamp DATETIME NOT NULL,
    conversation_summary TEXT,
    mood_detected VARCHAR,
    topics TEXT,  -- JSON array
    duration_seconds INTEGER,
    message_count INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### Messages Table

```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY,
    conversation_id INTEGER NOT NULL,
    role VARCHAR NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    flagged BOOLEAN DEFAULT FALSE,
    metadata TEXT,  -- JSON
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);
```

## Testing

Run the test suite:

```bash
cd backend
pytest tests/test_conversation_tracker.py -v
```

### Test Coverage

- ✅ Daily check-in detection
- ✅ Streak calculation (current and longest)
- ✅ Streak bonus awards (3, 7, 30 days)
- ✅ Message activity detection (all types)
- ✅ Conversation quality tiering
- ✅ Points accumulation
- ✅ Statistics calculation
- ✅ Edge cases (no conversations, gaps, etc.)

## Performance Considerations

- **Streak calculation**: O(n) where n = number of conversation days (typically < 365)
- **Activity detection**: O(1) simple string matching
- **Statistics queries**: Optimized with database aggregations
- **Point awards**: Atomic database updates

## Future Enhancements

### Planned Features

1. **Conversation Topics**
   - Track most discussed topics
   - Suggest conversation starters based on history

2. **Time of Day Patterns**
   - Identify preferred conversation times
   - Send notifications at optimal times

3. **Engagement Score**
   - Composite score from multiple metrics
   - Quality vs. quantity weighting

4. **Weekly/Monthly Reports**
   - Summary of conversations and growth
   - Achievements unlocked
   - Streak milestones celebrated

5. **Social Comparisons** (Optional)
   - Compare streaks with friends
   - Leaderboards for engagement

6. **Conversation Insights**
   - Sentiment analysis over time
   - Mood patterns and trends
   - Topic evolution

## Best Practices

### For Developers

1. **Always call tracker methods in correct order:**
   - `on_conversation_start()` before first message
   - `on_message_sent()` for each user message
   - `on_conversation_end()` when closing conversation

2. **Handle errors gracefully:**
   - Tracker methods return empty results on errors
   - Don't let tracking failures break conversation flow

3. **Database transactions:**
   - Tracker automatically commits changes
   - Ensure db session is valid before calling

4. **Testing:**
   - Use in-memory SQLite for unit tests
   - Mock datetime for streak testing

### For API Consumers

1. **Stats caching:**
   - Cache stats responses (update every 5 minutes)
   - Reduces database load for dashboard displays

2. **Pagination:**
   - Use `limit` parameter for recent conversations
   - Maximum 50 conversations per request

3. **Error handling:**
   - Check `success` field in responses
   - Handle 404 for non-existent users

## Conclusion

The Conversation Tracking System provides comprehensive monitoring of user engagement while automatically rewarding quality interactions through the Friendship Progression System. By tracking daily check-ins, streaks, message activities, and conversation quality, it creates a rich engagement loop that encourages consistent, meaningful interactions with the chatbot.

The system is designed to be:
- **Automatic**: No manual intervention needed
- **Transparent**: All tracking visible through API
- **Fair**: Rewards both quantity and quality
- **Scalable**: Efficient database queries
- **Extensible**: Easy to add new activities
