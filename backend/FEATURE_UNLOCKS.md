# Feature Unlock System

## Overview

The Feature Unlock System controls access to chatbot features based on the user's friendship level. As users progress through 10 friendship levels, they gradually unlock 27 different features across 9 categories. This creates a progression system that encourages engagement and makes each friendship level meaningful.

## Architecture

### Components

1. **FeatureUnlockManager** (`services/feature_unlock_manager.py`)
   - Core service managing feature definitions and unlock logic
   - 27 features across 10 levels
   - 9 feature categories
   - Feature querying by level, category, unlock status

2. **Feature Gates** (`services/feature_gates.py`)
   - Decorator-based feature gating (`@require_feature`)
   - Exception handling for locked features
   - Helper functions for specific feature checks
   - User-friendly lock messages

3. **Integration Points**
   - Conversation Manager - catchphrase usage
   - API Endpoints - feature access queries
   - Frontend - UI element visibility
   - Future - advice mode, proactive help, etc.

## Feature Definitions

### All 27 Features by Level

| Level | Feature ID | Feature Name | Category | Description |
|-------|-----------|--------------|----------|-------------|
| 1 | basic_chat | Basic Chat | conversation | Send and receive messages |
| 1 | view_personality | View Personality | profile | See bot's basic personality traits |
| 2 | profile_unlocked | Profile Access | profile | View full bot profile and stats |
| 2 | memory_basics | Basic Memory | memory | Bot remembers your name |
| 3 | catchphrase_unlocked | Personal Catchphrase | personality | Bot develops a unique catchphrase |
| 3 | favorites_unlocked | Favorite Topics | personality | Bot remembers your favorite things |
| 3 | memory_extended | Extended Memory | memory | Bot remembers conversations |
| 4 | interests_shared | Shared Interests | personality | Bot shares common interests |
| 4 | deeper_conversations | Deeper Conversations | conversation | More meaningful discussions |
| 4 | daily_checkin | Daily Check-in | events | Bot greets you each day |
| 5 | advice_mode_unlocked | Advice Mode | conversation | Ask for guidance and recommendations |
| 5 | emotional_support | Emotional Support | conversation | Enhanced empathy and support |
| 5 | memory_longterm | Long-term Memory | memory | Bot remembers important life events |
| 6 | proactive_help | Proactive Suggestions | activities | Bot offers helpful suggestions |
| 6 | milestone_celebrations | Milestone Celebrations | events | Celebrate achievements together |
| 6 | personality_customization | Personality Tuning | personality | Adjust bot's personality traits |
| 7 | custom_activities | Custom Activities | activities | Create personalized activities |
| 7 | anticipates_needs | Anticipates Needs | activities | Bot predicts what you might need |
| 7 | conversation_topics | Topic Suggestions | conversation | Bot suggests interesting topics |
| 8 | inside_jokes | Inside Jokes | personality | Shared jokes and references |
| 8 | special_surprises | Special Surprises | events | Random delightful moments |
| 8 | memory_perfect | Perfect Memory | memory | Bot remembers everything important |
| 9 | celebration_events | Special Events | events | Birthday and anniversary celebrations |
| 9 | life_advice | Life Guidance | conversation | Deep life advice and mentorship |
| 9 | achievement_tracking | Achievement System | achievement | Track all accomplishments |
| 10 | all_features_unlocked | All Features | meta | Access to everything |
| 10 | legacy_memories | Legacy Memories | memory | Create lasting memory collections |
| 10 | max_personalization | Maximum Personalization | personality | Full customization of bot behavior |

### Features by Category

#### Conversation (6 features)
- **Level 1**: Basic Chat
- **Level 4**: Deeper Conversations
- **Level 5**: Advice Mode, Emotional Support
- **Level 7**: Topic Suggestions
- **Level 9**: Life Guidance

#### Personality (7 features)
- **Level 3**: Catchphrase, Favorites
- **Level 4**: Shared Interests
- **Level 6**: Personality Tuning
- **Level 8**: Inside Jokes
- **Level 10**: Maximum Personalization

