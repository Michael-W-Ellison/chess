# Drift Rate Limiting System

## Overview

The Drift Rate Limiting System prevents personality traits from changing too quickly by enforcing limits on how much drift can occur per conversation and over time periods. This ensures personality stability and prevents erratic behavior.

## Why Rate Limiting?

Without rate limiting:
- Traits could change drastically in a single conversation
- Personality could feel unstable and unpredictable
- User experience would be inconsistent
- Bot could swing between extremes rapidly

With rate limiting:
- ✅ Gradual, natural personality evolution
- ✅ Stable and consistent behavior
- ✅ Prevents gaming the system
- ✅ Realistic personality development

## Rate Limit Configuration

| Limit Type | Value | Description |
|------------|-------|-------------|
| **Per Conversation** | 0.02 | Maximum drift per trait per conversation |
| **Per Day** | 0.05 | Maximum drift per trait in 24 hours |
| **Per Week** | 0.10 | Maximum drift per trait in 7 days |
| **Per Month** | 0.15 | Maximum drift per trait in 30 days |
| **Cooldown Period** | 6 hours | Wait time after large drift (≥0.04) |
| **Large Drift Threshold** | 0.04 | Drift amount considered "large" |

### Example Timeline

With these limits, here's a realistic drift scenario for the humor trait:

| Time | Event | Drift | Daily Total | Monthly Total | Status |
|------|-------|-------|-------------|---------------|--------|
| Day 1, 10am | Funny conversation | +0.02 | 0.02 | 0.02 | ✅ Allowed |
| Day 1, 2pm | More laughs | +0.02 | 0.04 | 0.04 | ✅ Allowed |
| Day 1, 6pm | Try more drift | +0.02 | 0.06 | 0.06 | ❌ Capped to +0.01 (daily limit) |
| Day 2, 10am | New day | +0.02 | 0.02 | 0.08 | ✅ Allowed |
| ... | ... | ... | ... | ... | ... |
| Day 8 | Continue | +0.02 | 0.02 | 0.14 | ✅ Allowed |
| Day 8, later | Try more | +0.02 | 0.04 | 0.16 | ❌ Capped to +0.01 (monthly limit) |

## How It Works

### 1. Conversation Limit Check

```python
# User has funny conversation
requested_drift = +0.05  # Bot wants to increase humor

# Rate limiter caps it
final_drift = +0.02  # Maximum per conversation

# Message: "Drift capped from +0.050 to +0.020 (max per conversation: 0.02)"
```

### 2. Time Period Limit Check

```python
# Check last 30 days
drift_history = [+0.02, +0.03, +0.02, +0.04, +0.03]  # Total: 0.14
requested = +0.05

# Would total 0.19, exceeds 0.15 monthly limit
remaining = 0.15 - 0.14 = 0.01
final_drift = +0.01  # Capped to remaining allowance
```

### 3. Cooldown Check

```python
# Large drift occurred 2 hours ago (+0.05)
cooldown_until = last_large_drift_time + 6 hours
time_remaining = 4 hours

# All drift blocked until cooldown expires
final_drift = 0.0
message = "Trait in cooldown for 4.0 more hours"
```

### 4. Final Application

All limits are checked in sequence, and the most restrictive limit wins:

```python
requested = +0.10

# Check conversation limit: caps to +0.02
# Check daily limit: caps to +0.01 (already used 0.04 today)
# Check weekly limit: OK
# Check monthly limit: OK
# Check cooldown: No cooldown

final_drift = +0.01  # Most restrictive was daily limit
```

## Integration

### Automatic Integration

The rate limiter is automatically integrated into the personality drift calculator. All drift is rate-limited by default:

```python
# In personality_drift_calculator.py
from services.drift_rate_limiter import drift_rate_limiter

# When applying drift
rate_limited_drift, messages = drift_rate_limiter.apply_rate_limits(
    personality,
    trait_name,
    requested_drift,
    db,
    conversation_id,
    enforce_cooldown=True
)

# rate_limited_drift is guaranteed to be within all limits
```

###  Drift Event Tracking

Rate limit information is stored in drift events:

```python
drift_event.set_trigger_details({
    "reasons": ["User laughed 3 times"],
    "requested_change": 0.05,           # Original request
    "rate_limited_change": 0.02,         # After rate limits
    "actual_change": 0.02,              # After bounds check
    "rate_limited": True,               # Was capping applied?
    "bounded": False,                   # Was bounds check applied?
    "limit_messages": [                 # Why it was limited
        "Drift capped from +0.050 to +0.020 (max per conversation: 0.02)"
    ]
})
```

## API Endpoints

### GET `/api/friendship/drift/rate-limits/allowance/{trait_name}`

