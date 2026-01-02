# LLM Setup Script for Tamagotchi Chatbot (Windows)
# Installs llama-cpp-python with appropriate backend support

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Tamagotchi Chatbot - LLM Setup (Windows)" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python version
try {
    $pythonVersion = python --version 2>&1 | Out-String
    Write-Host "Python version: $pythonVersion"

    if ($pythonVersion -match "Python (\d+)\.(\d+)") {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]

        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 10)) {
            Write-Host "Error: Python 3.10 or higher required" -ForegroundColor Red
            exit 1
        }
        Write-Host "Python version OK" -ForegroundColor Green
    }
}
catch {
    Write-Host "Error: Python not found. Please install Python 3.10+" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Check/create virtual environment
if (Test-Path "venv") {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    . .\venv\Scripts\Activate.ps1
    Write-Host "Virtual environment activated" -ForegroundColor Green
}
else {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    . .\venv\Scripts\Activate.ps1
    Write-Host "Virtual environment created and activated" -ForegroundColor Green
}

Write-Host ""

# Detect GPU support
$gpuSupport = "cpu"

try {
    $ErrorActionPreference = 'Stop'
    $nvidiaCheck = & nvidia-smi 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "NVIDIA GPU detected" -ForegroundColor Green
        $gpuSupport = "cuda"
    }
    else {
        Write-Host "No NVIDIA GPU detected, using CPU" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "No NVIDIA GPU detected, using CPU" -ForegroundColor Yellow
}
finally {
    $ErrorActionPreference = 'Continue'
}

Write-Host ""
Write-Host "Installing llama-cpp-python with $gpuSupport support..." -ForegroundColor Cyan
Write-Host ""

# Install based on GPU support
if ($gpuSupport -eq "cuda") {
    Write-Host "Installing with CUDA support..." -ForegroundColor Yellow
    $env:CMAKE_ARGS = "-DLLAMA_CUBLAS=on"
    pip install llama-cpp-python --force-reinstall --no-cache-dir
}
else {
    Write-Host "Installing with CPU-only support..." -ForegroundColor Yellow
    pip install llama-cpp-python
}

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "llama-cpp-python installed successfully" -ForegroundColor Green
}
else {
    Write-Host ""
    Write-Host "Installation failed" -ForegroundColor Red
    exit 1
}

# Install other dependencies
Write-Host ""
Write-Host "Installing remaining dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Installation complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Download a model (run: .\scripts\download_model.ps1)"
Write-Host "2. Configure .env file (copy .env.example to .env)"
Write-Host "3. Start the backend (python main.py)"
Write-Host ""
