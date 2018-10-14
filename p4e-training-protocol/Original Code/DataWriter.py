''' Generic sensor reading and data writer used for classification'''
from datetime import datetime, timedelta
import socket
import subprocess
import pickle
import csv
import sys
import os
import copy
import random
import argparse
import time
from threading import Thread
import logging
import msvcrt # only works for Windows.
import psutil

import wiiuse
import Utilities as pyUt
import Button
import Compass
import Distance
import Harness
import CaninePosition
import Pressure
import Wiimote
import KeyboardInput


########################################################################################
# Program used to receive the harness sensor data
#########################################################################################
# pylint: disable=global-statement,too-many-nested-blocks, too-many-boolean-expressions


########################################################
# Read in the arguments
########################################################
parser = argparse.ArgumentParser()
parser.add_argument('--debug', default=False, dest='debug', \
       action='store_true', \
       help="Boolean whether debug is on or off. Default False")
parser.add_argument('--dog', dest='dog', required=True, \
       choices=pyUt.DATAWRITER_DOGS, \
       help="One of the dogs defined in the YAML file.")

parser.add_argument('--trainersInControl', dest='control', default=False, \
       action='store_true', \
       help="Specify if the trainersInControl.  Otherwise the program's in control")


parser.add_argument('--mode', dest='mode',  required=True, \
       choices=pyUt.DATAWRITER_MODES, \
       help="The mode of experiment.  Valid values are: %s" % str(pyUt.DATAWRITER_MODES))

parser.add_argument('--shapeValue', dest='shapeValue', type=int,\
       help="The starting shape value for the dog.  Default=0")
parser.set_defaults(shapeValue=0)
#parser.add_argument('--labeling', default=False, dest='labeling', \
#       action='store_true', \
#       help="Boolean set to true if labeling is done")

#parser.add_argument('--distance',  dest='distance', type=int, default=None, \
#       help="Distance from wall in feet. 0 implies no distance ultrasonic sensors attached")

parser.add_argument('--compass-low',  dest='compassLow', type=int, default=None, \
       help="Low compass value")
parser.add_argument('--compass-high', dest='compassHigh', type=int, default=None, \
       help="High compass value")

parser.add_argument('--back-compass', dest='backCompass', default=False,\
       action='store_true', \
       help="Should the back magnetometer be used as a compass. Default=False")
parser.add_argument('--no-front-compass', dest='frontCompass', default=True,\
       action='store_false', \
       help="Should the front magnetometer NOT be used as a compass. Default=False")

parser.add_argument('--no-wiimote', dest='wiimoteUsed', action='store_false', \
       help="If not using a Wiimote, use --no-wiimote")
parser.add_argument('--no-pressure', dest='pressureUsed', action='store_false', \
       help="If testing and not using the pressure, use --no-pressure")
parser.add_argument('--no-distance', dest='distanceUsed', action='store_false', \
       help="If testing and not using the distaance, use --no-distance")
parser.add_argument('--no-distanceOverride', dest='distanceOverride', action='store_false', \
       help="If you want to NOT over ride the distance sensor")
parser.add_argument('--no-laser', dest='useLaser', action='store_false', \
       help="Don't use a laser pointer")
parser.set_defaults(wiimoteUsed=True)
parser.set_defaults(pressureUsed=True)
parser.set_defaults(distanceUsed=True)
parser.set_defaults(help=False)
parser.set_defaults(distanceOverride=True)
parser.set_defaults(useLaser=True)
args   = parser.parse_args()

debug         = args.debug         # Global debug, somewhat works
dog           = args.dog           # Required dog name in DATAWRITER_DOGS yaml Datawriter->Dogs
wiimoteUsed   = args.wiimoteUsed   # Is Wiimote being used for experiment or labeling
pressureUsed  = args.pressureUsed  # Is Pressure/wall socket being used
distanceUsed  = args.distanceUsed
compassLow    = args.compassLow    # Compass low override
compassHigh   = args.compassHigh   # Compass high override
#distance      = args.distance     # Distance to be from the wall
distance      = 1                  # Distance fixed at one foot
frontCompass  = args.frontCompass
backCompass   = args.backCompass
shapeValue    = args.shapeValue
distanceOverride = args.distanceOverride
useLaser     = args.useLaser

programsInControl = not args.control           # Program's only in control

labelingMode        = (args.mode == 'labeling')        # Labeling or experimenting
acqBehvMode         = (args.mode == 'acquireBehavior') # Count the number of button pushes / minute
acqDiscMode         = (args.mode == 'acquireDiscrim')  # See extinction
assert (labelingMode or acqBehvMode or acqDiscMode) and (len(pyUt.DATAWRITER_MODES) == 3) , \
  "labelingMode=%s acqBehvMode=%s acqDiscMode=%s DATAWRITER_MODES=%s" % \
  (labelingMode, acqBehvMode, acqDiscMode, str(pyUt.DATAWRITER_MODES))

# Don't use Laser pointer during labeling
if labelingMode and useLaser:
   useLaser = False

# Set up logging before anything, else logging doesn't work
date = datetime.now()
logFilenameTimestamp =  date.strftime("%Y-%m-%d-%H-%M-%S")
assert dog is not None , \
   '--dog must be specified!'
pyUt.ensureDogDirectoryCreated(dog)
logFilename = "data/%s/%s.%s.DataWriter.log" % (dog, logFilenameTimestamp, args.mode)
logging.basicConfig(filename=logFilename, level=logging.INFO, filemode='w')

# Check the compass settings
assert (not labelingMode or ((compassLow is None) and (compassHigh is None))), \
   pyUt.logError( "In --labelingMode, --compass-low and --compass-high must not")
assert (((compassLow is None) and (compassHigh is None)) or
        ((compassLow is not None) and (compassHigh is not None))), \
   pyUt.logError( "If --compassLow is specified, --compassHigh must be specified! %s %s" %
                  (str(compassLow), str(compassHigh)))
if compassLow is None:
   compassLow  = pyUt.COMPASS_LOW
   compassHigh = pyUt.COMPASS_HIGH
assert compassLow >= 0 and compassHigh >= 0, \
   pyUt.logError( "Both --compassLow and --compassHigh must be non-negative! %d %d" % \
                 (compassLow, compassHigh))

# Check the which compass to use
assert (not labelingMode or (frontCompass and not backCompass)), \
   pyUt.logError( "In --labelingMode, --back-compass and --no-front-compass must not." )
assert (labelingMode or (frontCompass or backCompass)), \
   pyUt.logError( "In experiments either the front or back compass must be set")

# Set up experiment counters
startExperiment   = False # Wait for trainer to start experiment
programShapeUpLastMin = False
programShapeDownLastMin = False
experimentCounter = 0     # Count of intervals since the start of experiment
blockCount        = 0
blockMetrics = []  # An array of dictionaries
blockMetric = {'trainerLight': 0, 'trainerTreat': 0, 'programLight': 0, 'programTreat': 0}
for i in range(pyUt.DATAWRITER_EXPLEN):
   blockMetrics.append(copy.copy(blockMetric))

# Initialize all shaping to zero
assert (not labelingMode and not acqBehvMode) or shapeValue==0 , \
   "Shape value should not be specified during acquireBehaver or labeling mode"
assert shapeValue>-1 and shapeValue<len(pyUt.ACQ_DISC_SHAPING), "ShapeValue value invalid"
programShapeValue = shapeValue
trainerShapeValue = shapeValue
pyUt.logInfo("%s Initial shape value is %d" % (pyUt.getPrintTimeString(), shapeValue))


if labelingMode:
   # If labeling is done, no pressure button
   pressureUsed = False
   distanceUsed = False
   assert programsInControl, \
      "If you specify labeling, you should NOT specify --trainersInControl"