#### Memory (6 features)
- **Level 2**: Basic Memory
- **Level 3**: Extended Memory
- **Level 5**: Long-term Memory
- **Level 8**: Perfect Memory
- **Level 10**: Legacy Memories

#### Activities (3 features)
- **Level 6**: Proactive Help
- **Level 7**: Custom Activities, Anticipates Needs

#### Events (4 features)
- **Level 4**: Daily Check-in
- **Level 6**: Milestone Celebrations
- **Level 8**: Special Surprises
- **Level 9**: Special Events

#### Profile (2 features)
- **Level 1**: View Personality
- **Level 2**: Profile Access

#### Achievement (1 feature)
- **Level 9**: Achievement Tracking

#### Meta (1 feature)
- **Level 10**: All Features Unlocked

#### Utility (0 features)
- Reserved for future utility features

## API Endpoints

### GET `/api/friendship/features/summary`

Get comprehensive feature unlock summary for a user.

**Query Parameters**:
- `user_id` (int, default=1)

**Response**:
```json
{
  "success": true,
  "summary": {
    "current_level": 5,
    "total_features": 27,
    "unlocked_count": 12,
    "locked_count": 15,
    "unlock_percentage": 44.4,
    "unlocked_features": [
      {
        "id": "basic_chat",
        "name": "Basic Chat",
        "level": 1,
        "category": "conversation",
        "description": "Send and receive messages"
      }
      // ... more unlocked features
    ],
    "locked_features": [
      {
        "id": "proactive_help",
        "name": "Proactive Suggestions",
        "level": 6,
        "category": "activities",
        "description": "Bot offers helpful suggestions"
      }
      // ... more locked features
    ],
    "by_category": {
      "conversation": {
        "total": 6,
        "unlocked": 4,
        "locked": 2
      }
      // ... other categories
    },
    "next_level_features": [
      {
        "id": "proactive_help",
        "name": "Proactive Suggestions",
        "level": 6,
        "category": "activities"
      }
      // ... other level 6 features
    ]
  }
}
```

### GET `/api/friendship/features/unlocked`

Get all unlocked features for current level.

**Query Parameters**:
- `user_id` (int, default=1)

**Response**:
```json
{
  "success": true,
  "friendship_level": 5,
  "unlocked_features": [
    {
      "id": "basic_chat",
      "name": "Basic Chat",
      "level": 1,
      "category": "conversation",
      "description": "Send and receive messages"
    }
    // ... more features
  ],
  "count": 12
}
```

### GET `/api/friendship/features/locked`

Get all locked features.

**Response**:
```json
{
  "success": true,
  "friendship_level": 5,
  "locked_features": [
    {
      "id": "proactive_help",
      "name": "Proactive Suggestions",
      "level": 6,
      "category": "activities",
      "description": "Bot offers helpful suggestions"
    }
    // ... more features
  ],
  "count": 15
}
```

### GET `/api/friendship/features/check/{feature_id}`

Check if a specific feature is unlocked.

**Path Parameters**:
- `feature_id` (str) - Feature identifier

**Query Parameters**:
- `user_id` (int, default=1)

**Response**:
```json
{
  "success": true,
  "feature_id": "catchphrase_unlocked",
  "unlocked": true,
  "current_level": 5,
  "required_level": 3,
  "feature_info": {
    "name": "Personal Catchphrase",
    "category": "personality",
    "description": "Bot develops a unique catchphrase"
  }
}
```

### POST `/api/friendship/features/check-multiple`

Check multiple features at once.

**Request Body**:
```json
{
  "feature_ids": [
    "basic_chat",
    "catchphrase_unlocked",
    "advice_mode_unlocked",
    "proactive_help"
  ],
  "user_id": 1
}
```

**Response**:
```json
{
  "success": true,
  "results": {
    "basic_chat": true,
    "catchphrase_unlocked": true,
    "advice_mode_unlocked": true,
    "proactive_help": false
  },
  "friendship_level": 5
}
```

