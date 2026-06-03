# =============================================================
#  Akilli Kapi Zili - PC Kurulum Scripti
#  (Windows, Conda YOK, Python 3.10)
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

Write-Host "[1/6] Sanal ortam (.venv) olusturuluyor (Python 3.10)..." -ForegroundColor Cyan
if (-not (Test-Path ".venv")) { py -3.10 -m venv .venv }

Write-Host "[2/6] pip guncelleniyor..." -ForegroundColor Cyan
& $py -m pip install --upgrade pip

Write-Host "[3/6] numpy kuruluyor..." -ForegroundColor Cyan
& $py -m pip install numpy

Write-Host "[4/6] dlib (prebuilt - DERLEME YOK) kuruluyor..." -ForegroundColor Cyan
& $py -m pip install dlib-bin

Write-Host "[5/6] face_recognition + modelleri kuruluyor..." -ForegroundColor Cyan
& $py -m pip install face_recognition_models click Pillow
& $py -m pip install --no-deps face_recognition

Write-Host "[6/6] opencv + pyserial + ESP32 araclari (esptool, mpremote) kuruluyor..." -ForegroundColor Cyan
& $py -m pip install opencv-python pyserial esptool mpremote

Write-Host ""
Write-Host "BITTI! Dogrulama icin:" -ForegroundColor Green
Write-Host "   .\.venv\Scripts\python.exe pc\dogrula_kurulum.py"
