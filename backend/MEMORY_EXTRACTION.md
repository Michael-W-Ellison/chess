# Memory Extraction System

The memory extraction system uses LLM-based prompts to extract structured facts from user messages, building a persistent memory profile.

## Overview

The system extracts user information in 6 categories:
- **favorite** - Things the user likes
- **dislike** - Things the user dislikes
- **person** - Important people (friends, family, etc.)
- **goal** - Things they want to achieve
- **achievement** - Things they've accomplished
- **basic** - Basic info (name, age, grade, etc.)

## Architecture

```
User Message
    ↓
Memory Manager (extract_and_store_memories)
    ↓
┌───────────────────────────────┐
│  LLM-based Extraction         │  ← Enabled by default
│  (uses prompts.py)            │
└───────────────────────────────┘
    ↓ (fallback on error)
┌───────────────────────────────┐
│  Keyword-based Extraction     │  ← Backup method
│  (simple pattern matching)    │
└───────────────────────────────┘
    ↓
Extracted Facts (category, key, value)
    ↓
Database (UserProfile table)
```

## LLM-Based Extraction

### Prompt Template

Location: `backend/services/prompts.py`

The `MemoryExtractionPrompt` class contains:
- **SYSTEM_PROMPT**: Detailed instructions for the LLM
- **USER_TEMPLATE**: Template for the user message
- **format_prompt()**: Combines them into complete prompt

### Extraction Process

1. **Format Prompt**: User message is inserted into template
2. **LLM Generation**: Calls `llm_service.generate()` with:
   - `max_tokens=300`
   - `temperature=0.3` (low for consistency)
3. **Parse Response**: Extracts JSON array from response
4. **Validate**: Checks category, key, value, confidence
5. **Filter**: Only keeps items with confidence ≥ 0.7
6. **Store**: Creates/updates UserProfile records

### Example Extraction

**Input Message:**
```
"My name is Alex and I'm 11 years old. My favorite color is blue!"
```

**LLM Response:**
```json
[
  {"category": "basic", "key": "name", "value": "Alex", "confidence": 1.0},
  {"category": "basic", "key": "age", "value": "11", "confidence": 1.0},
  {"category": "favorite", "key": "color", "value": "blue", "confidence": 0.95}
]
```

**Database Records Created:**
- UserProfile(category="basic", key="name", value="Alex", confidence=1.0)
- UserProfile(category="basic", key="age", value="11", confidence=1.0)
- UserProfile(category="favorite", key="color", value="blue", confidence=0.95)

## Prompt Design

### Key Features

1. **Clear Categories**: 6 specific categories with examples
2. **Extraction Rules**: Guidelines for what to extract
3. **Confidence Scoring**: LLM provides confidence (0.7-1.0)
4. **Few-Shot Examples**: Multiple examples showing correct extraction
5. **Edge Cases**: Examples of what NOT to extract

### Extraction Rules

✅ **DO Extract:**
- Clear factual statements
- Persistent preferences
- Named people and relationships
- Specific goals and achievements
- Basic demographic info

❌ **DON'T Extract:**
- Temporary situations or moods
- Hypotheticals or questions
- Vague preferences
- Low-confidence guesses

### Example Prompts

**Good Extraction:**
```
User: "I really want to make the soccer team this year."
→ Extract: goal/make_soccer_team, favorite/sport=soccer
```

**No Extraction (temporary):**
```
User: "I'm feeling sad today."
→ Extract: [] (temporary mood, not a fact)
```

**No Extraction (question):**
```
User: "What's the weather like?"
→ Extract: [] (question, no facts about user)
```

## Configuration

### Enable/Disable LLM Extraction

```python
from services.memory_manager import memory_manager

# Enable LLM extraction (default)
memory_manager.use_llm_extraction = True

# Disable LLM extraction (use keywords only)
memory_manager.use_llm_extraction = False
```

### Per-Call Override

```python
# Force use of LLM
memories = memory_manager.extract_and_store_memories(
    user_message="I love pizza!",
    user_id=1,
    db=db,
    use_llm=True
)

# Force use of keywords
memories = memory_manager.extract_and_store_memories(
    user_message="I love pizza!",
    user_id=1,
    db=db,
    use_llm=False
)
```

## Fallback Behavior

The system gracefully handles LLM failures:

