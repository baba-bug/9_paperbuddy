import pyaudio
import numpy as np
import time
import sys
import os

# Robust import
try:
    from .audio_detector import AudioEmotionDetector
except ImportError:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from audio_detector import AudioEmotionDetector

# Constants
FORMAT = pyaudio.paFloat32
CHANNELS = 1
RATE = 16000
CHUNK = 1024
RECORD_SECONDS = 3

def main():
    print("⏳ Initializing Audio Emotion Model (this may take a moment)...")
    detector = AudioEmotionDetector()
    
    p = pyaudio.PyAudio()
    
    # List devices to help user if needed
    info = p.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')
    # default_device_index = p.get_default_input_device_info()["index"]
    
    # Open stream
    # Use default input device
    try:
        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)
    except Exception as e:
        print(f"❌ Failed to open audio stream: {e}")
        return

    print(f"🎙️ Start recording... (Analyzing every {RECORD_SECONDS}s) - Ctrl+C to stop")
    
    try:
        while True:
            frames = []
            # Record for RECORD_SECONDS
            for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                try:
                    data = stream.read(CHUNK, exception_on_overflow=False)
                    frames.append(np.frombuffer(data, dtype=np.float32))
                except IOError as e:
                    print(f"⚠️ Audio read error: {e}")
                    continue
                
            if not frames:
                continue

            audio_data = np.concatenate(frames)
            
            # Calibration: Check RMS volume
            rms = np.sqrt(np.mean(audio_data**2))
            if rms < 0.01: # Threshold for silence
                print("🔇 [Silence]") # Output silence instead of waiting
                continue

            # Analyze
            label, score = detector.analyze(audio_data, sample_rate=RATE)
            if label:
                print(f"🔊 Audio Emotion: {label} ({score:.2f})")
            
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        if 'stream' in locals():
            stream.stop_stream()
            stream.close()
        p.terminate()

if __name__ == "__main__":
    main()
