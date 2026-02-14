import numpy as np
import torch
from transformers import pipeline
import logging

# Suppress warnings
logging.getLogger("transformers").setLevel(logging.ERROR)

class AudioEmotionDetector:
    def __init__(self, model_name="superb/wav2vec2-base-superb-er"):
        print(f"🎤 Loading Audio Emotion model: {model_name}...")
        try:
            # device=0 for GPU if available, else -1 for CPU
            device = 0 if torch.cuda.is_available() else -1
            self.classifier = pipeline("audio-classification", model=model_name, device=device)
            print(f"✅ Audio Emotion model loaded (device={device}).")
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            self.classifier = None
        
    def analyze(self, audio_data, sample_rate=16000):
        """
        Analyze audio chunk.
        audio_data: numpy array (float32), mono
        sample_rate: sampling rate (default 16000 for wav2vec2)
        """
        if self.classifier is None:
            return None, 0.0
            
        try:
            # Ensure float32
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # Pipeline expects dict for raw audio
            input_data = {"array": audio_data, "sampling_rate": sample_rate}
            
            # Run inference
            # top_k=1 returns the top prediction
            results = self.classifier(input_data, top_k=1)
            
            if results:
                top = results[0]
                return top['label'], top['score']
                
            return None, 0.0
            
        except Exception as e:
            print(f"Audio analysis error: {e}")
            return None, 0.0
