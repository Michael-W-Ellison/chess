# Trait Adjustment System

## Overview

The Trait Adjustment System provides a centralized, validated service for adjusting personality traits with proper bounds checking. All personality trait modifications should go through this system to ensure consistency, validation, and proper bounds enforcement.

## Core Concept

**Bounded Trait Adjustment** ensures that all personality trait values:
- Stay within valid range **[0.0, 1.0]**
- Use validated trait names only
- Are properly clamped if out of bounds
- Are logged and trackable
- Can be reset to defaults

This system provides a single source of truth for trait modification, used by all other systems (personality drift, personality manager, manual adjustments).

## The Four Personality Traits

| Trait | Default | Description | High (1.0) | Low (0.0) |
|-------|---------|-------------|------------|-----------|
| **humor** | 0.5 | Frequency and intensity of jokes | Very playful, lots of jokes | Serious, minimal humor |
| **energy** | 0.6 | Enthusiasm and liveliness | Highly enthusiastic, energetic | Calm, subdued, relaxed |
| **curiosity** | 0.5 | How often bot asks questions | Very inquisitive, engaged | More passive, less questioning |
| **formality** | 0.3 | Casual vs formal language | Very formal, proper language | Very casual, informal |

## Trait Adjuster Service

### Core Features

1. **Bounded Adjustments** - All values automatically clamped to [0.0, 1.0]
2. **Validation** - Trait names and values validated before changes
3. **Clamping Notification** - Warns when values are clamped
4. **Flexible API** - Absolute values, deltas, single or multiple traits
5. **Reset Capability** - Reset individual or all traits to defaults
6. **Query Methods** - Get current values, validate states, get trait info

### TraitAdjuster Class

```python
from services.trait_adjuster import trait_adjuster, TraitAdjuster

# Global singleton instance
adjuster = trait_adjuster

# Or create your own instance
adjuster = TraitAdjuster()
```

### Methods

#### adjust_trait()

Adjust a trait to a specific absolute value.

```python
old_value, new_value, actual_change = adjuster.adjust_trait(
    personality,
    trait_name="humor",
    new_value=0.8,
    db=db,
    commit=True
)

# Returns:
# old_value: 0.5
# new_value: 0.8
# actual_change: 0.3
```

**Parameters**:
- `personality` (BotPersonality): Personality object to modify
- `trait_name` (str): Name of trait ("humor", "energy", "curiosity", "formality")
- `new_value` (float): New value to set
- `db` (Session): Database session
- `commit` (bool): Whether to commit (default True)

**Returns**: `Tuple[float, float, float]` - (old_value, new_value_clamped, actual_change)

**Raises**: `ValueError` if trait_name is invalid

#### adjust_trait_by_delta()

Adjust a trait by a delta amount (relative change).

```python
old_value, new_value, actual_change = adjuster.adjust_trait_by_delta(
    personality,
    trait_name="energy",
    delta=0.2,  # Increase by 0.2
    db=db
)

# If energy was 0.6, it becomes 0.8
```

**Parameters**:
- `personality` (BotPersonality): Personality object to modify
- `trait_name` (str): Name of trait
- `delta` (float): Amount to change (positive or negative)
- `db` (Session): Database session
- `commit` (bool): Whether to commit (default True)

**Returns**: `Tuple[float, float, float]` - (old_value, new_value, actual_change)

**Note**: If delta would push value out of bounds, it's clamped and actual_change will differ from delta.

#### adjust_multiple_traits()

Adjust multiple traits at once (more efficient).

```python
adjustments = {
    "humor": 0.8,
    "energy": 0.7,
    "curiosity": 0.6,
}

results = adjuster.adjust_multiple_traits(
    personality,
    adjustments=adjustments,
    db=db,
    is_delta=False  # False = absolute values, True = deltas
)

# Returns dict of:
# {
#     "humor": (0.5, 0.8, 0.3),
#     "energy": (0.6, 0.7, 0.1),
#     "curiosity": (0.5, 0.6, 0.1),
# }
```