if acqBehvMode:
   assert pressureUsed, "If you specify --mode=acquireBehavior the pressure sensor must be active"
   programsInControl = False # The trainer's always in control when doing acquireBehavior

if acqDiscMode:

   # Initialize program delay to -1 to signify no delay in progress
   programDelayValue = -1

# Are we testing? Is the Pressure buttons going to be used?
if not pressureUsed:
   if 'Pressure' in pyUt.PARTS_USED:
      pyUt.PARTS_USED.remove('Pressure')
      pyUt.logInfo("PARTS_USED has Pressure removed and is now: %s " % str(pyUt.PARTS_USED) )


# Are we testing? Is the Wiimote going to be used?
if not wiimoteUsed and 'Wiimote' in pyUt.PARTS_USED:
   pyUt.PARTS_USED.remove('Wiimote')
   pyUt.logError( "PARTS_USED has Wiimote removed and is now: %s" % pyUt.PARTS_USED )


# Read in the dog name and create the logging file
if not (dog in pyUt.DATAWRITER_DOGS):
   line = "DataWriter: The dog specified must be one of: %s" % str(pyUt.DATAWRITER_DOGS)
   pyUt.logError( line )
   assert dog in pyUt.DATAWRITER_DOGS, line

# Display title information
title ="Title: DataWriter: --dog=%s --mode=%s" % (dog, args.mode)
if debug:
   title += " --debug"
if not pressureUsed:
   title += " --no-pressure"
if not wiimoteUsed:
   title += " --no-wiimote"
if not labelingMode:
   title += " ---compass-low=%d --compass-high=%d" % (compassLow, compassHigh)
if not programsInControl:
   title += " --trainersInControl"
print title
if os.name != 'nt':
   print "This only runs on Windows"
   sys.exit(1)
os.system(title)
stillRunning = 1

#####################################################################################
# Determine what are the valid labels available for this invocation and their counts
#####################################################################################
validLabels = pyUt.STANDINGLABELS + pyUt.POSTURELABELS + pyUt.SITTINGLABELS + ['q']
if labelingMode:
   validLabels += pyUt.WIIMOTE_BUTTONLIST_LABELING.values()
else:
   validLabels += pyUt.WIIMOTE_BUTTONLIST_EXPERIMENTING.values()
validLabels = list(set(validLabels))
validLabels.sort()
validLabelCounts={}
for vl in validLabels:
   validLabelCounts[ vl ] = 0



##########################################################
# Periodicaly display the number of labels entered
##########################################################
def labelThread():
   ''' Thread to periodically display the label or training counts'''

   assert labelingMode, \
      "The label thread should not be called when in experimenting mode"

   # Determine what latels are required for labeling or training
   requiredLabels= pyUt.POSTURELABELS
   requiredLabels.sort()
   requiredLabelsFromWiimote = pyUt.WIIMOTE_BUTTONLIST_LABELING.values()
   requiredLabelsFromWiimote.sort()


   while (stillRunning):
      labelTime = pyUt.getPrintTimeString()

      # Create the print line
      labelLine    = "%s label counts:" % labelTime[:-4]
      requiredLine = "%s missing required labels:" % labelTime[:-4]
      someNonZeroLabelsFound = someReqLowLabelsFound = False
      for v in validLabels:
         if validLabelCounts[v] > 0:
            labelLine += "\t%s:%d" % ( v, validLabelCounts[v] )
            someNonZeroLabelsFound = True
         if v in requiredLabels and \
            validLabelCounts[v] < pyUt.REQUIRED_LABEL_COUNTS:
            requiredLine += "\t%s:%d" % ( v, validLabelCounts[v] )
            someReqLowLabelsFound = True
      if someNonZeroLabelsFound:
         pyUt.logInfo( labelLine )
      if someReqLowLabelsFound:
         pyUt.logInfo( requiredLine )

      # It's OK if we're off by a little bit here
      time.sleep( pyUt.TRAINER_DISPLAY_INTERVAL )

   if debug:
      pyUt.logInfo( "labelThread: Done" )



##########################################################
# Watch the keyboard and store the line in notesDataValue
##########################################################
lastLabel = pyUt.NOINPUT
if useLaser:
   keyboardInput = KeyboardInput.KeyboardInput(debug)

def notesThread():
   ''' Thread to handle notes or labels from the keyboard/WiiMote.
       Should be a thread because, imagine someone typing a note in
       but not hitting enter, it would hold up the DataWriter main
       loop.
       But this leaves the possibility of the thread being 0.0001 off from
       harness socket, so make this at 0.x50 seconds and the harness will
       read at 0.x00.  Hopefully we won't miss readings'''
   # pylint: disable=too-many-nested-blocks,too-many-lines
   global notesDataValue, stillRunning
   global lastLabel # pylint: disable=global-variable-not-assigned

   notesThreadTimeInterval = timedelta(0, 0, pyUt.WIIMOTE_INTERVAL * 1000000.0)
   pyUt.tryToGetToOneTenthSecondBoundary()
   time.sleep( 0.050 ) # This should get us half cycle (0.050) off harness socket
   notesThreadNextTime = datetime.now()

   while (stillRunning):
      notesThreadNextTime += notesThreadTimeInterval
      notesTime = pyUt.getPrintTimeString()
      if useLaser:
         label = keyboardInput.input_key()
         # If we got input, and it doesn't match the last input or it wasn't a dispense treat....
         # Basically, don't dispense multiple treats, but leave the cue on
         if label != pyUt.NOINPUT:
            notesLine = label
            notesDataValue = {'notesTime' : notesTime,
                              'notesLine' : notesLine}
            notesThreadNextTime = datetime.now()

            # Should we quit?
            if notesLine.lower() == 'q':
               stillRunning = 0
               pyUt.logInfo("%s: Received a quit" % pyUt.getPrintTimeString())

      elif msvcrt.kbhit():
         if labelingMode:
            # Got a keyboard hit
            notesLine = sys.stdin.readline()
            notesLine = notesLine[:-1] # Remote the \n
            notesDataValue = {'notesTime' : notesTime,
                              'notesLine' : notesLine}
            notesThreadNextTime = datetime.now()

            # Should we quit?
            if notesLine.lower() == 'q':
               pyUt.logInfo("%s: Received a quit" % pyUt.getPrintTimeString())
               stillRunning = 0

            if debug:
               pyUt.logInfo( "NotesThread: %s: '%s'" % (notesTime, notesLine))
         else:
            # Got a keyboard hit
            notesLine = sys.stdin.readline()
            notesLine = notesLine[:-1] # Remote the \n
            notesDataValue = {'notesTime' : notesTime,
                              'notesLine' : notesLine}
            notesThreadNextTime = datetime.now()

            # Should we quit?
            if notesLine.lower() == 'q':
               stillRunning = 0
               pyUt.logInfo("%s: Received a quit" % pyUt.getPrintTimeString())

      elif labelingMode:
         # Use the label from the last key
         notesDataValue = {'notesTime' : notesTime,
                           'notesLine' : lastLabel}

         # Should the light cue be turned on
         notesLine = lastLabel
         if notesLine in validLabels:
            validLabelCounts[ notesLine ] += 1


      # Wait for the next interval
      notesThreadDt = datetime.now()
      if notesThreadDt > notesThreadNextTime:
         pyUt.logError( "%s DataWriter::notesThread nextTime=%s continue" % \
                  (notesThreadDt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3], \
                   notesThreadNextTime.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]))
         # print "JJM fix this you idiot"
         # notesThreadNextTime = notesThreadDt + pyUt.WIIMOTE_INTERVAL
         continue
      notesThreadIntervalCalculation = (notesThreadNextTime - notesThreadDt).microseconds \
                                         / 1000000.0
      if (notesThreadIntervalCalculation > 0.1):
         # We should never get here!!!
         pyUt.logError("%s notesThread::loop %s nextTime=%s dt=%s intervalalCalculation=%f" % \
               (pyUt.getPrintTimeString(), notesTime, \
                notesThreadNextTime.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3], \
                notesThreadDt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3], \
                notesThreadIntervalCalculation))
         notesThreadIntervalCalculation = .1
      time.sleep( notesThreadIntervalCalculation )

   if debug:
      pyUt.logInfo( "NotesThread: Done" )


