# =============================================================
#  SETUP VERIFICATION
# =============================================================
#  Checks if all required modules are installed.
#  Run:  .\.venv\Scripts\python.exe pc\verify_setup.py
# =============================================================

modules = ["cv2", "numpy", "serial", "dlib", "face_recognition"]

print("Module check:\n")
missing = []
for m in modules:
    try:
        mod = __import__(m)
        ver = getattr(mod, "__version__", "?")
        print(f"  [OK]   {m:18s} {ver}")
    except Exception as e:
        missing.append(m)
        print(f"  [ERROR] {m:18s} -> {e}")

print()
if not missing:
    print("EVERYTHING IS READY! PC side setup is complete.")
    print("Next step:  .\\.venv\\Scripts\\python.exe pc\\doorbell.py --test")
else:
    print(f"MISSING: {', '.join(missing)}")
    print("Please run setup.ps1 script again or share the error.")
