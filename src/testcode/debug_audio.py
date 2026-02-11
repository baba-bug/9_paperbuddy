import pyaudio
import numpy as np
import time

# Constants
RATE = 16000
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1

def debug_audio_level():
    p = pyaudio.PyAudio()
    
    try:
        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)
    except Exception as e:
        print(f"❌ Failed to open audio stream: {e}")
        return

    print("🎙️  Microphone Debug Mode")
    print("Please speak into your microphone. You should see the bar move.")
    print("Press Ctrl+C to exit.")
    print("-" * 50)

    try:
        while True:
            data = stream.read(CHUNK, exception_on_overflow=False)
            # Convert binary data to numpy array
            audio_data = np.frombuffer(data, dtype=np.int16)
            # Calculate volume (RMS)
            volume = np.linalg.norm(audio_data) / np.sqrt(len(audio_data))
            
            # Visualizer
            bars = "I" * int(volume / 50)  # Adjust sensitivity divisor if needed
            print(f"\rVolume: {int(volume):04d} |{bars.ljust(50)}|", end="")
            
    except KeyboardInterrupt:
        print("\n\nStopped.")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

if __name__ == "__main__":
    debug_audio_level()