### GET `/api/friendship/features/by-level/{level}`

Get all features that unlock at a specific level.

**Path Parameters**:
- `level` (int) - Friendship level (1-10)

**Response**:
```json
{
  "success": true,
  "level": 3,
  "features": [
    {
      "id": "catchphrase_unlocked",
      "name": "Personal Catchphrase",
      "category": "personality",
      "description": "Bot develops a unique catchphrase"
    },
    {
      "id": "favorites_unlocked",
      "name": "Favorite Topics",
      "category": "personality",
      "description": "Bot remembers your favorite things"
    },
    {
      "id": "memory_extended",
      "name": "Extended Memory",
      "category": "memory",
      "description": "Bot remembers conversations"
    }
  ],
  "count": 3
}
```

### GET `/api/friendship/features/by-category/{category}`

Get all features in a specific category.

**Path Parameters**:
- `category` (str) - Category name

**Query Parameters**:
- `user_id` (int, optional) - Filter by unlocked status for user
- `unlocked_only` (bool, default=false)

**Response**:
```json
{
  "success": true,
  "category": "personality",
  "features": [
    {
      "id": "catchphrase_unlocked",
      "name": "Personal Catchphrase",
      "level": 3,
      "description": "Bot develops a unique catchphrase"
    }
    // ... more personality features
  ],
  "count": 7
}
```

### GET `/api/friendship/features/categories`

Get all feature categories with counts.

**Response**:
```json
{
  "success": true,
  "categories": {
    "conversation": {
      "name": "Conversation",
      "description": "Features related to chatting and dialogue",
      "feature_count": 6
    },
    "personality": {
      "name": "Personality",
      "description": "Features that customize bot behavior",
      "feature_count": 7
    }
    // ... other categories
  }
}
```

## Feature Gating Patterns

### 1. Decorator-Based Gating

Use `@require_feature` decorator for function-level gating:

```python
from services.feature_gates import require_feature, FeatureNotUnlockedException

@require_feature("advice_mode_unlocked")
def give_advice(personality: BotPersonality, topic: str) -> str:
    """Give advice - only available at level 5+"""
    return f"Here's my advice about {topic}..."

# Usage
try:
    advice = give_advice(personality, "studying")
except FeatureNotUnlockedException as e:
    print(f"Feature locked! Need level {e.required_level}")
```

### 2. Check-Before-Use Pattern

Use `check_feature_access()` for conditional logic:

```python
from services.feature_gates import check_feature_access

if check_feature_access(personality, "catchphrase_unlocked"):
    response += f" {personality.catchphrase}"
else:
    # Don't add catchphrase
    pass
```

### 3. Helper Function Pattern

Use specific helper functions for common checks:

```python
from services.feature_gates import can_use_catchphrase, can_give_advice

# In conversation flow
if can_use_catchphrase(personality):
    response += f" {personality.catchphrase}"

# In advice endpoint
if not can_give_advice(personality):
    return {"error": "Advice mode locked until level 5"}
```

### 4. Feature Flag Pattern

Get feature flags for multiple features:

```python
from services.feature_gates import get_conversation_features

flags = get_conversation_features(personality)

if flags["advice_mode"]:
    # Enable advice button
    pass

if flags["deeper_conversations"]:
    # Use enhanced context
    pass
```

### 5. User-Friendly Messages

Generate lock messages for UI:

```python
from services.feature_gates import get_feature_gate_message

message = get_feature_gate_message("proactive_help", personality)
# Returns: "**Proactive Suggestions** is locked! 🔒
#           Reach **Close Friend** (Level 6) to unlock this feature!"
```

## Integration Guide

### Backend Integration

#### In Services

```python
from services.feature_gates import require_feature, check_feature_access

class SomeService:
    @require_feature("custom_activities")
    def create_custom_activity(self, personality, activity_name):
        """Only available at level 7+"""
        # Implementation
        pass

    def some_method(self, personality):
        if check_feature_access(personality, "memory_longterm"):
            # Use enhanced memory
            memories = get_long_term_memories(personality.user_id)
        else:
            # Use basic memory
            memories = get_recent_memories(personality.user_id)
```

