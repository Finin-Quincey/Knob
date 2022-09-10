import soundcard as sc
import numpy as np
import sys

SAMPLE_FRAMES = 1024
AVERAGING_WINDOW = 15 # Controls the 'smoothness' of the signal, where 0 is effectively no smoothing
WINDOW_WEIGHTS = np.array([np.linspace(0, 1, AVERAGING_WINDOW)]).transpose() # Controls how the contribution of previous samples decays over time
BINS = [10**n for n in np.linspace(0, 2, 12)]
BLOCK_CHARS = ["\U00002581", "\U00002582", "\U00002583", "\U00002584", "\U00002585", "\U00002586", "\U00002587", "\U00002588"]

#print(" ".join([c*2 for c in BLOCK_CHARS]))
print(BINS)

prev_samples = np.zeros((AVERAGING_WINDOW, len(BINS)-1))

mic = sc.all_microphones(include_loopback = True)[0]

with mic.recorder(samplerate = 48000) as rec:
    while True:
        data = rec.record(numframes = SAMPLE_FRAMES)
        mono = np.max(data, axis = 1)
        freq = np.abs(np.fft.fft(mono))
        freq_binned, bins = np.histogram(freq, bins = BINS)
        prev_samples = np.row_stack([prev_samples[1:, :], freq_binned])
        freq_avg = np.sum(prev_samples * WINDOW_WEIGHTS, axis = 0) / sum(WINDOW_WEIGHTS)
        freq_levels = [int(min(x/50, 1) * (len(BLOCK_CHARS)-1)) for x in freq_avg * bins[1:]]
        sys.stdout.write("\033[K")
        print("     " + " ".join([BLOCK_CHARS[i]*2 for i in freq_levels]), end = "\r") # Spaces to avoid the caret