import time
import datetime
import json
import os
import logging
from logging.handlers import TimedRotatingFileHandler
import RPi.GPIO as GPIO
import Adafruit_MCP3008
import smtplib
import sys
import socket
import busio
import board
import adafruit_bme680
import adafruit_sgp30
import digitalio
import adafruit_character_lcd.character_lcd as characterlcd

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# LCD Config:
lcd_columns = 16
lcd_rows = 2
lcd_rs = digitalio.DigitalInOut(board.D5)
lcd_en = digitalio.DigitalInOut(board.D6)
lcd_d4 = digitalio.DigitalInOut(board.D12)
lcd_d5 = digitalio.DigitalInOut(board.D16)
lcd_d6 = digitalio.DigitalInOut(board.D20)
lcd_d7 = digitalio.DigitalInOut(board.D21)
lcd_backlight = digitalio.DigitalInOut(board.D4)
red = digitalio.DigitalInOut(board.D13)
green = digitalio.DigitalInOut(board.D19)
blue = digitalio.DigitalInOut(board.D26)

lcd = characterlcd.Character_LCD_RGB(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, lcd_columns, lcd_rows, red, green,
                                     blue, lcd_backlight)
lcd.color = [0, 100, 0]  # green color

# Sensors - Protocols initialization
i2c = busio.I2C(board.SCL, board.SDA)
bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c, debug=False)
sgp30 = adafruit_sgp30.Adafruit_SGP30(i2c)
sgp30.iaq_init()

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

# Readings time start
Readings_start = None
Reading_now = None
JSON_dump_timer = None

# Errors
Readings = False
General_Error = False
General_Error_MSG = None
BME680_Error = False
BME680_Error_MSG = None
SGP30_Error = False
SGP30_Error_MSG = None

# BME 680 sensor
BME680_Read = False
BME680_Temperature = None
BME680_Humidity = None
BME680_Gas = None
BME680_Pressure = None
# BME680_Altitude = None

# SGP30 sensor
SGP30_Read = False
SGP30_ECO2 = None
SGP30_TVOC = None
SGP30_ECO2_Baseline = 0x8b80
SGP30_TVOC_Baseline = 0x90c8
SGP30_Baseline_Timer = None
SGP30_Baseline_Now = None
SGP30_Baseline = False


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
                "BME680": [
                    {"BME680_Temperature": BME680_Temperature} if BME680_Read is True else None,
                    {"BME680_Humidity": BME680_Humidity} if BME680_Read is True else None,
                    {"BME680_Gas": BME680_Gas} if BME680_Read is True else None,
                    {"BME680_Pressure": BME680_Pressure} if BME680_Read is True else None,
                ] if BME680_Read is True else None,
                "SGP30": [
                    {"SGP30_ECO2": SGP30_ECO2} if SGP30_Read is True else None,
                    {"SGP30_TVOC": SGP30_TVOC} if SGP30_Read is True else None,
                    {"SGP30_TVOC_Baseline": SGP30_ECO2_Baseline} if SGP30_Read is True else None,
                    {"SGP30_TVOC_Baseline": SGP30_TVOC_Baseline} if SGP30_Read is True else None,
                ] if SGP30_Read is True else None,
            }
        elif not Readings:
            Data = {
                "Node_Name": Node_Name,
                "Date": time.strftime("%d-%m-%Y %H:%M:%S"),
                "General_Error": General_Error,
                "General_Error_Message": General_Error_MSG if General_Error is True else None,
                "Error Data": [
                    {"BME680_Error": BME680_Error} if BME680_Error is True else None,
                    {"BME680_Error_MSG": BME680_Error_MSG} if BME680_Error is True else None,
                    {"SGP30_Error": SGP30_Error} if SGP30_Error is True else None,
                    {"SGP30_Error_MSG": SGP30_Error_MSG} if SGP30_Error is True else None,
                ] if BME680_Error or SGP30_Error is True else None
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


# Method for getting BME 680 sensor readings
def getBME680Data():
    global BME680_Error
    global BME680_Error_MSG
    global BME680_Read
    global BME680_Temperature
    global BME680_Humidity
    global BME680_Gas
    global BME680_Pressure
    global Readings

    try:
        time.sleep(0.1)

        Readings = True
        BME680_Read = True
        BME680_Temperature = str(round(bme680.temperature, 5))
        BME680_Humidity = str(round(bme680.humidity, 5))
        BME680_Gas = str(bme680.gas)
        BME680_Pressure = str(round(bme680.pressure, 5))
        
        print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : Reading : " +
              "getBME680Data" + " : " + BME680_Temperature + "C : " + BME680_Humidity + "% : " + BME680_Gas + "ohm : " +
              BME680_Pressure + "hPA")   
        logger.info(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : Reading : " + "getBME680Data" +
                    " : " + BME680_Temperature + "C : " + BME680_Humidity + "% : " + BME680_Gas + "ohm : " +
                    BME680_Pressure + "hPa")

        lcd.clear()
        lcd.color = [0, 100, 0]  # green color
        lcd.message = BME680_Temperature[:4] + "C - " + BME680_Humidity[:4] + "%\n" + time.strftime("%d-%m-%Y %H:%M:%S")

    except Exception as bme680error:
        lcd.clear()
        lcd.color = [100, 0, 0]  # red color
        lcd.message = "Error!!!\nR-getBME680Data"
        Readings = False
        BME680_Read = False
        BME680_Error = True
        BME680_Error_MSG = str(bme680error)
        print(Node_Name + " : " + time.strftime(
            "%d-%m-%Y %H:%M:%S") + " : ERROR : " + "getBME680Data" + " : " + BME680_Error_MSG)
        logger.info(Node_Name + " : " + time.strftime(
            "%d-%m-%Y %H:%M:%S") + " : ERROR : " + "getBME680Data" + " : " + BME680_Error_MSG)

    finally:
        pass


