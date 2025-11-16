# Tamagotchi Chatbot Friend

A safe, engaging desktop chatbot companion for preteens (ages 9-13) that develops a unique personality over time through simulated growth mechanics.

## Project Overview

This application provides emotional support, good advice, and companionship while maintaining strict safety controls. All data is stored locally with no cloud sync required.

### Core Features

- **Evolving Personality**: Bot develops traits, quirks, and catchphrases over time
- **10-Level Friendship System**: Relationship deepens with more conversations
- **Safe & Age-Appropriate**: Multi-layer content filtering and crisis detection
- **Memory System**: Remembers user preferences, important people, and past conversations
- **Parent Dashboard**: Transparent monitoring without invading privacy
- **Local LLM**: All processing happens on-device using Llama 3.2 3B or Phi-3 Mini

## Technology Stack

### Frontend
- **Electron**: Cross-platform desktop application
- **React + TypeScript**: UI components
- **Tailwind CSS**: Styling
- **Vite**: Build tool

### Backend
- **Python 3.10+**: Backend runtime
- **FastAPI**: REST API framework
- **llama-cpp-python**: Local LLM inference
- **SQLite + SQLAlchemy**: Database and ORM
- **ChromaDB** (optional): Vector storage for semantic memory

## Prerequisites

- Node.js 18+ and npm
- Python 3.10+
- 8GB+ RAM (for LLM)
- 4GB+ disk space (for model files)

## Installation

### Frontend Setup

```bash
# Install dependencies
npm install

# Run in development mode
npm run dev

# Build for production
npm run build

# Package for distribution
npm run package
```

### Backend Setup

```bash
# Navigate to backend directory (to be created)
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download LLM model (instructions to be added)
# Place model in backend/models/

# Run backend server
python main.py
```

## Project Structure

```
tamagotchi-chatbot-friend/
├── src/
│   ├── main/              # Electron main process
│   │   ├── main.ts       # App initialization
│   │   ├── ipc-handlers.ts
│   │   └── backend-manager.ts
│   ├── renderer/          # React frontend
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── styles/
│   │   └── main.tsx
│   └── shared/            # Shared TypeScript types
├── backend/               # Python FastAPI backend (to be created)
│   ├── main.py
│   ├── models/
│   ├── routes/
│   ├── services/
│   └── database/
├── dist/                  # Build output
├── package.json
└── README.md
```

## Development Roadmap

See [TODO.md](./TODO.md) for detailed task breakdown (183 tasks across 7 phases).

### Phase Overview

1. **Foundation** (Weeks 1-3): Basic chatbot with simple personality
2. **Memory System** (Weeks 4-5): Bot remembers user and conversations
3. **Personality Growth** (Weeks 6-7): Evolving traits and friendship levels
4. **Safety & Advice** (Weeks 8-9): Content filtering and expert advice
5. **Parent Dashboard** (Week 10): Monitoring and transparency
6. **Polish & Features** (Weeks 11-12): Games, achievements, customization
7. **Testing & Refinement** (Weeks 13-14): User testing and documentation

## Safety Features

- Multi-layer content filtering
- Crisis keyword detection (self-harm, bullying, abuse)
- Automatic parent notifications for critical events
- Age-appropriate advice templates reviewed by experts
- No data leaves the device

## License

MIT

## Contributing

This is a personal project. Contributions welcome after initial release.