##########################################################
# Create a file name that's dog/date/time based
# Set up the header and the csvindex
##########################################################
def setupCSVFilenameHarnessTime(dogParm, logFilenameTimestampParm):
   ''' Set up the filenames, indexes etc '''
   global wiimoteWmp

   # Setup the csvFilename data\dog directory
   pyUt.ensureDogDirectoryCreated(dogParm)

   localCsvFilename = "data/%s/%s.%s.csv" % (dogParm, logFilenameTimestampParm, args.mode)

   # setup the csvheader and data
   localCsvHeader  = ['timestamp', 'wiimoteTime', 'sensorTime', 'pressureTime', 'notesTime']
   localCsvHeader += ['distanceTime']
   localCsvHeader += ['notesLine', 'wiimoteDataLen', 'sensorDataLen', 'pressureDataLen']
   localCsvHeader += [ 'programsInControl', 'tutorSignaled', 'compassLow', 'compassHigh' ]
   localCsvHeader += copy.deepcopy( pyUt.WIIMOTE_BUTTONLIST )
   localCsvHeader += copy.deepcopy( pyUt.WIIMOTE_FUNCTIONLIST )
   localCsvHeader += [ 'trainerShapeUp', 'trainerShapeDown', 'experimentCounter', 'blockCount',
                       'programShapeUp', 'programShapeDown', 'startExperiment', 'inMovementGracePeriod']
   localCsvHeader += ['distance', 'programShapeValue', 'programDelayValue', 'trainerShapeValue']
   localCsvHeader += ['msgNoFunction', 'nullFunction'] # Implied wiimote buttons
   localCsvHeader += copy.deepcopy( pyUt.HARNESS_SENSORLIST )
   localCsvHeader += copy.deepcopy( pyUt.HEADING_SENSORLIST )
   localCsvHeader += copy.deepcopy( pyUt.DISTANCE_SENSORLIST )
   localCsvHeader += copy.deepcopy( pyUt.PRESSURE_SENSORLIST )
   localCsvHeader += copy.deepcopy( pyUt.CANINEPOSITION_FUNCTION )
   localCsvHeader += copy.deepcopy( pyUt.TRAINER_FUNCTION )
   for j in range(pyUt.DATAWRITER_EXPLEN):
      localCsvHeader += [ 'blockCountTrainerTreat' + str(j), 'blockCountProgramTreat' + str(j),
                          'blockCountTrainerLight' + str(j), 'blockCountProgramLight' + str(j)]
   localCsvHeader = list(set(localCsvHeader))  # gotta find the duplicate!

   # Mapping of where values go in csvdata by column name
   localCsvdata = []
   localCsvindex = {}
   localIndex = 0
   for x in localCsvHeader:
      localCsvindex[ x ] = localIndex
      #if x == 'blueLight': # JJM
      #   print "JJM csvdata[csvindex[%s]=%d] = %s" % (x, localCsvindex[x], localCsvdata[localCsvindex[x]])
      localCsvdata.append(' ')
      localIndex += 1
   assert len(localCsvindex) == len(localCsvdata)


   # If not using pressure sensor, don't leave the csvdata blank
   if not pressureUsed:
      for sen in pyUt.PRESSURE_SENSORLIST:
         localCsvdata[ localCsvindex[ sen ]]= '1.0'

   if 'Wiimote' in pyUt.PARTS_USED:
      # Set up the wiimote
      nmotes = 2
      wiimotes = wiiuse.init(nmotes)
      while stillRunning and (not wiiuse.find(wiimotes, nmotes, 5)):
         pyUt.logError( "Waiting for wiimote to connect" )
         time.sleep(1)
      wiimoteWmp = wiimotes[0]

   # Set the time, as best we can, on the harness
   # Cannot do as could hang
   # os.system("setTime1.bat")

   return localCsvFilename, localCsvHeader, localCsvdata, localCsvindex




# In order to make the CSV file more readable, keep track of the previous
# trainerLight, clear it when the release button is pressed and copy it when nothing is pressed
previousIterationTrainerLight = ""

