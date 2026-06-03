# =============================================================
#  KURULUM DOGRULAMA
# =============================================================
#  Tum gerekli modullerin kurulu oldugunu kontrol eder.
#  Calistir:  .\.venv\Scripts\python.exe pc\dogrula_kurulum.py
# =============================================================

moduller = ["cv2", "numpy", "serial", "dlib", "face_recognition"]

print("Modul kontrolu:\n")
eksik = []
for m in moduller:
    try:
        mod = __import__(m)
        ver = getattr(mod, "__version__", "?")
        print(f"  [OK]   {m:18s} {ver}")
    except Exception as e:
        eksik.append(m)
        print(f"  [HATA] {m:18s} -> {e}")

print()
if not eksik:
    print("HEPSI HAZIR! PC tarafi kurulumu tamam.")
    print("Sonraki adim:  .\\.venv\\Scripts\\python.exe pc\\doorbell.py --test")
else:
    print(f"EKSIK: {', '.join(eksik)}")
    print("kurulum.ps1 scriptini tekrar calistir veya hatayi paylas.")
