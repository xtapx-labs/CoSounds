from fastapi import FastAPI
from pathlib import Path
import numpy as np
import librosa
import sounddevice as sd

app = FastAPI()

# Global buffer and stream
playing = {"buffer": None, "sr": None, "stream": None, "pos": 0}

BUFFER_SIZE = 44100 * 120  # 60 seconds buffer, adjust as needed

def callback(outdata, frames, time, status):
    if playing["buffer"] is None:
        outdata.fill(0)
        return

    start = playing["pos"]
    end = start + frames
    if end > len(playing["buffer"]):
        end = len(playing["buffer"])
    
    outdata[: end - start] = playing["buffer"][start:end].reshape(-1, 1)
    
    # Fill remaining with zeros if buffer is shorter
    if frames > end - start:
        outdata[end - start :] = 0

    playing["pos"] = end % len(playing["buffer"])


@app.on_event("startup")
async def startup_event():
    audio_file = Path(__file__).parent / ".audio" / "gmulyk-edit__7965__ingeos__hong-linh-ha-tinh-vietnam.wav"
    y, sr = librosa.load(str(audio_file), sr=None)
    
    # Initialize buffer
    buffer = np.zeros(max(len(y), BUFFER_SIZE))
    buffer[:len(y)] = y
    playing["buffer"] = buffer
    playing["sr"] = sr
    playing["pos"] = 0
    
    # Start output stream
    stream = sd.OutputStream(channels=1, samplerate=sr, callback=callback)
    stream.start()
    playing["stream"] = stream