#### reset_trait()

Reset a single trait to its default value.

```python
old_value, default_value, change = adjuster.reset_trait(
    personality,
    trait_name="humor",
    db=db
)

# Humor is reset to 0.5 (default)
```

#### reset_all_traits()

Reset all traits to their defaults.

```python
results = adjuster.reset_all_traits(personality, db)

# All traits reset:
# humor -> 0.5
# energy -> 0.6
# curiosity -> 0.5
# formality -> 0.3
```

#### Validation and Query Methods

```python
# Validate trait name
is_valid = adjuster.validate_trait_name("humor")  # True

# Validate trait value
is_valid = adjuster.validate_trait_value(0.5)  # True

# Clamp a value
clamped = adjuster.clamp_value(1.5)  # Returns 1.0

# Get single trait value
value = adjuster.get_trait_value(personality, "humor")

# Get all trait values
values = adjuster.get_all_trait_values(personality)
# Returns: {"humor": 0.5, "energy": 0.6, ...}

# Validate all traits are within bounds
validation = adjuster.validate_all_traits(personality)
# Returns: {"humor": True, "energy": True, ...}

# Get trait information
info = adjuster.get_trait_info("humor")
# Returns detailed trait metadata

# Get all trait information
all_info = adjuster.get_all_trait_info()
```

## API Endpoints

### POST `/api/friendship/traits/adjust`

Adjust a single trait to a specific value.

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
    "trait_name": "humor",
    "old_value": 0.5,
    "new_value": 0.8,
    "change": 0.3,
    "was_clamped": false,
    "personality": {
        "name": "Buddy",
        "traits": {
            "humor": 0.8,
            "energy": 0.6,
            "curiosity": 0.5,
            "formality": 0.3
        },
        ...
    }
}
```

**Error Response (400)**:
```json
{
    "detail": "Invalid trait name 'invalid'. Must be one of: humor, energy, curiosity, formality"
}
```

### POST `/api/friendship/traits/adjust-delta`

Adjust a single trait by a delta amount.

**Request Body**:
```json
{
    "user_id": 1,
    "trait_name": "energy",
    "delta": 0.2
}
```

**Response**:
```json
{
    "success": true,
    "message": "Trait energy adjusted by +0.200",
    "trait_name": "energy",
    "old_value": 0.6,
    "new_value": 0.8,
    "requested_delta": 0.2,
    "actual_change": 0.2,
    "was_clamped": false,
    "personality": {...}
}
```

**Clamped Example**:
If energy is 0.9 and you try to add 0.5, it will be clamped:
```json
{
    "old_value": 0.9,
    "new_value": 1.0,
    "requested_delta": 0.5,
    "actual_change": 0.1,
    "was_clamped": true
}
```

### POST `/api/friendship/traits/adjust-multiple`

Adjust multiple traits at once.

**Request Body**:
```json
{
    "user_id": 1,
    "adjustments": {
        "humor": 0.8,
        "energy": 0.7,
        "curiosity": 0.6
    },
    "is_delta": false
}
```

**Response**:
```json
{
    "success": true,
    "message": "Adjusted 3 traits successfully",
    "results": {
        "humor": {
            "old_value": 0.5,
            "new_value": 0.8,
            "change": 0.3
        },
        "energy": {
            "old_value": 0.6,
            "new_value": 0.7,
            "change": 0.1
        },
        "curiosity": {
            "old_value": 0.5,
            "new_value": 0.6,
            "change": 0.1
        }
    },
    "personality": {...}
}
```

**With Deltas**:
```json
{
    "user_id": 1,
    "adjustments": {
        "humor": 0.1,
        "energy": -0.2
    },
    "is_delta": true
}
```

### POST `/api/friendship/traits/reset/{trait_name}`

Reset a trait to its default value.

**Query Parameters**:
- `user_id` (int, default=1)

**Response**:
```json
{
    "success": true,
    "message": "Trait humor reset to default value",
    "trait_name": "humor",
    "old_value": 0.8,
    "default_value": 0.5,
    "change": -0.3,
    "personality": {...}
}
```

### POST `/api/friendship/traits/reset-all`

Reset all traits to their default values.

**Query Parameters**:
- `user_id` (int, default=1)

**Response**:
```json
{
    "success": true,
    "message": "All traits reset to default values",
    "results": {
        "humor": {
            "old_value": 0.8,
            "default_value": 0.5,
            "change": -0.3
        },
        "energy": {
            "old_value": 0.9,
            "default_value": 0.6,
            "change": -0.3
        },
        "curiosity": {
            "old_value": 0.7,
            "default_value": 0.5,
            "change": -0.2
        },
        "formality": {
            "old_value": 0.2,
            "default_value": 0.3,
            "change": 0.1
        }
    },
    "personality": {...}
}
```

### GET `/api/friendship/traits/info/{trait_name}`

Get information about a specific trait.

**Response**:
```json
{
    "success": true,
    "trait_name": "humor",
    "info": {
        "name": "Humor",
        "description": "Frequency and intensity of jokes",
        "high": "Very playful, lots of jokes",
        "low": "Serious, minimal humor",
        "min_value": 0.0,
        "max_value": 1.0,
        "default_value": 0.5
    }
}
```

### GET `/api/friendship/traits/info`

Get information about all traits.

**Response**:
```json
{
    "success": true,
    "traits": {
        "humor": {
            "name": "Humor",
            "description": "Frequency and intensity of jokes",
            "high": "Very playful, lots of jokes",
            "low": "Serious, minimal humor",
            "min_value": 0.0,
            "max_value": 1.0,
            "default_value": 0.5
        },
        "energy": {...},
        "curiosity": {...},
        "formality": {...}
    }
}
```

### GET `/api/friendship/traits/validate`

Validate that all traits are within bounds.

**Query Parameters**:
- `user_id` (int, default=1)

**Response**:
```json
{
    "success": true,
    "user_id": 1,
    "all_valid": true,
    "validation": {
        "humor": true,
        "energy": true,
        "curiosity": true,
        "formality": true
    },
    "current_values": {
        "humor": 0.5,
        "energy": 0.6,
        "curiosity": 0.5,
        "formality": 0.3
    },
    "bounds": {
        "min": 0.0,
        "max": 1.0
    }
}
```

## Usage Examples

### Example 1: User Personality Customization

```python
from services.trait_adjuster import trait_adjuster

