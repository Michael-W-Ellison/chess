# Friendship Progression System

## Overview

The Friendship Progression System tracks and manages the developing relationship between the user and their chatbot companion. Unlike simple conversation counting, this system uses a comprehensive **points-based approach** that rewards various types of engagement and interaction quality.

## Architecture

### Components

1. **FriendshipProgressionManager** (`services/friendship_progression.py`)
   - Core service managing friendship logic
   - Handles points calculation and level progression
   - Provides progression tracking and analytics

2. **BotPersonality Model** (`models/personality.py`)
   - Stores `friendship_level` (1-10)
   - Stores `friendship_points` (accumulated points)
   - Tracks `total_conversations` for historical data

3. **API Endpoints** (`routes/personality.py`)
   - `/api/friendship/progress` - Get current progress
   - `/api/friendship/add-points` - Award points for activities
   - `/api/friendship/levels` - Get all level definitions
   - `/api/friendship/history` - Get historical stats
   - `/api/friendship/simulate/{level}` - Simulate progression

## Friendship Levels

The system has **10 distinct friendship levels**, each with unique characteristics:

### Level 1: Stranger 👋
- **Points Required:** 0 - 99
- **Description:** Just met! Getting to know each other.
- **Perks:** Basic conversations

### Level 2: Acquaintance 🙂
- **Points Required:** 100 - 299
- **Description:** Starting to get familiar with each other.
- **Perks:** Basic conversations, Remembers your name

### Level 3: Buddy 😊
- **Points Required:** 300 - 599
- **Description:** Becoming friends! More comfortable together.
- **Perks:** Casual conversations, Personal catchphrase, Remembers favorites

### Level 4: Friend 🤗
- **Points Required:** 600 - 999
- **Description:** Good friends! Enjoy chatting together.
- **Perks:** Deeper conversations, Shares interests, Remembers goals

### Level 5: Good Friend 😄
- **Points Required:** 1,000 - 1,599
- **Description:** Close friends! Trust is building.
- **Perks:** Personal advice, Emotional support, Remembers achievements

### Level 6: Close Friend 🥰
- **Points Required:** 1,600 - 2,399
- **Description:** Very close! Strong bond forming.
- **Perks:** Deep understanding, Proactive help, Celebrates milestones

### Level 7: Best Friend 💙
- **Points Required:** 2,400 - 3,499
- **Description:** Best friends! Always there for each other.
- **Perks:** Complete trust, Anticipates needs, Custom activities

### Level 8: Bestie 💖
- **Points Required:** 3,500 - 4,999
- **Description:** Inseparable besties! Deep connection.
- **Perks:** Inside jokes, Shared experiences, Special surprises

### Level 9: Soul Friend ✨
- **Points Required:** 5,000 - 7,499
- **Description:** Soul-level friendship! Incredibly close.
- **Perks:** Deep understanding, Life advice, Celebration events

### Level 10: Lifelong Companion 🌟
- **Points Required:** 7,500+
- **Description:** Lifelong companions! Unbreakable bond.
- **Perks:** All features unlocked, Maximum personalization, Legacy memories

## Point Rewards System

### Conversation-Based Rewards

| Activity | Points | Description |
|----------|--------|-------------|
| `message_sent` | 5 | Each message in conversation |
| `conversation_completed` | 20 | Completing a conversation |
| `long_conversation` | 30 | 10+ messages in conversation |
| `quality_conversation` | 40 | 20+ messages in conversation |

### Engagement Rewards

| Activity | Points | Description |
|----------|--------|-------------|
| `daily_checkin` | 15 | First conversation of the day |
| `streak_3_days` | 50 | 3 consecutive days |
| `streak_7_days` | 100 | 7 consecutive days |
| `streak_30_days` | 300 | 30 consecutive days |

### Trust and Sharing Rewards

| Activity | Points | Description |
|----------|--------|-------------|
| `shares_personal_info` | 25 | Shares favorite, goal, etc. |
| `shares_achievement` | 35 | Shares accomplishment |
| `shares_feelings` | 30 | Expresses emotions |
| `asks_for_advice` | 20 | Seeks bot's advice |

### Response Quality Rewards

| Activity | Points | Description |
|----------|--------|-------------|
| `positive_feedback` | 40 | User gives positive response |
| `thanks_bot` | 15 | User says thanks |
| `laughs_at_joke` | 10 | User responds to humor |

### Milestone Rewards

| Activity | Points | Description |
|----------|--------|-------------|
| `completes_profile` | 100 | Fills out profile info |
| `first_goal_set` | 50 | Sets first goal |
| `goal_achieved` | 75 | Achieves a goal |
| `week_active` | 150 | Active for a week |
| `month_active` | 500 | Active for a month |

## Usage Examples

### 1. Adding Friendship Points

