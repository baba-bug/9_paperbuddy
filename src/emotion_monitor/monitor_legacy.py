import cv2
import time
import threading
import queue
import sys
import os

# Robust import for running as script vs module
try:
    from .detector_fer import EmotionDetector
    from .ui_drawer import EmotionUI
    from .data_logger import EmotionLogger
except ImportError:
    # If running directly file, add current dir to path
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from detector_fer import EmotionDetector
    from ui_drawer import EmotionUI
    from data_logger import EmotionLogger

class EmotionMonitorApp:
    def __init__(self, camera_index=0, check_interval=0.5):
        self.camera_index = camera_index
        self.check_interval = check_interval
        self.running = False
        self.current_emotion = "Waiting..."
        self.current_confidence = 0.0
        
        self.cap = None
        self.frame_queue = queue.Queue(maxsize=1)
        self.lock = threading.Lock()
        
        # Modules
        self.detector = EmotionDetector(smoothing_window=5) # Smooth over last 5 frames
        self.ui = EmotionUI()
        self.logger = EmotionLogger()
        
        print(f"👀 Emotion Monitor initialized.")
        print(f"📝 Logging to: {self.logger.get_log_path()}")

    def start(self):
        # Use CAP_DSHOW on Windows to avoid MSMF errors
        backend = cv2.CAP_DSHOW if os.name == 'nt' else cv2.CAP_ANY
        self.cap = cv2.VideoCapture(self.camera_index, backend)
        
        if not self.cap.isOpened():
            print(f"❌ Cannot open camera {self.camera_index}")
            return

        self.running = True
        
        # Start analysis thread
        analysis_thread = threading.Thread(target=self._analyze_loop, daemon=True)
        analysis_thread.start()
        
        print("▶️ Monitor running... Press 'q' to quit.")
        
        try:
            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    print("❌ Failed to grab frame")
                    break

                # Flip for mirror effect
                frame = cv2.flip(frame, 1)

                # Update frame for analysis thread (overwrite old if full)
                if self.frame_queue.full():
                    try:
                        self.frame_queue.get_nowait()
                    except queue.Empty:
                        pass
                self.frame_queue.put(frame.copy())

                # Draw UI
                emo_text = f"{self.current_emotion} ({self.current_confidence:.1f}%)"
                self.ui.draw_overlay(frame, emo_text)
                
                cv2.imshow('Emotion Monitor (Smoothed)', frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.running = False
                    break
        finally:
            self.stop()

    def stop(self):
        self.running = False
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        print("👋 Emotion Monitor stopped.")

    def _analyze_loop(self):
        """Background thread for heavy DeepFace inference."""
        last_check = 0
        while self.running:
            try:
                frame = self.frame_queue.get(timeout=1)
            except queue.Empty:
                continue

            # Rate limit analysis
            now = time.time()
            if now - last_check < self.check_interval:
                continue
            
            last_check = now
            
            try:
                # Run DeepFace analysis via Detector
                emotion, confidence = self.detector.analyze(frame)
                
                if emotion:
                    self.current_emotion = emotion
                    self.current_confidence = confidence
                    
                    # Log
                    self.logger.log(emotion, confidence)
                    
                    # Console log (optional, minimal)
                    # print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {emotion} ({confidence:.1f}%)")
                    
                else:
                    self.current_emotion = "No face"
                    
            except Exception as e:
                print(f"Analysis loop error: {e}")

if __name__ == "__main__":
    app = EmotionMonitorApp()
    app.start()
