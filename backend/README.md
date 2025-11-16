# Tamagotchi Chatbot Backend

Python FastAPI backend for the Tamagotchi Chatbot Friend application.

## Features

- **FastAPI** REST API for chatbot functionality
- **Local LLM** using llama-cpp-python (Llama 3.2 3B or Phi-3 Mini)
- **SQLite Database** with SQLAlchemy ORM
- **Safety System** with content filtering and crisis detection
- **Memory System** for user profile and conversation history
- **Personality System** with evolving traits and friendship levels
- **Parent Dashboard** with monitoring and notifications

## Prerequisites

- Python 3.10 or higher
- 8GB+ RAM (for LLM)
- 4GB+ disk space (for model files)

## Installation

### 1. Create Virtual Environment

```bash
cd backend
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 2. Install Dependencies

```bash
# Standard installation (CPU)
pip install -r requirements.txt

# For GPU support (NVIDIA CUDA)
CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python --force-reinstall --no-cache-dir

# For Apple Silicon (M1/M2/M3)
CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python --force-reinstall --no-cache-dir
```

### 3. Download LLM Model

Download one of these models:

**Option 1: Llama 3.2 3B Instruct (Recommended)**
```bash
mkdir -p models
# Download from HuggingFace
# Example: https://huggingface.co/TheBloke/Llama-3.2-3B-Instruct-GGUF
# Place the .gguf file in models/ directory
```

**Option 2: Phi-3 Mini**
```bash
mkdir -p models
# Download from HuggingFace
# Example: https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf
# Place the .gguf file in models/ directory
```

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env and set your configuration
# Especially update MODEL_PATH to point to your downloaded model
```

### 5. Initialize Database

```bash
# Database will be automatically created on first run
# Located at: data/chatbot.db
python main.py
```

## Running the Backend

### Development Mode

```bash
# With auto-reload
uvicorn main:app --reload --host 127.0.0.1 --port 8000

# Or use the main.py script
python main.py
```

### Production Mode

```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --workers 1
```

**Note:** Keep workers=1 because the LLM model is loaded in memory and shouldn't be duplicated.

## Project Structure

```
backend/
├── main.py                 # FastAPI app initialization
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── README.md              # This file
├── routes/                # API endpoint handlers
│   ├── __init__.py
│   ├── conversation.py    # Conversation endpoints
│   ├── personality.py     # Personality endpoints
│   ├── profile.py         # Profile endpoints
│   └── parent.py          # Parent dashboard endpoints
├── models/                # SQLAlchemy database models
│   ├── __init__.py
│   ├── user.py           # User model
│   ├── personality.py    # BotPersonality model
│   ├── conversation.py   # Conversation & Message models
│   ├── memory.py         # UserProfile model
│   └── safety.py         # SafetyFlag model
├── services/             # Business logic
│   ├── __init__.py
│   ├── llm_service.py    # LLM wrapper and inference
│   ├── conversation_manager.py  # Conversation flow
│   ├── memory_manager.py        # Memory extraction/retrieval
│   ├── personality_manager.py   # Personality updates
│   ├── safety_filter.py         # Safety checks
│   └── advice_system.py         # Advice templates
├── database/             # Database configuration
│   ├── __init__.py
│   ├── database.py       # SQLAlchemy setup
│   └── seed.py           # Seed data (advice templates)
├── utils/                # Utility functions
│   ├── __init__.py
│   ├── config.py         # Configuration loader
│   └── logging.py        # Logging setup
├── data/                 # Database and user data (created at runtime)
│   └── chatbot.db        # SQLite database
├── models/               # LLM model files (you must download)
│   └── *.gguf            # Model file
└── logs/                 # Application logs (created at runtime)
    └── chatbot.log
```

## API Endpoints

Visit `http://localhost:8000/docs` for interactive API documentation (Swagger UI).

### Health & Status
- `GET /` - Root endpoint with API info
- `GET /health` - Health check with LLM and database status

### Conversation
- `POST /api/conversation/start` - Start new conversation session
  - Query: `user_id` (default: 1)
  - Returns: conversation_id, greeting, personality snapshot
- `POST /api/message` - Send message and get response
  - Body: `{"user_message": "...", "conversation_id": 123, "user_id": 1}`
  - Returns: bot response with safety metadata
- `POST /api/conversation/end/{conversation_id}` - End conversation
  - Updates personality traits and friendship level
- `GET /api/conversation/{conversation_id}` - Get conversation details
  - Returns: messages, summary, topics, duration

### Personality
- `GET /api/personality` - Get current bot personality
  - Query: `user_id` (default: 1)
  - Returns: traits, mood, friendship level, quirks, interests, stats
- `GET /api/personality/description` - Get human-readable trait descriptions
  - Query: `user_id` (default: 1)
  - Returns: descriptive text for each trait level

### Profile & Memory
- `GET /api/profile` - Get user profile summary
  - Query: `user_id` (default: 1)
  - Returns: favorites, dislikes, goals, people, achievements
- `GET /api/profile/memories` - Get memory items
  - Query: `user_id` (default: 1), `category` (optional filter)
  - Returns: list of profile items with confidence scores
- `PUT /api/profile/update` - Update user information
  - Body: `{"user_id": 1, "name": "Alex", "age": 12, "grade": 7}`
  - Returns: updated user data

### Parent Dashboard (Coming Soon)
- `GET /api/parent/dashboard` - Get parent dashboard (password protected)
- `GET /api/parent/safety-events` - Get safety event log

## Configuration

See `.env.example` for all configuration options:

- **LLM Settings:** Model path, context length, temperature
- **Database:** SQLite path
- **Safety:** Content filtering toggles
- **Email:** SMTP settings for parent notifications
- **Features:** Enable/disable optional features

## Development

### Code Formatting

```bash
black .
```

### Type Checking

```bash
mypy .
```

### Testing

```bash
pytest
```

## Safety Features

- Content filtering for inappropriate language
- Crisis keyword detection (self-harm, bullying, abuse)
- Automatic parent notifications for critical events
- All messages logged with safety flags
- Age-appropriate response generation

## Performance Notes

- LLM inference time: 1-3 seconds per response (CPU), faster with GPU
- Memory usage: ~4-6GB with model loaded
- Database: SQLite is sufficient for single-user desktop app
- Recommended: Close other memory-intensive applications

## Troubleshooting

### Model Loading Issues
- Ensure model file exists at the path specified in MODEL_PATH
- Check that you have enough RAM (8GB minimum)
- Try reducing MODEL_CONTEXT_LENGTH if out of memory

### GPU Issues
- Verify CUDA/Metal is properly installed
- Check MODEL_N_GPU_LAYERS setting
- Fall back to CPU with MODEL_N_GPU_LAYERS=0

### Port Already in Use
- Change PORT in .env
- Kill process using port: `lsof -ti:8000 | xargs kill` (Mac/Linux)

## License

MIT