1. **LLM Not Loaded**: Falls back to keyword extraction
2. **Invalid JSON Response**: Logs error, uses keyword extraction
3. **Empty Extraction**: Returns empty list (normal behavior)
4. **Exception During Extraction**: Logs error, uses keyword extraction

## Storage Logic

### Confidence Scores

- **Initial Confidence**: 0.8 (keyword) or LLM-provided (0.7-1.0)
- **Mention Increase**: +0.1 per additional mention
- **Maximum**: 1.0 (capped)

### Memory Updates

**New Memory:**
```python
UserProfile(
    user_id=1,
    category="favorite",
    key="color",
    value="blue",
    confidence=0.95,
    first_mentioned=datetime.now(),
    last_mentioned=datetime.now(),
    mention_count=1
)
```

**Existing Memory Update:**
```python
# User mentions "blue" is their favorite color again
existing.value = "blue"  # Update value
existing.last_mentioned = datetime.now()
existing.mention_count += 1  # Increment
existing.confidence = min(1.0, existing.confidence + 0.1)  # Increase
```

## Integration

### Conversation Flow

Memory extraction is automatically called during message processing:

```python
# conversation_manager.py, line 140
memory_manager.extract_and_store_memories(user_message, user_id, db)
```

### Memory Retrieval

Extracted memories are used in conversation context:

```python
# Get relevant memories based on keywords
keywords = memory_manager.extract_keywords(user_message)
memories = memory_manager.get_relevant_memories(user_id, keywords, db, limit=5)

# Format for prompt
memory_text = memory_manager.format_memories_for_prompt(memories)
```

## Testing

### Manual Testing

```python
from services.memory_manager import memory_manager
from database.database import SessionLocal

db = SessionLocal()

# Test extraction
message = "My name is Alex and I love soccer!"
memories = memory_manager.extract_and_store_memories(
    message, user_id=1, db=db, use_llm=True
)

print(f"Extracted {len(memories)} memories:")
for m in memories:
    print(f"  {m.category}/{m.key} = {m.value} (confidence: {m.confidence})")
```

### Test Cases

**Basic Info:**
```python
"My name is Sarah and I'm 12 years old in 7th grade"
→ Should extract: name, age, grade
```

**Favorites:**
```python
"I love playing basketball and my favorite food is pizza"
→ Should extract: sport=basketball, food=pizza
```

**People:**
```python
"My best friend Emma and I love to read together"
→ Should extract: friend_emma, favorite_activity=reading
```

**Goals:**
```python
"I really want to get better at math this year"
→ Should extract: goal_improve_math
```

**Negative Cases:**
```python
"What's your favorite color?"  # Question
"I might like pizza"  # Hypothetical
"I'm happy today"  # Temporary mood
→ Should extract: nothing
```

## Monitoring

### Logging

The memory extraction system logs:

```python
# Debug: Individual extractions
logger.debug(f"Extracted: {category}/{key} = {value} (confidence: {confidence})")

# Info: Summary
logger.info(f"LLM extracted {len(extracted)} memories from message")

# Warning: Fallback
logger.warning("LLM not loaded, falling back to keyword extraction")

# Error: Failures
logger.error(f"Failed to parse LLM extraction response: {response}")
```

### Metrics to Track

- Extraction count per message
- LLM vs keyword extraction ratio
- Average confidence scores
- Fallback frequency
- Parse error rate

## Optimization

### Prompt Tuning

Adjust the prompt template for better results:

1. Add more examples for edge cases
2. Refine category definitions
3. Adjust confidence thresholds
4. Add domain-specific patterns

### Performance

- **LLM Temperature**: 0.3 (lower = more consistent, higher = more creative)
- **Max Tokens**: 300 (adjust based on expected extraction count)
- **Confidence Threshold**: 0.7 (adjust based on accuracy needs)

## Future Enhancements

1. **Contextual Extraction**: Use conversation history for better context
2. **Multi-turn Extraction**: Extract across multiple messages
3. **Conflict Resolution**: Handle contradictory facts
4. **Temporal Tracking**: Track when preferences change over time
5. **Validation**: Cross-check extractions for consistency
6. **Active Learning**: Improve based on user corrections

## References

- Prompt Template: `backend/services/prompts.py`
- Memory Manager: `backend/services/memory_manager.py`
- UserProfile Model: `backend/models/memory.py`
- Conversation Integration: `backend/services/conversation_manager.py`