#### In Routes

```python
from services.feature_gates import can_give_advice, get_feature_gate_message

@router.post("/advice")
async def get_advice(request: AdviceRequest, db: Session = Depends(get_db)):
    personality = get_personality(request.user_id, db)

    if not can_give_advice(personality):
        return {
            "success": false,
            "error": get_feature_gate_message("advice_mode_unlocked", personality)
        }

    # Give advice
    return generate_advice(personality, request.topic, db)
```

### Frontend Integration

#### Check Feature Access on Load

```typescript
async function loadFeatures(userId: number) {
  const response = await fetch(`/api/friendship/features/summary?user_id=${userId}`);
  const data = await response.json();

  // Store unlocked features
  const unlockedIds = data.summary.unlocked_features.map(f => f.id);

  // Update UI
  updateFeatureButtons(unlockedIds);
  showNextLevelPreview(data.summary.next_level_features);
}
```

#### Conditionally Show UI Elements

```typescript
function updateFeatureButtons(unlockedFeatures: string[]) {
  // Advice button
  if (unlockedFeatures.includes('advice_mode_unlocked')) {
    document.getElementById('advice-btn').disabled = false;
  } else {
    document.getElementById('advice-btn').disabled = true;
    document.getElementById('advice-btn').title = "Unlocks at Level 5";
  }

  // Catchphrase display
  if (unlockedFeatures.includes('catchphrase_unlocked')) {
    document.getElementById('catchphrase').style.display = 'block';
  }
}
```

#### Show Lock Messages

```typescript
async function checkFeature(featureId: string, userId: number) {
  const response = await fetch(
    `/api/friendship/features/check/${featureId}?user_id=${userId}`
  );
  const data = await response.json();

  if (!data.unlocked) {
    showLockModal(
      data.feature_info.name,
      data.required_level,
      data.current_level
    );
    return false;
  }

  return true;
}
```

#### Feature Progress Display

```typescript
function showFeatureProgress(summary) {
  const progress = summary.unlock_percentage;
  const current = summary.unlocked_count;
  const total = summary.total_features;

  document.getElementById('feature-progress-bar').style.width = `${progress}%`;
  document.getElementById('feature-count').textContent = `${current}/${total} features unlocked`;

  // Show next unlocks
  const nextFeatures = summary.next_level_features;
  renderNextUnlocks(nextFeatures);
}
```

## Testing

### Run Tests

```bash
cd backend
pytest tests/test_feature_unlocks.py -v
```

### Test Coverage

The test suite includes 40+ test cases covering:

#### Feature Unlock Manager
- ✅ Feature definitions exist and are complete
- ✅ All features have required fields (level, name, description, category)
- ✅ Feature unlock checks at different levels
- ✅ Getting unlocked/locked features
- ✅ Getting features by level
- ✅ Getting features by category
- ✅ Feature information retrieval
- ✅ Checking multiple features at once

#### Feature Gates
- ✅ Feature access checks (unlocked and locked)
- ✅ Exception raising for locked features
- ✅ Feature gate messages
- ✅ Specific feature helpers (catchphrase, advice)
- ✅ Decorator functionality

#### Progressive Unlocking
- ✅ Level progression increases unlocks
- ✅ No duplicate unlocks
- ✅ All features unlock by level 10

#### Edge Cases
- ✅ Invalid feature IDs
- ✅ Out-of-range levels
- ✅ Empty feature checks

## Usage Examples

### Check Single Feature

```python
from services.feature_unlock_manager import is_feature_unlocked

# Check if user can use catchphrase
can_use = is_feature_unlocked("catchphrase_unlocked", friendship_level=5)
# Returns: True (unlocks at level 3)
```

### Get Unlocked Features