# Method for getting TSL 2591 sensor readings
def getSGP30Data():
    global SGP30_Error
    global SGP30_Error_MSG
    global SGP30_Read
    global SGP30_ECO2
    global SGP30_TVOC
    global SGP30_ECO2_Baseline
    global SGP30_TVOC_Baseline
    global Readings

    try:
        time.sleep(0.1)

        Readings = True
        SGP30_Read = True

        SGP30_ECO2 = str(sgp30.eCO2)
        SGP30_TVOC = str(sgp30.TVOC)

        SGP30_ECO2_Baseline = sgp30.baseline_eCO2
        SGP30_TVOC_Baseline = sgp30.baseline_TVOC

        print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : Reading : " + "getSGP30Data" + " : " +
              "eCO2: " + SGP30_ECO2 + " - TVOC :" + SGP30_TVOC +
              " - SGP30_ECO2_Baseline: 0x%x - SGP30_TVOC_Baseline: 0x%x" % (SGP30_ECO2_Baseline, SGP30_TVOC_Baseline))     
        logger.info(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : Reading : " + "getSGP30Data" + " : " +
                    "eCO2: " + SGP30_ECO2 + " - TVOC :" + SGP30_TVOC +
                    " - SGP30_ECO2_Baseline: 0x%x - SGP30_TVOC_Baseline: 0x%x" % (SGP30_ECO2_Baseline,
                                                                                  SGP30_TVOC_Baseline))
        
        lcd.clear()
        lcd.color = [0, 100, 0]  # green color
        lcd.message = SGP30_ECO2 + "CO2-" + SGP30_TVOC + "TVOC\n" + time.strftime("%d-%m-%Y %H:%M:%S")
                
    except Exception as sgp30error:
        lcd.clear()
        lcd.color = [100, 0, 0]  # red color
        lcd.message = "Error!!!\nR-getSGP30Data"
        Readings = False
        SGP30_Read = False
        SGP30_Error = True
        SGP30_Error_MSG = str(sgp30error)
        print(Node_Name + " : " + time.strftime(
            "%d-%m-%Y %H:%M:%S") + " : ERROR : " + "getSGP30Data" + " : " + SGP30_Error_MSG)
        logger.info(Node_Name + " : " + time.strftime(
            "%d-%m-%Y %H:%M:%S") + " : ERROR : " + "getSGP30Data" + " : " + SGP30_Error_MSG)

    finally:
        pass


