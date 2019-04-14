import time
import datetime
import json
import socket
import os
import logging
from logging.handlers import TimedRotatingFileHandler
import RPi.GPIO as GPIO
import Adafruit_MCP3008
import picamera

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# MCP3008 initialization
CLK = 18
MISO = 23
MOSI = 24
CS = 27
mcp = Adafruit_MCP3008.MCP3008(clk=CLK, cs=CS, miso=MISO, mosi=MOSI)

# Node information
Node_Name = socket.gethostname()
Node_Name = Node_Name.replace(" ", "-")

# Set logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
timeLog = time.strftime("%d-%m-%Y_%H-%M-%S")
timeLog = timeLog.replace(" ", "-")
logDirectory = "/home/pi/NodePrograms/Logs/"
if not os.path.exists(logDirectory):
    os.makedirs(logDirectory)
logFilename = logDirectory + Node_Name + "_ReadingsLog_" + timeLog + ".log"
# handler = logging.FileHandler(logFilename)
handler = TimedRotatingFileHandler(logFilename, when="midnight", interval=1)
handler.suffix = "%d-%m-%Y_%H-%M-%S.log".replace(" ", "-")
logger.addHandler(handler)

# set JSON
JSONDirectoryNew = "/home/pi/NodePrograms/JSON_NEW_FILES/"
if not os.path.exists(JSONDirectoryNew):
    os.makedirs(JSONDirectoryNew)

# Camera initialization
camera = picamera.PiCamera()
PictureDirectoryNew = "/home/pi/NodePrograms/PICS_NEW_FILES/"
if not os.path.exists(PictureDirectoryNew):
    os.makedirs(PictureDirectoryNew)

# Readings time start
Readings_start = None
Reading_now = None
JSON_dump_timer = None

# Errors
Readings = False
General_Error = False
General_Error_MSG = None
CarCounter_Error = False
CarCounter_Error_MSG = False
Picture_Error = False
Picture_Error_MSG = False

# MCP3008
MCP3008_output = None

# Car counter
CarCounter_Read = False
CarCounter_In = 0
CarCounter_Out = 0

# Pictures
Picture_Read = False
Picture_Start = None
Picture_now = None

# Method for writing JSON dumps
def writeJSON():
    global Data
    global General_Error
    global General_Error_MSG

    try:
        if Readings:
            Data = {
                "Node_Name": Node_Name,
                "Date": time.strftime("%d-%m-%Y %H:%M:%S"),
                "General_Error": General_Error,
                "General_Error_Message": General_Error_MSG if General_Error is True else None,
                "Readings": Readings,
                "CarCounter": [
                    {"CarCounter_In": CarCounter_In} if CarCounter_Read is True else None,
                    {"CarCounter_Out": CarCounter_Out} if CarCounter_Read is True else None,
                ] if CarCounter_Read is True else None,
            }
        elif not Readings:
            Data = {
                "Node_Name": Node_Name,
                "Date": time.strftime("%d-%m-%Y %H:%M:%S"),
                "General_Error": General_Error,
                "General_Error_Message": General_Error_MSG if General_Error is True else None,
                "Error Data": [
                    {"CarCounter_Error": CarCounter_Error} if CarCounter_Error is True else None,
                    {"CarCounter_Error_MSG": CarCounter_Error_MSG} if CarCounter_Error is True else None,
                ] if CarCounter_Error is True else None
            }

        logger.info(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : " + "writeJSON" + " : " + "JSON dump")
        print(json.dumps(Data))
        logger.info(Node_Name + " : " + time.strftime(
            "%d-%m-%Y %H:%M:%S") + " : " + "writeJSON" + " : " + str(json.dumps(Data)))

        JSONFilename = JSONDirectoryNew + Node_Name + "_ReadingsJSON_ " +\
            time.strftime("%d-%m-%Y_%H-%M-%S").replace(" ", "-") + ".txt"

        with open(JSONFilename, 'w') as outputFile:
            json.dump(Data, outputFile)

    except Exception as jsonError:
        General_Error = True
        General_Error_MSG = str(jsonError)
        print(Node_Name + " : " + time.strftime(
            "%d-%m-%Y %H:%M:%S") + " : ERROR : " + "writeJSON" + " : " + General_Error_MSG)
        logger.info(Node_Name + " : " + time.strftime(
            "%d-%m-%Y %H:%M:%S") + " : ERROR : " + "writeJSON" + " : " + General_Error_MSG)

    finally:
        pass


# Method for counting incoming and outgoing cars with distance sensors
def getCarData():
    global CarCounter_Error
    global CarCounter_Error_MSG
    global CarCounter_Read
    global CarCounter_In
    global CarCounter_Out
    global MCP3008_output
    global Readings

    try:
        count_in = False
        count_out = False

        Readings = True
        CarCounter_Read = True

        MCP3008_output = mcp.read_adc(2)
        print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : Reading : " + "getCarData" +
                  " : " + "MCP3008_output #1" + " : " + str(MCP3008_output))

        if 550 < MCP3008_output < 1000:
            time.sleep(1)
            MCP3008_output = mcp.read_adc(2)
            print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : Reading : " + "getCarData" +
                  " : " + "MCP3008_output #2" + " : " + str(MCP3008_output))
            if 550 < MCP3008_output < 1000:
                CarCounter_In += 1
                count_in = True
                count_out = False

        if 450 < MCP3008_output < 550:
            time.sleep(1)
            MCP3008_output = mcp.read_adc(2)
            print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : Reading : " + "getCarData" +
                  " : " + "MCP3008_output #2" + " : " + str(MCP3008_output))
            if 450 < MCP3008_output < 550:
                CarCounter_Out += 1
                count_out = True
                count_in = False

        if count_in:
            print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : Reading : " + "getCarData" +
                  " : " + "MCP3008_output" + " : " + str(MCP3008_output) + " : " + "Incoming car count increased - Total : "
                  + str(CarCounter_In))
            logger.info(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : Reading : " + "getCarData"
                        + " : " + "MCP3008_output" + " : " + str(MCP3008_output) + " : " +
                        "Incoming car count increased - Total : " + str(CarCounter_In))
        if count_out:
            print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : Reading : " + "getCarData" +
                  " : " + "MCP3008_output" + " : " + str(MCP3008_output) + " : " + "Outgoing car count increased - Total : "
                  + str(CarCounter_Out))
            logger.info(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : Reading : " + "getCarData"
                        + " : " + "MCP3008_output" + " : " + str(MCP3008_output) + " : " +
                        "Incoming car count increased - Total : " + str(CarCounter_Out))
        if not count_in and not count_out:
            print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : Reading : " + "getCarData" +
                  " : " + "MCP3008_output" + " : " + str(MCP3008_output) + " : " + "No car count increased")
            logger.info(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : Reading : " + "getCarData" +
                        " : " + "MCP3008_output" + " : " + str(MCP3008_output) + " : " + "No car count increased")

    except Exception as CarCounterError:
        Readings = False
        CarCounter_Read = False
        CarCounter_Error = True
        CarCounter_Error_MSG = str(CarCounterError)
        print(Node_Name + " : " + time.strftime(
            "%d-%m-%Y %H:%M:%S ") + " : ERROR : " + "getCarData" + " : " + CarCounter_Error_MSG)
        logger.info(Node_Name + " : " + time.strftime(
            "%d-%m-%Y %H:%M:%S ") + " : ERROR : " + "getCarData" + " : " + CarCounter_Error_MSG)

    finally:
        pass