# User adjusts humor slider to 0.8
old, new, change = trait_adjuster.adjust_trait(
    personality,
    "humor",
    0.8,
    db
)

print(f"Humor changed from {old:.2f} to {new:.2f}")
# Output: Humor changed from 0.50 to 0.80
```

### Example 2: Automatic Adjustment from Game

```python
# User wins a game, increase energy
old, new, change = trait_adjuster.adjust_trait_by_delta(
    personality,
    "energy",
    0.1,  # 10% boost
    db
)

# User completes homework, slightly increase formality
trait_adjuster.adjust_trait_by_delta(
    personality,
    "formality",
    0.05,
    db
)
```

### Example 3: Batch Adjustments

```python
# After a very funny conversation
adjustments = {
    "humor": 0.05,  # Increase humor
    "energy": 0.03,  # Increase energy
    "formality": -0.02,  # Decrease formality (more casual)
}

results = trait_adjuster.adjust_multiple_traits(
    personality,
    adjustments,
    db,
    is_delta=True
)

for trait, (old, new, change) in results.items():
    print(f"{trait}: {old:.2f} -> {new:.2f} ({change:+.2f})")
```

### Example 4: Reset After Testing

```python
# Testing complete, reset all traits
results = trait_adjuster.reset_all_traits(personality, db)

print("All traits reset to defaults:")
for trait, (old, new, change) in results.items():
    print(f"  {trait}: {old:.2f} -> {new:.2f}")
```

### Example 5: Validation Before Display

```python
# Check if personality is valid before showing to user
validation = trait_adjuster.validate_all_traits(personality)