# Method for zeroing values
def zeroValues():
    global Readings
    global General_Error
    global General_Error_MSG
    global BME680_Error
    global BME680_Error_MSG
    global SGP30_Error
    global SGP30_Error_MSG
    global BME680_Read
    global BME680_Temperature
    global BME680_Humidity
    global BME680_Gas
    global SGP30_Read
    global SGP30_ECO2
    global SGP30_TVOC
    global SGP30_ECO2_Baseline
    global SGP30_TVOC_Baseline

    try:
        Readings = False
        General_Error = False
        General_Error_MSG = None
        BME680_Error = False
        BME680_Error_MSG = None
        SGP30_Error = False
        SGP30_Error_MSG = None
        BME680_Read = False
        BME680_Temperature = None
        BME680_Humidity = None
        BME680_Gas = None
        SGP30_Read = False
        SGP30_ECO2 = None
        SGP30_TVOC = None
        SGP30_ECO2_Baseline = None
        SGP30_TVOC_Baseline = None
        Data.clear()

        print(Node_Name + " : " + time.strftime(
            "%d-%m-%Y %H:%M:%S") + " : " + "zeroValues" + " : " + "Zeroing values...")
        logger.info(Node_Name + " : " + time.strftime(
            "%d-%m-%Y %H:%M:%S") + " : " + "zeroValues" + " : " + "Zeroing values...")

    except Exception as zeroValuesError:
        lcd.clear()
        lcd.color = [100, 0, 0]  # red color
        lcd.message = "Error!!!\nR-zeroValues"
        General_Error = True
        General_Error_MSG = str(zeroValuesError)
        print(Node_Name + " : " + time.strftime(
            "%d-%m-%Y %H:%M:%S") + " : ERROR : " + "zeroValues" + " : " + General_Error_MSG)
        logger.info(Node_Name + " : " + time.strftime(
            "%d-%m-%Y %H:%M:%S") + " : ERROR : " + "zeroValues" + " : " + General_Error_MSG)

    finally:
        pass


# Method for reading SGP30 baseline from file
def setSGPBaseline():
    global General_Error
    global General_Error_MSG
    global SGP30_Baseline
    global SGP30_ECO2_Baseline
    global SGP30_TVOC_Baseline
    global sgp30
    
    try:
        with open('/home/pi/NodePrograms/SGP30Baselines.json', 'r') as SGP30B:
            baseline = json.load(SGP30B)

        SGP30_ECO2_Baseline = int(baseline["SGP30_ECO2_Baseline"], 16)
        SGP30_TVOC_Baseline = int(baseline["SGP30_TVOC_Baseline"], 16)

        print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : " + "Setting" + " : " +
              "Setting SGP30 baselines - " + baseline["SGP30_ECO2_Baseline"] + ", " + baseline["SGP30_TVOC_Baseline"])
        logger.info(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : " + "Setting" + " : " +
                    "Setting SGP30 baselines - " + baseline["SGP30_ECO2_Baseline"] + ", " +
                    baseline["SGP30_TVOC_Baseline"])

        sgp30.set_iaq_baseline(SGP30_ECO2_Baseline, SGP30_TVOC_Baseline)

    except Exception as getSGPBaselineError:
        SGP30_Baseline = False
        sgp30.set_iaq_baseline(SGP30_ECO2_Baseline, SGP30_TVOC_Baseline)
        lcd.clear()
        lcd.color = [100, 0, 0]  # red color
        lcd.message = "Error!!!\nR-setSGPBaseline"
        General_Error = True
        General_Error_MSG = str(getSGPBaselineError)
        print(Node_Name + " : " + time.strftime(
            "%d-%m-%Y %H:%M:%S") + " : ERROR : " + "setSGPBaseline" + " : " + General_Error_MSG)
        logger.info(Node_Name + " : " + time.strftime(
            "%d-%m-%Y %H:%M:%S") + " : ERROR : " + "setSGPBaseline" + " : " + General_Error_MSG)


# Method for saving SGP30 Baseline to file
def saveSGP30Baseline():
    global BaselineData
    global SGP30_ECO2_Baseline
    global SGP30_TVOC_Baseline
    global General_Error
    global General_Error_MSG
    
    try:
        if SGP30_ECO2_Baseline is not None:
            BaselineData = {
                "Node_Name": Node_Name,
                "Date": time.strftime("%d-%m-%Y %H:%M:%S"),
                "SGP30_ECO2_Baseline": hex(SGP30_ECO2_Baseline),
                "SGP30_TVOC_Baseline": hex(SGP30_TVOC_Baseline)
                }
                    
            with open('/home/pi/NodePrograms/SGP30Baselines.json', 'w') as outputFile2:
                json.dump(BaselineData, outputFile2)
            
            logger.info(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : " +
                        "Saving" + " : " + "Saving baselines for SGP30")
            print(json.dumps(BaselineData))
            logger.info(Node_Name + " : " + time.strftime(
                "%d-%m-%Y %H:%M:%S") + " : " + "Saving" + " : " + str(json.dumps(BaselineData)))
            
    except Exception as saveSGP30BaselineError:
        lcd.clear()
        lcd.color = [100, 0, 0]  # red color
        lcd.message = "Error!!!\nR-saveSGP30Baseline"
        General_Error = True
        General_Error_MSG = str(saveSGP30BaselineError)
        print(Node_Name + " : " + time.strftime(
            "%d-%m-%Y %H:%M:%S") + " : ERROR : " + "saveSGP30Baseline" + " : " + General_Error_MSG)
        logger.info(Node_Name + " : " + time.strftime(
            "%d-%m-%Y %H:%M:%S") + " : ERROR : " + "saveSGP30Baseline" + " : " + General_Error_MSG)


