import soundcard as sc
import numpy as np

#mic = sc.default_microphone()

# This almost seems *too* easy...
mic = sc.all_microphones(include_loopback = True)[0]

with mic.recorder(samplerate = 48000) as mic:
    for _ in range(500):
        data = mic.record(numframes=1024)
        print("#" * (int(np.max(data) * 500)))