if not all(validation.values()):
    print("Warning: Some traits are out of bounds!")
    for trait, is_valid in validation.items():
        if not is_valid:
            value = trait_adjuster.get_trait_value(personality, trait)
            print(f"  {trait}: {value} (invalid)")
```

## Integration with Other Systems

### Personality Drift Calculator

The drift calculator should use trait_adjuster for all adjustments:

```python
# In personality_drift_calculator.py
from services.trait_adjuster import trait_adjuster

# Apply drift
old, new, change = trait_adjuster.adjust_trait(
    personality,
    trait_name,
    new_value,
    db,
    commit=False  # Drift calculator commits manually
)
```

### Personality Manager

The personality manager should use trait_adjuster for trait updates:

```python
# In personality_manager.py
from services.trait_adjuster import adjust_trait_by_delta

# Apply conversation-based adjustment
old, new, change = adjust_trait_by_delta(
    personality,
    "humor",
    delta=0.01,
    db
)
```

### Manual User Adjustments

Frontend sliders should call the trait adjustment API:

```typescript
async function adjustTrait(traitName: string, newValue: number) {
    const response = await fetch('/api/friendship/traits/adjust', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            user_id: 1,
            trait_name: traitName,
            new_value: newValue
        })
    });

    const data = await response.json();

    if (data.success) {
        console.log(`${traitName} adjusted from ${data.old_value} to ${data.new_value}`);

        if (data.was_clamped) {
            alert(`Value was clamped to valid range [0.0, 1.0]`);
        }

        updateUI(data.personality);
    }
}
```

## Testing

### Run Tests

```bash
cd backend
pytest tests/test_trait_adjuster.py -v
```

### Test Coverage

The test suite includes 50+ test cases covering:

#### Initialization and Constants
- ✅ Adjuster constants (MIN, MAX, VALID_TRAITS)
- ✅ Default trait values

#### Validation
- ✅ Trait name validation (valid and invalid names)
- ✅ Trait value validation (within and outside bounds)

#### Value Clamping
- ✅ Clamping values within bounds (no change)
- ✅ Clamping values above maximum
- ✅ Clamping values below minimum

#### Single Trait Adjustment
- ✅ Adjust to valid value
- ✅ Adjust with clamping (high and low)
- ✅ Invalid trait name error
- ✅ Adjust without commit

#### Delta Adjustment
- ✅ Positive and negative deltas
- ✅ Delta adjustment with clamping
- ✅ Actual change differs from requested delta

#### Multiple Trait Adjustment
- ✅ Multiple traits with absolute values
- ✅ Multiple traits with deltas
- ✅ Multiple adjustments with clamping

#### Reset Functionality
- ✅ Reset single trait to default
- ✅ Reset all traits to defaults

#### Query Methods
- ✅ Get single and all trait values
- ✅ Validate all traits
- ✅ Get trait information

#### Global Instance
- ✅ Global instance exists
- ✅ Convenience functions work

#### Edge Cases
- ✅ Adjust to same value
- ✅ Adjust by zero delta
- ✅ Adjust to exact bounds
- ✅ Multiple sequential adjustments

## Best Practices

### For Backend Developers

1. **Always Use TraitAdjuster**
   ```python
   # Bad - direct modification
   personality.humor = 0.8

   # Good - use adjuster
   trait_adjuster.adjust_trait(personality, "humor", 0.8, db)
   ```

2. **Check for Clamping**
   ```python
   old, new, change = adjust_trait(personality, "humor", 1.5, db)

   if abs(1.5 - new) > 0.001:
       logger.warning(f"Value was clamped from 1.5 to {new}")
   ```

3. **Use Batch Adjustments When Possible**
   ```python
   # More efficient than multiple single adjustments
   adjustments = {"humor": 0.8, "energy": 0.7}
   results = adjust_multiple_traits(personality, adjustments, db)
   ```

4. **Validate Before Display**
   ```python
   validation = validate_all_traits(personality)
   if not all(validation.values()):
       # Handle invalid state
       reset_all_traits(personality, db)
   ```

### For Frontend Developers

1. **Use Sliders with Validation**
   ```typescript
   function TraitSlider({traitName, value, onChange}) {
       return (
           <input
               type="range"
               min="0"
               max="1"
               step="0.01"
               value={value}
               onChange={(e) => onChange(traitName, parseFloat(e.target.value))}
           />
       );
   }
   ```

2. **Show Clamping Feedback**
   ```typescript
   if (response.was_clamped) {
       showNotification(
           `Value was adjusted to fit within valid range (0.0-1.0)`,
           'warning'
       );
   }
   ```

3. **Provide Reset Option**
   ```typescript
   function ResetButton({traitName, onReset}) {
       return (
           <button onClick={() => onReset(traitName)}>
               Reset to Default
           </button>
       );
   }
   ```

4. **Display Trait Information**
   ```typescript
   async function loadTraitInfo() {
       const response = await fetch('/api/friendship/traits/info');
       const data = await response.json();

       // Show descriptions and ranges
       for (const [name, info] of Object.entries(data.traits)) {
           displayTraitInfo(name, info);
       }
   }
   ```

## Bounds Enforcement

### How Clamping Works

When a value is set outside the valid range [0.0, 1.0], it's automatically clamped:

```python
# Example: Setting humor to 1.5
old_val, new_val, change = adjust_trait(personality, "humor", 1.5, db)

