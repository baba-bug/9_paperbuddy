import threading
import time
import datetime
import os
from .utils import save_wav, HEARTBEAT_INTERVAL
from .audio_recorder import AudioRecorder
from .screen_recorder import ScreenRecorder


class Logger:
    """Orchestrates data collection: VAD-triggered AV recording + heartbeat screenshots."""

    def __init__(self, session):
        self.session = session
        self.recorder = AudioRecorder()
        self.screen = ScreenRecorder()
        self._running = False
        self._paused = False  # New pause flag
        self._is_recording_speech = False  # True when currently recording a speech clip
        self._last_toggle_time = 0

    def toggle_pause(self):
        """Toggle the pause state with debounce."""
        now = time.time()
        if now - self._last_toggle_time < 0.5:
            return self._paused
        
        self._last_toggle_time = now
        self._paused = not self._paused
        state = "⏸️ PAUSED" if self._paused else "▶️ RESUMED"
        print(f"\n{state} " + "-"*20)
        return self._paused

    def start(self):
        """Start the logger: open mic stream and begin heartbeat + VAD loop."""
        if not self.recorder.start_stream():
            return False

        self._running = True

        # Start heartbeat screenshot thread
        self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._heartbeat_thread.start()
        print(f"📷 Heartbeat screenshots every {HEARTBEAT_INTERVAL}s → pending/")

        # Run VAD loop on main thread (blocking)
        self._vad_loop()
        return True

    def stop(self):
        """Stop the logger gracefully."""
        self._running = False
        if self._is_recording_speech:
            self.screen.stop_recording()
        self.recorder.close()
        self.screen.close()

    # ──────────────────────────────────────────────────────────
    # A1: VAD-triggered AV recording
    # ──────────────────────────────────────────────────────────
    def _vad_loop(self):
        """Main VAD loop: detect speech → record audio + screen → save to pending."""
        import collections
        ring_buffer = collections.deque(maxlen=20)
        voiced_frames = []
        triggered = False

        try:
            while self._running:
                # If paused, just read and discard to keep buffer clean
                if self._paused:
                    self.recorder.read()
                    if triggered:
                        # If we were recording when paused, force stop
                        print("\n⏸️  Paused during recording - discarding segment.")
                        triggered = False
                        self._is_recording_speech = False
                        self.screen.stop_recording()
                        voiced_frames = []
                        ring_buffer.clear()
                        self.recorder.history.clear()
                        self.recorder.reset_vad()
                    time.sleep(0.01)
                    continue

                chunk = self.recorder.read()
                is_speech = self.recorder.is_speech(chunk)

                if not triggered:
                    ring_buffer.append(chunk)
                    if is_speech:
                        print("🔴 检测到语音，开始录制...")
                        triggered = True
                        self._is_recording_speech = True
                        voiced_frames.extend(ring_buffer)
                        voiced_frames.append(chunk)

                        # Start screen recording simultaneously
                        ts = datetime.datetime.now().strftime("%H%M%S")
                        video_path = os.path.join(self.session.pending_dir, f"{ts}_speech_clip.mp4")
                        self.screen.start_recording(video_path)
                    
                else:
                    voiced_frames.append(chunk)
                    if is_speech:
                        self.recorder.history.clear()
                    else:
                        self.recorder.history.append(chunk)
                        
                        silence_duration = len(self.recorder.history) * 32  # ~32ms per chunk
                        print(f"🟡 静音中... {silence_duration}ms / 3000ms", end="\r")

                        if len(self.recorder.history) == self.recorder.history.maxlen:
                            print("\n⏹️  语音结束，保存片段...")
                            triggered = False
                            self._is_recording_speech = False

                            # Stop screen recording
                            self.screen.stop_recording()

                            # Save audio
                            ts = datetime.datetime.now().strftime("%H%M%S")
                            audio_path = os.path.join(self.session.pending_dir, f"{ts}_speech_clip.wav")
                            save_wav(voiced_frames, audio_path)

                            # Reset
                            voiced_frames = []
                            ring_buffer.clear()
                            self.recorder.history.clear()
                            self.recorder.reset_vad()
                            print("🎙️  继续监听中...")

        except KeyboardInterrupt:
            print("\n👋 停止采集")

    # ──────────────────────────────────────────────────────────
    # A2: Heartbeat screenshots
    # ──────────────────────────────────────────────────────────
    def _heartbeat_loop(self):
        """Take a screenshot every HEARTBEAT_INTERVAL seconds.
        Skips screenshots while VAD-triggered screen recording is active.
        """
        elapsed = 0.0
        poll_interval = 0.5  # Check recording flag every 0.5s

        while self._running:
            time.sleep(poll_interval)
            if not self._running:
                break
            
            if self._paused:
                elapsed = 0.0 # Reset timer while paused
                continue

            elapsed += poll_interval

            if elapsed < HEARTBEAT_INTERVAL:
                continue
            elapsed = 0.0

            # Skip heartbeat while screen is being video-recorded
            if self._is_recording_speech:
                print("📷 (录屏中，跳过心跳截图)")
                continue

            ts = datetime.datetime.now().strftime("%H%M%S")
            filepath = os.path.join(self.session.pending_dir, f"{ts}_interval_screen.jpg")
            self.screen.take_screenshot(filepath)
            print(f"📷 心跳截图: {os.path.basename(filepath)}")
