import collections
import threading
import datetime
import os
import pyautogui
from .utils import save_wav, compress_image
from .gemini_client import analyze_content


class SpeechProcessor:
    def __init__(self, recorder, session):
        self.recorder = recorder
        self.session = session
        self.triggered = False
        self.voiced_frames = []
        self.ring_buffer = collections.deque(maxlen=20)

    def process_loop(self):
        """Main blocking loop for speech detection."""
        try:
            while True:
                chunk = self.recorder.read()
                is_speech = self.recorder.is_speech(chunk)

                if not self.triggered:
                    self.ring_buffer.append(chunk)
                    if is_speech:
                        print("🔴 [调试] 检测到语音，开始录制...", end="\r")
                        self.triggered = True
                        self.voiced_frames.extend(self.ring_buffer)
                        self.voiced_frames.append(chunk)
                else:
                    self.voiced_frames.append(chunk)
                    if is_speech:
                        self.recorder.history.clear()
                    else:
                        self.recorder.history.append(chunk)

                        silence_duration = len(self.recorder.history) * 30
                        print(f"🟡 [调试] 静音中... {silence_duration}ms / 3000ms", end="\r")

                        if len(self.recorder.history) == self.recorder.history.maxlen:
                            print("\n⏹️  说话结束，开始处理...")
                            self.triggered = False
                            self._handle_completed_utterance()

                            self.voiced_frames = []
                            self.ring_buffer.clear()
                            self.recorder.history.clear()
                            self.recorder.reset_vad()
                            print("🎙️  继续监听中...")

        except KeyboardInterrupt:
            print("\n👋 停止监听")

    def _handle_completed_utterance(self):
        """Save files and trigger async analysis."""
        try:
            timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            audio_filename = os.path.join(self.session.recordings_dir, f"capture_{timestamp_str}.wav")
            screenshot_filename = os.path.join(self.session.screenshots_dir, f"capture_{timestamp_str}.png")

            save_wav(self.voiced_frames, audio_filename)

            print(f"📸 截取屏幕...")
            pyautogui.screenshot(screenshot_filename)
            compress_image(screenshot_filename, screenshot_filename)

            print(f"🚀 发送给 AI 分析...")
            analysis_thread = threading.Thread(
                target=analyze_content,
                args=(audio_filename, screenshot_filename, self.session.log_file)
            )
            analysis_thread.start()

        except Exception as e:
            print(f"❌ 处理出错: {e}")
