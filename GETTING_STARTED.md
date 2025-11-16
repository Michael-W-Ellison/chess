# Getting Started with Tamagotchi Chatbot Friend

This guide will walk you through setting up the Tamagotchi Chatbot Friend application from scratch. Follow each step carefully to ensure a smooth setup.

## 📋 Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation](#installation)
3. [Backend Setup](#backend-setup)
4. [LLM Model Setup](#llm-model-setup)
5. [Frontend Setup](#frontend-setup)
6. [Running the Application](#running-the-application)
7. [First Conversation](#first-conversation)
8. [Troubleshooting](#troubleshooting)
9. [Next Steps](#next-steps)

---

## System Requirements

### Minimum Requirements

- **Operating System**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 20.04+)
- **RAM**: 8GB minimum (16GB recommended)
- **Storage**: 10GB free disk space
  - 2GB for application code and dependencies
  - 4GB for LLM model file
  - 4GB for data and cache
- **CPU**: Modern multi-core processor (Intel i5/AMD Ryzen 5 or better)
- **GPU** (optional): NVIDIA GPU with CUDA support for faster inference

### Software Prerequisites

- **Python**: Version 3.10 or higher
- **Node.js**: Version 18 or higher
- **Git**: For cloning the repository
- **Internet connection**: For initial setup only (optional for offline use afterwards)

### Verify Prerequisites

Open a terminal and run these commands to verify your setup:

```bash
# Check Python version (should be 3.10+)
python --version
# or
python3 --version

# Check Node.js version (should be 18+)
node --version

# Check npm version
npm --version

# Check Git
git --version
```

---

## Installation

### 1. Clone the Repository

```bash
# Clone the repository
git clone <repository-url>

# Navigate to the project directory
cd chess

# Verify the structure
ls -la
```

You should see directories like `backend/`, `src/`, `package.json`, etc.

---

## Backend Setup

### 2. Create Python Virtual Environment

Navigate to the backend directory and create an isolated Python environment:

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv
# or on some systems:
python3 -m venv venv
```

### 3. Activate Virtual Environment

**On Linux/macOS:**
```bash
source venv/bin/activate
```

**On Windows (Command Prompt):**
```cmd
venv\Scripts\activate
```

**On Windows (PowerShell):**
```powershell
venv\Scripts\Activate.ps1
```

You should see `(venv)` appear at the beginning of your terminal prompt.

### 4. Install Python Dependencies

```bash
# Make sure you're in the backend/ directory with venv activated
pip install -r requirements.txt
```

This will install:
- FastAPI (REST API framework)
- SQLAlchemy (database ORM)
- llama-cpp-python (LLM inference)
- Better-profanity (content filtering)
- And other dependencies

**Note**: Installing `llama-cpp-python` may take several minutes as it compiles C++ code.

### 5. Configure Environment Variables

```bash
# Copy the example configuration
cp .env.example .env

# Open .env in your text editor
nano .env
# or
vim .env
# or use any text editor
```

**Minimum required changes:**
- `MODEL_PATH`: Update if you download a model with a different name
- Everything else can use defaults for now

**Example .env configuration:**
```bash
HOST=127.0.0.1
PORT=8000
DEBUG=true
DATABASE_URL=sqlite:///./data/chatbot.db
MODEL_PATH=./models/llama-3.2-3b-instruct-q4_k_m.gguf
MODEL_N_GPU_LAYERS=0  # Set to -1 if you have NVIDIA GPU
```

---

## LLM Model Setup

You have two options: use the chatbot with or without a local LLM model.

### Option 1: Without LLM Model (Quick Start)

The application will work with fallback responses if no model is present. This is useful for testing the interface.

**Skip to [Frontend Setup](#frontend-setup)**

### Option 2: With LLM Model (Recommended)

Download a language model for full chatbot functionality.

#### Automatic Installation (Recommended)

**On Linux/macOS:**
```bash
# Make sure you're in backend/ directory
./scripts/setup_llm.sh
```

**On Windows:**
```powershell
# Run PowerShell as Administrator
Set-ExecutionPolicy Bypass -Scope Process
.\scripts\setup_llm.ps1
```

The script will:
1. Detect your hardware (CPU/GPU)
2. Recommend a model
3. Guide you through downloading

#### Manual Installation

1. **Create models directory:**
   ```bash
   mkdir -p models
   cd models
   ```

2. **Choose and download a model:**

   **Option A: Llama 3.2 3B (Recommended)**
   - Size: ~2.5GB
   - Quality: Excellent
   - Speed: Medium

   Download from HuggingFace:
   ```bash
   # Visit: https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF
   # Download: Llama-3.2-3B-Instruct-Q4_K_M.gguf
   ```

   **Option B: Phi-3 Mini**
   - Size: ~2.3GB
   - Quality: Very good
   - Speed: Fast

   Download from HuggingFace:
   ```bash
   # Visit: https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf
   # Download: Phi-3-mini-4k-instruct-q4.gguf
   ```

3. **Verify download:**
   ```bash
   ls -lh models/
   # You should see a .gguf file around 2-3GB
   ```

4. **Update .env:**
   ```bash
   # Edit backend/.env and set MODEL_PATH to your downloaded file
   MODEL_PATH=./models/Llama-3.2-3B-Instruct-Q4_K_M.gguf
   ```

#### GPU Acceleration (Optional)

If you have an NVIDIA GPU:

**On Linux:**
```bash
# Reinstall llama-cpp-python with CUDA support
CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python --force-reinstall --no-cache-dir
```

**On macOS (Apple Silicon M1/M2/M3):**
```bash
# Reinstall with Metal support
CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python --force-reinstall --no-cache-dir
```

Then update `.env`:
```bash
MODEL_N_GPU_LAYERS=-1  # Use all GPU layers
```

---

## Frontend Setup

### 6. Install Node.js Dependencies

```bash
# Navigate to project root (from backend/)
cd ..

# Install dependencies
npm install
```

This will install:
- Electron (desktop framework)
- React (UI library)
- Vite (build tool)
- TypeScript
- Tailwind CSS
- And other frontend dependencies

**Note**: This may take a few minutes.

### 7. Verify Installation

```bash
# Check that node_modules was created
ls node_modules/

# Verify package.json scripts
npm run
```

---

## Running the Application

### 8. Start the Backend Server

**Terminal 1 - Backend:**

```bash
# Navigate to backend (if not already there)
cd backend

# Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Start the server
python main.py
```

You should see output like:
```
INFO:     Starting application...
INFO:     Database initialized
INFO:     LLM model loaded successfully
INFO:     Application startup complete
INFO:     Uvicorn running on http://127.0.0.1:8000
```

**If you see errors**, check the [Troubleshooting](#troubleshooting) section.

The backend will:
- Create `data/` directory for SQLite database
- Create `logs/` directory for application logs
- Attempt to load the LLM model (if present)
- Start the REST API server on port 8000

### 9. Start the Frontend Application

**Terminal 2 - Frontend:**

```bash
# Navigate to project root (new terminal)
cd chess

# Start the development server
npm run dev
```

You should see output like:
```
VITE v5.x.x  ready in xxx ms
➜  Local:   http://localhost:5173/
```

The Electron app should launch automatically. If not, open your browser to `http://localhost:5173/`

---

## First Conversation

### 10. Using the Application

Once the app opens:

1. **Chat View** (default):
   - You'll see a greeting from the bot
   - Type a message in the input box at the bottom
   - Press Enter or click the send button
   - The bot will respond (may take 1-3 seconds with LLM)

2. **Profile View** (click 🤖 Profile):
   - **Personality Tab**: See the bot's traits and friendship level
   - **Your Profile Tab**: See what the bot has learned about you
   - **Memories Tab**: View extracted facts and preferences

3. **Settings View** (click ⚙️ Settings):
   - Update your name, age, and grade
   - View privacy information
   - See app version and status

4. **Parent Dashboard** (click 👨‍👩‍👧):
   - Coming soon placeholder

### 11. Example First Conversation

Try these messages to get started:

```
You: Hi! My name is Alex and I'm 12 years old.
Bot: Hi Alex! It's so nice to meet you! I'm [Bot Name]...

You: I love playing video games, especially Minecraft.
Bot: Minecraft is awesome! I'd love to hear about your builds...

You: What's your favorite color?
Bot: I think I really like blue! It's calm and creative...
```

The bot will:
- Remember your name and age
- Extract facts about your interests (video games, Minecraft)
- Build a personality based on your conversations
- Increase friendship level as you chat more

---

## Troubleshooting

### Backend Issues

#### "ModuleNotFoundError" when running main.py
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

#### "Address already in use" error
```bash
# Port 8000 is already taken. Either:

# Option 1: Kill the process using port 8000
# On Linux/Mac:
lsof -ti:8000 | xargs kill

# On Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Option 2: Change port in .env
PORT=8001
```

#### LLM model fails to load
```bash
# Check file exists
ls -lh backend/models/

# Check .env MODEL_PATH is correct
cat backend/.env | grep MODEL_PATH

# Try reducing context length in .env
MODEL_CONTEXT_LENGTH=1024
MODEL_N_GPU_LAYERS=0
```

#### Database errors
```bash
# Reset database
cd backend
python -c "from database.database import reset_database; reset_database()"
```

### Frontend Issues

#### Electron doesn't launch
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install

# Or try browser mode
npm run dev
# Then open http://localhost:5173 in browser
```

#### "CORS error" in browser console
```bash
# Make sure backend is running on port 8000
# Check backend/.env CORS_ORIGINS includes frontend URL
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

#### TypeScript errors
```bash
# Rebuild TypeScript
npm run build

# Or ignore and run anyway
npm run dev
```

### General Issues

#### Out of memory when loading model
```bash
# Use a smaller model or reduce context length
MODEL_CONTEXT_LENGTH=1024

# Or run without model (fallback responses)
# Just don't put a model in models/ directory
```

#### Slow response times
```bash
# Enable GPU if available (see GPU Acceleration section)
# Or use a smaller model
# Or reduce max tokens in .env
MODEL_MAX_TOKENS=100
```

---

## Next Steps

### Understanding Friendship Levels

The bot's personality evolves through 10 friendship levels:

| Level | Conversations Needed | Features Unlocked |
|-------|---------------------|-------------------|
| 1 | 0 (start) | Basic conversation |
| 2 | 5 | Quirks appear |
| 3 | 15 | Catchphrase unlocked |
| 4-6 | 30-99 | Deeper personality |
| 7-9 | 100-149 | Advanced features |
| 10 | 151+ | Max level! |

Have at least 15 conversations to unlock the catchphrase!

### Safety Features

The app includes multi-layer safety:

- **Crisis Detection**: Keywords for self-harm, suicide trigger resources
- **Content Filtering**: Profanity and inappropriate content blocked
- **Local Only**: No data sent to cloud
- **Parent Monitoring**: Dashboard for parents (coming soon)

If you're in crisis:
- **National Suicide Prevention Lifeline**: 988
- **Crisis Text Line**: Text HOME to 741741

### Customization

Edit `backend/.env` to customize:
- Personality drift speed
- Friendship level thresholds
- Safety filter sensitivity
- Model parameters (temperature, max tokens)

### Testing the API

```bash
# Run backend tests
cd backend
python test_api.py

# Test LLM directly
python test_llm.py
```

### Building for Production

```bash
# Build Electron app
npm run build

# Package for distribution
npm run package

# Find distributables in release/ folder
```

---

## Support

### Documentation

- **[README.md](./README.md)**: Project overview
- **[Backend README](./backend/README.md)**: API documentation
- **[Installation Guide](./backend/INSTALL.md)**: LLM setup details
- **[TODO.md](./TODO.md)**: Development roadmap

### Getting Help

- Check the troubleshooting section above
- Review backend logs: `backend/logs/chatbot.log`
- Test the API: `http://localhost:8000/docs`
- Open a GitHub issue

---

## Success Checklist

Before reporting issues, verify:

- [ ] Python 3.10+ installed and activated in venv
- [ ] All Python dependencies installed (`pip install -r requirements.txt`)
- [ ] Backend .env file created and configured
- [ ] Backend server starts without errors (port 8000)
- [ ] Node.js 18+ installed
- [ ] All Node dependencies installed (`npm install`)
- [ ] Frontend starts without errors (port 5173)
- [ ] Can see the chat interface
- [ ] Can send a message and receive a response

---

**Congratulations! You're all set up. Enjoy chatting with your new AI friend! 🎉**
