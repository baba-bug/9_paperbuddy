import os
import datetime

class EmotionLogger:
    def __init__(self, log_dir="data/emotion_logs"):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        ts_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(self.log_dir, f"emotion_{ts_str}.csv")
        
        # Write header
        with open(self.log_file, "w", encoding="utf-8") as f:
            f.write("timestamp,emotion,confidence\n")
            
    def log(self, emotion, confidence, timestamp=None):
        if timestamp is None:
            timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"{timestamp},{emotion},{confidence:.2f}\n")
            
    def get_log_path(self):
        return self.log_file
