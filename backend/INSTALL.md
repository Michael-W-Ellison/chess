# LLM Installation Guide

This guide covers installing llama-cpp-python with GPU or CPU support for the Tamagotchi Chatbot backend.

## Quick Start

### Automated Installation (Recommended)

**Linux/Mac:**
```bash
cd backend
./scripts/setup_llm.sh
```

**Windows:**
```powershell
cd backend
.\scripts\setup_llm.ps1
```

### Manual Installation

#### 1. Create Virtual Environment

```bash
python3 -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

#### 2. Install llama-cpp-python

Choose based on your hardware:

**CPU Only (All platforms):**
```bash
pip install llama-cpp-python
```

**NVIDIA GPU (CUDA):**
```bash
# Linux/Mac
CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python --force-reinstall --no-cache-dir

# Windows
$env:CMAKE_ARGS = "-DLLAMA_CUBLAS=on"
pip install llama-cpp-python --force-reinstall --no-cache-dir
```

**Apple Silicon (M1/M2/M3):**
```bash
CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python --force-reinstall --no-cache-dir
```

#### 3. Install Other Dependencies

```bash
pip install -r requirements.txt
```

## Prerequisites

### All Platforms

- Python 3.10 or higher
- 8GB+ RAM (for LLM)
- 4GB+ disk space (for model files)

### GPU Support Prerequisites

**NVIDIA GPU (CUDA):**
- NVIDIA GPU with Compute Capability 6.0+
- CUDA Toolkit 11.8+ installed
- cuBLAS library

**Apple Silicon:**
- M1, M2, or M3 chip
- macOS 12.3+ (Monterey or later)
- Xcode Command Line Tools

## Downloading Models

### Using the Download Script

**Linux/Mac:**
```bash
./scripts/download_model.sh
```

The script offers several options:
1. Llama 3.2 3B Instruct (Recommended) - ~2GB
2. Phi-3 Mini 4K Instruct - ~2.3GB
3. TinyLlama 1.1B Chat - ~650MB (faster, lower quality)
4. Custom URL

### Manual Download

1. Visit HuggingFace and find a GGUF format model:
   - [Llama 3.2 3B Instruct](https://huggingface.co/TheBloke/Llama-3.2-3B-Instruct-GGUF)
   - [Phi-3 Mini](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf)

2. Download the `.gguf` file

3. Place it in `backend/models/`

4. Update `.env`:
   ```
   MODEL_PATH=./models/your-model-name.gguf
   ```

## Recommended Models

### For Best Quality (Recommended)

**Llama 3.2 3B Instruct**
- Size: ~2GB
- RAM Required: 8GB+
- Best for: Production use, high-quality responses
- Quantization: Q4_K_M (good balance of quality/speed)

### For Speed/Lower Hardware

**TinyLlama 1.1B Chat**
- Size: ~650MB
- RAM Required: 4GB+
- Best for: Development, testing, low-end hardware
- Quantization: Q4_K_M

### Alternative

**Phi-3 Mini**
- Size: ~2.3GB
- RAM Required: 8GB+
- Best for: Alternative to Llama, good quality
- Quantization: Q4

## Configuration

### Update .env File

```bash
# Copy template
cp .env.example .env

# Edit and set:
MODEL_PATH=./models/llama-3.2-3b-instruct.gguf
MODEL_CONTEXT_LENGTH=2048
MODEL_MAX_TOKENS=512
MODEL_TEMPERATURE=0.7
MODEL_N_GPU_LAYERS=0      # 0=CPU, -1=full GPU, or specific layer count
```

### GPU Configuration

**For CPU-only:**
```
MODEL_N_GPU_LAYERS=0
```

**For full GPU offload:**
```
MODEL_N_GPU_LAYERS=-1
```

**For partial GPU offload (NVIDIA):**
```
MODEL_N_GPU_LAYERS=20  # Adjust based on VRAM
```

## Verification

### Verify Installation

```bash
python scripts/verify_setup.py
```

This checks:
- Python version
- All dependencies installed
- Configuration files present
- Model file exists
- Directory structure

### Test the Backend

```bash
python main.py
```

Visit http://localhost:8000/docs to see the API documentation.

## Troubleshooting

### Import Error: llama_cpp

**Problem:** `ImportError: No module named 'llama_cpp'`

**Solutions:**
1. Ensure virtual environment is activated
2. Reinstall: `pip install llama-cpp-python --force-reinstall`
3. Check Python version: `python --version` (need 3.10+)

### CUDA Not Found (NVIDIA GPU)

**Problem:** GPU not being used despite CUDA installation

**Solutions:**
1. Verify CUDA: `nvidia-smi`
2. Check CUDA version: `nvcc --version`
3. Reinstall with CUDA: `CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python --force-reinstall --no-cache-dir`
4. Set GPU layers in .env: `MODEL_N_GPU_LAYERS=-1`

### Metal Not Working (Apple Silicon)

**Problem:** Not using Metal acceleration on Mac

**Solutions:**
1. Update macOS to 12.3+
2. Install Xcode Command Line Tools: `xcode-select --install`
3. Reinstall with Metal: `CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python --force-reinstall --no-cache-dir`

### Out of Memory

**Problem:** Backend crashes or freezes due to memory

**Solutions:**
1. Use a smaller model (TinyLlama instead of Llama 3.2)
2. Reduce context length: `MODEL_CONTEXT_LENGTH=1024`
3. Reduce max tokens: `MODEL_MAX_TOKENS=256`
4. Close other applications
5. Use lower quantization (Q3 instead of Q4)

### Slow Response Times

**Problem:** LLM takes too long to respond (>5 seconds)

**Solutions:**
1. Enable GPU acceleration (see above)
2. Use a smaller model
3. Reduce context length
4. Use higher quantization (Q5 instead of Q4) if you have enough RAM

### Model File Not Found

**Problem:** `Error: Model file not found at...`

**Solutions:**
1. Verify model file exists: `ls -lh models/`
2. Check .env MODEL_PATH matches actual filename
3. Use absolute path in .env if relative path fails
4. Download model using script: `./scripts/download_model.sh`

### Permission Denied (Linux/Mac)

**Problem:** Cannot execute setup scripts

**Solution:**
```bash
chmod +x scripts/*.sh scripts/*.py
```

## Performance Benchmarks

### Expected Response Times (CPU)

- **Intel i7 (modern):** 1-3 seconds
- **Intel i5 (older):** 3-5 seconds
- **Apple M1/M2 (Metal):** 0.5-2 seconds

### Expected Response Times (GPU)

- **NVIDIA RTX 3060:** 0.3-1 second
- **NVIDIA GTX 1080:** 0.5-1.5 seconds

### Memory Usage

- **Llama 3.2 3B:** ~4-6GB RAM
- **Phi-3 Mini:** ~4-7GB RAM
- **TinyLlama:** ~2-3GB RAM

## Getting Help

1. Run verification: `python scripts/verify_setup.py`
2. Check logs: `tail -f logs/chatbot.log`
3. Enable debug mode in .env: `DEBUG=True`
4. Review backend README: `backend/README.md`

## Additional Resources

- [llama-cpp-python Documentation](https://github.com/abetlen/llama-cpp-python)
- [HuggingFace Models](https://huggingface.co/models?other=gguf)
- [GGUF Format Explanation](https://github.com/ggerganov/llama.cpp/blob/master/gguf-py/README.md)