# Main
try:
    Data = {}
    BaselineData = {}
    Data.clear()
    BaselineData.clear()

    print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : " + "Main" + " : " + "Program started")
    logger.info(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : " + "Main" + " : " + "Program started")

    setSGPBaseline()

    while True:
        if Readings_start is None:
            Readings_start = time.time()
        if SGP30_Baseline_Timer is None:
            SGP30_Baseline_Timer = time.time()
        
        print(Node_Name + " : " + time.strftime(
            "%d-%m-%Y %H:%M:%S") + " : " + "Main" + " : " + "Getting BME680 readings!!")
        getBME680Data()
        time.sleep(2)

        print(Node_Name + " : " + time.strftime(
            "%d-%m-%Y %H:%M:%S") + " : " + "Main" + " : " + "Getting SGP30 readings!!")
        getSGP30Data() 
        time.sleep(2)
        
        Readings_now = time.time()
        SGP30_Baseline_now = time.time()
        
        if General_Error or BME680_Error or SGP30_Error:
            lcd.clear()
            lcd.color = [100, 0, 0]  # red color
            lcd.message = "JSON error dump\n" + time.strftime("%d-%m-%Y %H:%M:%S")
            print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : " + "Main" + " : " +
                  "Json error dump!!")
            writeJSON()
            time.sleep(1)

        if (SGP30_Baseline_now - SGP30_Baseline_Timer > 1800) and \
                ((SGP30_ECO2_Baseline or SGP30_TVOC_Baseline) is not None):
            lcd.clear()
            lcd.color = [50, 0, 50]  # purple color
            lcd.message = "Storing baseline\n" + time.strftime("%d-%m-%Y %H:%M:%S")
            
            print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : " + "Main" + " : " + "Setting" +
                  " - SGP30_ECO2_Baseline: 0x%x - SGP30_TVOC_Baseline: 0x%x" %
                  (SGP30_ECO2_Baseline, SGP30_TVOC_Baseline))
            logger.info(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : " + "Main" +
                        " : " + "Setting" + " - SGP30_ECO2_Baseline: 0x%x - SGP30_TVOC_Baseline: 0x%x" %
                        (SGP30_ECO2_Baseline, SGP30_TVOC_Baseline))
            
            sgp30.set_iaq_baseline(SGP30_ECO2_Baseline, SGP30_TVOC_Baseline)

            SGP30_Baseline_Timer = None
            time.sleep(1)
  
        if (Readings_now - Readings_start > 90) and Readings:
            print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : " + "Main" + " : " + "Json dump!!")
            lcd.clear()
            lcd.color = [50, 0, 50]  # purple color
            lcd.message = "JSON dump\n" + time.strftime("%d-%m-%Y %H:%M:%S")
            
            writeJSON()
            Data.clear()
            
            saveSGP30Baseline()
            
            BaselineData.clear()
            
            Readings_start = None
            time.sleep(1)
            
            # print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : " + "Main" + ":" + "Zeroing values!!")
            # zeroValues()
        if Readings_start is not None:    
            print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : " + "Main" + " : " + "JSON timer = " +
                  str(Readings_now - Readings_start)[:6] + " seconds")
        
        if SGP30_Baseline_Timer is not None:
            print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : " + "Main" + " : " + "Baseline timer = "
                  + str(SGP30_Baseline_now - SGP30_Baseline_Timer)[:6] + " seconds")
         
        print("*******************************")

        time.sleep(1)

except Exception as mainError:
    lcd.clear()
    lcd.color = [100, 0, 0]  # red color
    lcd.message = "Error!!!\nR-MainProgram"
    General_Error = True
    General_Error_MSG = str(mainError)
    print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : ERROR : " + "Main" + " : " + General_Error_MSG)
    logger.info(
        Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : ERROR : " + "Main" + " : " + General_Error_MSG)

finally:
    lcd.color = [0, 0, 0]
    lcd.clear()
    lcd.display = False
    GPIO.cleanup()