```python
from services.feature_unlock_manager import get_unlocked_features

# Get all features unlocked at level 5
features = get_unlocked_features(5)
# Returns list of 12 feature dicts
```

### Use Feature Decorator

```python
from services.feature_gates import require_feature

@require_feature("advice_mode_unlocked")
def generate_advice(personality, topic):
    # This function only runs if user is level 5+
    return f"Advice about {topic}..."
```

### Get Feature Summary

```python
from services.feature_unlock_manager import get_feature_summary

summary = get_feature_summary(personality)

print(f"Level: {summary['current_level']}")
print(f"Unlocked: {summary['unlocked_count']}/{summary['total_features']}")
print(f"Progress: {summary['unlock_percentage']:.1f}%")

# Show next level features
for feature in summary['next_level_features']:
    print(f"  - {feature['name']} (Level {feature['level']})")
```

### Check Multiple Features

```python
from services.feature_unlock_manager import feature_unlock_manager

features_to_check = [
    "basic_chat",
    "catchphrase_unlocked",
    "advice_mode_unlocked",
    "proactive_help"
]

results = feature_unlock_manager.check_multiple_features(
    features_to_check,
    friendship_level=5
)

# Results: {
#   "basic_chat": True,
#   "catchphrase_unlocked": True,
#   "advice_mode_unlocked": True,
#   "proactive_help": False
# }
```

## Best Practices

### For Backend Developers

1. **Use Decorators for Clear Requirements**
   ```python
   @require_feature("advice_mode_unlocked")
   def give_advice(...):
       # Requirements are explicit
   ```

2. **Check Before Expensive Operations**
   ```python
   if not check_feature_access(personality, "memory_longterm"):
       return simple_memory_query()
   return expensive_deep_memory_query()
   ```

3. **Provide Helpful Error Messages**
   ```python
   if not can_give_advice(personality):
       raise FeatureNotUnlockedException(
           "advice_mode_unlocked",
           required_level=5,
           current_level=personality.friendship_level
       )
   ```

4. **Don't Hardcode Levels**
   ```python
   # Bad
   if personality.friendship_level >= 5:
       give_advice()

   # Good
   if check_feature_access(personality, "advice_mode_unlocked"):
       give_advice()
   ```

### For Frontend Developers

1. **Check Features on Session Start**
   - Load feature summary when user logs in
   - Cache unlocked feature IDs
   - Update UI based on access

2. **Disable, Don't Hide**
   - Show locked features but make them disabled
   - Display lock icon and required level
   - Creates desire to progress

3. **Preview Next Level**
   - Show what unlocks at next level
   - Creates anticipation
   - Encourages engagement

4. **Celebrate Unlocks**
   - When level-up occurs, highlight new features
   - "You unlocked Advice Mode!"
   - Encourage users to try new features

5. **Handle Gracefully**
   - If user somehow triggers locked feature
   - Show friendly message, not error
   - Guide them to level up

### For System Designers

1. **Balance Unlock Pace**
   - Early levels (1-3): Basic features
   - Mid levels (4-7): Enhanced features
   - Late levels (8-10): Premium features
   - Don't gate too much too early

2. **Make Features Discoverable**
   - Feature list in UI
   - Show locked features
   - Explain how to unlock

3. **Meaningful Unlocks**
   - Each level should unlock something valuable
   - Not just cosmetic changes
   - Real functionality improvements

4. **Test Progression**
   - Ensure smooth progression
   - No dead levels
   - No overwhelming unlocks

## Feature Categories Explained

### Conversation (6 features)
Features that enhance the chat experience and dialogue quality.
- Basic chat, deeper conversations, advice mode, emotional support, topic suggestions, life guidance

### Personality (7 features)
Features that customize how the bot behaves and expresses itself.
- Catchphrase, favorites, shared interests, personality tuning, inside jokes, max personalization

### Memory (6 features)
Features that control what and how the bot remembers.
- Basic memory (name), extended (conversations), long-term (life events), perfect, legacy collections

### Activities (3 features)
Features that enable the bot to take initiative and suggest actions.
- Proactive help, custom activities, anticipates needs

