import struct
from threading import Thread

import numpy
import pyaudio

import Config
import Logger

has_dog_barked = False
thresh = -5
SHORT_NORMALIZE = (1.0 / 32768.0)


def get_db(block):
    # RMS amplitude is defined as the square root of the 
    # mean over time of the square of the amplitude.
    # so we need to convert this string of bytes into 
    # a string of 16-bit samples...

    # we will get one short out for each 
    # two chars in the string.
    count = len(block) / 2
    formats = "%dh" % count
    shorts = struct.unpack(formats, block)

    # iterate over the block.
    for sample in shorts:
        # sample is a signed short in +/- 32768. 
        # normalize it to 1.0
        n = sample * SHORT_NORMALIZE

    return 10 * numpy.log10(abs(n) + 0.0000001)


def reset_bark_status():
    global has_dog_barked
    has_dog_barked = False


def record_bark_status():
    thread_audio = Thread(target=__start__)
    thread_audio.start()


def __start__():
    # This will be where code is written for the microphone
    Logger.debug("Starting recording of dog bark status.")
    # detect bark with a threshold

    pyaud = pyaudio.PyAudio()  # initialize
    chunk = 1024

    mic_dict = pyaud.get_default_input_device_info()  # outputs dict of device
    mic_index = mic_dict['index']  # the index is the third entry of the dict

    stream = pyaud.open(  # initializes a stream object
        format=pyaudio.paInt16,
        channels=2,
        rate=48000,  # sample rate in hz
        input_device_index=mic_index,  # whichever USB port the microphone is plugged in to
        input=True)

    Logger.debug("Audio stream is open.")
    while Config.RUN_FLAG:
        global has_dog_barked
        # read raw mic data
        rawsamps = stream.read(chunk)
        # convert to NumPy array
        amplitude = get_db(rawsamps)

        if amplitude >= Config.MIC_SENSITIVITY:
            has_dog_barked = True
            Logger.debug("Dog just barked at %sdb." % amplitude)

    stream.stop_stream()
    stream.close()
