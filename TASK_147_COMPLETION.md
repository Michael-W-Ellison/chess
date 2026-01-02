# Task 147: POST /api/message Endpoint - COMPLETED ✅

## Overview
Task 147 requested the creation of a POST /api/message endpoint for sending user messages and receiving bot responses. This endpoint is **already fully implemented** and functional with extensive safety and AI features.

## Implementation Details

### Endpoint Location
- **File**: `/home/user/chess/backend/routes/conversation.py`
- **Lines**: 83-135
- **Route**: `POST /api/message`
- **URL**: `http://localhost:8000/api/message`

### Endpoint Signature
```python
@router.post("/message", response_model=SendMessageResponse)
async def send_message(request: SendMessageRequest, db: Session = Depends(get_db))
```

### Request Model
```python
class SendMessageRequest(BaseModel):
    content: str              # The user's message text
    conversation_id: int      # Active conversation ID
    user_id: int = 1         # User ID (default 1 for single-user app)
```

### Response Model
```python
class SendMessageResponse(BaseModel):
    message_id: int          # Unique message ID
    content: str             # Bot's response text
    timestamp: str           # ISO format timestamp
    metadata: dict           # Rich metadata (see below)
```

## Message Processing Pipeline

The endpoint orchestrates a sophisticated 11-step message processing flow through the `ConversationManager.process_message()` service:

### 1. Safety Filtering
- Checks user message for inappropriate content, bullying, or crisis signals
- Uses pattern matching and keyword detection
- Severity levels: none, low, medium, high, critical

### 2. Crisis Response Handling
- If critical severity detected:
  - Changes bot mood to "concerned"
  - Generates empathetic, category-specific crisis response
  - Flags message in database
  - Logs safety event
  - Optionally notifies parent (configurable)
- Crisis categories:
  - Self-harm
  - Depression/anxiety
  - Bullying victim
  - Family issues
  - Academic stress
  - Social issues

### 3. Message Storage
- Stores user message in database with timestamp
- Links to conversation record
- Tracks message count

### 4. Activity Detection & Points
- Detects activities mentioned in message:
  - Sports/exercise
  - Creative activities (art, music, writing)
  - Academic achievements
  - Social activities
  - Reading
- Awards friendship points for activities
- Tracks engagement metrics

### 5. Memory Extraction
- Uses LLM to extract structured memories:
  - **Favorites**: Hobbies, sports, subjects, foods, etc.
  - **Dislikes**: Things the user doesn't like
  - **Goals**: Aspirations and objectives
  - **Achievements**: Accomplishments
  - **People**: Important people in user's life
  - **Short-term**: Recent context (7-day window)
- Stores in searchable database with timestamps
- Enables personalized future responses

### 6. Context Building
- Retrieves relevant memories from database
- Analyzes conversation history
- Detects current mood from message
- Extracts keywords/topics
- Builds comprehensive context for LLM

### 7. LLM Response Generation
- Generates response using local LLM (llama-cpp-python)
- Prompt includes:
  - Bot personality traits
  - Relevant memories
  - Conversation context
  - User mood
  - Response guidelines
- Parameters: max_tokens=150, temperature=0.7
- Falls back to rule-based response if LLM unavailable

### 8. Personality Application
- Applies personality traits to response:
  - **Humor** (0.0-1.0): Adds jokes/puns
  - **Energy** (0.0-1.0): Adjusts enthusiasm level
  - **Curiosity** (0.0-1.0): Asks follow-up questions
  - **Formality** (0.0-1.0): Casual vs. formal tone
- Injects quirks:
  - Emoji usage
  - Pun telling
  - Random facts
- Adds catchphrase (unlocked at friendship level 3+)
- Adjusts tone based on mood

### 9. Response Safety Check
- Validates bot response for safety
- Prevents inappropriate bot outputs
- Falls back to safe default if needed

### 10. Response Storage
- Stores bot response in database
- Links to conversation and user message
- Records timestamp and metadata

### 11. Conversation Update
- Updates message count
- Tracks conversation duration
- Maintains conversation state

## Response Metadata

The endpoint returns rich metadata with each response:

```json
{
  "message_id": 123,
  "content": "That's awesome! What's your favorite thing about basketball?",
  "timestamp": "2025-11-18T14:30:45.123456",
  "metadata": {
    "safety_flag": false,
    "mood_detected": "excited",
    "topics_extracted": ["basketball", "sports", "team"],
    "points_awarded": [
      {
        "activity": "playing_sports",
        "points": 10,
        "message": "Nice! You earned 10 points for playing sports!"
      }
    ],
    "activities_detected": ["sports"],
    "notify_parent": false
  }
}
```

### Crisis Response Metadata
When crisis is detected:
```json
{
  "metadata": {
    "safety_flag": true,
    "severity": "critical",
    "crisis_response": true,
    "flags": ["self_harm", "depression"],
    "notify_parent": true,
    "mood_change": "concerned"
  }
}
```

## Example Usage

### Request
```bash
curl -X POST http://localhost:8000/api/message \
  -H "Content-Type: application/json" \
  -d '{
    "content": "I just scored the winning goal in soccer today!",
    "conversation_id": 42,
    "user_id": 1
  }'
```