Get drift allowance for a trait over a time period.

**Query Parameters**:
- `user_id` (int, default=1)
- `period_days` (int, default=30)

**Response**:
```json
{
    "success": true,
    "user_id": 1,
    "trait_name": "humor",
    "allowance": {
        "period_days": 30,
        "max_drift": 0.15,
        "used_drift": 0.08,
        "remaining_drift": 0.07,
        "usage_percentage": 53.3,
        "can_drift": true
    }
}
```

### GET `/api/friendship/drift/rate-limits/all-allowances/{trait_name}`

Get all allowances (daily, weekly, monthly) for a trait.

**Response**:
```json
{
    "success": true,
    "user_id": 1,
    "allowances": {
        "trait_name": "humor",
        "daily": {
            "period_days": 1,
            "max_drift": 0.05,
            "used_drift": 0.02,
            "remaining_drift": 0.03,
            "usage_percentage": 40.0,
            "can_drift": true
        },
        "weekly": {
            "period_days": 7,
            "max_drift": 0.10,
            "used_drift": 0.06,
            "remaining_drift": 0.04,
            "usage_percentage": 60.0,
            "can_drift": true
        },
        "monthly": {
            "period_days": 30,
            "max_drift": 0.15,
            "used_drift": 0.08,
            "remaining_drift": 0.07,
            "usage_percentage": 53.3,
            "can_drift": true
        },
        "per_conversation_limit": 0.02
    }
}
```

### GET `/api/friendship/drift/rate-limits/stats`

Get comprehensive rate limit statistics for all traits.

**Response**:
```json
{
    "success": true,
    "stats": {
        "user_id": 1,
        "traits": {
            "humor": {
                "allowances": {...},
                "in_cooldown": false,
                "cooldown_until": null,
                "cooldown_message": "No cooldown active"
            },
            "energy": {...},
            "curiosity": {...},
            "formality": {...}
        }
    }
}
```

### GET `/api/friendship/drift/rate-limits/cooldown/{trait_name}`

Check if a trait is in cooldown.

**Response**:
```json
{
    "success": true,
    "user_id": 1,
    "trait_name": "humor",
    "in_cooldown": true,
    "cooldown_until": "2024-01-15T18:30:00",
    "message": "Trait humor in cooldown for 3.5 more hours after large drift of +0.050",
    "cooldown_hours": 6.0,
    "large_drift_threshold": 0.04
}
```

### GET `/api/friendship/drift/rate-limits/config`

Get current rate limit configuration.

**Response**:
```json
{
    "success": true,
    "config": {
        "max_drift_per_conversation": 0.02,
        "max_drift_per_day": 0.05,
        "max_drift_per_week": 0.10,
        "max_drift_per_month": 0.15,
        "cooldown_after_large_drift_hours": 6.0,
        "large_drift_threshold": 0.04
    }
}
```

## Usage Examples

### Example 1: Check Remaining Allowance

```python
from services.drift_rate_limiter import drift_rate_limiter

# Before planning drift, check what's allowed
allowance = drift_rate_limiter.get_drift_allowance(
    personality,
    "humor",
    db,
    period_days=1  # Check today
)

print(f"Used: {allowance['used_drift']:.3f}")
print(f"Remaining: {allowance['remaining_drift']:.3f}")
print(f"Can drift: {allowance['can_drift']}")

# Output:
# Used: 0.023
# Remaining: 0.027
# Can drift: True
```

### Example 2: Apply Rate Limits

```python
# This is done automatically in drift calculator, but you can call it:
requested_drift = 0.05

final_drift, messages = drift_rate_limiter.apply_rate_limits(
    personality,
    "humor",
    requested_drift,
    db,
    conversation_id=42,
    enforce_cooldown=True
)

print(f"Requested: {requested_drift:+.3f}")
print(f"Final: {final_drift:+.3f}")
print(f"Messages: {messages}")

# Output:
# Requested: +0.050
# Final: +0.020
# Messages: ['Drift capped from +0.050 to +0.020 (max per conversation: 0.02)']
```

### Example 3: Frontend - Show Drift Budget

```typescript
async function showDriftBudget(userId: number, traitName: string) {
    const response = await fetch(
        `/api/friendship/drift/rate-limits/all-allowances/${traitName}?user_id=${userId}`
    );
    const data = await response.json();

    const { daily, weekly, monthly } = data.allowances;

    console.log(`Drift Budget for ${traitName}:`);
    console.log(`Today: ${daily.remaining_drift.toFixed(3)} / ${daily.max_drift} remaining`);
    console.log(`This week: ${weekly.remaining_drift.toFixed(3)} / ${weekly.max_drift} remaining`);
    console.log(`This month: ${monthly.remaining_drift.toFixed(3)} / ${monthly.max_drift} remaining`);

    // Show warning if approaching limits
    if (daily.usage_percentage > 80) {
        alert(`Daily drift limit almost reached! (${daily.usage_percentage.toFixed(0)}%)`);
    }
}
```

