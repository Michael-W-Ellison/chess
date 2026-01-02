# Developer Setup Guide

**Chatbot Friend - Complete Development Environment Setup**

This comprehensive guide will walk you through setting up a complete development environment for the Chatbot Friend application, from prerequisites to running tests and debugging.

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Prerequisites Installation](#prerequisites-installation)
3. [Project Setup](#project-setup)
4. [IDE Configuration](#ide-configuration)
5. [Running the Application](#running-the-application)
6. [Development Workflow](#development-workflow)
7. [Testing](#testing)
8. [Debugging](#debugging)
9. [Code Style & Linting](#code-style--linting)
10. [Common Issues](#common-issues)
11. [Contributing Guidelines](#contributing-guidelines)
12. [Project Architecture](#project-architecture)

---

## System Requirements

### Minimum Requirements

- **OS:** Windows 10/11, macOS 10.15+, or Linux (Ubuntu 20.04+)
- **RAM:** 8GB minimum, 16GB recommended
- **Disk Space:** 10GB free space (4GB for LLM model, 6GB for development tools)
- **CPU:** Multi-core processor (4+ cores recommended)
- **Network:** Internet connection for initial setup

### Recommended Specifications

- **RAM:** 16GB+ for comfortable development
- **CPU:** 8+ cores for faster LLM inference
- **GPU:** NVIDIA GPU with CUDA support (optional, for faster LLM)
- **SSD:** For faster database and model loading

---

## Prerequisites Installation

### 1. Python 3.10+

**Check if installed:**
```bash
python --version  # or python3 --version
```

**Installation:**

**macOS** (using Homebrew):
```bash
brew install python@3.10
```

**Ubuntu/Debian**:
```bash
sudo apt update
sudo apt install python3.10 python3.10-venv python3.10-dev
```

**Windows**:
- Download from [python.org](https://www.python.org/downloads/)
- Ensure "Add Python to PATH" is checked during installation

### 2. Node.js 18+

**Check if installed:**
```bash
node --version
npm --version
```

**Installation:**

**macOS** (using Homebrew):
```bash
brew install node@18
```

**Ubuntu/Debian** (using NodeSource):
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

**Windows**:
- Download LTS version from [nodejs.org](https://nodejs.org/)
- Run the installer with default options

### 3. Git

**Check if installed:**
```bash
git --version
```

**Installation:**

**macOS**:
```bash
brew install git
```

**Ubuntu/Debian**:
```bash
sudo apt install git
```

**Windows**:
- Download from [git-scm.com](https://git-scm.com/)
- Use default options, select "Git Bash" terminal

### 4. C++ Build Tools (Required for llama-cpp-python)

**macOS**:
```bash
xcode-select --install
```

**Ubuntu/Debian**:
```bash
sudo apt install build-essential cmake
```

**Windows**:
- Install [Visual Studio Build Tools](https://visualstudio.microsoft.com/downloads/)
- Select "Desktop development with C++" workload
- Alternatively, install [MinGW-w64](https://www.mingw-w64.org/)

---

## Project Setup

### 1. Clone the Repository

```bash
# Clone the repository
git clone https://github.com/your-username/chatbot-friend.git
cd chatbot-friend

# Verify you're in the correct directory
ls -la  # Should see package.json, backend/, src/, etc.
```

### 2. Backend Setup

#### Create Virtual Environment

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate

# Windows (Command Prompt):
venv\Scripts\activate.bat

# Windows (PowerShell):
venv\Scripts\Activate.ps1

# Windows (Git Bash):
source venv/Scripts/activate

# Verify activation (should show (venv) in prompt)
which python  # macOS/Linux
where python  # Windows
```

#### Install Python Dependencies

```bash
# Ensure virtual environment is activated
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt

# For GPU support (NVIDIA CUDA):
CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python --force-reinstall --no-cache-dir

# For Apple Silicon (M1/M2/M3):
CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python --force-reinstall --no-cache-dir
```

**Note:** The initial `llama-cpp-python` installation may take 5-15 minutes as it compiles from source.

#### Download LLM Model

**Option 1: Automated Script (Recommended)**

```bash
# macOS/Linux:
chmod +x scripts/setup_llm.sh
./scripts/setup_llm.sh

# Windows (PowerShell):
powershell -ExecutionPolicy Bypass -File scripts\setup_llm.ps1
```

**Option 2: Manual Download**

1. Create models directory:
   ```bash
   mkdir -p models
   ```

2. Download a GGUF model from HuggingFace:
   - **Llama 3.2 3B Instruct** (Recommended):
     - [TheBloke/Llama-3.2-3B-Instruct-GGUF](https://huggingface.co/TheBloke/Llama-3.2-3B-Instruct-GGUF)
     - Download `llama-3.2-3b-instruct.Q4_K_M.gguf` (2.1GB)

   - **Phi-3 Mini** (Alternative):
     - [microsoft/Phi-3-mini-4k-instruct-gguf](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf)
     - Download `Phi-3-mini-4k-instruct-q4.gguf` (2.4GB)

3. Place the `.gguf` file in `backend/models/`

#### Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your preferred text editor
nano .env  # or vim, code, notepad, etc.
```

**Key settings in `.env`:**

```env
# Path to your downloaded model
MODEL_PATH=models/llama-3.2-3b-instruct.Q4_K_M.gguf

# Context length (default: 2048)
MODEL_CONTEXT_LENGTH=2048

# GPU layers (0 for CPU only, 20-35 for GPU)
MODEL_N_GPU_LAYERS=0

# Temperature for creativity (0.0-1.0)
MODEL_TEMPERATURE=0.7

# Database path
DATABASE_URL=sqlite:///./data/chatbot.db

# Safety features
ENABLE_PROFANITY_FILTER=true
ENABLE_CRISIS_DETECTION=true

# Development mode
DEBUG=true
```

#### Initialize Database

```bash
# Start the backend to create database
python main.py

# Database will be created at backend/data/chatbot.db
# Stop with Ctrl+C
```

### 3. Frontend Setup

```bash
# Return to project root
cd ..

# Install Node.js dependencies
npm install

# This will install:
# - Electron
# - React + TypeScript
# - Tailwind CSS
# - Vite
# - All other dependencies

# Verify installation
npm list --depth=0
```

### 4. Verify Installation

```bash
# Check Python backend
cd backend
python -c "import fastapi, sqlalchemy, llama_cpp; print('✓ All Python packages installed')"

# Check Node.js frontend
cd ..
npm run build:renderer  # Should complete without errors
```

---

## IDE Configuration

### Visual Studio Code (Recommended)

#### Install VS Code

Download from [code.visualstudio.com](https://code.visualstudio.com/)

#### Recommended Extensions

Install these extensions for the best development experience:

**Python Development:**
- `ms-python.python` - Python language support
- `ms-python.vscode-pylance` - Fast Python language server
- `ms-python.black-formatter` - Code formatting
- `ms-python.pylint` - Linting
- `ms-toolsai.jupyter` - Jupyter notebook support (optional)

**TypeScript/React Development:**
- `dbaeumer.vscode-eslint` - JavaScript/TypeScript linting
- `esbenp.prettier-vscode` - Code formatting
- `bradlc.vscode-tailwindcss` - Tailwind CSS IntelliSense
- `dsznajder.es7-react-js-snippets` - React snippets

**General:**
- `eamodio.gitlens` - Git integration
- `gruntfuggly.todo-tree` - TODO highlighting
- `christian-kohler.path-intellisense` - Path autocomplete
- `yzhang.markdown-all-in-one` - Markdown support

#### Workspace Settings

Create `.vscode/settings.json`:

```json
{
  // Python
  "python.defaultInterpreterPath": "${workspaceFolder}/backend/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length", "100"],

  // TypeScript
  "typescript.tsdk": "node_modules/typescript/lib",
  "typescript.enablePromptUseWorkspaceTsdk": true,

  // Editor
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  },

  // Files
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    "**/node_modules": true,
    "**/venv": true,
    "**/.pytest_cache": true
  }
}
```

Create `.vscode/launch.json` for debugging:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["main:app", "--reload", "--host", "127.0.0.1", "--port", "8000"],
      "cwd": "${workspaceFolder}/backend",
      "env": {
        "PYTHONPATH": "${workspaceFolder}/backend"
      }
    },
    {
      "name": "Electron: Main",
      "type": "node",
      "request": "launch",
      "cwd": "${workspaceFolder}",
      "runtimeExecutable": "${workspaceFolder}/node_modules/.bin/electron",
      "args": ["."],
      "outputCapture": "std"
    }
  ]
}
```

### PyCharm (Alternative)

#### Configuration

1. Open `backend/` as a project
2. Configure Python Interpreter:
   - File → Settings → Project → Python Interpreter
   - Select the venv interpreter: `backend/venv/bin/python`
3. Enable FastAPI support:
   - File → Settings → Languages & Frameworks → Python → FastAPI
   - Check "Enable FastAPI support"
4. Configure code style:
   - File → Settings → Editor → Code Style → Python
   - Set line length to 100
   - Enable Black formatter

---

## Running the Application

### Development Mode (Recommended)

**Terminal 1 - Backend with Hot Reload:**
```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
python main.py
# or
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Backend will start at `http://localhost:8000`

**Terminal 2 - Frontend with Hot Reload:**
```bash
# From project root
npm run dev
```

Electron app will launch automatically.

### Production Build

```bash
# Build renderer process
npm run build:renderer

# Build main process
npm run build:main

# Package application
npm run package

# Distributables will be in release/ folder
```

### Running Tests

**Backend Tests:**
```bash
cd backend
source venv/bin/activate

# Run all tests
pytest

# Run specific test file
pytest tests/test_safety_filter.py

# Run with coverage
pytest --cov=. --cov-report=html

# Run with verbose output
pytest -v
```

**Frontend Tests** (when implemented):
```bash
npm test
```

---

## Development Workflow

### Daily Development Process

1. **Start your day:**
   ```bash
   cd backend
   source venv/bin/activate
   git pull origin main
   ```

2. **Create feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Start development servers:**
   - Terminal 1: `python main.py`
   - Terminal 2: `npm run dev`

4. **Make changes:**
   - Backend: Edit files in `backend/`
   - Frontend: Edit files in `src/`
   - Auto-reload will apply changes

5. **Test changes:**
   ```bash
   # Backend tests
   cd backend && pytest

   # Manual testing in Electron app
   ```

6. **Commit changes:**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   git push origin feature/your-feature-name
   ```

### Git Workflow

We follow [Conventional Commits](https://www.conventionalcommits.org/):

**Commit Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting)
- `refactor:` - Code refactoring
- `test:` - Adding tests
- `chore:` - Maintenance tasks

**Examples:**
```bash
git commit -m "feat: add achievement system"
git commit -m "fix: resolve memory leak in chat window"
git commit -m "docs: update API documentation"
git commit -m "test: add tests for safety filter"
```

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation
- `refactor/description` - Refactoring
- `test/description` - Tests

---

## Testing

### Backend Testing Strategy

**Unit Tests:**
```python
# tests/test_safety_filter.py
def test_profanity_detection():
    filter = SafetyFilter()
    result = filter.check_message("This contains profanity")
    assert result.flagged == True
    assert result.flag_type == "profanity"
```

**Integration Tests:**
```python
# tests/test_api.py
def test_send_message_endpoint(client):
    response = client.post("/api/message", json={
        "user_message": "Hello!",
        "conversation_id": 1,
        "user_id": 1
    })
    assert response.status_code == 200
    assert "content" in response.json()
```

**Running Tests:**
```bash
# All tests
pytest

# Specific test
pytest tests/test_safety_filter.py::test_profanity_detection

# With coverage
pytest --cov=services --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Frontend Testing (Future)

```bash
# Unit tests (React components)
npm test

# E2E tests
npm run test:e2e

# Coverage
npm run test:coverage
```

---

## Debugging

### Backend Debugging

#### VS Code Debugging

1. Set breakpoints in Python code (click left of line numbers)
2. Press F5 or Run → Start Debugging
3. Select "Python: FastAPI" configuration
4. Interact with API through frontend or curl
5. Debugger will pause at breakpoints

#### Print Debugging

```python
# Add logging
import logging
logger = logging.getLogger(__name__)

def some_function():
    logger.info(f"Variable value: {variable}")
    logger.debug(f"Detailed debug info: {data}")
```

View logs:
```bash
tail -f backend/logs/chatbot.log
```

#### Interactive Debugging (pdb)

```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# When hit, use commands:
# n - next line
# s - step into function
# c - continue
# p variable - print variable
# q - quit
```

### Frontend Debugging

#### Chrome DevTools

1. Open Electron app
2. Open DevTools:
   - macOS: `Cmd + Option + I`
   - Windows/Linux: `Ctrl + Shift + I`
   - Or View → Toggle Developer Tools

3. Use Console, Network, React DevTools tabs

#### React DevTools

Install React DevTools extension in Electron:

```typescript
// src/main/main.ts (development only)
if (isDev) {
  const { default: installExtension, REACT_DEVELOPER_TOOLS } = require('electron-devtools-installer');

  app.whenReady().then(() => {
    installExtension(REACT_DEVELOPER_TOOLS)
      .then((name) => console.log(`Added Extension:  ${name}`))
      .catch((err) => console.log('An error occurred: ', err));
  });
}
```

#### Debugging Tips

**Network Issues:**
- Check if backend is running: `curl http://localhost:8000/health`
- Check browser console for failed requests
- Verify API endpoints in Network tab

**State Issues:**
- Use React DevTools to inspect component state
- Add console.log in useEffect hooks
- Check Redux DevTools (if using Redux)

**Performance Issues:**
- Use Chrome Performance profiler
- Check for memory leaks in Memory tab
- Use React Profiler for component renders

---

## Code Style & Linting

### Python (Backend)

**Formatter: Black**
```bash
cd backend

# Format all files
black .

# Format specific file
black services/llm_service.py

# Check without modifying
black --check .
```

**Linter: Pylint**
```bash
# Lint all files
pylint **/*.py

# Lint specific file
pylint services/llm_service.py

# Disable specific rule
pylint --disable=C0111 services/  # Disable missing docstring
```

**Type Checking: mypy**
```bash
# Check types
mypy .

# Ignore missing imports
mypy --ignore-missing-imports .
```

**Style Guide:**
- PEP 8 compliance
- Line length: 100 characters
- Use type hints for function parameters and returns
- Docstrings for all public functions
- Descriptive variable names

**Example:**
```python
def extract_memory_items(
    message: str,
    category: MemoryCategory
) -> List[ProfileItem]:
    """Extract memory items from user message.

    Args:
        message: User's message text
        category: Category to extract (favorite, dislike, etc.)

    Returns:
        List of extracted profile items with confidence scores
    """
    items = []
    # ... implementation
    return items
```

### TypeScript/React (Frontend)

**Formatter: Prettier**
```bash
# Format all files
npm run format

# Check formatting
npm run format:check
```

**Linter: ESLint**
```bash
# Lint all files
npm run lint

# Fix auto-fixable issues
npm run lint:fix
```

**Configuration** (`.prettierrc`):
```json
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 100,
  "tabWidth": 2,
  "arrowParens": "always"
}
```

**Style Guide:**
- Use functional components with hooks
- Avoid `any` type, use specific types
- Props interfaces for all components
- Descriptive variable and function names
- One component per file

**Example:**
```typescript
interface MessageBubbleProps {
  message: ChatMessage;
  isUser: boolean;
  onRetry?: () => void;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({
  message,
  isUser,
  onRetry,
}) => {
  return (
    <div className={isUser ? 'user-message' : 'bot-message'}>
      {message.content}
    </div>
  );
};
```

---

## Common Issues

### Backend Issues

#### 1. Model Loading Fails

**Symptom:**
```
FileNotFoundError: Model file not found at models/...
```

**Solution:**
```bash
# Verify model file exists
ls -lh backend/models/

# Check MODEL_PATH in .env
grep MODEL_PATH backend/.env

# Download model if missing
cd backend
./scripts/setup_llm.sh
```

#### 2. Out of Memory

**Symptom:**
```
RuntimeError: Failed to allocate memory for model
```

**Solutions:**
```env
# Reduce context length in .env
MODEL_CONTEXT_LENGTH=1024

# Disable GPU layers
MODEL_N_GPU_LAYERS=0

# Use smaller model
# Switch from Q6 to Q4 quantization
```

#### 3. Port Already in Use

**Symptom:**
```
OSError: [Errno 48] Address already in use
```

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill the process
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows

# Or change port in .env
PORT=8001
```

#### 4. Database Locked

**Symptom:**
```
sqlite3.OperationalError: database is locked
```

**Solution:**
```bash
# Stop all processes accessing database
# Delete database lock file
rm backend/data/chatbot.db-journal

# If persists, recreate database
rm backend/data/chatbot.db
python main.py  # Will recreate
```

#### 5. Import Errors

**Symptom:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Solution:**
```bash
# Verify virtual environment is activated
which python  # Should point to venv

# Reinstall dependencies
pip install -r requirements.txt

# If still fails, recreate venv
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend Issues

#### 1. npm install Fails

**Symptom:**
```
npm ERR! code EACCES
```

**Solution:**
```bash
# Fix permissions (macOS/Linux)
sudo chown -R $(whoami) ~/.npm
sudo chown -R $(whoami) node_modules

# Or install with --no-optional
npm install --no-optional

# Clear cache and retry
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

#### 2. Electron Won't Start

**Symptom:**
```
Error: Electron failed to install correctly
```

**Solution:**
```bash
# Reinstall Electron
npm uninstall electron
npm install electron --save-dev

# If on Linux, install dependencies
sudo apt install libgtk-3-0 libnotify4 libnss3 libxss1
```

#### 3. TypeScript Errors

**Symptom:**
```
TS2307: Cannot find module '@/components/...'
```

**Solution:**
```bash
# Restart TypeScript server in VS Code
# Cmd+Shift+P → "TypeScript: Restart TS Server"

# Verify tsconfig.json paths
cat tsconfig.json | grep paths

# Rebuild
npm run build:renderer
```

#### 4. Hot Reload Not Working

**Solution:**
```bash
# Restart dev server
# Ctrl+C to stop
npm run dev

# Clear Vite cache
rm -rf node_modules/.vite
npm run dev
```

### Cross-Platform Issues

#### Windows-Specific

**Line Endings:**
```bash
# Configure git to handle CRLF
git config --global core.autocrlf true
```

**Path Separators:**
```python
# Always use os.path or pathlib
from pathlib import Path
model_path = Path("models") / "model.gguf"
```

#### macOS-Specific

**Gatekeeper:**
```bash
# If Electron won't open
xattr -cr node_modules/electron/dist/Electron.app
```

---

## Contributing Guidelines

### Before You Start

1. **Check existing issues** to avoid duplicate work
2. **Open an issue** to discuss major changes
3. **Fork the repository** for external contributions

### Development Process

1. **Create feature branch:**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make changes:**
   - Write clean, documented code
   - Follow style guidelines
   - Add tests for new features

3. **Test thoroughly:**
   ```bash
   # Backend tests
   cd backend && pytest

   # Lint checks
   black . && pylint **/*.py

   # Frontend lint
   npm run lint
   ```

4. **Commit with conventional commits:**
   ```bash
   git commit -m "feat: add new feature"
   ```

5. **Push and create PR:**
   ```bash
   git push origin feature/my-feature
   # Then create Pull Request on GitHub
   ```

### Pull Request Guidelines

**PR Title:** Use conventional commit format
```
feat: add achievement system
fix: resolve memory leak in chat
docs: update installation guide
```

**PR Description:**
```markdown
## Description
Brief description of changes

## Related Issue
Closes #123

## Changes Made
- Added feature X
- Fixed bug Y
- Updated documentation Z

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] No new linting errors

## Screenshots (if applicable)
[Add screenshots]

## Checklist
- [ ] Code follows style guidelines
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

### Code Review Process

1. **Self-review** before submitting
2. **Address feedback** from reviewers
3. **Keep commits clean** (squash if needed)
4. **Update branch** if main has changed

---

## Project Architecture

### Application Structure

```
chatbot-friend/
├── backend/                  # Python FastAPI backend
│   ├── main.py              # FastAPI app initialization
│   ├── routes/              # API endpoints
│   │   ├── conversation.py  # Chat endpoints
│   │   ├── personality.py   # Personality management
│   │   ├── profile.py       # User profile
│   │   └── parent.py        # Parent dashboard
│   ├── services/            # Business logic layer
│   │   ├── llm_service.py   # LLM inference wrapper
│   │   ├── conversation_manager.py  # Chat orchestration
│   │   ├── memory_manager.py        # Memory extraction
│   │   ├── personality_manager.py   # Trait evolution
│   │   ├── safety_filter.py         # Content filtering
│   │   └── advice_system.py         # Advice templates
│   ├── models/              # SQLAlchemy ORM models
│   │   ├── user.py         # User data
│   │   ├── personality.py  # Bot personality
│   │   ├── conversation.py # Chat history
│   │   ├── memory.py       # User profile items
│   │   └── safety.py       # Safety events
│   ├── database/           # Database configuration
│   │   ├── database.py    # SQLAlchemy setup
│   │   └── seed.py        # Seed data
│   ├── utils/             # Utilities
│   │   ├── config.py      # Environment config
│   │   └── logging.py     # Logging setup
│   └── tests/             # Backend tests
├── src/
│   ├── main/              # Electron main process
│   │   ├── main.ts        # App lifecycle, window management
│   │   ├── preload.ts     # IPC bridge (contextBridge)
│   │   ├── ipc-handlers.ts # IPC request handlers
│   │   ├── backend-manager.ts  # Python backend lifecycle
│   │   └── store.ts       # electron-store configuration
│   ├── renderer/          # React frontend (Electron renderer)
│   │   ├── App.tsx        # Root component, routing
│   │   ├── components/    # React components
│   │   │   ├── common/    # Reusable components
│   │   │   └── parent/    # Parent dashboard
│   │   ├── contexts/      # React contexts (theme, color, etc.)
│   │   ├── hooks/         # Custom React hooks
│   │   │   ├── useChat.ts
│   │   │   ├── usePersonality.ts
│   │   │   ├── useProfile.ts
│   │   │   └── useElectronStore.ts
│   │   ├── services/      # API client layer
│   │   │   └── api.ts     # HTTP requests to backend
│   │   └── styles/        # CSS files
│   └── shared/            # Shared types and utilities
│       ├── types.ts       # TypeScript interfaces
│       ├── settings-schema.ts    # Settings types
│       ├── settings-defaults.ts  # Default values
│       ├── settings-validation.ts # Validation
│       ├── constants.ts   # App constants
│       ├── utils.ts       # Utility functions
│       └── soundEffects.ts # Audio synthesis
├── dist/                  # Build output (gitignored)
├── release/               # Packaged apps (gitignored)
├── node_modules/          # Node dependencies (gitignored)
└── docs/                  # Additional documentation
```

### Data Flow

```
User Input (Renderer)
    ↓ (IPC)
Main Process (IPC Handler)
    ↓ (HTTP Request)
Backend API Endpoint
    ↓
Route Handler
    ↓
Service Layer (Business Logic)
    ↓
├─→ LLM Service (Generate Response)
├─→ Safety Filter (Check Content)
├─→ Memory Manager (Extract/Retrieve)
├─→ Personality Manager (Update Traits)
└─→ Database (Store Data)
    ↓
Response (JSON)
    ↓ (HTTP Response)
Main Process
    ↓ (IPC)
Renderer Process (Update UI)
```

### Technology Stack

**Backend:**
- **FastAPI** - Modern async Python web framework
- **SQLAlchemy 2.0** - SQL toolkit and ORM
- **llama-cpp-python** - Python bindings for llama.cpp (LLM)
- **Pydantic** - Data validation using Python type hints
- **Better-profanity** - Profanity filter

**Frontend:**
- **Electron** - Cross-platform desktop framework
- **React 18** - UI library with hooks
- **TypeScript 5** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **Vite** - Fast build tool and dev server

**Database:**
- **SQLite** - Embedded SQL database (single file)

**Development Tools:**
- **pytest** - Python testing framework
- **Black** - Python code formatter
- **Pylint** - Python linter
- **ESLint** - TypeScript/JavaScript linter
- **Prettier** - Code formatter

### Key Design Patterns

**Backend:**
- **Service Layer Pattern** - Business logic separated from routes
- **Repository Pattern** - Database access abstraction
- **Dependency Injection** - FastAPI's dependency system
- **Strategy Pattern** - Multiple LLM implementations

**Frontend:**
- **Component Pattern** - Reusable React components
- **Hook Pattern** - Custom hooks for state logic
- **Context Pattern** - Global state (theme, settings)
- **Service Pattern** - API client layer

### Security Considerations

**Content Security:**
- All user input filtered through safety system
- Multi-layer filtering (profanity, crisis, bullying)
- Parent notification system for critical events

**Data Privacy:**
- All data stored locally (no cloud services)
- SQLite database in user's data directory
- Parental dashboard password-protected

**Electron Security:**
- `contextIsolation: true` - Separate renderer context
- `nodeIntegration: false` - No direct Node.js access in renderer
- `sandbox: true` - Renderer process sandboxed
- IPC channel whitelisting

---

## Next Steps

### After Setup

1. **Explore the codebase:**
   ```bash
   # Read main components
   cat src/renderer/App.tsx
   cat backend/main.py
   ```

2. **Run the application:**
   ```bash
   # Terminal 1
   cd backend && python main.py

   # Terminal 2
   npm run dev
   ```

3. **Make a small change:**
   - Edit a component's text
   - See hot-reload in action
   - Verify your environment works

4. **Run tests:**
   ```bash
   cd backend && pytest -v
   ```

5. **Read documentation:**
   - See `backend/README.md` for API docs
   - Check `TODO.md` for development roadmap
   - Read `TASK_*_COMPLETION.md` for implementation details

### Learning Resources

**Python/FastAPI:**
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Tutorial](https://docs.sqlalchemy.org/en/20/tutorial/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)

**TypeScript/React:**
- [React Documentation](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)
- [Tailwind CSS Docs](https://tailwindcss.com/docs)

**Electron:**
- [Electron Documentation](https://www.electronjs.org/docs/latest/)
- [Electron Security](https://www.electronjs.org/docs/latest/tutorial/security)

**LLM Development:**
- [llama.cpp Documentation](https://github.com/ggerganov/llama.cpp)
- [GGUF Model Format](https://github.com/ggerganov/ggml/blob/master/docs/gguf.md)

---

## Getting Help

### Documentation

- **Main README:** `README.md`
- **Backend API:** `backend/README.md`
- **API Docs:** `http://localhost:8000/docs` (when backend running)
- **Task Completions:** `TASK_*_COMPLETION.md` files

### Troubleshooting

1. Check [Common Issues](#common-issues) section above
2. Search existing GitHub issues
3. Enable debug logging:
   ```env
   # backend/.env
   DEBUG=true
   LOG_LEVEL=DEBUG
   ```
4. Check logs:
   ```bash
   tail -f backend/logs/chatbot.log
   ```

### Community

- **Issues:** Report bugs via GitHub Issues
- **Discussions:** Ask questions in GitHub Discussions
- **Contributing:** See [Contributing Guidelines](#contributing-guidelines)

---

**Happy coding! 🚀**

*Last updated: 2025-11-19*