def getWiimoteButtonValues():
   '''  Read from the wiimoteData, fill in the wiimoteButtoVaues,
        and call the button functions '''
   global lastLabel
   global wiimotePreviousButtonValues
   # global wiimoteButtonValues
   global previousIterationTrainerLight
   global startExperiment
   global trainerShapeValue

   # Get the data from the wiimote receiver
   if wiimoteUsed:
      data =wiimote.getData()
   else:
      data = wiimotePreviousButtonValues.copy()
   for but in data.keys():
      wiimoteButtonValues[but] = data[but]

   # Reset time and functions called
   csvdata[ csvindex['wiimoteDataLen']] = wiimoteButtonValues['wiimoteDataLen']
   csvdata[ csvindex['wiimoteTime']]    = wiimoteButtonValues['wiimoteTime']
   for x in pyUt.WIIMOTE_FUNCTIONLIST + ['nullFunction', 'msgNoFunction']:
      csvdata[ csvindex[x] ] = ''

   # Reset values
   lastLabel = pyUt.NOINPUT  # Reset/clear the key entered if no wiimote button pressed
   for fun in pyUt.TRAINER_FUNCTION + ['trainerShapeDown', 'trainerShapeUp', 'startExperiment', 'inMovementGracePeriod', 'blockCount', 'programShapeUp', 'programShapeDown']:
      csvdata[ csvindex[ fun ]] = ''

   # Call the button function
   for wiiButton in pyUt.WIIMOTE_BUTTONLIST:
      # For readability in the CSV file, erase the RELSE value if the prevous value
      # for the button was not 'press'
      if wiimoteButtonValues[wiiButton] == 'RELSE' and \
         wiimotePreviousButtonValues[wiiButton] != 'press':
         wiimoteButtonValues[wiiButton] = ''

      # Copy the button value to the csvdata
      csvdata[ csvindex[ wiiButton ]] = wiimoteButtonValues[wiiButton]

      if labelingMode:
         if wiiButton in pyUt.WIIMOTE_BUTTONLIST_LABELING and \
            wiimoteButtonValues[wiiButton] == 'press':
            lastLabel = pyUt.WIIMOTE_BUTTONLIST_LABELING[ wiiButton ]
            pyUt.logInfo( "%s Button %s entered for key %s." % \
                    (pyUt.getPrintTimeString(), wiiButton, lastLabel))
      else: # acqBehvMode or acqDiscMode
         # Execute the function if the trainer's in control
         # otherwise don't do any function
         # If button is pressed and wasn't before, call OnPres
         if wiimoteButtonValues[wiiButton] == 'press' and \
            wiimotePreviousButtonValues[wiiButton] != 'press':
            functValue = wiimoteButtons.buttonFunction(wiiButton, "OnPress", \
                                                 wiimoteWmp, False) # donot executeFunction
            if functValue != 'nullFunction':
               pyUt.logInfo("%s Button %s pressed for function %s" % \
                     (pyUt.getPrintTimeString(), wiiButton, functValue))
               if functValue == 'blueLightOn':
                  csvdata[ csvindex['trainerLight']] = 'Blue'
                  previousIterationTrainerLight = csvdata[ csvindex['trainerLight']]
               elif functValue == 'yellowLightOn':
                  csvdata[ csvindex['trainerLight']] = 'Yellow'
                  previousIterationTrainerLight = csvdata[ csvindex['trainerLight']]
               elif functValue == 'whiteLightOn':
                  csvdata[ csvindex['trainerLight']] = 'White'
                  previousIterationTrainerLight = csvdata[ csvindex['trainerLight']]
               elif functValue == 'dispenseTreat':
                  # dispenseTreat wiimote -> trainerTreat -> if not programsInControl -> tutorSignaled
                  csvdata[ csvindex['trainerTreat']] = 'True'
               elif functValue == 'shapeDown':
                  csvdata[ csvindex['trainerShapeDown']] = 'True'
                  if trainerShapeValue == 0:
                     pyUt.logError("%s trainer attempted to shape down below zero." % pyUt.getPrintTimeString())
                  else:
                     trainerShapeValue -= 1
                     pyUt.logInfo("%s trainer shaped down to %d" % (pyUt.getPrintTimeString(), trainerShapeValue))
               elif functValue == 'shapeUp':
                  csvdata[ csvindex['trainerShapeUp']] = 'True'
                  if trainerShapeValue+1 == len(pyUt.ACQ_DISC_SHAPING):
                     pyUt.logError("%s trainer attempted to shape up from %d to limit of %d" % \
                                   (pyUt.getPrintTimeString(), trainerShapeValue, len(pyUt.ACQ_DISC_SHAPING)))
                  else:
                     trainerShapeValue += 1
                     pyUt.logInfo("%s trainerShapeUp trainerShapeValue %d" % (pyUt.getPrintTimeString(), trainerShapeValue))
               elif functValue == 'startExperiment':
                  csvdata[ csvindex['startExperiment']] = 'True'
                  if not startExperiment:
                     pyUt.logInfo("%s Wiimote Experiment start" % pyUt.getPrintTimeString()) # appears in log twice?
                     csvdata[ csvindex['blockCount']] = 0 # Only set the first time startExperiment
                  startExperiment = True
            csvdata[ csvindex[ functValue ]] = 'EXEC'

         # For readability in the CSV file, if the button is still pressed,
         # and copy over the trainerLight value
         elif wiimoteButtonValues[wiiButton] == 'press' and\
            wiimotePreviousButtonValues[wiiButton] == 'press':
            csvdata[ csvindex[ 'trainerLight' ]] = previousIterationTrainerLight

         # If button isn't pressed and was before, call OnRelease
         elif wiimoteButtonValues[wiiButton] != 'press' and \
              wiimotePreviousButtonValues[wiiButton] == 'press':
            functValue = wiimoteButtons.buttonFunction(wiiButton, "OnRelease", wiimoteWmp, not programsInControl)
            if functValue == 'blueLightOff':
               pyUt.logInfo("%s Trainer %s blue light" %
                            (csvdata[ csvindex['timestamp']][1:-1],
                             ('planned to turn off' if programsInControl else 'turned off')))
               lightFunctArray[0]['trainerLightIsOn'] = False
            # If the previous trainerLight had a value that is part of the release function. I.E,
            # trainerLight=Blue and OnRelease=blueLightOff, clear the previous trainerLight value
            if previousIterationTrainerLight and \
               previousIterationTrainerLight.lower() in functValue.lower():
               previousIterationTrainerLight = ''
            csvdata[ csvindex[ functValue ]] = 'EXEC'

   wiimotePreviousButtonValues = wiimoteButtonValues.copy()



##########################################################
# Set up wiimote socket/variables for reading
##########################################################
if wiimoteUsed:
   wiimote = Wiimote.Wiimote( logFilename, debug)
   wiimote.start()
wiimoteButtons     = Button.Button( args.debug )
wiimoteWmp         = None
wiimotePreviousButtonValues = {}
wiimotePreviousButtonValues['wiimoteTime'] = 'N/A'
wiimoteButtonValues         = {}   # Wiimote Values as received from WiimoteSender
for button in pyUt.WIIMOTE_BUTTONLIST:
   wiimotePreviousButtonValues[button] = 'RELSE'
if wiimoteUsed:
   pyUt.logInfo("%s DataWriter: Ready to read from WiiMoteSender %s:%s" % \
                (pyUt.getPrintTimeString(), pyUt.WIIMOTE_IP, pyUt.WIIMOTE_PORT))
else:
   pyUt.logInfo("%s DataWriter: Not using WiiMoteSender to signal petTutor. " % \
                 pyUt.getPrintTimeString() + \
                "Setting socket %s:%s to PetTudor directionly" % \
                (pyUt.PETTUTOR_IP, pyUt.PETTUTOR_PORT))
# Set up the socket to talk to the petTutorReceiver
petTutorSocket  = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
petTutorAddress = (pyUt.PETTUTOR_IP, pyUt.PETTUTOR_PORT)



##########################################################
# Set up harness socket/variables for reading
##########################################################
harness = Harness.Harness( logFilename, debug)
harness.start()


##########################################################
# Set up the direction variables
##########################################################
directionDataValues = {}
for dataValue in pyUt.HEADING_SENSORLIST:
   directionDataValues[ dataValue ] = -1
compass = Compass.Compass()

##########################################################
# Set up pressure sensor socket/variables for reading
##########################################################
if pressureUsed:
   pressure = Pressure.Pressure( logFilename, debug)
   pressure.start()

##########################################################
# Set up the dashboard socket to send data
##########################################################
dashboardSocket              = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
dashboardAddress             = (pyUt.DASHBOARD_IP, pyUt.DASHBOARD_PORT)

# Light structure has the csvLabel, is light on funciton, light off function, etc
lightFunctArray = []
lightFunctArray.append( { 'programLight' : 'blue',
                          'programLightIsOn'   : False,
                          'trainerLightIsOn'   : False,
                          'lightOn'      : wiimoteButtons.blueLightOn,
                          'lightOff'     : wiimoteButtons.blueLightOff } )
lightFunctArray.append( { 'programLight' : 'white',
                          'programLightIsOn'   : False,
                          'trainerLightIsOn'   : False,
                          'lightOn'      : wiimoteButtons.whiteLightOn,
                          'lightOff'     : wiimoteButtons.whiteLightOff } )
lightFunctArray.append( { 'programLight' : 'yellow',
                          'programLightIsOn'   : False,
                          'trainerLightIsOn'   : False,
                          'lightOn'      : wiimoteButtons.yellowLightOn,
                          'lightOff'     : wiimoteButtons.yellowLightOff } )


##########################################################
# Set up the notes reading thread
##########################################################
notesDataValue = {'notesTime' : pyUt.getPrintTimeString(),
                  'notesLine' : ''}
print "Enter Q to quit"
t = Thread(target=notesThread, )
t.start()

#########################################################
# Set up the Arduino distance
#########################################################
if distanceUsed:
   distanceLogfile = "%s.Distance.log" % logFilenameTimestamp
   distanceSensor = Distance.Distance(distanceLogfile, debug)
   distanceSensor.start()

