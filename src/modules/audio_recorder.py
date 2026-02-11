import pyaudio
import torch
import numpy as np
import collections
from silero_vad import load_silero_vad
from .utils import FORMAT, CHANNELS, RATE, CHUNK_SIZE, PADDING_DURATION_MS, VAD_THRESHOLD


class AudioRecorder:
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.stream = None

        # Load Silero VAD model (neural network, runs on CPU)
        print("🧠 Loading Silero VAD model...")
        self.model = load_silero_vad()
        self.model.eval()
        torch.set_num_threads(1)  # Silero recommends single thread for efficiency

        # Silence history: how many consecutive silent chunks we've seen
        # CHUNK_SIZE=512 at 16kHz = 32ms per chunk
        # PADDING_DURATION_MS=3000ms → need 3000/32 ≈ 94 chunks of silence
        chunk_duration_ms = (CHUNK_SIZE / RATE) * 1000
        self.history = collections.deque(maxlen=int(PADDING_DURATION_MS / chunk_duration_ms))

    def start_stream(self):
        try:
            self.stream = self.p.open(format=FORMAT,
                                      channels=CHANNELS,
                                      rate=RATE,
                                      input=True,
                                      frames_per_buffer=CHUNK_SIZE)
            return True
        except OSError as e:
            print(f"❌ Failed to open audio stream: {e}")
            print("Please ensure a microphone is connected and accessible.")
            self.stream = None
            return False

    def read(self):
        if self.stream:
            try:
                data = self.stream.read(CHUNK_SIZE, exception_on_overflow=False)
                return data
            except Exception as e:
                print(f"Audio read error: {e}")
                return b'\x00' * (CHUNK_SIZE * 2)  # 2 bytes per sample (16-bit)
        return b'\x00' * (CHUNK_SIZE * 2)

    def is_speech(self, chunk):
        """Use Silero VAD to detect speech. Returns True if probability > threshold."""
        try:
            # Convert raw bytes to float32 tensor
            audio_int16 = np.frombuffer(chunk, dtype=np.int16)
            audio_float32 = audio_int16.astype(np.float32) / 32768.0
            audio_tensor = torch.from_numpy(audio_float32)

            # Run model — returns speech probability (0.0 to 1.0)
            prob = self.model(audio_tensor, RATE).item()
            return prob > VAD_THRESHOLD
        except Exception:
            return False

    def reset_vad(self):
        """Reset model states between utterances for clean detection."""
        self.model.reset_states()

    def close(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()
