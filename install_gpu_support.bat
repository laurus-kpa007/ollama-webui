@echo off
echo ==============================================
echo   Ollama WebUI GPU Support Installation
echo ==============================================
echo.

echo [1/4] Removing existing PyTorch (CPU version)...
pip uninstall torch torchvision torchaudio xformers -y

echo.
echo [2/4] Installing PyTorch with CUDA support...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

echo.
echo [3/4] Installing other ML dependencies...
pip install -r requirements.txt

echo.
echo [4/4] Installing xFormers for performance...
pip install xformers

echo.
echo ==============================================
echo   Installation Complete!
echo ==============================================
echo.
echo Testing installation...
python test_model_load.py

echo.
echo If test passed, restart the server:
echo   python app.py
echo.
pause