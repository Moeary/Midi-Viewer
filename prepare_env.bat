@echo off
echo ===== Preparing environment for MIDI Reader compilation =====

REM Install required packages
pip install --upgrade pip
pip install --upgrade setuptools wheel

REM Install dependencies
pip install backports.tarfile
pip install ordered-set
pip install importlib_metadata
pip install PyQt5
pip install qfluentwidgets
pip install mido
pip install python-rtmidi

echo Environment prepared successfully!
pause
