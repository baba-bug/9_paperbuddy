import cv2

class EmotionUI:
    def __init__(self):
        pass

    def _get_color(self, text):
        lbl = text.lower()
        if "ang" in lbl: return (0, 0, 255) # Red
        if "hap" in lbl or "sur" in lbl: return (0, 255, 255) # Yellow
        if "sad" in lbl or "fear" in lbl: return (255, 0, 0) # Blue
        if "neu" in lbl: return (200, 200, 200) # Gray
        if "silence" in lbl or "waiting" in lbl or "no face" in lbl: return (100, 100, 100) # Dark Gray
        return (0, 255, 0) # Green (default)

    def draw_overlay(self, frame, emotion_text):
        h, w, _ = frame.shape
        cv2.rectangle(frame, (0, 0), (w, 40), (0, 0, 0), -1)
        color = self._get_color(emotion_text)
        cv2.putText(frame, f"Emotion: {emotion_text}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        return frame

    def draw_av_overlay(self, frame, video_text, audio_text):
        h, w, _ = frame.shape
        # Taller background for 2 lines
        cv2.rectangle(frame, (0, 0), (w, 70), (0, 0, 0), -1)
        
        v_color = self._get_color(video_text)
        cv2.putText(frame, f"Video: {video_text}", (10, 25), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, v_color, 2)
                    
        a_color = self._get_color(audio_text)
        cv2.putText(frame, f"Audio: {audio_text}", (10, 55), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, a_color, 2)
        return frame