```python
from services.friendship_progression import add_friendship_points

# Award points for a completed conversation
personality, level_increased, event_info = add_friendship_points(
    personality=bot_personality,
    activity="conversation_completed",
    db=db_session
)

if level_increased:
    print(f"Level up! Now {event_info['level_info']['name']}")
    print(f"Message: {event_info['message']}")
```

### 2. Getting Friendship Progress

```python
from services.friendship_progression import get_friendship_progress

progress = get_friendship_progress(bot_personality)

print(f"Current Level: {progress['current_level']}")
print(f"Current Points: {progress['current_points']}")
print(f"Points to Next Level: {progress['points_to_next_level']}")
print(f"Progress: {progress['progress_percentage']}%")
```

### 3. Custom Point Awards

```python
# Award custom points for special events
personality, level_increased, event_info = add_friendship_points(
    personality=bot_personality,
    activity="special_event",
    db=db_session,
    custom_points=200  # Custom amount
)
```

## API Endpoints

### GET `/api/friendship/progress`

Get detailed friendship progression information.

**Query Parameters:**
- `user_id` (int, default=1): User ID

**Response:**
```json
{
  "success": true,
  "progress": {
    "current_level": 3,
    "current_level_info": {
      "level": 3,
      "name": "Buddy",
      "min_points": 300,
      "max_points": 599,
      "description": "Becoming friends! More comfortable together.",
      "perks": ["Casual conversations", "Personal catchphrase", "Remembers favorites"],
      "icon": "😊"
    },
    "current_points": 450,
    "points_to_next_level": 150,
    "next_level_threshold": 600,
    "progress_percentage": 50.0,
    "is_max_level": false
  }
}
```

### GET `/api/friendship/levels`

Get information about all friendship levels.

**Response:**
```json
{
  "success": true,
  "levels": [
    {
      "level": 1,
      "name": "Stranger",
      "min_points": 0,
      "max_points": 99,
      "description": "Just met! Getting to know each other.",
      "perks": ["Basic conversations"],
      "icon": "👋"
    },
    // ... all 10 levels
  ]
}
```

### GET `/api/friendship/level/{level}`

Get information about a specific friendship level.

**Path Parameters:**
- `level` (int, 1-10): Friendship level

**Response:**
```json
{
  "success": true,
  "level_info": {
    "level": 5,
    "name": "Good Friend",
    "min_points": 1000,
    "max_points": 1599,
    "description": "Close friends! Trust is building.",
    "perks": ["Personal advice", "Emotional support", "Remembers achievements"],
    "icon": "😄"
  }
}
```

### POST `/api/friendship/add-points`

Add friendship points for an activity.

**Query Parameters:**
- `user_id` (int, default=1): User ID

**Request Body:**
```json
{
  "activity": "conversation_completed",
  "custom_points": null  // Optional custom points
}
```

**Response:**
```json
{
  "success": true,
  "personality": {
    // Full personality object
    "friendship_level": 3,
    "friendship_points": 350,
    // ...
  },
  "level_increased": false,
  "event_info": {
    "activity": "conversation_completed",
    "points_earned": 20,
    "old_points": 330,
    "new_points": 350,
    "old_level": 3,
    "new_level": 3,
    "level_increased": false
  }
}
```

### GET `/api/friendship/activities`

Get all available activities and their point values.

**Response:**
```json
{
  "success": true,
  "activities": {
    "message_sent": 5,
    "conversation_completed": 20,
    "long_conversation": 30,
    "quality_conversation": 40,
    "daily_checkin": 15,
    // ... all activities
  }
}
```

### GET `/api/friendship/history`

Get friendship progression history summary.

**Query Parameters:**
- `user_id` (int, default=1): User ID

**Response:**
```json
{
  "success": true,
  "history": {
    "total_points_earned": 1250,
    "current_level": 5,
    "total_conversations": 75,
    "days_active": 30,
    "avg_points_per_day": 41.7,
    "avg_points_per_conversation": 16.7,
    "account_created": "2025-01-01T00:00:00",
    "last_updated": "2025-01-31T12:00:00"
  }
}
```

### GET `/api/friendship/simulate/{target_level}`

Simulate how many points/activities needed for a target level.

**Path Parameters:**
- `target_level` (int, 1-10): Target friendship level

**Response:**
```json
{
  "success": true,
  "simulation": {
    "target_level": 7,
    "level_name": "Best Friend",
    "points_required": 2400,
    "estimated_activities": {
      "message_sent": 480.0,
      "conversation_completed": 120.0,
      "daily_checkin": 160.0,
      "quality_conversation": 60.0,
      // ... estimates for all activities
    },
    "level_info": {
      // Full level 7 information
    }
  }
}
```

## Integration Guide

### In Conversation Flow

