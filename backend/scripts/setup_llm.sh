#!/bin/bash
#
# LLM Setup Script for Tamagotchi Chatbot
# Installs llama-cpp-python with appropriate backend support
#

set -e  # Exit on error

echo "=========================================="
echo "Tamagotchi Chatbot - LLM Setup"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Detect platform
OS=$(uname -s)
ARCH=$(uname -m)

echo "Detected platform: ${OS} ${ARCH}"
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

echo "Python version: ${PYTHON_VERSION}"

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    echo -e "${RED}Error: Python 3.10 or higher required${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python version OK${NC}"
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
    echo -e "${GREEN}✓ Virtual environment activated${NC}"
else
    echo -e "${YELLOW}Warning: No virtual environment found. Creating one...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    echo -e "${GREEN}✓ Virtual environment created and activated${NC}"
fi

echo ""

# Detect GPU support
GPU_SUPPORT="none"

if command -v nvidia-smi &> /dev/null; then
    echo -e "${GREEN}NVIDIA GPU detected${NC}"
    GPU_SUPPORT="cuda"
elif [ "$OS" = "Darwin" ] && [ "$ARCH" = "arm64" ]; then
    echo -e "${GREEN}Apple Silicon detected${NC}"
    GPU_SUPPORT="metal"
else
    echo -e "${YELLOW}No GPU detected, using CPU${NC}"
    GPU_SUPPORT="cpu"
fi

echo ""
echo "Installing llama-cpp-python with ${GPU_SUPPORT} support..."
echo ""

# Install based on platform
case $GPU_SUPPORT in
    cuda)
        echo "Installing with CUDA support..."
        CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python --force-reinstall --no-cache-dir
        ;;
    metal)
        echo "Installing with Metal support (Apple Silicon)..."
        CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python --force-reinstall --no-cache-dir
        ;;
    cpu)
        echo "Installing with CPU-only support..."
        pip install llama-cpp-python
        ;;
esac

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ llama-cpp-python installed successfully${NC}"
else
    echo ""
    echo -e "${RED}✗ Installation failed${NC}"
    exit 1
fi

# Install other dependencies
echo ""
echo "Installing remaining dependencies..."
pip install -r requirements.txt

echo ""
echo -e "${GREEN}=========================================="
echo "Installation complete!"
echo "==========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Download a model (run: ./scripts/download_model.sh)"
echo "2. Configure .env file (cp .env.example .env)"
echo "3. Start the backend (python main.py)"
echo ""
