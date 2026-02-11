import sys
import shutil
import importlib
import os

def check_package(package_name):
    try:
        importlib.import_module(package_name)
        print(f"✅ {package_name} is installed.")
        return True
    except ImportError:
        print(f"❌ {package_name} is NOT installed.")
        return False

def check_ffmpeg():
    if shutil.which("ffmpeg"):
        print("✅ FFmpeg is found in PATH.")
        return True
    else:
        print("❌ FFmpeg is NOT found in PATH.")
        return False

def check_api_key():
    key = os.getenv("GOOGLE_API_KEY")
    if key:
        print("✅ GOOGLE_API_KEY environment variable is set.")
    else:
        print("⚠️  GOOGLE_API_KEY environment variable is NOT set (Setup might still work if hardcoded in script).")

def main():
    print("Checking environment for AI Paper Companion...\n")
    
    packages = ["google.generativeai", "pyautogui", "pyaudio", "webrtcvad", "numpy", "PIL"]
    all_packages_ok = True
    for pkg in packages:
        if pkg == "PIL":
            if not check_package("PIL"):
                all_packages_ok = False
        else:
            if not check_package(pkg):
                all_packages_ok = False
    
    print("-" * 20)
    ffmpeg_ok = check_ffmpeg()
    
    print("-" * 20)
    check_api_key()
    
    print("-" * 20)
    if all_packages_ok and ffmpeg_ok:
        print("🎉 Environment looks good! You can run 'python ai_assistant.py'.")
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")

if __name__ == "__main__":
    main()
