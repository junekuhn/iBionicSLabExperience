import argparse
import re
import signal
import time
from msvcrt import getch
from threading import Thread

import Config
import phases.PhaseFive as PhaseFive
import phases.PhaseFour as PhaseFour
import phases.PhaseOne as PhaseOne
import phases.PhaseThree as PhaseThree
import phases.PhaseTwo as PhaseTwo
import util.FileIOUtil as FileIOUtil
import util.Logger as Logger
import util.PetTutorUtil as PetTutorUtil

force_quit = False


def argbool(s):
    if s.lower() in ('yes', 'true'):
        return True
    elif s.lower() in ('no', 'false'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def main():
    Logger.open_log_files()  # This must be run before any logging is done
    Logger.info("P4E Training Protocol is Starting...")

    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)

    # Read in Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', default='False', dest='debug',
                        help="Boolean whether debug is on or off. Default False", type=argbool)
    parser.add_argument('--com', default=Config.PETTUTOR_COMPORT, dest='comport',
                        help="COM port to use. Default is %s" % Config.PETTUTOR_COMPORT, type=int)
    parser.add_argument('--wait', default=Config.PETTUTOR_ERROR_WAIT_INTERVAL, dest='error_wait',
                        help="Number of seconds to wait if connection fails before retrying. -1 to not retry. Default is %s" % Config.PETTUTOR_ERROR_WAIT_INTERVAL,
                        type=int)
    parser.add_argument('--mic', default=Config.MIC_SENSITIVITY, dest='mic', type=float,
                        help="Number in decibels for dog barking sensitivity. Default is %s" % Config.MIC_SENSITIVITY)
    parser.add_argument('--camera', default=Config.CAMERA_ID, dest='camera', type=int,
                        help="Camera ID, generally 0 or 1. Default is %s" % Config.CAMERA_ID)
    parser.add_argument('--disable-pettutor', default='False', dest='disable_pettutor',
                        help="True to disable connection to PetTutor (testing purposes only)", type=argbool)

    # Set values
    argvalues = parser.parse_args()
    Config.PRINT_DEBUG = argvalues.debug
    Config.PETTUTOR_COMPORT = argvalues.comport
    Config.PETTUTOR_ERROR_WAIT_INTERVAL = argvalues.error_wait
    Config.MIC_SENSITIVITY = argvalues.mic
    Config.CAMERA_ID = argvalues.camera
    Config.DISABLE_PETTUTOR = argvalues.disable_pettutor

    # Log Configuration
    Logger.debug("Debug is %s" % Config.PRINT_DEBUG)
    Logger.debug("PetTutor Comport: %s" % Config.PETTUTOR_COMPORT)
    Logger.debug("PetTutor Wait Time: %s" % Config.PETTUTOR_ERROR_WAIT_INTERVAL)
    Logger.debug("Mic Sensitivity: %s" % Config.MIC_SENSITIVITY)

    # Connect to PetTutor
    PetTutorUtil.connect(Config.PETTUTOR_COMPORT)

    while True:
        Logger.prompt("Dog ID (-1 to Quit): ")
        dog_id = raw_input()
        Logger.debug("Dog ID is %s" % dog_id)

        if dog_id == '-1':
            break

        if re.match('^[\w-]+$', dog_id) is None:
            Logger.error("'%s' is not a valid dog ID. Please only use alphanumeric characters." % dog_id)
            continue

        Config.RUN_FLAG = True

        data = FileIOUtil.load(dog_id)

        if data.get('dog_size') is None:
            Logger.prompt("Please enter dog's size (small/medium/large): ")
            dog_size = raw_input()
            Logger.debug("Dog Size is %s " % dog_size)
            if dog_size.lower() in ("small", "s", "0"):
                dog_size = 0
                FileIOUtil.save_size(dog_id, 0)
            elif dog_size.lower() in ("medium", "m", "1"):
                dog_size = 1
                FileIOUtil.save_size(dog_id, 1)
            elif dog_size.lower() in ("large", "l", "2"):
                dog_size = 2
                FileIOUtil.save_size(dog_id, 2)
            else:
                Logger.error("'%s' did not match expected input (small/medium/large)" % dog_size)
                continue
        else:
            dog_size = data["dog_size"]

        (phase, level) = find_next_level(data)
        input_required = False

        if phase != -1 and level != -1:
            Logger.info("Dog %s's first incomplete level is Phase %s Level %s." % (dog_id, phase, level))
        else:
            Logger.info("Dog %s has completed all Phases/Levels." % dog_id)
            input_required = True

        if not input_required:
            Logger.prompt("Continue? (Y/n): ")
            input_required = raw_input().lower() == 'n'
            Logger.debug("Continue is %s" % (not input_required))

        if input_required:
            Logger.info("Please specify which Phase you want to run.")
            Logger.prompt("Enter a Phase Number (-1 to go back): ")
            try:
                phase = int(raw_input())
            except ValueError:
                Logger.error("Phases can only be numbers.")
                continue
            Logger.debug("Selected phase is %d" % phase)
            if phase == -1:
                continue
            Logger.prompt("Enter a Level Number (-1 to go back): ")
            level = raw_input()
            Logger.debug("Selected level is %s" % level)
            if level == '-1':
                continue

        keyboard_thread = Thread(target=keyboard_listener)
        keyboard_thread.start()

        # Start a phase.
        if phase == 1:
            PhaseOne.start(dog_id, int(level))
            Config.RUN_FLAG = False
            continue
        elif phase == 2:
            PhaseTwo.start(dog_id, int(level))
            Config.RUN_FLAG = False
            continue
        elif phase == 3:
            PhaseThree.start(dog_id, int(level))
            Config.RUN_FLAG = False
            continue
        elif phase == 4:
            PhaseFour.start(dog_id, dog_size, int(level))
            Config.RUN_FLAG = False
            continue
        elif phase == 5:
            PhaseFive.start(dog_id, level.upper())
            Config.RUN_FLAG = False
            continue

        Logger.error("You entered an invalid Phase.")

    Config.RUN_FLAG = False
    time.sleep(1)
    Logger.close_log_files()


