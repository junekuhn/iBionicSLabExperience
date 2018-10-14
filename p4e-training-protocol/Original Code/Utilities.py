from datetime import datetime, timedelta
import yaml

# Standardize time stamp
TIMEFMT = "%Y-%m-%d %H:%M:%S.%f"
def getPrintTimeString():
   return datetime.now().strftime(TIMEFMT)[:-3]


# The YAML file is where all configuration is kept.
YAML_FILE = "MoA.yaml"
with open(YAML_FILE, 'r') as f:
   moa = yaml.load(f)

TITLE                  = moa['Dashboard']['Title']

LEFTMARGIN             = int(moa['Dashboard']['LeftMargin'])
RIGHTMARGIN            = int(moa['Dashboard']['RightMargin'])
TOPMARGIN              = int(moa['Dashboard']['TopMargin'])
BOTTOMMARGIN           = int(moa['Dashboard']['BottomMargin'])
 
SITBOX                 = int(moa['Dashboard']['SitBox'])

SENSORMARGIN           = int(moa['Dashboard']['SensorMargin'])
SENSORDIVIDER          = int(moa['Dashboard']['SensorDivider'])
SENSORSEPERATOR        = int(moa['Dashboard']['SensorPixles'])

SENSORNAMES            = moa['Dashboard']['SensorNames']
SENSORCOLORS           = moa['Dashboard']['SensorColors']

SENSORMAX              = int(moa['Dashboard']['SensorMax'])
SENSORMIN              = int(moa['Dashboard']['SensorMin'])
SENSORPIXLES           = int(moa['Dashboard']['SensorPixles'])

BAR_CANVAS_WIDTH       = int(moa['Dashboard']['BarCanvasWidth'])

# Standardize time stamp
TIMEFMT = "%Y-%m-%d %H:%M:%S.%f"
def getPrintTimeString():
   return datetime.now().strftime(TIMEFMT)[:-3]


# The YAML file is where all configuration is kept.
with open("Harness.yaml", 'r') as f:
   doc = yaml.load(f)


FOLDS                  = doc['CrossValidation']['Folds']

DASHBOARD_IP           = doc['Dashboard']['IP']
DASHBOARD_PORT         = doc['Dashboard']['Port']

PRESSURE_COLORS        = doc['Dashboard']['PressureColors']
PRESSURE_MAX           = doc['Dashboard']['PressureMax']
PRESSURE_DELAY         = doc['Dashboard']['PressureDelay']
PRESSURE_SENSORLIST    = doc['Pressure']['RawDataColumns']
PRESSURE_IP          = doc['Pressure']['IP']
PRESSURE_PORT        = doc['Pressure']['Port']

IMU_COLORS             = doc['Dashboard']['IMUColors']
IMU_MAX                = doc['Dashboard']['IMUMax']

WIIMOTE_BUTTONLIST     = doc['WiiMote']['ButtonList']
WIIMOTE_FUNCTIONLIST   = doc['WiiMote']['ButtonFunctonList']
WIIMOTE_PORT           = doc['WiiMote']['Port']
WIIMOTE_IP             = doc['WiiMote']['IP']
WIIMOTE_INTERVAL       = doc['WiiMote']['Interval']
WIIMOTE_BUTTONLIST     = doc['WiiMote']['ButtonList']
WIIMOTE_MAG_BUTTONLIST = doc['WiiMote']['MagButtonList']
WIIMOTE_FUNCTIONABBREV = doc['WiiMote']['ButtonFunctonAbbr']
WIIMOTE_BUTTONSETTINGS = doc['WiiMote']['ButtonSettings']
WIIMOTE_BUTTONEVENTS   = doc['WiiMote']['ButtonEvents']

HARNESS_IP            = doc['Harness']['LocalIP']
HARNESS_PORT          = doc['Harness']['Port']
MAX_NUMBER_DOGS       = doc['Harness']['MaximumNumberOfDogs']
KEYBOARD_TIMEOUT      = doc['Predictor']['TimeoutSec']

HARNESS_SENSORLIST   = doc['Sensor']['RawDataColumns']
HARNESS_SENSORLIST_PLUS_NOTESLINE = HARNESS_SENSORLIST + ['notesLine']
HARNESS_INTERVAL     = doc['Sensor']['Interval']

DASHBOARD_IP           = doc['Dashboard']['IP']
DASHBOARD_PORT         = doc['Dashboard']['Port']

PETTUTOR_COMPORT    = doc['PetTutor']['ComPort']
PETTUTOR_IP         = doc['PetTutor']['IP']
PETTUTOR_PORT       = doc['PetTutor']['Port']
PETTUTOR_INTERVAL   = doc['PetTutor']['ReconnectInterval']

PARTS_USED           = doc['DataWriter']['PartsUsed']

DATAWRITER_DOGS      = doc['DataWriter']['Dogs']

SPEAKER_IP          = doc['Speaker']['LocalIP']
SPEAKER_PORT        = doc['Speaker']['Port']

LIGHTS_IP           = doc['Lights']['LocalIP']
LIGHTS_PORT         = doc['Lights']['Port']
LIGHTS_WHITE_GPIO   = doc['Lights']['WhiteGPIOPin']
LIGHTS_YELLOW_GPIO  = doc['Lights']['YellowGPIOPin']
LIGHTS_BLUE_GPIO    = doc['Lights']['BlueGPIOPin']
LIGHTS_SLEEP_INTERVAL = doc['Lights']['SleepInterval']

WAV_BLUE              = doc['WiiMote']['Sounds']['Blue']
WAV_YELLOW            = doc['WiiMote']['Sounds']['Yellow']
WAV_WHITE             = doc['WiiMote']['Sounds']['White']
SOUNDS_BLUE           = doc['WAV'][ WAV_BLUE ]
SOUNDS_YELLOW         = doc['WAV'][ WAV_YELLOW ]
SOUNDS_WHITE          = doc['WAV'][ WAV_WHITE ]
SOUNDS_SLEEP_INTERVAL = doc['WiiMote']['Sounds']['SleepInterval']

CANINEPOSITION_FUNCTION              = doc['CaninePosition']['RawDataColumnNames']
CANINEPOSITION_STILL_DURATION        = doc['CaninePosition']['Still']['Duration']
CANINEPOSITION_SIT_DURATION          = doc['CaninePosition']['Sit']['Duration']
CANINEPOSITION_STILL_PERCENTAGE      = doc['CaninePosition']['Still']['Percentage']
CANINEPOSITION_STILL_SENSOR_DIFFERENTIATION = doc['Trainer']['ColumnsUsedForDifferentiation']
CANINEPOSITION_MOVE_DURATION         = doc['CaninePosition']['Move']['Duration']
CANINEPOSITION_ACCEPTABLE_POSTURES   = doc['CaninePosition']['Still']['AcceptablePostures']
CANINEPOSITION_STAND_DURATION        = doc['CaninePosition']['Stand']['Duration']

NOINPUT                              = doc['Trainer']['NoInput']
TRAINER_RAW_DATA_COLUMN_NAMES        = doc['Trainer']['RawDataColumnNames']

CANINEPOSITION_PETTUTOR_MIN_WAIT_TIME = doc['CaninePosition']['PetTutor']['MinimumWaitTime']

CANINEPOSITION_POSTURES              = doc['CaninePosition']['Postures']
STANDINGDIRECTIONS                   = doc['CaninePosition']['Stand']['Directions']


