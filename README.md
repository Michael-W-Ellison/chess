# Tamagotchi Chatbot Friend

A safe, private desktop chatbot companion for preteens (ages 9-13) with an evolving personality and local AI processing.

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![Node](https://img.shields.io/badge/node-18+-green)
![License](https://img.shields.io/badge/license-MIT-blue)

## 🌟 Features

### Core Functionality
- **🤖 Evolving Personality**: Bot personality that changes based on interactions
- **📈 Friendship Levels**: 10-level progression system (1-151+ conversations)
- **🧠 Memory System**: Remembers user preferences, goals, and important facts
- **💬 Natural Conversations**: Powered by local LLM (Llama 3.2 3B or Phi-3 Mini)
- **🛡️ Multi-Layer Safety**: Crisis detection, profanity filtering, content monitoring
- **🔒 100% Local & Private**: All data stored on device, no cloud services

### Interface
- **Chat View**: Full conversation interface with safety indicators
- **Profile View**: Personality traits, user profile, and memory visualization
- **Settings View**: User profile management and preferences
- **Parent Dashboard**: Monitoring and safety alerts (coming soon)

### Safety Features
- Crisis keyword detection (self-harm, suicide, abuse)
- Automatic resource provision (988 hotline, Crisis Text Line)
- Profanity filtering
- Bullying and harassment detection
- Parent notification system
- All conversations logged with safety flags

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         Electron Desktop App            │
│  (React + TypeScript + Tailwind CSS)    │
└──────────────┬──────────────────────────┘
               │ REST API
               │ (http://localhost:8000)
┌──────────────▼──────────────────────────┐
│         FastAPI Backend                 │
│  (Python 3.10+ with llama-cpp-python)   │
└──────────────┬──────────────────────────┘
               │
    ┌──────────┼──────────┐
    ▼          ▼          ▼
┌───────┐  ┌───────┐  ┌────────┐
│SQLite │  │  LLM  │  │ Safety │
│  DB   │  │ Model │  │ Filter │
└───────┘  └───────┘  └────────┘
```

### Tech Stack

**Frontend:**
- Electron 28 (desktop framework)
- React 18 (UI library)
- TypeScript 5 (type safety)
- Tailwind CSS (styling)
- Vite 5 (build tool)

**Backend:**
- Python 3.10+
- FastAPI (REST API)
- SQLAlchemy 2.0 (ORM)
- llama-cpp-python (LLM inference)
- SQLite (database)
- Better-profanity (content filtering)

## 🚀 Quick Start

### Prerequisites

- **Python 3.10 or higher**
- **Node.js 18 or higher**
- **8GB+ RAM** (for LLM model)
- **4GB+ disk space** (for model files)
- **Git**

### 1. Clone Repository

```bash
git clone <repository-url>
cd chess
```

### 2. Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download LLM model (optional but recommended)
# Linux/Mac:
./scripts/setup_llm.sh
# Windows:
powershell -ExecutionPolicy Bypass -File scripts\setup_llm.ps1

# Create .env file
cp .env.example .env
# Edit .env and configure MODEL_PATH if you downloaded a model

# Start backend server
python main.py
```

The backend will start at `http://localhost:8000`

### 3. Frontend Setup

```bash
# In a new terminal, navigate to project root
cd chess

# Install dependencies
npm install

# Start development server
npm run dev
```

The Electron app will launch automatically.

## 📖 Detailed Documentation

- **[Backend README](./backend/README.md)** - Backend API documentation
- **[Installation Guide](./backend/INSTALL.md)** - LLM model installation
- **[TODO List](./TODO.md)** - Development roadmap (180 tasks)

## 🎮 Usage

### Basic Workflow

1. **Start Backend**: `cd backend && python main.py`
2. **Start Frontend**: `npm run dev`
3. **Chat**: Click the 💬 Chat tab and start talking
4. **View Profile**: Click 🤖 Profile to see personality and memories
5. **Adjust Settings**: Click ⚙️ Settings to update your profile

### Friendship Level Progression

| Level | Conversations | Name | Features Unlocked |
|-------|--------------|------|-------------------|
| 1 | 0-4 | New Friend | Basic conversation |
| 2 | 5-14 | New Friend | Quirks appear |
| 3 | 15-29 | Good Friend | Catchphrase unlocked |
| 4 | 30-49 | Good Friend | More personality traits |
| 5 | 50-74 | Close Friend | Advanced memory |
| 6 | 75-99 | Close Friend | Deeper conversations |
| 7 | 100-124 | Best Friend | Personal advice |
| 8 | 125-149 | Best Friend | Story collaboration |
| 9 | 150+ | Lifelong Friend | All features |
| 10 | 151+ | Lifelong Friend | Max level! |

### Personality Traits

The bot has four evolving traits (0.0-1.0):

- **😄 Humor**: Playfulness and joke frequency
- **⚡ Energy**: Enthusiasm and expressiveness
- **🔍 Curiosity**: Question asking and exploration
- **💼 Formality**: Casual vs. professional tone

Traits drift slowly based on conversations (max 0.02 per chat).

## 🧪 Testing

### Backend API Tests

```bash
cd backend
python test_api.py
```

### LLM Integration Tests

```bash
cd backend
python test_llm.py
```

### Frontend (Coming Soon)

```bash
npm test
```

## 📊 Project Structure

```
chess/
├── backend/                    # Python FastAPI backend
│   ├── main.py                # App entry point
│   ├── requirements.txt       # Python dependencies
│   ├── .env.example          # Environment variables template
│   ├── routes/               # API endpoints
│   │   ├── conversation.py   # Chat endpoints
│   │   ├── personality.py    # Personality endpoints
│   │   └── profile.py        # Profile endpoints
│   ├── services/             # Business logic
│   │   ├── llm_service.py    # LLM wrapper
│   │   ├── safety_filter.py  # Content filtering
│   │   ├── memory_manager.py # Memory extraction
│   │   ├── personality_manager.py
│   │   └── conversation_manager.py
│   ├── models/               # Database models (SQLAlchemy)
│   ├── database/             # DB configuration
│   ├── utils/                # Utilities
│   └── scripts/              # Setup scripts
├── src/
│   ├── main/                 # Electron main process
│   │   ├── main.ts          # Window management
│   │   ├── preload.ts       # IPC bridge
│   │   └── ipc-handlers.ts  # IPC handlers
│   ├── renderer/            # React frontend
│   │   ├── App.tsx          # Root component
│   │   ├── components/      # UI components
│   │   │   ├── ChatWindow.tsx
│   │   │   ├── ProfilePanel.tsx
│   │   │   ├── SettingsPanel.tsx
│   │   │   ├── MessageBubble.tsx
│   │   │   ├── InputArea.tsx
│   │   │   └── FriendshipMeter.tsx
│   │   ├── hooks/           # React hooks
│   │   │   ├── useChat.ts
│   │   │   ├── usePersonality.ts
│   │   │   └── useProfile.ts
│   │   └── services/        # API client
│   │       └── api.ts
│   └── shared/              # Shared types
│       ├── types.ts         # TypeScript types
│       ├── constants.ts     # App constants
│       └── utils.ts         # Utilities
├── package.json             # Node dependencies
├── tsconfig.json           # TypeScript config
├── vite.config.ts          # Vite config
├── tailwind.config.js      # Tailwind config
├── TODO.md                 # Development roadmap
└── README.md               # This file
```

## 🔒 Privacy & Security

### Data Storage
- **Database**: SQLite file at `backend/data/chatbot.db`
- **Model**: Local GGUF file in `backend/models/`
- **Logs**: Application logs in `backend/logs/`
- **No cloud services**: Everything runs locally

### Safety Measures
- Content filtering on all messages (input and output)
- Crisis keyword detection with immediate resource provision
- Parent notification system (configurable)
- Safety event logging
- Age-appropriate response generation

### Crisis Resources
- **National Suicide Prevention Lifeline**: 988
- **Crisis Text Line**: Text HOME to 741741
- **For parents**: Monitor via Parent Dashboard

## 🛠️ Development

### Running in Development Mode

```bash
# Terminal 1 - Backend with auto-reload
cd backend
uvicorn main:app --reload

# Terminal 2 - Frontend with hot-reload
npm run dev
```

### Building for Production

```bash
# Build Electron app
npm run build

# Package for distribution
npm run package
```

Distributables will be in the `release/` folder.

### Code Style

```bash
# Backend (Python)
cd backend
black .
mypy .

# Frontend (TypeScript)
npm run lint
npm run format
```

## 🗺️ Roadmap

See [TODO.md](./TODO.md) for the complete 180-task roadmap.

### Phase 1: Foundation (Weeks 1-2) ✅
- [x] Project setup
- [x] Database models
- [x] Core services
- [x] Basic UI

### Phase 2: Core Features (Weeks 3-5) ✅
- [x] Chat interface
- [x] Personality system
- [x] Memory extraction
- [x] Safety filtering

### Phase 3: Advanced Features (Weeks 6-8) 🚧
- [ ] Achievement system
- [ ] Text games
- [ ] Parent dashboard
- [ ] Memory book export

### Phase 4: Polish (Weeks 9-10) 📋
- [ ] User testing
- [ ] Performance optimization
- [ ] Bug fixes
- [ ] Documentation

## 🤝 Contributing

This is a personal project for a safe chatbot companion. Contributions focused on safety, privacy, and age-appropriate features are welcome.

## 📄 License

MIT License - See LICENSE file for details.

## ⚠️ Disclaimer

This chatbot is designed as a companion tool and should not replace professional mental health support, parental guidance, or emergency services. Always seek professional help for serious issues.

## 📧 Support

For issues, questions, or feedback, please open a GitHub issue.

---

**Built with ❤️ for safe, private, educational AI companionship**
