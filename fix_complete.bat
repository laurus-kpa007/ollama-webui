@echo off
echo ======================================================
echo   Complete Fix for Qwen-Image Generation
echo ======================================================
echo.

echo [1/5] Removing all problematic packages...
pip uninstall torch torchvision torchaudio diffusers transformers xformers -y

echo.
echo [2/5] Installing PyTorch with CUDA (if you have NVIDIA GPU)...
echo Choose your option:
echo 1 = Install CUDA version (NVIDIA GPU)
echo 2 = Install CPU version (No GPU or AMD)
set /p choice="Enter choice (1 or 2): "

if "%choice%"=="1" (
    echo Installing CUDA version...
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
) else (
    echo Installing CPU version...
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
)

echo.
echo [3/5] Installing compatible ML libraries...
pip install diffusers==0.25.0
pip install transformers==4.40.0
pip install accelerate

echo.
echo [4/5] Installing additional dependencies...
pip install safetensors Pillow requests

echo.
echo [5/5] Testing installation...
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "from transformers import CLIPImageProcessor; print('CLIPImageProcessor: OK')"
python -c "from diffusers import DiffusionPipeline; print('DiffusionPipeline: OK')"

echo.
echo ======================================================
echo   Installation Complete!
echo ======================================================
echo.
echo Now test with: python test_qwen_simple.py
pause