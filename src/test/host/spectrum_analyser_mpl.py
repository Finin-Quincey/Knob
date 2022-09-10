import soundcard as sc
import numpy as np
import sys
import matplotlib.pyplot as plt

# Lots of good info on numpy's FFT here:
# https://stackoverflow.com/questions/8573702/units-of-frequency-when-using-fft-in-numpy

SAMPLE_RATE = 48000
# TODO: Keep a rolling list of samples to improve fft output resolution and min frequency without slowing refresh rate
# 2048 isn't bad, it allows us to get down to 20Hz and still have a reasonable refresh rate but is very low-res in the <100Hz region
SAMPLE_FRAMES = 1024 # Remember that the shorter this window, the greater the minimum detectable frequency
FREQ_RES = SAMPLE_RATE / SAMPLE_FRAMES
AVERAGING_WINDOW = 15 # Controls the 'smoothness' of the signal, where 0 is effectively no smoothing
WINDOW_WEIGHTS = np.array([np.linspace(0, 1, AVERAGING_WINDOW)]).transpose() # Controls how the contribution of previous samples decays over time
NBINS = 30
BINS = [(2 * 10**n) for n in np.linspace(1, 3, NBINS+1)] # Logarithmic frequency bins (20Hz - 2kHz seems pretty good)
BLOCK_CHARS = ["\U00002581", "\U00002582", "\U00002583", "\U00002584", "\U00002585", "\U00002586", "\U00002587", "\U00002588"]

#print(" ".join([c*2 for c in BLOCK_CHARS]))
print([b * FREQ_RES for b in BINS])

prev_samples = np.zeros((AVERAGING_WINDOW, NBINS))

mic = sc.get_microphone(sc.default_speaker().id, include_loopback = True)

freq = np.fft.rfftfreq(SAMPLE_FRAMES, 1/SAMPLE_RATE)
freq_binned = np.digitize(freq, BINS) # Quantise transform frequencies into bins

fig = plt.figure()
ax = fig.add_subplot(211)
line = ax.semilogx(freq, np.zeros((int(SAMPLE_FRAMES/2)+1)))[0]
plt.xlim([20, 2000])
plt.ylim([0, 20])

ax = fig.add_subplot(212)
rects = ax.bar(BINS[1:], [0]*(NBINS), width = [BINS[i+1] - BINS[i] for i in range(NBINS)], align = "edge")
plt.xscale("log")
plt.xlim([20, 2000])
plt.ylim([0, 20])

plt.show(block = False)

with mic.recorder(samplerate = SAMPLE_RATE) as rec:
    while True:
        data = rec.record(numframes = SAMPLE_FRAMES)
        mono = np.max(data, axis = 1)
        # Apply Hanning window before FFT to combat spectral leakage (see link at top for details)
        # This really does seem to improve how the signal responds to the music
        amps = np.abs(np.fft.rfft(mono * np.hanning(len(mono))))

        line.set_ydata(amps)
        amps_binned = np.array([np.mean(amps[np.where(freq_binned == i)]) for i in range(NBINS)])
        amps_binned = np.nan_to_num(amps_binned)

        for rect, h in zip(rects, amps_binned):
            rect.set_height(h)

        fig.canvas.draw()
        fig.canvas.flush_events()

        # Shift prev samples up 1, discard the oldest and append the current sample
        prev_samples = np.row_stack([prev_samples[1:, :], amps_binned])
        # Calculate average across frames
        freq_avg = np.sum(prev_samples * WINDOW_WEIGHTS, axis = 0) / sum(WINDOW_WEIGHTS)
        # Multiply each bin amplitude by the frequency of that bin so we get a more even distribution
        freq_levels = [int(min(x/20, 1) * (len(BLOCK_CHARS)-1)) for x in freq_avg]# * BINS[:-1]]
        sys.stdout.write("\033[K")
        print("     " + " ".join([BLOCK_CHARS[i]*2 for i in freq_levels]), end = "\r") # Spaces to avoid the caret