# old_val: 0.5
# new_val: 1.0 (clamped from 1.5)
# change: 0.5 (actual change)
```

### Clamping Notification

The adjuster logs a warning when clamping occurs:

```
WARNING: Trait value 1.50 was clamped to 1.00 (bounds: [0.0, 1.0])
```

API responses include a `was_clamped` field to inform the frontend.

### When to Clamp vs Reject

The system **clamps** values rather than rejecting them because:
1. Users may drag sliders past limits
2. Automatic adjustments might overshoot
3. Clamping is more user-friendly than errors
4. Actual change is always returned

## Troubleshooting

### Problem: Trait value not changing

**Possible Causes**:
1. Database not committing
2. Wrong personality object
3. Value already at requested value

**Debug**:
```python
old, new, change = adjust_trait(personality, "humor", 0.8, db)
print(f"Old: {old}, New: {new}, Change: {change}")

# Check database
db.refresh(personality)
print(f"DB value: {personality.humor}")
```

**Solution**: Ensure `commit=True` or manually commit, verify correct personality object.

### Problem: Invalid trait name error

**Possible Causes**:
1. Typo in trait name
2. Case mismatch (trait names are lowercase)
3. Using non-existent trait

**Solution**:
```python
# Check valid traits
print(trait_adjuster.VALID_TRAITS)
# ['humor', 'energy', 'curiosity', 'formality']

# Use exact names
adjust_trait(personality, "humor", 0.8, db)  # Correct
adjust_trait(personality, "Humor", 0.8, db)  # Wrong - case sensitive
```

### Problem: Value being clamped unexpectedly

**Possible Causes**:
1. Value outside [0.0, 1.0]
2. Delta pushing value out of bounds

**Debug**:
```python
current = get_trait_value(personality, "humor")
print(f"Current: {current}")

# Check what the new value would be
requested = 1.5
would_be_clamped = not validate_trait_value(requested)
print(f"Would be clamped: {would_be_clamped}")
```

**Solution**: This is expected behavior - values are automatically bounded. Check `was_clamped` in response to detect this.

## Conclusion

The Trait Adjustment System provides a robust, centralized solution for managing personality trait changes with proper validation and bounds enforcement. By using this system consistently across all parts of the application, you ensure:

- ✅ All traits stay within valid range [0.0, 1.0]
- ✅ Trait names are validated
- ✅ Changes are logged and trackable
- ✅ Easy reset to defaults
- ✅ Comprehensive API for all use cases
- ✅ 50+ test cases ensuring correctness
- ✅ Consistent behavior across systems

All personality trait modifications should use TraitAdjuster to maintain data integrity and provide a consistent user experience.
