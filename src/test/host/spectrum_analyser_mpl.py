import soundcard as sc
import numpy as np
import sys
import matplotlib.pyplot as plt

# Lots of good info on numpy's FFT here:
# https://stackoverflow.com/questions/8573702/units-of-frequency-when-using-fft-in-numpy

SAMPLE_RATE = 48000
# 2048 isn't bad, it allows us to get down to 20Hz and still have a reasonable refresh rate but is very low-res in the <100Hz region
SAMPLE_FRAMES = 1024 # Remember that the shorter this window, the greater the minimum detectable frequency
ROLLING_SAMPLES = 4 # Any less than 4 and parts of the histogram have no data, too high and we get too much latency
FREQ_RES = SAMPLE_RATE / SAMPLE_FRAMES
AVERAGING_WINDOW = 5 # Controls the 'smoothness' of the signal, where 0 is effectively no smoothing
WINDOW_WEIGHTS = np.array([np.linspace(0, 1, AVERAGING_WINDOW)]).transpose() # Controls how the contribution of previous samples decays over time
NBINS = 12
BINS = [(2 * 10**n) for n in np.linspace(1, 4, NBINS+1)] # Logarithmic frequency bins (20Hz - 2kHz seems pretty good)
BLOCK_CHARS = ["\U00002581", "\U00002582", "\U00002583", "\U00002584", "\U00002585", "\U00002586", "\U00002587", "\U00002588"]

#print(" ".join([c*2 for c in BLOCK_CHARS]))
#print([b * FREQ_RES for b in BINS])

prev_samples = np.zeros([SAMPLE_FRAMES * ROLLING_SAMPLES, 2])

prev_hist_data = np.zeros((AVERAGING_WINDOW, NBINS))

mic = sc.get_microphone(sc.default_speaker().id, include_loopback = True)

freq = np.fft.rfftfreq(SAMPLE_FRAMES * ROLLING_SAMPLES, 1/SAMPLE_RATE)
freq_binned = np.digitize(freq, BINS) # Quantise transform frequencies into bins

fig = plt.figure()
ax = fig.add_subplot(211)
line = ax.semilogx(freq, np.zeros((int((SAMPLE_FRAMES * ROLLING_SAMPLES)/2)+1)))[0]
plt.xlim([BINS[0], BINS[-1]])
plt.ylim([0, 20])

ax = fig.add_subplot(212)
rects = ax.bar(BINS[:-1], [0]*(NBINS), width = [(BINS[i+1] - BINS[i]) * 0.8 for i in range(NBINS)], align = "edge")
plt.xscale("log")
plt.xlim([BINS[0], BINS[-1]])
plt.ylim([0, 20])

plt.show(block = False)

with mic.recorder(samplerate = SAMPLE_RATE) as rec:

    while True:
        
        data = rec.record(numframes = SAMPLE_FRAMES)
        prev_samples = np.row_stack([prev_samples[SAMPLE_FRAMES:, :], data])

        mono = np.max(prev_samples, axis = 1)
        # Apply Hanning window before FFT to combat spectral leakage (see link at top for details)
        # This really does seem to improve how the signal responds to the music
        amps = np.abs(np.fft.rfft(mono * np.hanning(len(mono))))

        line.set_ydata(amps)
        amps_binned = np.array([np.max(amps[np.where(freq_binned == i+1)]) for i in range(NBINS)])
        amps_binned = np.nan_to_num(amps_binned)

        for rect, h in zip(rects, amps_binned):
            rect.set_height(h)

        fig.canvas.draw()
        fig.canvas.flush_events()

        # Shift prev samples up 1, discard the oldest and append the current sample
        prev_hist_data = np.row_stack([prev_hist_data[1:, :], amps_binned])
        # Calculate average across frames
        freq_avg = np.sum(prev_hist_data * WINDOW_WEIGHTS, axis = 0) / sum(WINDOW_WEIGHTS)
        # Multiply each bin amplitude by the frequency of that bin so we get a more even distribution
        freq_levels = [int(min(x/10, 1) * (len(BLOCK_CHARS)-1)) for x in freq_avg]# * BINS[:-1]]
        sys.stdout.write("\033[K")
        print("     " + " ".join([BLOCK_CHARS[i]*2 for i in freq_levels]), end = "\r") # Spaces to avoid the caret