#########################################################
# getDistanceData
#########################################################
def getDistanceData():
   ''' Read the five distance values ad get the minimal value '''

   distanceData = distanceSensor.getData()
   # print "JJM Distance.getData distanceTime=%s timestamp=%s" % (distanceData['distanceTime'], csvdata[csvindex['timestamp']][1:-1])
   minDistance = 999999999999
   for dKey,dValue in distanceData.iteritems():
      if dKey == 'distanceTime':
         csvdata[ csvindex[dKey] ] = "'" + dValue + "'"
      else:
         try:
            csvdata[ csvindex[dKey] ] = float(dValue) / 30.5
            csvdata[ csvindex[dKey] ] = "%0.1f" %  csvdata[ csvindex[dKey] ]
            csvdata[ csvindex[dKey] ] = float(  csvdata[ csvindex[dKey] ])
            if csvdata[ csvindex[dKey] ] < 0.2: # JJM
               csvdata[ csvindex[dKey] ] = 99999.9
         except Exception as e: # pylint: disable=broad-except
            csvdata[ csvindex[dKey] ] = 99999.9
            print "JJM distance dKey=%s dValue=%s exception %s" % (dKey, dValue, str(e))
         #if minDistance > csvdata[ csvindex[dKey] ] and \
         #   (dKey != 'dist4') and (dKey != 'dist3'):
         if minDistance > csvdata[ csvindex[dKey] ]:
            minDistance = csvdata[ csvindex[dKey] ]
   if distanceOverride:
      minDistance = 1.0
   csvdata[ csvindex['distance']] = minDistance

# Start up the label thread if labeling
if labelingMode:
   n = Thread(target=labelThread, )
   n.start()

##########################################################
# Setup filename, logging, etc
##########################################################
csvFilename, csvheader, csvdata, csvindex = \
         setupCSVFilenameHarnessTime(dog, logFilenameTimestamp)
pyUt.logInfoNoPrint("%s %s" % (pyUt.getPrintTimeString(), title))
socketInfo = "petTutor (%s:%s) harness (%s:%s) " % \
             (pyUt.PETTUTOR_IP, pyUt.PETTUTOR_PORT, pyUt.HARNESS_IP, pyUt.HARNESS_PORT)
socketInfo += "dashboard (%s:%s) " % (pyUt.DASHBOARD_IP, pyUt.DASHBOARD_PORT)
if wiimoteUsed:
   socketInfo += "wiimote (%s:%s) " % (pyUt.WIIMOTE_IP , pyUt.WIIMOTE_PORT)
pyUt.logInfoNoPrint("%s %s\n" % (pyUt.getPrintTimeString(),  socketInfo ))


if labelingMode:
   if wiimoteUsed:
      # Since this printout fragilely depends on the YAML file, assert to be safe
      assert pyUt.WIIMOTE_BUTTONLIST_LABELING['Left']  == 's'
      assert pyUt.WIIMOTE_BUTTONLIST_LABELING['Up']    == 't'
      assert pyUt.WIIMOTE_BUTTONLIST_LABELING['Right'] == 'e'
   print "You must hold keys / labels!"
   print "Sit -> Left / s, Stand -> Up / t, Eat -> Right / e"
else:
   # Experimenting
   if wiimoteUsed:
      assert pyUt.WIIMOTE_BUTTONLIST_EXPERIMENTING['Up']    == 'shapeUp'
      assert pyUt.WIIMOTE_BUTTONLIST_EXPERIMENTING['Down']  == 'shapeDown'
      assert pyUt.WIIMOTE_BUTTONLIST_EXPERIMENTING['A']     == 'dispenseTreat'
      assert pyUt.WIIMOTE_BUTTONLIST_EXPERIMENTING['Left']  == 'cue'
      assert pyUt.WIIMOTE_BUTTONLIST_EXPERIMENTING['Home']  == 'startExperiment'
      assert pyUt.TRAINER_FUNCTION[0] == 'trainerTreat'
      assert pyUt.TRAINER_FUNCTION[1] == 'trainerLight'
   caninePosition = CaninePosition.CaninePosition( csvindex, dog, compassLow, compassHigh, debug)
   line = "The still percentage of %s is: %s\n" % \
          (str(pyUt.CANINEPOSITION_STILL_PERCENTAGE), caninePosition.getStillPercentageValues())
   notesDataValue['notesLine'] = line
   pyUt.logInfo("%s %s" % (pyUt.getPrintTimeString(), line))

   # Fill in the direction information
   csvdata[ csvindex['compassLow']]  = str(compassLow)
   csvdata[ csvindex['compassHigh']] = str(compassHigh)

##########################################################
# Do analysis of the experiment sensor data
##########################################################
def getRandomDelay(parmShapeValue):
   ''' Given a shaping value, get the random delay before starting the cue '''
   delayValue  = pyUt.ACQ_DISC_SHAPING[parmShapeValue]['delay']
   randomValue = pyUt.ACQ_DISC_SHAPING[parmShapeValue]['random']

   # Get the number of 10 Hz intervals to delay
   delayIntervals = int(delayValue * 10) + random.randint( 0, randomValue * 10)
   return delayIntervals

shouldWriteToDashboard = False # Should the dashboard be updated due to some lights?
lastLight = {}
lastLight['sitInstance'] = False
lastLight['sitState']    = False
lastLight['eatInstance'] = False
lastLight['standInstance'] = False
lastLight['standState']    = False
lastLight['stillInstance'] = False
lastLight['stillState']    = False
lastLight['distanceInstance'] = False
lastLight['distanceState']    = False
lastLight['orientInstance'] = False
lastLight['orientState']    = False