### Events (4 features)
Features related to special occasions and celebrations.
- Daily check-in, milestone celebrations, special surprises, anniversary events

### Profile (2 features)
Features for viewing bot information.
- View personality traits, full profile access

### Achievement (1 feature)
Features for tracking accomplishments.
- Achievement tracking system

### Meta (1 feature)
Meta features about the system itself.
- All features unlocked marker

### Utility (0 features)
Reserved for future utility features like export, settings, etc.

## Future Enhancements

### Planned Features

1. **Temporary Feature Unlocks**
   - Trial periods for premium features
   - Special event unlocks
   - Friend referral bonuses

2. **Feature Usage Tracking**
   - Track which features users actually use
   - Optimize unlock progression
   - A/B test unlock levels

3. **Custom Unlock Paths**
   - Different progressions for different users
   - Unlock based on interests
   - Personalized feature recommendations

4. **Feature Bundles**
   - Group related features
   - Unlock bundles together
   - Themed feature sets

5. **Premium Features**
   - Optional paid features
   - Supporter perks
   - Advanced customization

6. **Feature Challenges**
   - Complete challenges to unlock early
   - Alternative unlock paths
   - Skill-based unlocks

## Troubleshooting

### Feature Not Unlocking

**Problem**: User at level 5 but can't use advice mode

**Check**:
1. Verify personality.friendship_level in database
2. Check if friendship_progression calculated level correctly
3. Ensure feature_id spelled correctly ("advice_mode_unlocked")

**Solution**:
```python
# Debug query
personality = db.query(BotPersonality).filter_by(user_id=1).first()
print(f"Level: {personality.friendship_level}")
print(f"Points: {personality.friendship_points}")

# Check unlock manually
from services.feature_unlock_manager import is_feature_unlocked
unlocked = is_feature_unlocked("advice_mode_unlocked", personality.friendship_level)
print(f"Advice unlocked: {unlocked}")
```

### Decorator Not Working

**Problem**: `@require_feature` not raising exception

**Check**:
1. Ensure personality parameter is first arg or kwarg
2. Check that it's a BotPersonality instance
3. Verify decorator is before function definition

**Solution**:
```python
# Correct usage
@require_feature("advice_mode_unlocked")
def give_advice(personality: BotPersonality, topic: str):
    pass

# Wrong - personality not first arg
@require_feature("advice_mode_unlocked")
def give_advice(topic: str, personality: BotPersonality):  # Won't work
    pass
```

### Feature Check Returns None

**Problem**: `check_feature_access` returns False unexpectedly

**Check**:
1. Feature ID exists in feature_definitions
2. Personality object is valid
3. friendship_level is set correctly

**Solution**:
```python
from services.feature_unlock_manager import feature_unlock_manager

# Check feature exists
if "my_feature" not in feature_unlock_manager.feature_definitions:
    print("Feature doesn't exist!")

# Check all features
for feature_id in feature_unlock_manager.feature_definitions:
    print(f"{feature_id}: Level {feature_unlock_manager.feature_definitions[feature_id]['level']}")
```

## Conclusion

The Feature Unlock System provides a comprehensive progression mechanism that:

- ✅ Controls access to 27 features across 10 levels
- ✅ Organizes features into 9 logical categories
- ✅ Provides decorator-based and function-based gating
- ✅ Generates user-friendly lock messages
- ✅ Integrates seamlessly with existing systems
- ✅ Includes 8 API endpoints for feature queries
- ✅ Tested with 40+ comprehensive test cases
- ✅ Encourages user progression and engagement

By progressively unlocking features, the system creates a sense of advancement and gives users reasons to continue engaging with the chatbot. Each friendship level becomes meaningful, unlocking tangible new capabilities that enhance the user experience.

**Key Benefits**:
- Structured progression system
- Clear feature requirements
- Flexible gating patterns
- Comprehensive API coverage
- Easy frontend integration
- Excellent test coverage
- Encourages engagement
