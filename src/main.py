import os
import sys
import time
import collections
import threading
import datetime
import pyautogui

# Add src to path to ensure modules can be imported if run from root
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.utils import check_ffmpeg, ensure_directories, save_wav, compress_image, OUTPUT_FILE, RECORDINGS_DIR, SCREENSHOTS_DIR, RATE
from modules.audio_recorder import AudioRecorder
from modules.gemini_client import analyze_content

def main():
    print(f"🚀 AI 论文伴侣 (模块化版) 已启动")
    
    if not check_ffmpeg():
        return

    ensure_directories()

    print(f"📝 笔记将保存至: {os.path.abspath(OUTPUT_FILE)}")
    print(f"📂 录音将保存至: {os.path.abspath(RECORDINGS_DIR)}")
    print("🎙️  请开始看论文并说话 (检测到静音会自动提交)... 按 Ctrl+C 退出")

    recorder = AudioRecorder()
    if not recorder.start_stream():
        return

    # State variables
    triggered = False
    voiced_frames = []
    ring_buffer = collections.deque(maxlen=20) 
    
    try:
        while True:
            chunk = recorder.read()
            is_speech = recorder.is_speech(chunk)
            
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
                        compress_image(screenshot_filename, screenshot_filename)
                        
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
