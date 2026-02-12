import threading
import time
import os
import numpy as np
import cv2
import mss
from .utils import SCREEN_FPS


class ScreenRecorder:
    """Handles screen capture: both continuous video recording and single screenshots.
    
    Note: mss is thread-local, so each method creates its own mss instance
    to support cross-thread usage (heartbeat thread vs VAD thread).
    """

    def __init__(self):
        self._recording = False
        self._record_thread = None
        self._video_writer = None
        self._output_path = None
        self._primary_idx = self._find_primary_monitor()
        print(f"🖥️  使用显示器 #{self._primary_idx}")

    @property
    def is_recording(self):
        return self._recording

    @staticmethod
    def _find_primary_monitor():
        """Find the primary monitor index. Primary is typically at position (0,0)."""
        with mss.mss() as sct:
            for i, m in enumerate(sct.monitors):
                if i == 0:
                    continue  # index 0 is the virtual "all monitors" screen
                if m['left'] == 0 and m['top'] == 0:
                    return i
        return 1  # fallback

    def _get_monitor(self):
        """Get primary monitor dimensions (creates a fresh mss instance)."""
        with mss.mss() as sct:
            return sct.monitors[1].copy()

    def take_screenshot(self, filepath):
        """Capture a single screenshot and save as compressed JPEG.
        Thread-safe: creates its own mss instance.
        """
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[self._primary_idx]
                img = sct.grab(monitor)
                frame = np.array(img)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

                # Resize for efficiency (max 1280px width)
                h, w = frame.shape[:2]
                if w > 1280:
                    scale = 1280 / w
                    frame = cv2.resize(frame, (1280, int(h * scale)))

                cv2.imwrite(filepath, frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            return True
        except Exception as e:
            print(f"❌ Screenshot error: {e}")
            return False

    def start_recording(self, filepath):
        """Start screen recording in a background thread."""
        if self._recording:
            return
        self._output_path = filepath
        self._recording = True
        self._record_thread = threading.Thread(target=self._record_loop, daemon=True)
        self._record_thread.start()

    def stop_recording(self):
        """Stop screen recording and finalize the video file."""
        if not self._recording:
            return None
        self._recording = False
        if self._record_thread:
            self._record_thread.join(timeout=5)
        path = self._output_path
        self._output_path = None
        return path

    def _record_loop(self):
        """Internal loop that captures frames and writes to video.
        Thread-safe: creates its own mss instance.
        """
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[self._primary_idx]

                # Grab one frame to get dimensions
                sample = sct.grab(monitor)
                frame = np.array(sample)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                h, w = frame.shape[:2]

                # Resize for performance
                if w > 1280:
                    scale = 1280 / w
                    w_out, h_out = 1280, int(h * scale)
                else:
                    w_out, h_out = w, h

                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                self._video_writer = cv2.VideoWriter(self._output_path, fourcc, SCREEN_FPS, (w_out, h_out))

                frame_interval = 1.0 / SCREEN_FPS

                while self._recording:
                    start_time = time.time()

                    img = sct.grab(monitor)
                    frame = np.array(img)
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

                    if w_out != w:
                        frame = cv2.resize(frame, (w_out, h_out))

                    self._video_writer.write(frame)

                    # Maintain target FPS
                    elapsed = time.time() - start_time
                    sleep_time = frame_interval - elapsed
                    if sleep_time > 0:
                        time.sleep(sleep_time)

        except Exception as e:
            print(f"❌ Screen recording error: {e}")
        finally:
            if self._video_writer:
                self._video_writer.release()
                self._video_writer = None

    def close(self):
        self.stop_recording()
