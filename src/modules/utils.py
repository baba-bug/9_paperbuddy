import os
import shutil
import wave
import pyaudio
import sys
import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL_NAME = 'gemini-2.5-flash'

# Paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')

# Audio Config
RATE = 16000 
CHANNELS = 1
FORMAT = pyaudio.paInt16
CHUNK_SIZE = 512               # Silero VAD requires 512 samples at 16kHz (~32ms)
PADDING_DURATION_MS = 3000     # Silence timeout before processing
VAD_THRESHOLD = 0.5            # Silero probability threshold (0.0-1.0, higher = less sensitive)


class Session:
    """Represents a single recording session with its own folder structure."""

    def __init__(self, name):
        self.name = name
        self.base_dir = os.path.join(DATA_DIR, name)
        self.recordings_dir = os.path.join(self.base_dir, "recordings")
        self.screenshots_dir = os.path.join(self.base_dir, "screenshots")
        self.log_file = os.path.join(self.base_dir, "Research_Log.md")

    def ensure_directories(self):
        os.makedirs(self.recordings_dir, exist_ok=True)
        os.makedirs(self.screenshots_dir, exist_ok=True)

    def is_existing(self):
        return os.path.isdir(self.base_dir)


def create_session(resume_name=None):
    """Create a new session or resume an existing one."""
    if resume_name:
        session = Session(resume_name)
        if not session.is_existing():
            print(f"❌ Session '{resume_name}' not found in {DATA_DIR}")
            print("Available sessions:")
            list_sessions()
            return None
        print(f"📂 Resuming session: {resume_name}")
    else:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"session_{timestamp}"
        session = Session(name)
        print(f"📂 New session: {name}")

    session.ensure_directories()
    return session


def list_sessions():
    """Print all available sessions."""
    if not os.path.isdir(DATA_DIR):
        print("  (no sessions yet)")
        return
    sessions = sorted([
        d for d in os.listdir(DATA_DIR)
        if os.path.isdir(os.path.join(DATA_DIR, d)) and d.startswith("session_")
    ])
    if not sessions:
        print("  (no sessions yet)")
    else:
        for s in sessions:
            log = os.path.join(DATA_DIR, s, "Research_Log.md")
            size = os.path.getsize(log) if os.path.exists(log) else 0
            print(f"  📁 {s}  (log: {size} bytes)")


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
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        print(f"💾 Audio saved: {os.path.basename(filename)} ({len(frames)} frames)")
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