def analyzeExperimentData( ):
   ''' Call the canine postion which does all analysis for the light board'''
   # pylint: disable=too-many-nested-blocks
   global programDelayValue # Delay calculated because of dog's progress toward the goal of waiting upto 5 seconds
   global shouldWriteToDashboard

   # Call the caninePosition to do the analysis of the csvdata
   proximityDict = caninePosition.addCsvdata( csvdata )
   for cf in pyUt.CANINEPOSITION_FUNCTION + ['inMovementGracePeriod']:
      csvdata[ csvindex[ cf ]] = proximityDict[ cf ]
   #if (csvdata[csvindex['programLight']].strip() or csvdata[csvindex['programTreat']].strip() or csvdata[csvindex['trainerLight']].strip()): # JJM
   #   print("%s JJM programLight=%s programTreat=%s trainerLight=%s" % (csvdata[csvindex['timestamp']][1:-1], csvdata[csvindex['programLight']], csvdata[csvindex['programTreat']], csvdata[csvindex['trainerLight']]))

   # Should the dashboard be updated due to some lights?
   shouldWriteToDashboard = False
   for lastKey in lastLight:
      if lastLight[lastKey] != (csvdata[csvindex[lastKey]].strip().lower() != 'true'):
         lastLight[lastKey]  = (csvdata[csvindex[lastKey]].strip().lower() != 'true')
         shouldWriteToDashboard = True

   # Check if a light should be turned off
   if (lightFunctArray[0]['programLightIsOn'] and
       (programsInControl     and (csvdata[ csvindex[ 'programLight' ]].strip() == ''))):
      pyUt.logInfo("%s %s turned off light" % ('program' if programsInControl else 'trainer',
                                               csvdata[ csvindex['timestamp']][1:-1]))
      lightFunctArray[0]['programLightIsOn'] = False
      programDelayValue = -1
      lightFunctArray[0]['lightOff']()
   if (lightFunctArray[0]['trainerLightIsOn'] and
       (not programsInControl  and (csvdata[ csvindex[ 'trainerLight' ]].strip() == ''))):
      pyUt.logInfo("Trainer %s turned off light" % csvdata[ csvindex['timestamp']][1:-1])
      lightFunctArray[0]['trainerLightIsOn'] = False
      programDelayValue = -1
      lightFunctArray[0]['lightOff']()

   # Check if a light should be turned on
   if (csvdata[ csvindex[ 'programLight' ]].strip() != '') or \
      (csvdata[ csvindex[ 'trainerLight' ]].strip() != ''):
      # lightFunctArray is an array of lightStructures which is a dictionary of:
      # programLight, lightIsOff <boolean> and lightOn/Off to toggle the light
      for lightFunct in lightFunctArray:
         programLight = lightFunct['programLight'].lower()  # shorthand

         # Did caninePosition say that the light should go on?
         if csvdata[ csvindex[ 'programLight' ]].lower() == programLight:
            if not lightFunct[ 'programLightIsOn' ]:
               if programsInControl:
                  if acqDiscMode:
                     if programDelayValue == -1:
                        programDelayValue = getRandomDelay(programShapeValue)
                        pyUt.logInfo("%s Program turned on %s light %0.1f sec delay, shape value=%d" %\
                               (csvdata[ csvindex['timestamp']][1:-1], \
                                programLight, programDelayValue/10.0, programShapeValue))
                        caninePosition.setDelayValue(programDelayValue)
                     if programDelayValue == 0:
                        lightFunct[ 'lightOn' ]()
                        blockMetrics[blockCount]['programLight'] += 1
                        lightFunct[ 'programLightIsOn' ] = True
                        programDelayValue = -1  # Signify to next iteration, no delay set
                     else:
                        programDelayValue -= 1
                  else: # acqBehvMode
                     lightFunct[ 'lightOn' ]()
                     blockMetrics[blockCount]['programLight'] += 1
                     lightFunct[ 'programLightIsOn' ] = True
                     pyUt.logInfo("%s Program turned on %s light %0.1f sec delay, shape value =%d" % \
                               (csvdata[ csvindex['timestamp']][1:-1], programLight,
                                getRandomDelay(programShapeValue)/10.0, programShapeValue))
               else:
                  blockMetrics[blockCount]['programLight'] += 1
                  if acqDiscMode:
                     pyUt.logInfo("%s Program planned to turn on %s light" % \
                               (csvdata[ csvindex['timestamp']][1:-1], programLight))
            lightFunct[ 'lightIsOn' ] = True
         else:
            if lightFunct[ 'programLightIsOn' ]:
               if programsInControl:
                  lightFunct[ 'lightOff' ]()
                  pyUt.logInfo("%s Program turned off %s light" %\
                               (csvdata[ csvindex['timestamp']][1:-1], programLight))
               else:
                  pyUt.logInfo("%s Program planned to turn off %s light" % \
                               (csvdata[ csvindex['timestamp']][1:-1], programLight))
                  csvdata[ csvindex[ 'programLight' ]] = programLight
            lightFunct[ 'programLightIsOn' ] = False

         # Did the trainer say that the light should go on?
         if csvdata[ csvindex[ 'trainerLight' ]].lower() == programLight:
            if not lightFunct[ 'trainerLightIsOn' ]:
               if not programsInControl:
                  lightFunct[ 'lightOn' ]()
                  blockMetrics[blockCount]['trainerLight'] += 1
                  lightFunct[ 'trainerLightIsOn' ] = True
                  pyUt.logInfo("%s Trainer turned on %s light, shape value %d" % \
                               (csvdata[ csvindex['timestamp']][1:-1], programLight, trainerShapeValue))
               else:
                  blockMetrics[blockCount]['trainerLight'] += 1
                  pyUt.logInfo("%s Trainer planned to turn on %s light, shape value %d" % \
                               (csvdata[ csvindex['timestamp']][1:-1], programLight, trainerShapeValue))
         else:
            if lightFunct[ 'trainerLightIsOn' ]:
               if not programsInControl:
                  lightFunct[ 'lightOff' ]()
                  pyUt.logInfo("%s Trainer turned off %s light" % \
                               (csvdata[ csvindex['timestamp']][1:-1], programLight))
                  lightFunct[ 'trainerLightIsOn' ] = False
               else:
                  pyUt.logInfo("%s Trainer planned to turn off %s light" % \
                               (csvdata[ csvindex['timestamp']][1:-1], programLight))
                  csvdata[ csvindex[ 'trainerLight' ]] = programLight

   # Check if a treat should be dispensed
   csvdata[ csvindex[ 'tutorSignaled' ]] = ''
   if (csvdata[ csvindex[ 'programTreat' ]].strip() != '') or \
      (csvdata[ csvindex[ 'trainerTreat' ]].strip() != ''):
      if (programsInControl     and csvdata[ csvindex[ 'programTreat' ]].strip() != '') or \
         (not programsInControl and csvdata[ csvindex[ 'trainerTreat' ]].strip() != ''):
         if programsInControl:
            caninePosition.treatDispensed()
            blockMetrics[blockCount]['programTreat'] += 1
            lightFunctArray[0][ 'trainerLightIsOn' ] = False
            lightFunctArray[0][ 'programLightIsOn' ] = False
            lightFunctArray[0][ 'lightOff' ]()
            programDelayValue = -1
         else:
            blockMetrics[blockCount]['trainerTreat'] += 1
         #if wiimoteUsed:
         #   wiimoteButtons.dispenseTreat()
         #else:
         petTutorSocket.sendto( pickle.dumps( pyUt.getPrintTimeString ), \
                                                 petTutorAddress)
         pyUt.logInfo("%s Treat dispensed by %s" % \
                      (csvdata[ csvindex['timestamp']][1:-1], \
                      ('program' if programsInControl else 'trainer')))
         csvdata[ csvindex[ 'tutorSignaled' ]] = 'TRUE'
      else:
         if programsInControl:
            blockMetrics[blockCount]['trainerTreat'] += 1
         else:
            blockMetrics[blockCount]['programTreat'] += 1
         pyUt.logInfo("%s Treat planned for by %s" % \
                      (csvdata[ csvindex['timestamp']][1:-1],  \
                      ('trainer' if programsInControl else 'program')))

   if acqDiscMode:
      csvdata[ csvindex['trainerShapeValue']] = trainerShapeValue
      csvdata[ csvindex['programShapeValue']] = programShapeValue
      csvdata[ csvindex['programDelayValue']] = programDelayValue

