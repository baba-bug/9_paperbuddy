import threading
import time
import cv2
import numpy as np
import pyaudio
import sys
import os

# Ensure local imports work
try:
    from .video_detector import EmotionDetector
    from .ui_drawer import EmotionUI
    from .audio_detector import AudioEmotionDetector
except ImportError:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from video_detector import EmotionDetector
    from ui_drawer import EmotionUI
    from audio_detector import AudioEmotionDetector

class AVMonitor:
    def __init__(self):
        print("🚀 Initializing AV Monitor...")
        self.video_detector = EmotionDetector() # Uses FER (MTCNN)
        self.ui = EmotionUI()
        self.audio_detector = AudioEmotionDetector() # Uses Wav2Vec2
        
        self.latest_audio_emotion = "Waiting..."
        self.latest_video_emotion = "Waiting..."
        self.running = True
        
        # Audio config
        self.FORMAT = pyaudio.paFloat32
        self.CHANNELS = 1
        self.RATE = 16000
        self.CHUNK = 1024
        self.STRIDE_SECONDS = 0.5 # Update every 0.5s
        self.WINDOW_SECONDS = 2.0 # Analyze last 2s (shorter = less lag perception, still enough context)
        
    def start_audio_thread(self):
        self.audio_thread = threading.Thread(target=self._audio_loop, daemon=True)
        self.audio_thread.start()
        print("🎙️ Audio thread started.")
        
    def _audio_loop(self):
        import collections
        p = pyaudio.PyAudio()
        try:
            stream = p.open(format=self.FORMAT,
                            channels=self.CHANNELS,
                            rate=self.RATE,
                            input=True,
                            frames_per_buffer=self.CHUNK)
        except Exception as e:
            print(f"❌ Audio stream error: {e}")
            return

        # Buffer stores chunks. 
        # Total chunks needed = (RATE * WINDOW) / CHUNK
        chunks_per_window = int(self.RATE * self.WINDOW_SECONDS / self.CHUNK)
        audio_buffer = collections.deque(maxlen=chunks_per_window)
        
        stride_chunks = int(self.RATE * self.STRIDE_SECONDS / self.CHUNK)

        while self.running:
            new_chunks = []
            
            # Read stride duration
            for _ in range(stride_chunks):
                if not self.running: break
                try:
                    data = stream.read(self.CHUNK, exception_on_overflow=False)
                    new_chunks.append(np.frombuffer(data, dtype=np.float32))
                except: continue
            
            if not new_chunks: continue
            
            # Add to rolling buffer
            audio_buffer.extend(new_chunks)
            
            # Need enough data
            if len(audio_buffer) < chunks_per_window:
                # self.latest_audio_emotion = "Buffering..."
                continue
            
            # Concatenate buffer for analysis
            full_audio = np.concatenate(list(audio_buffer))
            
            # Silence check
            rms = np.sqrt(np.mean(full_audio**2))
            if rms < 0.01:
                self.latest_audio_emotion = "Silence"
            else:
                label, score = self.audio_detector.analyze(full_audio, self.RATE)
                if label:
                    self.latest_audio_emotion = f"{label} ({score:.2f})"
        
        # Cleanup
        try:
            stream.stop_stream()
            stream.close()
        except: pass
        p.terminate()
                    
    def run(self):
        self.start_audio_thread()
        
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                print("❌ Cannot open webcam.")
                return
        except Exception as e:
            print(f"❌ Webcam error: {e}")
            return
        
        last_log_time = time.time()
        
        print("▶️ AV Monitor running... Press 'q' to quit.")
        print("   (Logging fused results every 1.0s)")
        
        try:
            while self.running:
                ret, frame = cap.read()
                if not ret: break
                
                frame = cv2.flip(frame, 1)
                
                # Video Analysis (Frame-by-frame)
                # Note: FER might be slow on CPU. If lagging, we might need threading for video too.
                v_emo, v_conf = self.video_detector.analyze(frame)
                if v_emo:
                    self.latest_video_emotion = f"{v_emo} ({v_conf:.1f}%)"
                else:
                    self.latest_video_emotion = "No Face"
                
                # Draw Overlay
                frame = self.ui.draw_av_overlay(frame, self.latest_video_emotion, self.latest_audio_emotion)
                
                cv2.imshow('Emotion Monitor (AV Fusion)', frame)
                
                # Log every 1s
                current_time = time.time()
                if current_time - last_log_time >= 1.0:
                    timestamp = time.strftime('%H:%M:%S')
                    print(f"[{timestamp}] Video: {self.latest_video_emotion} | Audio: {self.latest_audio_emotion}")
                    last_log_time = current_time
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.running = False
        except KeyboardInterrupt:
            self.running = False
        finally:
            cap.release()
            cv2.destroyAllWindows()
            print("🛑 Stopped.")

if __name__ == "__main__":
    app = AVMonitor()
    app.run()
