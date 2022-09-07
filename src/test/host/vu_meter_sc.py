import soundcard as sc
import numpy as np
import sys

#mic = sc.default_microphone()

# This almost seems *too* easy...
mic = sc.all_microphones(include_loopback = True)[0]

with mic.recorder(samplerate = 48000) as rec:
    while True:
        data = rec.record(numframes=1024)
        sys.stdout.write("\033[K")
        print("#" * (int(np.max(data) * 500)), end = "\r")