##########################################################
# process the experiment counter
##########################################################
def processExperimentCounter():
   ''' Increment the experimentCounter '''
   global experimentCounter
   global programShapeValue
   global programShapeUpLastMin
   global programShapeDownLastMin
   global blockCount
   # assert startExperiment

   # Since the experiment is started, increment the counter
   experimentCounter += 1
   csvdata[ csvindex['experimentCounter'] ] = experimentCounter

   # If on a one minute boundary, one block, 600 intervals
   if experimentCounter % pyUt.DATAWRITER_BLOCKLEN == 0:
      if wiimoteUsed:
         # Rumble the wiimote if it exists
         rumbleThread = Thread(target=wiimoteButtons.rumbleRemote, kwargs={'timeLength': 0.1})
         rumbleThread.start()
      bc = str(blockCount)
      csvdata[ csvindex['blockCountTrainerTreat' + bc]] = blockMetrics[blockCount]['trainerTreat']
      csvdata[ csvindex['blockCountProgramTreat' + bc]] = blockMetrics[blockCount]['programTreat']
      csvdata[ csvindex['blockCountTrainerLight' + bc]] = blockMetrics[blockCount]['trainerLight']
      csvdata[ csvindex['blockCountProgramLight' + bc]] = blockMetrics[blockCount]['programLight']
      treats1Min = blockMetrics[blockCount]['programTreat']
      cues1Min   = blockMetrics[blockCount]['programLight']
      if cues1Min == 0:
         percent1Min = 0
      else:
         percent1Min = treats1Min * 100.0 / cues1Min
      if blockCount > 0:
         treats2Min = blockMetrics[blockCount-1]['programTreat'] + treats1Min
         cues2Min = blockMetrics[blockCount-1]['programLight'] + cues1Min
         if cues2Min == 0:
            percent2Min = 0
         else:
            percent2Min = treats2Min * 100.0 / cues2Min

      # Did we meet or exceed the 1 minute shape up criteria
      if (treats1Min  >= pyUt.CRITERIA_UP_TREAT_CNTS_1) and \
         (percent1Min >= pyUt.CRITERIA_UP_PERCENT_1):
         csvdata[ csvindex['programShapeUp']] = 'True'
         if programShapeValue+1 == len(pyUt.ACQ_DISC_SHAPING):
            pyUt.logError("%s program attempted to shape up from %d past limit %d." % \
                           (pyUt.getPrintTimeString(), programShapeValue, len(pyUt.ACQ_DISC_SHAPING)))
         else:
            programShapeValue += 1
            pyUt.logInfo("%s programShapeUp programShapeValue %d" % (pyUt.getPrintTimeString(), programShapeValue))
         programShapeUpLastMin   = True
         programShapeDownLastMin = False
      # Did we meet or exceed the 2 minute shape up criteria
      elif (blockCount > 0) and not programShapeUpLastMin and not programShapeDownLastMin and \
           ((treats2Min  >= pyUt.CRITERIA_UP_TREAT_CNTS_2) and \
            (percent2Min >= pyUt.CRITERIA_UP_PERCENT_2)):
         csvdata[ csvindex['programShapeUp']] = 'True'
         if programShapeValue+1 == len(pyUt.ACQ_DISC_SHAPING):
            pyUt.logError("%s program attempted to shape up to limit %d." % \
                           (pyUt.getPrintTimeString(), len(pyUt.ACQ_DISC_SHAPING)))
         else:
            programShapeValue += 1
            pyUt.logInfo("%s programShapeUp programShapeValue %d" % (pyUt.getPrintTimeString(), programShapeValue))
         programShapeUpLastMin   = True
         programShapeDownLastMin = False
      # Did we at least exceed the 1 minute shape down... do nothing
      elif (treats1Min  >= pyUt.CRITERIA_DOWN_TREAT_CNTS_1) and \
         (percent1Min >= pyUt.CRITERIA_DOWN_PERCENT_1):
         programShapeUpLastMin   = False
         programShapeDownLastMin = False
      # Did we meet the 1 minute shape down criteria
      elif (treats1Min  <= pyUt.CRITERIA_DOWN_TREAT_CNTS_1) or \
         (percent1Min <= pyUt.CRITERIA_DOWN_PERCENT_1):
         csvdata[ csvindex['programShapeDown']] = 'True'
         if programShapeValue == 0:
            pyUt.logError("%s program attempted to shape down below zero." % \
                            pyUt.getPrintTimeString())
         else:
            programShapeValue -= 1
            pyUt.logInfo("%s programShapeDown programShapeValue %d" % (pyUt.getPrintTimeString(), programShapeValue))
         programShapeUpLastMin   = False
         programShapeDownLastMin = True
      # Did we meet the 2 minute shape down criteria
      elif (blockCount > 0) and not programShapeUpLastMin and not programShapeDownLastMin and \
           ((treats2Min  <= pyUt.CRITERIA_UP_TREAT_CNTS_2) or  \
            (percent2Min <= pyUt.CRITERIA_UP_PERCENT_2)):
         csvdata[ csvindex['programShapeDown']] = 'True'
         if programShapeValue == 0:
            pyUt.logError("%s program attempted to shape down below zero." % \
                            pyUt.getPrintTimeString())
         else:
            programShapeValue -= 1
            pyUt.logInfo("%s programShapeDown programShapeValue %d" % (pyUt.getPrintTimeString(), programShapeValue))
         programShapeUpLastMin   = False
         programShapeDownLastMin = True
      # Maybe we didn't meet any of them, block 0 had 6 counts and 45%...
      else:
         programShapeUpLastMin   = False
         programShapeDownLastMin = False

      # Display pertainent information
      csvdata[ csvindex['blockCountTrainerTreat' + bc]] = blockMetrics[blockCount]['trainerTreat']
      csvdata[ csvindex['blockCountProgramTreat' + bc]] = blockMetrics[blockCount]['programTreat']
      csvdata[ csvindex['blockCountTrainerLight' + bc]] = blockMetrics[blockCount]['trainerLight']
      csvdata[ csvindex['blockCountProgramLight' + bc]] = blockMetrics[blockCount]['programLight']
      linett = ' trainerTreat=['
      linept = ' programTreat=['
      linetl = ' trainerLight=['
      linepl = ' programLight=['
      for inx in range(blockCount+1): # pylint: disable=unused-variable
         linett += '%d,' % blockMetrics[blockCount]['trainerTreat']
         linept += '%d,' % blockMetrics[blockCount]['programTreat']
         linetl += '%d,' % blockMetrics[blockCount]['trainerLight']
         linepl += '%d,' % blockMetrics[blockCount]['programLight']
      linett += ']'
      linept += ']'
      linetl += ']'
      linepl += ']'
      if blockCount+1 < pyUt.DATAWRITER_EXPLEN:
         statusLine = "%s blockCount %d" % (pyUt.getPrintTimeString(), blockCount)
         blockCount += 1
      else:
         statusLine = "%s attempted to go longer than the %d minute experiment length" %\
                       (pyUt.getPrintTimeString(), pyUt.DATAWRITER_EXPLEN)
      pyUt.logInfo("%s%s%s%s%s" % (statusLine, linett, linept, linetl, linepl))
      csvdata[ csvindex['blockCount'] ] = blockCount

def checkForMissingStartExperiment():
   ''' Do some sanity checks of whether startExperiment should have been pressed'''
   if labelingMode:
      return
   for colName in ['trainerLight', 'trainerTreat', 'trainerShapeUp', 'trainerShapeDown', 'AIN0Button1' ]:
      if csvdata[ csvindex[colName]].strip().lower() != '':
         pyUt.logError("\n%s %s set but no startExperiment\n" % \
                        (csvdata[ csvindex['timestamp']][1:-1], colName))

##########################################################
# Do reading from the socket until the keyboard input is a Q or q
##########################################################

# Dump the index of column names to data
with open("csvindex.p", "wb") as f:
   pickle.dump( csvindex, f)
   f.close()

