# p4e-training-protocol


## Dependencies
 - `pip install pyserial numpy pyaudio analyse` 
 - [Open CV - 3.2.0](http://opencv.org/releases.html)


## Program Limitations
 - To run each level, I use recursive calls, so if a phase is run for more than 1000 level runs, the program will quit.
   - Ex: `Level 1` -> `Level 2` -> `Level 1` -> `Level 2` -> `Level 3` is 5 level runs
 - To be able to change the sensitivity of the mic using the keyboard, the program must be run in command prompt

## Microphone
  - Make sure you set the Kinect microphone to the system's default.  
  - The default sensitivity is -20dB. You can change this with the `--mic` command line argument and using the keyboard's arrow up/down keys when the phase is running. (Press down if the mic is too sensitive (dog barking too much))
   
## Video
  - The camera ID defaults to 1 which should be the Kinect. Try 0 if that is not working.

## Date Format
  - The date format in the logs uses Month-Day-Year Hour:Minute:Second format