# Method for taking pictures
def getPicture():
    global Picture_Read
    global Picture_Error
    global Picture_Error_MSG
    global Readings

    try:
        temp = None
        camera.start_preview(fullscreen=False, window=(150, 150, 1024, 768))
        time.sleep(1)
        temp = PictureDirectoryNew + time.strftime("%d-%m-%Y_%H-%M-%S") + '.jpg'
        camera.capture(temp)
        camera.stop_preview()

        Picture_Read = True

        print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : Reading : " + "getPicture" +
              " : " + "Picture taken with file name " + " : " + temp)
        logger.info(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : Reading : " + "getPicture" +
                    " : " + "Picture taken with file name " + " : " + temp)


    except Exception as PictureError:
        Readings = False
        Picture_Read = False
        Picture_Error = True
        Picture_Error_MSG = str(PictureError)
        print(Node_Name + " : " + time.strftime(
            "%d-%m-%Y %H:%M:%S ") + " : ERROR : " + "getCarData" + " : " + CarCounter_Error_MSG)
        logger.info(Node_Name + " : " + time.strftime(
            "%d-%m-%Y %H:%M:%S ") + " : ERROR : " + "getCarData" + " : " + CarCounter_Error_MSG)

    finally:
        pass


# Main
try:
    Data = {}
    Data.clear()

    print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : " + "Main" + " : " + "Program started")
    logger.info(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : " + "Main" + " : " + "Program started")

    while True:
        if Readings_start is None:
            Readings_start = time.time()
        if Picture_Start is None:
            Picture_Start = time.time()

        print(Node_Name + " : " + time.strftime(
            "%d-%m-%Y %H:%M:%S") + " : " + "Main" + " : " + "Getting distance sensor readings!!")
        getCarData()
        time.sleep(1)

        Readings_now = time.time()
        Picture_now = time.time()

        if General_Error or Picture_Error or CarCounter_Error:
            print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : " + "Main" + " : " +
                  "Json error dump!!")
            writeJSON()
            time.sleep(0.5)

        if Picture_now - Picture_Start > 60:
            print(Node_Name + " : " + time.strftime(
                "%d-%m-%Y %H:%M:%S") + " : " + "Main" + " : " + "Getting picture!!")
            getPicture()
            Picture_Start = None
            time.sleep(0.5)

        if (Readings_now - Readings_start > 90) and Readings:
            print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : " + "Main" + " : " + "Json dump!!")

            writeJSON()
            Data.clear()
            CarCounter_In = 0
            CarCounter_Out = 0
            Readings_start = None
            time.sleep(0.5)

        if Readings_start is not None:
            print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : " + "Main" + " : " + "JSON timer = " +
                  str(Readings_now - Readings_start)[:6] + " seconds")

        if Picture_Start is not None:
            print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : " + "Main" + " : " + "Picture timer = "
                  + str(Picture_now - Picture_Start)[:6] + " seconds")

        print("*******************************")

        time.sleep(0.1)

except Exception as mainError:
    General_Error = True
    General_Error_MSG = str(mainError)
    print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : ERROR : " + "Main" + " : " + General_Error_MSG)
    logger.info(
        Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : ERROR : " + "Main" + " : " + General_Error_MSG)

finally:
    GPIO.cleanup()