```python
from services.friendship_progression import add_friendship_points

async def handle_message(message, personality, db):
    """Handle incoming message and award friendship points"""

    # Award points for message
    add_friendship_points(personality, "message_sent", db)

    # Check conversation length
    if conversation_length >= 20:
        add_friendship_points(personality, "quality_conversation", db)
    elif conversation_length >= 10:
        add_friendship_points(personality, "long_conversation", db)

    # Check for personal sharing
    if contains_personal_info(message):
        add_friendship_points(personality, "shares_personal_info", db)

    # Check for positive feedback
    if is_positive_feedback(message):
        add_friendship_points(personality, "positive_feedback", db)
```

### In Daily Check-in

```python
from datetime import datetime, timedelta

async def check_daily_login(user_id, personality, db):
    """Award points for daily check-in"""

    # Check if this is first conversation today
    last_conversation = get_last_conversation(user_id, db)

    if not last_conversation or last_conversation.date() < datetime.now().date():
        # First conversation today
        add_friendship_points(personality, "daily_checkin", db)

        # Check for streaks
        streak_days = calculate_streak(user_id, db)

        if streak_days >= 30:
            add_friendship_points(personality, "streak_30_days", db)
        elif streak_days >= 7:
            add_friendship_points(personality, "streak_7_days", db)
        elif streak_days >= 3:
            add_friendship_points(personality, "streak_3_days", db)
```

### In Profile Updates

```python
async def update_user_profile(user_id, profile_data, personality, db):
    """Award points when user completes their profile"""

    # Check if profile is now complete
    if is_profile_complete(profile_data):
        add_friendship_points(personality, "completes_profile", db)

    # Award points for sharing specific info
    if "favorite" in profile_data:
        add_friendship_points(personality, "shares_personal_info", db)
```

## Design Philosophy

### Multi-Factor Progression

The friendship system considers multiple factors:

1. **Frequency** - Regular interaction builds friendship
2. **Quality** - Longer, more meaningful conversations earn more points
3. **Trust** - Sharing personal information deepens the bond
4. **Consistency** - Daily streaks show commitment
5. **Milestones** - Special achievements are celebrated

### Balanced Progression

- **Early levels** (1-3) progress quickly to encourage engagement
- **Middle levels** (4-7) require sustained interaction
- **Late levels** (8-10) are prestigious achievements

### Time Estimates

Based on average daily activity:

| Level | Typical Time | Points Required |
|-------|-------------|-----------------|
| 1-2 | 1-2 days | 100 |
| 2-3 | 3-5 days | 300 |
| 3-4 | 1 week | 600 |
| 4-5 | 2-3 weeks | 1,000 |
| 5-6 | 1 month | 1,600 |
| 6-7 | 2 months | 2,400 |
| 7-8 | 3 months | 3,500 |
| 8-9 | 4-5 months | 5,000 |
| 9-10 | 6+ months | 7,500 |

## Testing

Run the test suite:

```bash
cd backend
pytest tests/test_friendship_progression.py -v
```

### Test Coverage

- ✅ Level definitions and thresholds
- ✅ Points-to-level calculation
- ✅ Point addition and accumulation
- ✅ Level-up detection and events
- ✅ Progress tracking
- ✅ History and analytics
- ✅ Edge cases and error handling

## Future Enhancements

### Planned Features

1. **Friendship Events**
   - Special celebrations on level-ups
   - Friendship anniversaries
   - Milestone achievements

2. **Bonus Multipliers**
   - Weekend bonuses
   - Birthday multipliers
   - Special event boosts

3. **Regression Prevention**
   - Points don't decrease
   - Inactivity doesn't reduce level
   - Optional "maintain friendship" activities

4. **Social Features**
   - Compare progression with friends
   - Leaderboards (optional)
   - Friendship badges

5. **Personalized Rewards**
   - Unlock custom bot features at levels
   - Special conversation modes
   - Exclusive content

## Database Schema

### BotPersonality Table

```sql
CREATE TABLE bot_personality (
    id INTEGER PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL,
    name VARCHAR NOT NULL,

    -- Friendship progression
    friendship_level INTEGER DEFAULT 1 NOT NULL,
    friendship_points INTEGER DEFAULT 0 NOT NULL,
    total_conversations INTEGER DEFAULT 0 NOT NULL,

    -- Other fields...
);
```

## Performance Considerations

- **Point calculations** are O(1) operations
- **Level lookups** use simple comparisons
- **Database updates** are atomic
- **Caching** can be added for frequently accessed data

## Security & Privacy

- Points can only be added, not removed (prevents abuse)
- User data is isolated by user_id
- No external exposure of sensitive progression data
- Custom points require validation

## Conclusion

The Friendship Progression System provides a comprehensive, engaging way to track and reward the developing relationship between users and their chatbot companion. By considering multiple factors beyond simple conversation count, it creates a more meaningful and rewarding experience that encourages quality interaction and long-term engagement.
