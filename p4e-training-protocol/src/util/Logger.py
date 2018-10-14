import os
import sys
from datetime import datetime

import Config

trace_log = None
data_log = None


def timestamp():
    now = datetime.now()
    return "%02d-%02d-%04d %02d:%02d:%02d" % (now.month, now.day, now.year, now.hour, now.minute, now.second)


def prompt(message):
    sys.stdout.write("%s [Prompt] %s" % (timestamp(), message))
    trace_log.write("%s [Prompt] %s" % (timestamp(), message) + '\n')


def debug(message):
    if Config.PRINT_DEBUG:
        print "%s [Debug] %s" % (timestamp(), message)
    trace_log.write("%s [Debug] %s" % (timestamp(), message) + '\n')


def info(message):
    print "%s [Info] %s" % (timestamp(), message)
    trace_log.write("%s [Info] %s" % (timestamp(), message) + '\n')


def warning(message):
    print "%s [WARNING] %s" % (timestamp(), message)
    trace_log.write("%s [WARNING] %s" % (timestamp(), message) + '\n')


def error(message):
    print "%s [ERROR] %s" % (timestamp(), message)
    trace_log.write("%s [ERROR] %s" % (timestamp(), message) + '\n')


def data(dog_id, phase, level, message):
    data_log.write("%s,%s,%s,%s,%s" % (timestamp(), dog_id, phase, level, message) + '\n')


def open_log_files():
    global data_log
    global trace_log
    if not os.path.exists(os.path.join(sys.path[0], "logs")):
        os.makedirs(os.path.join(sys.path[0], "logs"))
    data_log = open(os.path.join(sys.path[0], "logs", "data.log"), 'a', buffering=0)
    trace_log = open(os.path.join(sys.path[0], "logs", "trace.log"), 'a', buffering=0)
    debug("Opened Log Files")

    if os.path.getsize(os.path.join(sys.path[0], "logs", "data.log")) == 0:
        data_log.write("date,dog_id,phase,level,message" + '\n')


def close_log_files():
    debug("Closing Log Files")
    data_log.close()
    trace_log.close()
