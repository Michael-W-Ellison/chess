#!/bin/bash
#
# Model Download Helper
# Downloads recommended LLM models for the chatbot
#

set -e

echo "=========================================="
echo "Tamagotchi Chatbot - Model Downloader"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Create models directory
mkdir -p models

echo "Available models:"
echo ""
echo "1) Llama 3.2 3B Instruct (Recommended)"
echo "   - Size: ~2GB"
echo "   - Best quality for this application"
echo "   - Requires: 8GB+ RAM"
echo ""
echo "2) Phi-3 Mini 4K Instruct"
echo "   - Size: ~2.3GB"
echo "   - Good alternative, slightly larger"
echo "   - Requires: 8GB+ RAM"
echo ""
echo "3) TinyLlama 1.1B Chat"
echo "   - Size: ~650MB"
echo "   - Faster, lower quality"
echo "   - Requires: 4GB+ RAM"
echo ""
echo "4) Custom URL"
echo "   - Provide your own HuggingFace model URL"
echo ""

read -p "Select model (1-4): " choice

case $choice in
    1)
        echo -e "${YELLOW}Downloading Llama 3.2 3B Instruct...${NC}"
        MODEL_URL="https://huggingface.co/TheBloke/Llama-3.2-3B-Instruct-GGUF/resolve/main/llama-3.2-3b-instruct.Q4_K_M.gguf"
        MODEL_FILE="models/llama-3.2-3b-instruct.gguf"
        ;;
    2)
        echo -e "${YELLOW}Downloading Phi-3 Mini...${NC}"
        MODEL_URL="https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf"
        MODEL_FILE="models/phi-3-mini-4k-instruct.gguf"
        ;;
    3)
        echo -e "${YELLOW}Downloading TinyLlama...${NC}"
        MODEL_URL="https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
        MODEL_FILE="models/tinyllama-1.1b-chat.gguf"
        ;;
    4)
        read -p "Enter HuggingFace model URL: " MODEL_URL
        read -p "Enter filename for model: " filename
        MODEL_FILE="models/${filename}"
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo -e "${BLUE}Downloading model...${NC}"
echo "URL: ${MODEL_URL}"
echo "Destination: ${MODEL_FILE}"
echo ""

# Check if wget or curl is available
if command -v wget &> /dev/null; then
    wget -O "${MODEL_FILE}" "${MODEL_URL}" --progress=bar:force
elif command -v curl &> /dev/null; then
    curl -L -o "${MODEL_FILE}" "${MODEL_URL}" --progress-bar
else
    echo "Error: Neither wget nor curl found. Please install one of them."
    exit 1
fi

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Model downloaded successfully${NC}"
    echo ""
    echo "Model location: ${MODEL_FILE}"
    echo ""
    echo "Update your .env file:"
    echo "MODEL_PATH=${MODEL_FILE}"
    echo ""
else
    echo "Download failed"
    exit 1
fi
