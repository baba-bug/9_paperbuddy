from fer.fer import FER
import collections
import numpy as np
import cv2

class EmotionDetector:
    def __init__(self, smoothing_window=3):
        # mtcnn=True uses MTCNN for face detection (slower but more accurate)
        # If it's too slow on CPU, we can switch to mtcnn=False (OpenCV Haar)
        try:
            self.detector = FER(mtcnn=True)
            print("✅ FER: Loaded MTCNN detector.")
        except Exception as e:
            print(f"⚠️ FER: Failed to load MTCNN ({e}), falling back to OpenCV Haar.")
            self.detector = FER(mtcnn=False)
            
        self.smoothing_window = smoothing_window
        self.history = collections.deque(maxlen=smoothing_window)
        
    def analyze(self, frame):
        """
        Analyze frame and return smoothed emotion result.
        Returns: (emotion_label, confidence_score)
        """
        try:
            # FER expects RGB. OpenCV gives BGR.
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Detect emotions
            results = self.detector.detect_emotions(rgb_frame)
            
            if not results:
                return None, 0.0

            # Take the largest face (usually the user)
            # results is list of {'box':..., 'emotions':...}
            # We can sort by area if needed, but 'fer' usually returns primary face first?
            # Let's assume index 0 is fine or sort by box area.
            
            face_result = max(results, key=lambda x: x['box'][2] * x['box'][3])
            
            # Get output probabilities (dict)
            emotions = face_result['emotions']
            
            # Update history
            self.history.append(emotions)
            
            # Smooth results
            smoothed_emotions = self._smooth_predictions()
            
            # Find dominant emotion
            dominant_emotion = max(smoothed_emotions, key=smoothed_emotions.get)
            confidence = smoothed_emotions[dominant_emotion] * 100.0 # FER returns 0-1, we want 0-100
            
            return dominant_emotion, confidence
            
        except Exception as e:
            print(f"FER processing error: {e}")
            return None, 0.0

    def _smooth_predictions(self):
        """Average emotion probabilities over the history window."""
        if not self.history:
            return {}
            
        # Initialize aggregate scores
        avg_scores = collections.defaultdict(float)
        
        # Sum up
        for emotion_dict in self.history:
            for emotion, score in emotion_dict.items():
                avg_scores[emotion] += score
                
        # Average
        count = len(self.history)
        for emotion in avg_scores:
            avg_scores[emotion] /= count
            
        return avg_scores
