''' Receive commands from DataWriter to be
    sent to the USB/SSH connection to the PetTutor
'''
import sys
import time
import os
import socket
import select
from datetime import datetime
import argparse
import logging
import serial
import Utilities as pyUt


################################################################################
# Create a serial connection to the PetTutor remote
# Listen on UDP socket and dispense treat on any packet received
################################################################################


# Read in the arguments which is the com port and debug
parser = argparse.ArgumentParser()
parser.add_argument('--debug', default=False, dest='debug', \
                   help="Boolean whether debug is on or off. Default False")
parser.add_argument('--com'  , default=pyUt.PETTUTOR_COMPORT, dest='comport', \
                   help="COM port to use. JJM: Off by one. Default is " +\
                   str(pyUt.PETTUTOR_COMPORT), type=int)
argValues = parser.parse_args()
debug   = argValues.debug
comport = argValues.comport

# Display title information
title="PetTutorReceiver: --com=%d --debug=%s" % (comport, str(debug))
if debug:
   print title
if os.name != 'nt':
   print "This only runs on Windows"
   sys.exit(1)
os.system("title " + title)
logFilename = "%s.PetTutorReceiver.log" % datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
logging.basicConfig(filename=logFilename, level=logging.INFO, filemode='w')
pyUt.logInfo("Title: %s" % title)



################################################################################
# Create a serial connection (variable ser) to the PetTutor remote
# While the port is not found, keep trying to connect every 5 seconds
################################################################################
found = False
initialMsgDone = False
while (not found):
   try:
      if not initialMsgDone or debug:
         pyUt.logInfo("PetTutorReceiver: %s Attempting to connect to COM%d. Device Manager COM%d." % \
              (pyUt.getPrintTimeString(), comport, (comport+1)))
      ser = serial.Serial(port=comport,
                          baudrate=115,
                          bytesize=serial.EIGHTBITS,
                          parity=serial.PARITY_NONE,
                          timeout=1, # 1 second time out on reads. writes are blocking by default)
                          stopbits=serial.STOPBITS_ONE)
      found = True
   except serial.serialutil.SerialException as err:
      if not initialMsgDone or debug:
         pyUt.logInfo("PetTutorReceiver: %s cannot connect to PetTutor on COM%d port: %s" % \
               (pyUt.getPrintTimeString(), comport, err))
      found = False
      time.sleep( pyUt.PETTUTOR_INTERVAL ) # Default 5 seconds
   initialMsgDone = True




pyUt.logInfo("PetTutorReceiver: %s connected to COM%d. Device Manager COM%d" % \
      (pyUt.getPrintTimeString(), comport, (comport+1)))
################################################################################
# Listen on UDP socket and dispense treat on any packet received
# Send the dispenseMessage to the Pet Tutor whenever you receive any UDP packet
################################################################################
timeout_in_seconds = pyUt.PETTUTOR_INTERVAL
dispenseMessage="00SGL_CYC\r"
pettutorAddress = (pyUt.PETTUTOR_IP, pyUt.PETTUTOR_PORT)
pettutorSocket  = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
pettutorSocket.setblocking(0)
pettutorSocket.bind(pettutorAddress)
initialMsgDone = False

try:
   while(True):
      # Wait to see if a UDP packet is received
      readyTuple = select.select([pettutorSocket], [], [], timeout_in_seconds)
      if debug:
         status = "ready to read" if (readyTuple[0]) else "not ready to read"
         print "PetTutorReceiver: %s readyTuple %s timeout_in_seconds=%d" % \
              (pyUt.getPrintTimeString(), status, timeout_in_seconds)

      if readyTuple[0]:
         # Send the dispenseMessage to the Pet Tutor
         n = ser.write(dispenseMessage)
         status = "Success" if (n == len(dispenseMessage)) else "Unsuccess"
         pyUt.logInfo("PetTutorReceiver: %s rec'd packet. %sly triggered PetTutor." % \
              (pyUt.getPrintTimeString(), status))
         pettutorSocket.recv(4096)
      else:
         if not initialMsgDone or debug:
            print "PetTutorReceiver: %s no buttons pressed in %d seconds." % \
                  (pyUt.getPrintTimeString(), timeout_in_seconds)
         initialMsgDone = True
except Exception, e: #pylint: disable=broad-except
   pyUt.logError("PetTutorReceiver: %s exception %e" % (pyUt.getPrintTimeString(), e))
   ser.close()
pyUt.logInfo("PetTutorReceiver: %s done" % pyUt.getPrintTimeString())
time.sleep(1)
