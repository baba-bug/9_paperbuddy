import os
import time
import wave
import struct
import collections
import contextlib
import threading
import datetime
import sys
import shutil

# Check for required packages
try:
    import pyautogui
    import pyaudio
    import webrtcvad
    import numpy as np
    import google.generativeai as genai
    from PIL import Image
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Please run: pip install -r requirements.txt")
    sys.exit(1)

# ================= 配置区域 =================
# Try to get API key from environment variable, otherwise use the placeholder
API_KEY = 'AIzaSyC6nkwM8qSlIR1PJhho1LLFrStTCCDGJ1A'
MODEL_NAME = 'gemini-2.5-flash'

# Paths relative to src/
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), 'data')
OUTPUT_FILE = os.path.join(DATA_DIR, "Research_Log.md")
RECORDINGS_DIR = os.path.join(DATA_DIR, "recordings")
SCREENSHOTS_DIR = os.path.join(DATA_DIR, "screenshots")

# Ensure directories exist
os.makedirs(RECORDINGS_DIR, exist_ok=True)
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# Audio Configuration
RATE = 16000 
CHANNELS = 1
FORMAT = pyaudio.paInt16
FRAME_DURATION_MS = 30
PADDING_DURATION_MS = 1500
CHUNK_SIZE = int(RATE * FRAME_DURATION_MS / 1000)

# ================= 初始化 =================
if "在这里填入你的" in API_KEY:
    print("⚠️  WARNING: API Key not set. Please set GOOGLE_API_KEY env var or edit the script.")

try:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel(MODEL_NAME)
except Exception as e:
    print(f"❌ Failed to configure Gemini API: {e}")

vad = webrtcvad.Vad(3)

def check_ffmpeg():
    """Check if FFmpeg is installed and in PATH."""
    if not shutil.which("ffmpeg"):
        print("❌ FFmpeg not found! Please install FFmpeg and add it to your PATH.")
        print("Download: https://gyan.dev/ffmpeg/builds/")
        return False
    return True

class AudioRecorder:
    def __init__(self):
        self.p = pyaudio.PyAudio()
        try:
            self.stream = self.p.open(format=FORMAT,
                                      channels=CHANNELS,
                                      rate=RATE,
                                      input=True,
                                      frames_per_buffer=CHUNK_SIZE)
        except OSError as e:
            print(f"❌ Failed to open audio stream: {e}")
            print("Please ensure a microphone is connected and accessible.")
            self.stream = None
        
        self.history = collections.deque(maxlen=int(PADDING_DURATION_MS / FRAME_DURATION_MS))
        
    def read(self):
        if self.stream:
            try:
                data = self.stream.read(CHUNK_SIZE, exception_on_overflow=False)
                return data
            except Exception as e:
                print(f"Audio read error: {e}")
                return b'\x00' * CHUNK_SIZE
        return b'\x00' * CHUNK_SIZE # Return silence if no stream

    def close(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()

def save_wav(frames, filename):
    try:
        wf = wave.open(filename, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2) # 16-bit
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
    except Exception as e:
        print(f"❌ Error saving WAV: {e}")

def analyze_content(audio_path, screenshot_path):
    """Send to Gemini for multimodal analysis."""
    print(" -> 正在上传并分析...")
    try:
        # Check if files exist
        if not os.path.exists(audio_path):
            print(f"❌ Audio file not found: {audio_path}")
            return
        if not os.path.exists(screenshot_path):
            print(f"❌ Screenshot file not found: {screenshot_path}")
            return

        # Upload audio
        audio_file = genai.upload_file(path=audio_path)
        
        # Open image
        img = Image.open(screenshot_path)
        
        prompt = """
        场景：我正在电脑上看论文/写代码，这是我的屏幕截图，附件是我刚才说的话。
        任务：请结合屏幕内容，把我的口语（可能包含吐槽、疑问、思路）转化为这篇论文的结构化笔记。
        要求：
        1. **逐字稿**：首先你需要尽可能准确地转录我说的话（Verbatim Transcript）。
        2. **分析**：如果我在读特定段落，请结合截图指出我关注的内容。
        3. 用中文回答，格式简洁，使用Markdown结构。
        
        输出格式如下：
        ## 🗣️ 口语逐字稿
        (你的转录内容)
        
        ## 📝 结构化笔记
        (你的分析内容)
        """
        
        response = model.generate_content([prompt, img, audio_file])
        
        # Write to file
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        note_content = f"\n> **[{timestamp}]**\n{response.text}\n---\n"
        
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            f.write(note_content)
            
        print(f"✅ 笔记已更新: {OUTPUT_FILE}")
        
        # Cleanup - Delete from cloud but KEEP local files for records
        try:
            audio_file.delete()
        except:
            pass
        
    except Exception as e:
        print(f"❌ 分析出错: {e}")

def main():
    print(f"🚀 AI 论文伴侣已启动 (Windows/RTX4060版)")
    
    if not check_ffmpeg():
        return

    print(f"📝 笔记将保存至: {os.path.abspath(OUTPUT_FILE)}")
    print(f"📂 录音将保存至: {os.path.abspath(RECORDINGS_DIR)}")
    print("🎙️  请开始看论文并说话 (检测到静音会自动提交)... 按 Ctrl+C 退出")

    recorder = AudioRecorder()
    if not recorder.stream:
        print("❌ Microphone not initialized.")
        return

    # State variables
    triggered = False
    voiced_frames = []
    ring_buffer = collections.deque(maxlen=20) 
    
    try:
        while True:
            chunk = recorder.read()
            try:
                is_speech = vad.is_speech(chunk, RATE)
            except Exception:
                # If chunk is partial or invalid, assume silence
                is_speech = False
            
            if not triggered:
                ring_buffer.append(chunk)
                if is_speech:
                    print("🔴 检测到语音，开始录制...")
                    triggered = True
                    voiced_frames.extend(ring_buffer)
                    voiced_frames.append(chunk)
            else:
                voiced_frames.append(chunk)
                if is_speech:
                    recorder.history.clear()
                else:
                    recorder.history.append(chunk)
                    if len(recorder.history) == recorder.history.maxlen:
                        print("⏹️  说话结束，开始处理...")
                        triggered = False
                        
                        # 1. Generate unique filenames
                        timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                        audio_filename = os.path.join(RECORDINGS_DIR, f"capture_{timestamp_str}.wav")
                        screenshot_filename = os.path.join(SCREENSHOTS_DIR, f"capture_{timestamp_str}.png")
                        
                        save_wav(voiced_frames, audio_filename)
                        
                        # 2. Screenshot
                        pyautogui.screenshot(screenshot_filename)
                        
                        # 3. Asynchronous processing
                        analysis_thread = threading.Thread(target=analyze_content, args=(audio_filename, screenshot_filename))
                        analysis_thread.start()
                        
                        # Reset for next sentence
                        voiced_frames = []
                        ring_buffer.clear()
                        recorder.history.clear()
                        print("🎙️  继续监听中...")

    except KeyboardInterrupt:
        print("\n👋 退出程序")
        recorder.close()

if __name__ == "__main__":
    main()
