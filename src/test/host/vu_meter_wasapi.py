import pyaudio
import numpy as np

# List output devices
# Source: https://stackoverflow.com/questions/36894315/how-to-select-a-specific-input-device-with-pyaudio

# Alternative version using WASAPI (didn't work sadly)

WASAPI_HOST_INDEX = 2

p = pyaudio.PyAudio()
info = p.get_host_api_info_by_index(WASAPI_HOST_INDEX)
numdevices = info.get('deviceCount')

for i in range(0, numdevices):
    if (p.get_device_info_by_host_api_device_index(WASAPI_HOST_INDEX, i).get('maxInputChannels')) > 0:
        name = p.get_device_info_by_host_api_device_index(WASAPI_HOST_INDEX, i).get('name')
        print("Input Device id ", i, " - ", name)


# Visualise input stream for a few seconds
# Source: https://swharden.com/blog/2016-07-19-realtime-audio-visualization-in-python/# 

CHUNK = 2**11
RATE = 44100

p = pyaudio.PyAudio()
stream = p.open(format = pyaudio.paInt16,channels = 1,rate = RATE,input = True,
              frames_per_buffer = CHUNK, input_device_index = 3)

for i in range(int(10*44100/1024)): #go for a few seconds
    data = np.fromstring(stream.read(CHUNK),dtype = np.int16)
    peak = np.average(np.abs(data))*2
    bars = "#" * int(1000 * peak/2**16)
    print("%04d %05d %s"%(i,peak,bars))

stream.stop_stream()
stream.close()
p.terminate()