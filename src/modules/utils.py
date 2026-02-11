import os
import shutil
import wave
import pyaudio
import sys

# Configuration
API_KEY = os.getenv("GOOGLE_API_KEY", 'AIzaSyC6nkwM8qSlIR1PJhho1LLFrStTCCDGJ1A')
MODEL_NAME = 'gemini-2.5-flash'

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # e:/9_paperbuddy/src
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), 'data') # e:/9_paperbuddy/data
OUTPUT_FILE = os.path.join(DATA_DIR, "Research_Log.md")
RECORDINGS_DIR = os.path.join(DATA_DIR, "recordings")
SCREENSHOTS_DIR = os.path.join(DATA_DIR, "screenshots")

# Audio Config
RATE = 16000 
CHANNELS = 1
FORMAT = pyaudio.paInt16
FRAME_DURATION_MS = 30
PADDING_DURATION_MS = 3000
CHUNK_SIZE = int(RATE * FRAME_DURATION_MS / 1000)

def ensure_directories():
    os.makedirs(RECORDINGS_DIR, exist_ok=True)
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

def check_ffmpeg():
    """Check if FFmpeg is installed and in PATH."""
    if not shutil.which("ffmpeg"):
        print("❌ FFmpeg not found! Please install FFmpeg and add it to your PATH.")
        print("Download: https://gyan.dev/ffmpeg/builds/")
        return False
    return True

def save_wav(frames, filename):
    try:
        if not frames:
            print("❌ No audio frames to save.")
            return
        
        wf = wave.open(filename, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2) # 16-bit
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        print(f"💾 Audio saved: {filename} ({len(frames)} frames)")
    except Exception as e:
        print(f"❌ Error saving WAV: {e}")

def compress_image(input_path, output_path, max_size=(1024, 1024), quality=85):
    """Resize and compress image to reduce file size."""
    try:
        from PIL import Image
        with Image.open(input_path) as img:
            img.thumbnail(max_size)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.save(output_path, "JPEG", quality=quality)
        return True
    except Exception as e:
        print(f"❌ Error compressing image: {e}")
        return False
