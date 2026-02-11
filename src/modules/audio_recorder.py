import pyaudio
import webrtcvad
import collections
from .utils import FORMAT, CHANNELS, RATE, CHUNK_SIZE, PADDING_DURATION_MS, FRAME_DURATION_MS

class AudioRecorder:
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.vad = webrtcvad.Vad(3)
        self.history = collections.deque(maxlen=int(PADDING_DURATION_MS / FRAME_DURATION_MS))

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
                return b'\x00' * CHUNK_SIZE
        return b'\x00' * CHUNK_SIZE 

    def is_speech(self, chunk):
        try:
            return self.vad.is_speech(chunk, RATE)
        except:
            return False

    def close(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()
