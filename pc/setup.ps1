# =============================================================
#  Smart Doorbell - PC Setup Script
#  (Windows, NO Conda, Python 3.10+)
# =============================================================
#  Run in the project ROOT directory:
#     powershell -ExecutionPolicy Bypass -File pc\setup.ps1
#
#  What it does:
#   - Creates a .venv virtual environment
#   - Installs a PREBUILT version of dlib (no compiling/Visual Studio needed)
#   - Installs face_recognition without reinstalling/compiling dlib (--no-deps)
#   - Installs opencv, pyserial, etc.
# =============================================================
$ErrorActionPreference = "Stop"
$py = ".\.venv\Scripts\python.exe"

Write-Host "[1/7] Creating virtual environment (.venv)..." -ForegroundColor Cyan
if (-not (Test-Path ".venv")) { python -m venv .venv }

Write-Host "[2/7] Upgrading pip..." -ForegroundColor Cyan
& $py -m pip install --upgrade pip

Write-Host "[3/7] Installing numpy..." -ForegroundColor Cyan
& $py -m pip install numpy

Write-Host "[4/7] Installing dlib (prebuilt - NO COMPILATION)..." -ForegroundColor Cyan
& $py -m pip install dlib-bin

Write-Host "[5/7] Installing face_recognition + models..." -ForegroundColor Cyan
& $py -m pip install setuptools face_recognition_models click Pillow
& $py -m pip install --no-deps face_recognition

Write-Host "[6/7] Installing opencv + pyserial + ESP32 tools (esptool, mpremote)..." -ForegroundColor Cyan
& $py -m pip install opencv-python pyserial esptool mpremote

# Python 3.14+ compatibility patch: face_recognition_models use os.path instead of pkg_resources
Write-Host "[7/7] Checking Python 3.14+ compatibility..." -ForegroundColor Cyan
$modelsInit = ".\.venv\Lib\site-packages\face_recognition_models\__init__.py"
if (Test-Path $modelsInit) {
    $content = Get-Content $modelsInit -Raw
    if ($content -match "pkg_resources") {
        Write-Host "  Patching face_recognition_models (pkg_resources -> os.path)..." -ForegroundColor Yellow
        $patched = @"
# -*- coding: utf-8 -*-
__author__ = '''Adam Geitgey'''
__email__ = 'ageitgey@gmail.com'
__version__ = '0.1.0'

import os as _os
_models_dir = _os.path.join(_os.path.dirname(__file__), "models")

def pose_predictor_model_location():
    return _os.path.join(_models_dir, "shape_predictor_68_face_landmarks.dat")

def pose_predictor_five_point_model_location():
    return _os.path.join(_models_dir, "shape_predictor_5_face_landmarks.dat")

def face_recognition_model_location():
    return _os.path.join(_models_dir, "dlib_face_recognition_resnet_model_v1.dat")

def cnn_face_detector_model_location():
    return _os.path.join(_models_dir, "mmod_human_face_detector.dat")
"@
        Set-Content -Path $modelsInit -Value $patched -Encoding UTF8
        Write-Host "  Patch applied successfully." -ForegroundColor Green
    } else {
        Write-Host "  Patch not needed, already compatible." -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "DONE! To verify the installation:" -ForegroundColor Green
Write-Host "   .\.venv\Scripts\python.exe pc\verify_setup.py"