## Testing

### Run Tests

```bash
cd backend
pytest tests/test_drift_rate_limiter.py -v
```

### Test Coverage

The test suite includes 30+ test cases covering:

- ✅ Rate limiter initialization and constants
- ✅ Per-conversation limit enforcement
- ✅ Time period limits (daily, weekly, monthly)
- ✅ Cooldown detection and enforcement
- ✅ Combined limit application
- ✅ Drift allowance calculations
- ✅ Comprehensive statistics
- ✅ Global instance and convenience functions
- ✅ Edge cases (zero drift, independent trait limits)

## Best Practices

### For Backend Developers

1. **Trust the Rate Limiter**
   ```python
   # Don't bypass it
   # Bad - direct assignment
   personality.humor = 0.9

   # Good - goes through drift calculator and rate limiter
   drift_calculator.calculate_drift_after_conversation(...)
   ```

2. **Check Allowances Before Large Operations**
   ```python
   # Before batch operations, check if drift is possible
   allowance = get_drift_allowance(personality, "humor", db)
   if not allowance["can_drift"]:
       logger.warning("No drift allowance remaining")
       return
   ```

3. **Monitor Rate Limit Hits**
   ```python
   # Log when limits are reached frequently
   if abs(rate_limited_drift) < abs(requested_drift):
       metrics.increment("rate_limit_hits", tags={"trait": trait_name})
   ```

### For Frontend Developers

1. **Display Drift Budget**
   - Show users how much drift capacity remains
   - Use progress bars for visual representation
   - Warn when approaching limits

2. **Explain Cooldowns**
   - When drift is blocked, explain why
   - Show countdown timer for cooldown expiry
   - Suggest waiting or trying different interactions

3. **Set Expectations**
   - Don't promise instant personality changes
   - Explain that personality evolves gradually
   - Show drift history to demonstrate progress

## Troubleshooting

### Problem: Personality not changing

**Possible Causes**:
1. Hit rate limits (check allowances)
2. In cooldown period (check cooldown status)
3. Conversations too short (not enough triggers)

**Debug**:
```python
# Check allowances
stats = get_drift_rate_stats(personality, db)
for trait, info in stats["traits"].items():
    print(f"{trait}:")
    print(f"  Daily remaining: {info['allowances']['daily']['remaining_drift']}")
    print(f"  In cooldown: {info['in_cooldown']}")
```

### Problem: Drift blocked unexpectedly

**Possible Causes**:
1. Recent large drift triggered cooldown
2. Monthly limit exhausted
3. Multiple small drifts accumulated

**Solution**:
```python
# Check recent drift events
from services.personality_drift_calculator import personality_drift_calculator

history = personality_drift_calculator.get_drift_history(
    user_id, db, trait_name="humor", limit=10
)

for drift in history:
    details = drift.get_trigger_details()
    print(f"{drift.timestamp}: {drift.change_amount:+.3f}")
    if details.get("rate_limited"):
        print(f"  Rate limited: {details.get('limit_messages')}")
```

## Adjusting Rate Limits

If you need to adjust the limits (for testing or different use cases), modify the constants in `drift_rate_limiter.py`:

```python
class DriftRateLimiter:
    # Increase for faster drift (testing)
    MAX_DRIFT_PER_CONVERSATION = 0.05  # Was 0.02
    MAX_DRIFT_PER_DAY = 0.10           # Was 0.05
    MAX_DRIFT_PER_MONTH = 0.30         # Was 0.15

    # Decrease cooldown (more frequent changes)
    COOLDOWN_AFTER_LARGE_DRIFT = timedelta(hours=3)  # Was 6

    # Adjust large drift threshold
    LARGE_DRIFT_THRESHOLD = 0.06  # Was 0.04
```

**Warning**: Changing these values affects how quickly personality can change. Test thoroughly before deploying to production.

## Conclusion

The Drift Rate Limiting System provides essential controls for personality stability:

- ✅ Prevents rapid personality changes
- ✅ Ensures gradual, natural evolution
- ✅ Configurable limits for different time periods
- ✅ Cooldown system after large drifts
- ✅ Complete API for monitoring and management
- ✅ Comprehensive testing and documentation
- ✅ Automatic integration with drift calculator

By enforcing these limits, the system creates a more realistic and stable personality that evolves meaningfully over time while maintaining consistency and predictability.
