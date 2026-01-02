# Model Download Helper for Tamagotchi Chatbot (Windows)
# Downloads recommended LLM models for the chatbot

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Tamagotchi Chatbot - Model Downloader" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Create models directory
if (-not (Test-Path "models")) {
    New-Item -ItemType Directory -Path "models" | Out-Null
    Write-Host "Created models directory" -ForegroundColor Green
}

Write-Host "Available models:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1) Llama 3.2 3B Instruct (Recommended)"
Write-Host "   - Size: ~2GB"
Write-Host "   - Best quality for this application"
Write-Host "   - Requires: 8GB+ RAM"
Write-Host ""
Write-Host "2) Phi-3 Mini 4K Instruct"
Write-Host "   - Size: ~2.3GB"
Write-Host "   - Good alternative, slightly larger"
Write-Host "   - Requires: 8GB+ RAM"
Write-Host ""
Write-Host "3) TinyLlama 1.1B Chat"
Write-Host "   - Size: ~650MB"
Write-Host "   - Faster, lower quality"
Write-Host "   - Requires: 4GB+ RAM"
Write-Host ""
Write-Host "4) Custom URL"
Write-Host "   - Provide your own HuggingFace model URL"
Write-Host ""

$choice = Read-Host "Select model (1-4)"

switch ($choice) {
    "1" {
        Write-Host "Downloading Llama 3.2 3B Instruct..." -ForegroundColor Yellow
        $modelUrl = "https://huggingface.co/TheBloke/Llama-3.2-3B-Instruct-GGUF/resolve/main/llama-3.2-3b-instruct.Q4_K_M.gguf"
        $modelFile = "models\llama-3.2-3b-instruct.gguf"
    }
    "2" {
        Write-Host "Downloading Phi-3 Mini..." -ForegroundColor Yellow
        $modelUrl = "https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf"
        $modelFile = "models\phi-3-mini-4k-instruct.gguf"
    }
    "3" {
        Write-Host "Downloading TinyLlama..." -ForegroundColor Yellow
        $modelUrl = "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
        $modelFile = "models\tinyllama-1.1b-chat.gguf"
    }
    "4" {
        $modelUrl = Read-Host "Enter HuggingFace model URL"
        $filename = Read-Host "Enter filename for model (e.g., my-model.gguf)"
        $modelFile = "models\$filename"
    }
    default {
        Write-Host "Invalid choice" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "Downloading model..." -ForegroundColor Cyan
Write-Host "URL: $modelUrl"
Write-Host "Destination: $modelFile"
Write-Host ""
Write-Host "This may take several minutes depending on your connection speed..." -ForegroundColor Yellow
Write-Host ""

try {
    # Use BITS for better download experience with progress
    $usesBits = $true
    try {
        Start-BitsTransfer -Source $modelUrl -Destination $modelFile -DisplayName "Downloading LLM Model" -Description "Please wait..."
    }
    catch {
        $usesBits = $false
        Write-Host "BITS transfer not available, using Invoke-WebRequest..." -ForegroundColor Yellow

        # Fallback to Invoke-WebRequest with progress
        $ProgressPreference = 'Continue'
        Invoke-WebRequest -Uri $modelUrl -OutFile $modelFile -UseBasicParsing
    }

    if (Test-Path $modelFile) {
        $fileSize = (Get-Item $modelFile).Length / 1MB
        Write-Host ""
        Write-Host "Model downloaded successfully!" -ForegroundColor Green
        Write-Host "Size: $([math]::Round($fileSize, 2)) MB"
        Write-Host ""
        Write-Host "Model location: $modelFile" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Update your .env file with:" -ForegroundColor Yellow
        Write-Host "MODEL_PATH=./$modelFile"
        Write-Host ""
    }
    else {
        Write-Host "Download failed - file not found" -ForegroundColor Red
        exit 1
    }
}
catch {
    Write-Host "Download failed: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "You can manually download the model from:" -ForegroundColor Yellow
    Write-Host $modelUrl
    Write-Host ""
    Write-Host "Save it to: $modelFile"
    exit 1
}
