# FriendshipMeter Component

## Overview

The FriendshipMeter is a React component that displays friendship level progression with a visual progress bar. It shows the user's current friendship level with the bot and their progress toward the next level.

## Component Location

**File**: `src/renderer/components/FriendshipMeter.tsx`

## Features

### 1. Visual Progress Display

- **Progress Bar**: Animated gradient progress bar showing percentage toward next level
- **Level Icons**: Emoji indicators that change based on friendship level:
  - 🌱 New Friend (Levels 1-2)
  - 🌿 Good Friend (Levels 3-4)
  - 🌳 Close Friend (Levels 5-6)
  - ⭐ Best Friend (Levels 7-8)
  - 👑 Lifelong Friend (Levels 9-10)

### 2. Level Progression Information

The component displays:
- Current friendship level (1-10)
- Level name/title
- Progress percentage to next level
- Conversations required vs. conversations completed
- Maximum level indicator when level 10 is reached

### 3. Statistics Display

Shows key engagement metrics:
- **Total Conversations**: Total number of chat sessions
- **Total Messages**: All messages exchanged
- **Last Interaction**: Timestamp of most recent conversation

### 4. Level Thresholds

The progression system uses the following conversation thresholds:

| Level | Conversations Required |
|-------|----------------------|
| 1     | 0                    |
| 2     | 5                    |
| 3     | 15                   |
| 4     | 30                   |
| 5     | 50                   |
| 6     | 75                   |
| 7     | 100                  |
| 8     | 125                  |
| 9     | 150                  |
| 10    | 151+                 |

## Component Interface

### Props

```typescript
interface FriendshipMeterProps {
  friendshipLevel: number;  // Current level (1-10)
  stats: PersonalityStats;  // Statistics object
}
```

### PersonalityStats Type

```typescript
interface PersonalityStats {
  totalConversations: number;
  totalMessages: number;
  daysSinceMet: number;
  currentStreak: number;
  lastInteraction?: string;  // ISO date string
}
```

## Usage

The FriendshipMeter is integrated into the ProfilePanel component:

```tsx
import { FriendshipMeter } from './FriendshipMeter';

// In ProfilePanel
<FriendshipMeter
  friendshipLevel={personality.friendshipLevel}
  stats={personality.stats}
/>
```

## Styling

The component uses **Tailwind CSS** for styling with:
- Gradient backgrounds (purple/blue theme)
- Smooth animations and transitions
- Responsive grid layout for statistics
- Rounded corners and subtle borders
- Hover effects

### Color Palette

- **Primary Gradient**: Purple-to-blue (`from-purple-500 to-blue-500`)
- **Background**: Light purple/blue gradient (`from-purple-50 to-blue-50`)
- **Accents**: Purple borders and highlights
- **Text**: Gray scale for readability

## Backend Integration

### API Endpoint

**Endpoint**: `GET /api/personality`

**Query Parameters**:
- `user_id` (int, default=1)

**Response**:
```json
{
  "name": "BotName",
  "traits": { ... },
  "friendship_level": 3,
  "total_conversations": 18,
  "mood": "happy",
  "quirks": [...],
  "interests": [...],
  "catchphrase": "...",
  "stats": {
    "totalConversations": 18,
    "totalMessages": 142,
    "daysSinceMet": 7,
    "currentStreak": 3,
    "lastInteraction": "2025-11-17T12:30:45.123456"
  }
}
```

### Backend Changes (Task 66)

Updated `backend/routes/personality.py` to include:

1. **Total Messages Calculation**:
   ```python
   total_messages = (
       db.query(Message)
       .join(Conversation)
       .filter(Conversation.user_id == user_id)
       .count()
   )
   ```

2. **Last Interaction Timestamp**:
   ```python
   last_conversation = (
       db.query(Conversation)
       .filter(Conversation.user_id == user_id)
       .order_by(Conversation.timestamp.desc())
       .first()
   )
   last_interaction = (
       last_conversation.timestamp.isoformat() if last_conversation else None
   )
   ```

3. **Updated Response Model**:
   ```python
   class PersonalityResponse(BaseModel):
       stats: Dict[str, int | str | None]  # Flexible type for stats
   ```

### Database Fix

Fixed SQLAlchemy conflict in `models/conversation.py`:
- Renamed `metadata` column to `message_metadata`
- This avoids conflict with SQLAlchemy's reserved `metadata` attribute

```python
# Before
metadata = Column(Text, nullable=True)

# After
message_metadata = Column(Text, nullable=True)
```

## Progress Bar Calculation

The component calculates progress between levels:

```typescript
const getLevelProgress = (): { current: number; next: number; percentage: number } => {
  const levelThresholds = [ /* ... */ ];

  const currentThreshold = levelThresholds.find((t) => t.level === friendshipLevel);
  const nextThreshold = levelThresholds.find((t) => t.level === friendshipLevel + 1);

  const conversationsNeeded = nextThreshold.conversations - currentThreshold.conversations;
  const conversationsProgress = stats.totalConversations - currentThreshold.conversations;
  const percentage = Math.min(100, (conversationsProgress / conversationsNeeded) * 100);

  return { current, next, percentage: Math.max(0, percentage) };
};
```

## Visual Examples

### Level 1-2 (New Friend)
```
🌱 New Friend
Level 1 of 10

Progress to next level: 60%
[████████████░░░░░░░░]
3 / 5 conversations
```

### Level 5-6 (Close Friend)
```
🌳 Close Friend
Level 5 of 10

Progress to next level: 32%
[██████░░░░░░░░░░░░░░]
58 / 75 conversations
```

### Level 10 (Lifelong Friend)
```
👑 Lifelong Friend
Level 10 of 10

🎉 Max level reached!
```

## Edge Cases

The component handles:
- **No conversations yet**: Shows 0% progress
- **Max level reached**: Displays celebration message, no progress bar needed
- **No last interaction**: Gracefully omits the "last chat" timestamp
- **Smooth animations**: All progress changes animate smoothly

## Testing

The component can be tested by:

1. **Viewing in ProfilePanel**: Navigate to the Personality tab
2. **Checking responsiveness**: Resize window to test layout
3. **Verifying data**: Ensure stats match backend data
4. **Progress animation**: Watch progress bar animate when data changes

## Integration Points

The FriendshipMeter integrates with:

1. **ProfilePanel**: Main container for the component
2. **usePersonality Hook**: Fetches personality and stats data
3. **Backend API**: Receives updated stats from FastAPI
4. **Friendship Progression System**: Reflects backend level calculations

## Future Enhancements

Potential improvements:
- [ ] Add animation when level increases
- [ ] Show historical progression chart
- [ ] Display milestones and achievements
- [ ] Add tooltips explaining each stat
- [ ] Show XP-style points in addition to conversations
- [ ] Celebrate level-ups with confetti animation

## Conclusion

The FriendshipMeter component is **fully implemented and functional**. It provides:

✅ Visual progress bar with percentage display
✅ Level icons and descriptive names
✅ Statistics display (conversations, messages, last interaction)
✅ Smooth animations and transitions
✅ Backend integration with personality API
✅ Responsive design with Tailwind CSS
✅ Edge case handling (no data, max level, etc.)

**Task 66 Complete**: Build FriendshipMeter component with progress bar.