wasExperimentAlreadyStarted = False
with open(csvFilename, "wb") as csvfile:
   csvwriter = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
   csvwriter.writerow( csvheader )
   if debug:
      pyUt.logInfo( "DataWriter: Opened file %s for writing" % csvFilename )

   # try:
   timeInterval = timedelta(0, 0, pyUt.WIIMOTE_INTERVAL * 1000000.0)   # 0.1 seconds
   pyUt.tryToGetToOneTenthSecondBoundary()
   # This should get us to 0.x00 and be 0.x50 off notes thread
   nextTime = datetime.now()
   lastNotesLine = ''
   while (stillRunning):
      # Calculate when the next time interval is
      nextTime   += timeInterval
      if startExperiment:
         processExperimentCounter()

      # Get the WiiMote, Harness, Pressure, and Notes data
      if 'Wiimote'  in pyUt.PARTS_USED:
         getWiimoteButtonValues()
      else:
         csvdata[ csvindex['wiimoteTime']]= "'" + pyUt.getPrintTimeString() + "'"
      if 'Harness'  in pyUt.PARTS_USED:
         # Get and copy the harness data from the receiver thread
         harnessData = harness.getData()
         harnessRawData =harness.getRawData()
         for sensor in pyUt.HARNESS_SENSORLIST + ['sensorDataLen', 'sensorTime']:
            csvdata[ csvindex[ sensor ]] = harnessData[sensor]
         csvdata[ csvindex[ 'frontDir' ]] = compass.getDirection( harnessRawData, dirs='Front' )
         csvdata[  csvindex['backDir'  ]] = compass.getDirection( harnessRawData, dirs='Back' )
      if pressureUsed:
         pressureData = pressure.getData()
         for sensor in pyUt.PRESSURE_SENSORLIST + ['pressureTime','pressureDataLen']:
            csvdata[ csvindex[sensor]] = pressureData[sensor]
      else:
         csvdata[ csvindex[ 'pressureTime' ]]="'" + pyUt.getPrintTimeString() + "'"

      csvdata[ csvindex['notesTime'] ]  = "'" + notesDataValue['notesTime'] + "'"
      csvdata[ csvindex['notesLine'] ]  = notesDataValue['notesLine']
      csvdata[ csvindex['programsInControl']] = 'True' if programsInControl else ''
      if notesDataValue['notesLine'] != '':
         if notesDataValue['notesLine'].lower() == 'cue':
            if notesDataValue['notesLine'].lower() != previousIterationTrainerLight:
               pyUt.logInfo("%s: Received a cue" % pyUt.getPrintTimeString())
            csvdata[ csvindex['trainerLight']] = 'Blue'
            previousIterationTrainerLight = csvdata[ csvindex['trainerLight']]
         elif notesDataValue['notesLine'].lower() == 'u':
            pyUt.logInfo("%s: Received shape up" % pyUt.getPrintTimeString())
            csvdata[ csvindex['trainerShapeUp']] = 'True'
            if trainerShapeValue+1 == len(pyUt.ACQ_DISC_SHAPING):
               pyUt.logError("%s trainer attempted to shape up from %d to limit of %d" % \
                             (pyUt.getPrintTimeString(), trainerShapeValue, len(pyUt.ACQ_DISC_SHAPING)))
            else:
               trainerShapeValue += 1
               pyUt.logInfo("%s trainerShapeUp trainerShapeValue %d" % (pyUt.getPrintTimeString(), trainerShapeValue))
         elif notesDataValue['notesLine'].lower() == 'd':
            csvdata[ csvindex['trainerShapeDown']] = 'True'
            if trainerShapeValue == 0:
               pyUt.logError("%s trainer attempted to shape down below zero." % pyUt.getPrintTimeString())
            else:
               trainerShapeValue -= 1
               pyUt.logInfo("%s trainer shaped down to %d" % (pyUt.getPrintTimeString(), trainerShapeValue))
         elif notesDataValue['notesLine'].lower() == 'u':
            csvdata[ csvindex['trainerShapeUp']] = 'True'
            if trainerShapeValue+1 == len(pyUt.ACQ_DISC_SHAPING):
               pyUt.logError("%s trainer attempted to shape up from %d to limit of %d" % \
                             (pyUt.getPrintTimeString(), trainerShapeValue, len(pyUt.ACQ_DISC_SHAPING)))
            else:
               trainerShapeValue += 1
               pyUt.logInfo("%s trainerShapeUp trainerShapeValue %d" % (pyUt.getPrintTimeString(), trainerShapeValue))
         elif notesDataValue['notesLine'].lower() == 'dispenseTreat'.lower():
            if lastNotesLine.lower() != 'dispenseTreat'.lower():
               pyUt.logInfo("%s: Received trainer dispense treat" % pyUt.getPrintTimeString())
               csvdata[ csvindex['trainerTreat']] = 'True'
         elif notesDataValue['notesLine'].lower() == 'q':
            stillRunning = 0
            pyUt.logInfo("%s: Received a quit" % pyUt.getPrintTimeString())
         lastNotesLine = notesDataValue['notesLine']
         if not labelingMode:
            # Only clear the note out if we're not doing labeling
            notesDataValue['notesLine'] = ''
      else:  # notesDataValue['notesLine'] == '':
         lastNotesLine = ''

      # Read the distance data (if distance >= 0) in feet
      if distanceUsed:
         getDistanceData()

      csvdata[ csvindex['timestamp']] = "'" + pyUt.getPrintTimeString() + "'"
      if csvdata[ csvindex['notesLine'] ].lower() == 's' or csvdata[ csvindex['startExperiment']]:
         if not wasExperimentAlreadyStarted:
            pyUt.logInfo("%s DataWriter Experiment start" % csvdata[ csvindex['timestamp']][1:-1])
            csvdata[ csvindex['blockCount']] = 0 # Only set the first time startExperiment
            csvdata[ csvindex['startExperiment']] = 'True'
            wasExperimentAlreadyStarted = True
         startExperiment = True

      # Should the canine position classification be done?
      if not labelingMode:
         analyzeExperimentData( )
      elif not startExperiment:
         checkForMissingStartExperiment()

      csvwriter.writerow( csvdata )
      csvfile.flush()

      # Send the data to the dashboard every other interval
      if (experimentCounter % 5 == 0 or
          csvdata[ csvindex[ 'AIN0Button1'  ]].strip() != '0.0' or
          csvdata[ csvindex[ 'programLight' ]].strip() or
          csvdata[ csvindex[ 'trainerLight' ]].strip() or
          csvdata[ csvindex[ 'startExperiment' ]].strip() or
          csvdata[ csvindex[ 'programTreat' ]].strip() or
          csvdata[ csvindex[ 'trainerTreat' ]].strip()):
         #pyUt.logInfoNoPrint("%s DataWriter: cpu_percent=%0.1f" % (csvdata[csvindex['timestamp']][1:-1], psutil.cpu_percent()))
         dashboardData = {}
         for key in csvindex:
            dashboardData[key] = csvdata[ csvindex[ key ]]
         dashboardSocket.sendto( pickle.dumps( dashboardData ), dashboardAddress)

      # If the time is after the actual next time interval, just continue
      dt = datetime.now()
      if dt > nextTime:
         pyUt.logError( "%s DataWriter::loop nextTime=%s continue" % \
                  (dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3], \
                   nextTime.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]))
         nextTime    = dt
         nextTime   += timeInterval
         continue

      intervalCalculation = (nextTime - dt).microseconds / 1000000.0
      if (intervalCalculation > pyUt.WIIMOTE_INTERVAL):
         # We should never get here!!!
         pyUt.logError( "DataWriter::loop nextTime=%s dt=%s intervalalCalculation=%f" % \
               (nextTime.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3], \
                      dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3], intervalCalculation))
         nextTime    = dt
         nextTime   += timeInterval
         intervalCalculation = .1
      time.sleep( intervalCalculation )
   # except Exception, e:
   #   print "DataWriter: ending with exception %s" % str(e)
   csvfile.close()


###################
# close the sockets
###################
print "%s: closing all sockets" % pyUt.getPrintTimeString()
stillRunning = 0
if wiimoteUsed:
   wiimoteButtons.blueLightOff()
   wiimoteButtons.yellowLightOff()
   wiimoteButtons.whiteLightOff()
   wiimote.close()
if distanceUsed:
   distanceSensor.close()
harness.close()
if pressureUsed:
   pressure.close()
time.sleep(1)
pyUt.logInfo( "DataWriter: Output file %s" % csvFilename)

############################################################
# If labeling create the posture classifier
############################################################
if labelingMode:
   command = "python DoCreateThresholdClassifier.py --no-printFolds" + \
             " --filename=%s" % csvFilename
   pyUt.logInfo( "Now running command: %s" % command )
   #subprocess.call(command, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
   proc = subprocess.Popen(command, shell=True, \
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
   createClassifierStdout, createClassifierStderr = proc.communicate()
   if createClassifierStdout != '':
      print( 'DataWriter.py: stdout: ' + createClassifierStdout )
   if createClassifierStderr != '':
      pyUt.logError( createClassifierStderr )
      pyUt.logError( "Creation of classifier failed." )
   proc.terminate()