### Response
```json
{
  "message_id": 156,
  "content": "Wow, that's amazing! 🎉 Scoring the winning goal must have felt incredible! What position do you play?",
  "timestamp": "2025-11-18T14:30:45.123456",
  "metadata": {
    "safety_flag": false,
    "mood_detected": "excited",
    "topics_extracted": ["soccer", "sports", "goal", "winning"],
    "points_awarded": [
      {
        "activity": "playing_sports",
        "points": 10,
        "message": "You earned 10 points for playing sports!"
      }
    ],
    "activities_detected": ["sports"]
  }
}
```

## Supporting Services

### ConversationManager
- **File**: `/home/user/chess/backend/services/conversation_manager.py`
- **Method**: `process_message()` (lines 114-225)
- Orchestrates complete message processing pipeline

### SafetyFilter
- **File**: `/home/user/chess/backend/services/safety_filter.py`
- Detects inappropriate content and crisis situations
- Pattern-based and keyword detection
- Severity scoring and parent notification

### MemoryManager
- **File**: `/home/user/chess/backend/services/memory_manager.py`
- Extracts and stores structured memories
- Retrieves relevant memories for context
- Manages short-term and long-term memory

### LLMService
- **File**: `/home/user/chess/backend/services/llm_service.py`
- Local LLM integration (llama-cpp-python)
- Response caching for performance
- Background model loading

### PersonalityManager
- **File**: `/home/user/chess/backend/services/personality_manager.py`
- Applies personality traits to responses
- Manages quirks and catchphrases
- Updates personality over time (drift)

### ConversationTracker
- **File**: `/home/user/chess/backend/services/conversation_tracker.py`
- Tracks activity detection
- Awards friendship points
- Monitors engagement metrics

## Database Models

### Message Model
```python
class Message:
    id: int (primary key)
    conversation_id: int (foreign key → Conversation)
    role: str ('user' or 'assistant')
    content: str (message text)
    timestamp: datetime
    flagged: bool (safety flag)
    message_metadata: JSON (mood, topics, etc.)

    relationships:
    - conversation: Conversation
    - safety_flags: List[SafetyFlag]
```

### Safety Flag Model
```python
class SafetyFlag:
    id: int
    message_id: int (foreign key → Message)
    user_id: int
    severity: str ('low', 'medium', 'high', 'critical')
    flags: JSON array (specific flags)
    timestamp: datetime
    parent_notified: bool
```

## Test Coverage

### API Integration Tests
- **File**: `/home/user/chess/backend/test_api.py`
- **Lines**: 40-77 (conversation flow test)
- Tests complete flow:
  1. Start conversation
  2. Send first message
  3. Send second message
  4. Retrieve conversation
  5. End conversation

### Unit Tests
Multiple test files cover individual components:
- `tests/test_conversation_manager_mood.py` - Mood handling
- `tests/test_friendship_progression.py` - Point awarding
- `tests/test_safety_filter.py` - Safety detection
- `tests/test_memory_extraction_pytest.py` - Memory extraction
- `tests/test_personality_drift.py` - Personality updates

## Error Handling

The endpoint includes comprehensive error handling:

1. **Invalid conversation ID**: 404 if conversation doesn't exist
2. **Safety filter errors**: Logged, continues with safe defaults
3. **LLM failures**: Falls back to rule-based responses
4. **Database errors**: Rolled back, returns 500 with details
5. **Missing response**: 500 if bot response not found
6. **All exceptions**: Logged with stack traces, returns HTTP 500

## Performance Optimizations

1. **Response Caching**: LLM responses cached (configurable TTL)
2. **Database Indexing**: Optimized queries with indexes
3. **Async Operations**: FastAPI async endpoints
4. **Efficient Queries**: Joins and filters optimized
5. **Memory Search**: Vector similarity for fast memory retrieval

## Safety Features

1. **Input Validation**: Pydantic models validate all inputs
2. **SQL Injection Protection**: SQLAlchemy ORM prevents injection
3. **XSS Prevention**: No HTML rendering in responses
4. **Crisis Detection**: Multi-pattern crisis detection
5. **Parent Notifications**: Optional alerts for serious concerns
6. **Content Filtering**: Both input and output safety checks
7. **Audit Logging**: All safety events logged with metadata

## API Documentation

Interactive documentation available when server is running:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Configuration

Key settings (from `utils/config.py`):
- `AUTO_GENERATE_SUMMARIES`: Enable conversation summaries
- `ENABLE_RESPONSE_CACHE`: Enable LLM response caching
- `CACHE_TTL`: Cache time-to-live (seconds)
- `MODEL_PATH`: Path to local LLM model
- `MAX_MEMORY_ITEMS`: Max memories to retrieve for context
- `PARENT_NOTIFICATION_ENABLED`: Enable parent alerts

## Status: COMPLETE ✅

The POST /api/message endpoint is:
- ✅ Fully implemented with 11-step processing pipeline
- ✅ Safety filtering and crisis detection
- ✅ Memory extraction and storage
- ✅ LLM-powered response generation
- ✅ Personality application and quirks
- ✅ Activity detection and point system
- ✅ Comprehensive error handling
- ✅ Extensive test coverage
- ✅ Detailed logging and monitoring
- ✅ Performance optimizations
- ✅ API documentation
- ✅ Production-ready

No additional work is required for Task 147.
