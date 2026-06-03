# =============================================================
#  Akilli Kapi Zili - PC Kurulum Scripti
#  (Windows, Conda YOK, Python 3.10+)
# =============================================================
#  Proje KOK dizininde calistir:
#     powershell -ExecutionPolicy Bypass -File pc\kurulum.ps1
#
#  Yaptiklari:
#   - .venv sanal ortami olusturur
#   - dlib'i ONCEDEN DERLENMIS halde kurar (derleme/Visual Studio derdi yok)
#   - face_recognition'i dlib'i tekrar derlemeden (--no-deps) kurar
#   - opencv, pyserial vb. kurar
# =============================================================
$ErrorActionPreference = "Stop"
$py = ".\.venv\Scripts\python.exe"

Write-Host "[1/6] Sanal ortam (.venv) olusturuluyor..." -ForegroundColor Cyan
if (-not (Test-Path ".venv")) { python -m venv .venv }

Write-Host "[2/6] pip guncelleniyor..." -ForegroundColor Cyan
& $py -m pip install --upgrade pip

Write-Host "[3/6] numpy kuruluyor..." -ForegroundColor Cyan
& $py -m pip install numpy

Write-Host "[4/6] dlib (prebuilt - DERLEME YOK) kuruluyor..." -ForegroundColor Cyan
& $py -m pip install dlib-bin

Write-Host "[5/7] face_recognition + modelleri kuruluyor..." -ForegroundColor Cyan
& $py -m pip install setuptools face_recognition_models click Pillow
& $py -m pip install --no-deps face_recognition

Write-Host "[6/7] opencv + pyserial + ESP32 araclari (esptool, mpremote) kuruluyor..." -ForegroundColor Cyan
& $py -m pip install opencv-python pyserial esptool mpremote

# Python 3.14+ uyumluluk yamasi: face_recognition_models pkg_resources yerine os.path kullansin
Write-Host "[7/7] Python 3.14+ uyumluluk kontrolu..." -ForegroundColor Cyan
$modelsInit = ".\.venv\Lib\site-packages\face_recognition_models\__init__.py"
if (Test-Path $modelsInit) {
    $content = Get-Content $modelsInit -Raw
    if ($content -match "pkg_resources") {
        Write-Host "  face_recognition_models yamalaniyor (pkg_resources -> os.path)..." -ForegroundColor Yellow
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
        Write-Host "  Yama uygulandi." -ForegroundColor Green
    } else {
        Write-Host "  Yama gereksiz, zaten uyumlu." -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "BITTI! Dogrulama icin:" -ForegroundColor Green
Write-Host "   .\.venv\Scripts\python.exe pc\dogrula_kurulum.py"