def find_next_level(data):
    if data['phase_2']['level_1'] is None and data['phase_1']['level_1'] is None:
        return 1, 1
    if data['phase_2']['level_1'] is None:
        return 2, 1
    if data['phase_2']['level_2'] is None:
        return 2, 2
    if data['phase_2']['level_3'] is None:
        return 2, 3
    if data['phase_2']['level_4'] is None:
        return 2, 4
    #    if data['phase_3']['level_1'] is None:
    #        return 3, 1
    if data['phase_3']['level_2'] is None:
        return 3, 2
    if data['phase_3']['level_3'] is None:
        return 3, 3
    if data['phase_3']['level_4'] is None:
        return 3, 4
    if data['phase_3']['level_5'] is None:
        return 3, 5
    if data['phase_3']['level_6'] is None:
        return 3, 6
    if data['phase_4']['level_1'] is None:
        return 4, 1
    if data['phase_4']['level_2'] is None:
        return 4, 2
    if data['phase_4']['level_3'] is None:
        return 4, 3
    if data['phase_4']['level_4'] is None:
        return 4, 4
    if data['phase_4']['level_5'] is None:
        return 4, 5
    if data['phase_5']['level_1'] is None:
        return 5, 1
    if data['phase_5']["level_2"] is None:
        return 5, 2
    if data['phase_5']['level_1D'] is None:
        return 5, '1D'
    if data['phase_5']['level_2D'] is None:
        return 5, '2D'
    if data['phase_5']['level_3D'] is None:
        return 5, '3D'
    if data['phase_5']['level_4D'] is None:
        return 5, '4D'
    if data['phase_5']['level_5D'] is None:
        return 5, '5D'
    return -1, -1


def keyboard_listener():
    while Config.RUN_FLAG:
        key = ord(getch())
        if key == 27:  # Escape key
            Config.RUN_FLAG = False
            Logger.info("Stopping running phase.")
            PhaseOne.stop()
            PhaseTwo.stop()
            PhaseThree.stop()
            PhaseFour.stop()
            PhaseFive.stop()
            break
        if key == 224:  # Special Keys
            key = ord(getch())
            if key == 72:  # Up Arrow Key
                Config.MIC_SENSITIVITY -= 1
                Logger.info("Changed mic sensitivity to %s dB." % Config.MIC_SENSITIVITY)
            elif key == 80:  # Down Arrow Key
                Config.MIC_SENSITIVITY += 1
                Logger.info("Changed mic sensitivity to %s dB." % Config.MIC_SENSITIVITY)


def handler(signum, frame):
    global force_quit
    if not force_quit:
        Logger.data(-1, -1, -1, "force_quit")
        Logger.error("The program was force quit unexpectedly")
        force_quit = True

if __name__ == '__main__':
    main()
