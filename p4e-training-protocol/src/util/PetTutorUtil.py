import sys
import time

import serial

import Config
import Logger

ser = None


def connect(comport):
    if Config.DISABLE_PETTUTOR:
        Logger.info("[PetTutor Disabled] Not attempting connection to PetTutor.")
        return
    ################################################################################
    # Create a serial connection (variable ser) to the PetTutor remote
    # While the port is not found, keep trying to connect every 5 seconds
    ################################################################################
    found = False
    global ser
    while not found:
        try:
            Logger.info("PetTutor: Attempting to connect to COM%d." % comport)
            ser = serial.Serial(port='COM%d' % comport,
                                baudrate=115,
                                bytesize=serial.EIGHTBITS,
                                parity=serial.PARITY_NONE,
                                timeout=1,  # 1 second time out on reads. writes are blocking by default
                                stopbits=serial.STOPBITS_ONE)
            found = True
        except serial.serialutil.SerialException as e:
            Logger.info("PetTutor: Cannot connect to PetTutor on COM%d. Message: %s" % (comport, e.message))
            found = False
            if Config.PETTUTOR_ERROR_WAIT_INTERVAL is -1:
                sys.exit(1)
            else:
                time.sleep(Config.PETTUTOR_ERROR_WAIT_INTERVAL)  # Default 5 seconds

    Logger.info("PetTutor: Connected to COM%d." % comport)


def dispense_treat():
    if Config.DISABLE_PETTUTOR:
        Logger.info("[PetTutor Disabled] Dispensing Treat...")
        return
    if ser is None:
        Logger.warning("Attempted to dispense treat without connecting first. Using default comport.")
        connect(Config.PETTUTOR_COMPORT)
    Logger.debug("PetTutor: Begin dispensing treat")
    dispense_message = "00SGL_CYC\r"

    try:
        # Send the dispense_message to the Pet Tutor
        n = ser.write(dispense_message)
        if n == len(dispense_message):
            Logger.debug("PetTutor: Successfully triggered PetTutor.")
        else:
            Logger.warning("PetTutor: An error occurred while triggering PetTutor.")
    except Exception, e:  # pylint: disable=broad-except
        Logger.error("PetTutor: Exception %e" % e)
        close()


def close():
    Logger.debug("PetTutor: Closing connection")
    if ser is not None:
        ser.close()
