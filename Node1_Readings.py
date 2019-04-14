import time
import datetime
import json
import logging
import RPi.GPIO as GPIO
import Adafruit_MCP3008
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import sys
import socket
import busio
import board
import digitalio
import adafruit_bme680
import adafruit_tsl2591
import adafruit_character_lcd.character_lcd as characterlcd

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Sensors - Protocols initialization
i2c = busio.I2C(board.SCL, board.SDA)
bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c, debug=False)
tsl2591 = adafruit_tsl2591.TSL2591(i2c)
GPIO.setup(4, GPIO.OUT)

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
lcd = characterlcd.Character_LCD_RGB(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, lcd_columns,lcd_rows, red, green, blue, lcd_backlight)
lcd.color = [0, 100, 0]  # green color

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
logFilename = "/home/pi/Logs/" + Node_Name + "_ReadingsLog_" + timeLog + ".log"
handler = logging.FileHandler(logFilename)
logger.addHandler(handler)

# Readings time
Readings_start = None
Reading_now = None
JSON_dump_timer = None

# Errors
Readings = False
General_Error = False
General_Error_MSG = None
BME680_Error = False
BME680_Error_MSG = None
TSL2591_Error = False
TSL2591_Error_MSG = None
MFRC522_Error = False
MFRC522_Error_MSG = None
Anemometer_Error = False
Anemometer_Error_Msg = None

# BME 680 sensor
BME680_Read = False
BME680_Temperature = None
BME680_Humidity = None
BME680_Gas = None
## BME680_Pressure = None
## BME680_Altitude = None

# TSL2591 sensor
TSL2591_Read = False
TSL2591_Lux = None
TSL2591_Visible = None
TSL2591_IR = None
TSL2591_Full_Spectrum = None

# MCP3008
MCP3008_output = None

# Anemometer
Anemometer_Read = False
WindSpeedVoltage = None
WindSpeed = None


# Method for writing JSON dumps
def writeJSON():
    global Data
    global General_Error
    global General_Error_MSG

    try:
        if Readings:
            Data = {
                "Node_Name": Node_Name,
                "Date": time.strftime("%d-%m-%Y %H:%M:%S "),
                "General_Error": General_Error,
                "General_Error_Message": General_Error_MSG if General_Error is True else None,
                "Readings": Readings,
                "BME680": [
                    {"BME680_Temperature": BME680_Temperature} if BME680_Read is True else None,
                    {"BME680_Humidity": BME680_Humidity} if BME680_Read is True else None,
                    {"BME680_Gas": BME680_Gas} if BME680_Read is True else None,
                ] if BME680_Read is True else None,
                "TSL2591": [
                    {"TSL2591_Lux": TSL2591_Lux} if TSL2591_Read is True else None,
                    {"TSL2591_Visible": TSL2591_Visible} if TSL2591_Read is True else None,
                    {"TSL2591_IR": TSL2591_IR} if TSL2591_Read is True else None,
                    {"TSL2591_Full_Spectrum": TSL2591_Full_Spectrum} if TSL2591_Read is True else None,
                ] if TSL2591_Read is True else None,
                "Anemometer": [
                    {"WindSpeed": WindSpeed} if Anemometer_Read is True else None,
                    {"MCP3008_output": MCP3008_output} if Anemometer_Read is True else None,
                ] if Anemometer_Read is True else None
            }
        elif not Readings:
            Data = {
                "Node_Name": Node_Name,
                "Date": time.strftime("%d-%m-%Y %H:%M:%S "),
                "General_Error": General_Error,
                "General_Error_Message": General_Error_MSG if General_Error is True else None,
                "Error Data": [
                    {"BME680_Error": BME680_Error} if BME680_Error is True else None,
                    {"BME680_Error_MSG": BME680_Error_MSG} if BME680_Error is True else None,
                    {"TSL2591_Error": TSL2591_Error} if TSL2591_Error is True else None,
                    {"TSL2591_Error_MSG": TSL2591_Error_MSG} if TSL2591_Error is True else None,
                    {"Anemometer_Error": Anemometer_Error} if Anemometer_Error is True else None,
                    {"Anemometer_Error_Msg": Anemometer_Error_Msg} if Anemometer_Error is True else None,
                ] if BME680_Error or TSL2591_Error or Anemometer_Error is True else None
            }
        
        logger.info(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : " + "writeJSON" + " : " + "JSON dump")
        print(json.dumps(Data))
        logger.info(Node_Name + " : " + time.strftime(
            "%d-%m-%Y %H:%M:%S ") + " : " + "writeJSON" + " : " + str(json.dumps(Data)))

        timeJSON = time.strftime("%d-%m-%Y_%H-%M-%S")
        timeJSON = timeJSON.replace(" ", "-")

        jsonpath = "/home/pi/JSON_NEW_FILES/" + Node_Name + "_ReadingsJSON_ " + timeJSON + ".txt"
        with open(jsonpath, 'w') as outputfile:
            json.dump(Data, outputfile)
        timeJSON = ""

    except Exception as jsonerror:
        lcd.clear()
        lcd.color = [100, 0, 0] # red color
        lcd.message = "Error!!!\n(R)writeJSON"
        General_Error = True
        General_Error_MSG = str(jsonerror)
        print(Node_Name + " : " + time.strftime(
            "%d-%m-%Y %H:%M:%S ") + " : ERROR : " + "writeJSON" + " : " + General_Error_MSG)
        logger.info(Node_Name + " : " + time.strftime(
            "%d-%m-%Y %H:%M:%S ") + " : ERROR : " + "writeJSON" + " : " + General_Error_MSG)

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
    global Readings

    try:
        time.sleep(0.1)

        Readings = True
        BME680_Read = True
        BME680_Temperature = str(round(bme680.temperature, 3))
        BME680_Humidity = str(round(bme680.humidity, 3))
        BME680_Gas = str(bme680.gas)
        
        print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : Reading : " +
              "getBME680Data" + " : " + BME680_Temperature + "C : " + BME680_Humidity + "% : " + BME680_Gas + "ohm")
        logger.info(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : Reading : " + "getBME680Data" +
                    " : " + BME680_Temperature + "C : " + BME680_Humidity + "% : " + BME680_Gas + "ohm")
        
        lcd.clear()
        lcd.color = [0, 100, 0]  # green color
        lcd.message = BME680_Temperature[:4] + "C - " + BME680_Humidity[:4] + "%\n" + time.strftime("%d-%m-%Y %H:%M:%S")

    except Exception as bme680error:
        lcd.clear()
        lcd.color = [100, 0, 0] # red color
        lcd.message = "Error!!!\n(R)getBME680Data"
        Readings = False
        BME680_Read = False
        BME680_Error = True
        BME680_Error_MSG = str(bme680error)
        print(Node_Name + " : " + time.strftime(
            "%d-%m-%Y %H:%M:%S ") + " : ERROR : " + "getBME680Data" + " : " + BME680_Error_MSG)
        logger.info(Node_Name + " : " + time.strftime(
            "%d-%m-%Y %H:%M:%S ") + " : ERROR : " + "getBME680Data" + " : " + BME680_Error_MSG)

    finally:
        pass


# Method for getting TSL 2591 sensor readings
def getTSL2591Data():
    global TSL2591_Error
    global TSL2591_Error_MSG
    global TSL2591_Read
    global TSL2591_Lux
    global TSL2591_Visible
    global TSL2591_IR
    global TSL2591_Full_Spectrum
    global Readings

    try:
        time.sleep(0.1)

        Readings = True
        TSL2591_Read = True

        TSL2591_Lux = str(tsl2591.lux)
        TSL2591_Visible = str(tsl2591.visible)
        TSL2591_IR = str(tsl2591.infrared)
        TSL2591_Full_Spectrum = str(tsl2591.full_spectrum)

        print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : Reading : " + "getTSL2591Data" + " : " +
              TSL2591_Lux + "Lux : " + TSL2591_Visible + " : " + TSL2591_IR + " : " + TSL2591_Full_Spectrum)
        logger.info(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : Reading : " + "getTSL2591Data" + " : "
                    + TSL2591_Lux + "Lux : " + TSL2591_Visible + " : " + TSL2591_IR + " : " + TSL2591_Full_Spectrum)
        
        lcd.clear()
        lcd.color = [0, 100, 0]  # green color
        lcd.message = TSL2591_Lux[:4] + "Lux - " + TSL2591_IR[:4] + "IR\n" + time.strftime("%d-%m-%Y %H:%M:%S")

    except Exception as tsl2591error:
        lcd.clear()
        lcd.color = [100, 0, 0] # red color
        lcd.message = "Error!!!\n(R)getTSL2591Data"
        Readings = False
        TSL2591_Read = False
        TSL2591_Error = True
        TSL2591_Error_MSG = str(tsl2591error)
        print(Node_Name + " : " + time.strftime(
            "%d-%m-%Y %H:%M:%S ") + " : ERROR : " + "getTSL2591Data" + " : " + TSL2591_Error_MSG)
        logger.info(Node_Name + " : " + time.strftime(
            "%d-%m-%Y %H:%M:%S ") + " : ERROR : " + "getTSL2591Data" + " : " + TSL2591_Error_MSG)

    finally:
        pass


# Method for getting BME 680 sensor readings
def getAnemometerData():
    global Anemometer_Error
    global Anemometer_Error_Msg
    global Anemometer_Read
    global WindSpeedVoltage
    global WindSpeed
    global MCP3008_output
    global Readings

    try:
        time.sleep(0.1)

        Readings = True
        Anemometer_Read = True

        MCP3008_output = mcp.read_adc(0)
        WindSpeedVoltage = MCP3008_output / 310
        MCP3008_output2 = str(MCP3008_output)
        WindSpeed = ((WindSpeedVoltage - 0.4) / 1.6) * 32.4
        WindSpeed2 = str(round(WindSpeed,3))
        
        if MCP3008_output == 0 or WindSpeed < -1:
            Readings = False
            Anemometer_Error = True
            Anemometer_Error_Msg = "MCP3008 false output"
            print(Node_Name + " : " + time.strftime( "%d-%m-%Y %H:%M:%S ") + " : Reading : " + "getAnemometerData" +
                  " : " + "MCP3008_output" + " : " + MCP3008_output2  + " : " + "Error : " + Anemometer_Error_Msg)
            logger.info(Node_Name + " : " + time.strftime( "%d-%m-%Y %H:%M:%S ") + " : Reading : " + "getAnemometerData" +
                  " : " + "MCP3008_output" + " : " + MCP3008_output2  + " : " + "Error : " + Anemometer_Error_Msg)
        else:
            print(Node_Name + " : " + time.strftime( "%d-%m-%Y %H:%M:%S ") + " : Reading : " + "getAnemometerData" +
                  " : " + "MCP3008_output" + " : " + MCP3008_output2  + " : " + WindSpeed2 + " m/sec")
            logger.info(Node_Name + " : " + time.strftime( "%d-%m-%Y %H:%M:%S ") + " : Reading : " + "getAnemometerData" +
                  " : " + "MCP3008_output" + " : " + MCP3008_output2  + " : " + WindSpeed2 + " m/sec")
            
        lcd.clear()
        lcd.color = [0, 100, 0]  # green color
        lcd.message = WindSpeed2 + "m/sec" + "\n" + time.strftime("%d-%m-%Y %H:%M:%S")

    except Exception as anemometererror:
        lcd.clear()
        lcd.color = [100, 0, 0] # red color
        lcd.message = "Error!!!\n(R)getAnemometerData"
        Readings = False
        Anemometer_Read = False
        Anemometer_Error = True
        Anemometer_Error_Msg = str(anemometererror)
        print(Node_Name + " : " + time.strftime(
            "%d-%m-%Y %H:%M:%S ") + " : ERROR : " + "getAnemometerData" + " : " + Anemometer_Error_Msg)
        logger.info(Node_Name + " : " + time.strftime(
            "%d-%m-%Y %H:%M:%S ") + " : ERROR : " + "getAnemometerData" + " : " + Anemometer_Error_Msg)

    finally:
        pass


# Method for zeroing values
def zeroValues():
    global Readings
    global General_Error
    global General_Error_MSG
    global BME680_Error
    global BME680_Error_MSG
    global TSL2591_Error
    global TSL2591_Error_MSG
    global Anemometer_Error
    global Anemometer_Error_Msg
    global BME680_Read
    global BME680_Temperature
    global BME680_Humidity
    global BME680_Gas
    global Anemometer_Read
    global WindSpeedVoltage
    global WindSpeed
    global MCP3008_output
    global TSL2591_Read
    global TSL2591_Lux
    global TSL2591_Visible
    global TSL2591_IR
    global TSL2591_Full_Spectrum
    global Readings_start

    try:
        Readings = False
        General_Error = False
        General_Error_MSG = None
        BME680_Error = False
        BME680_Error_MSG = None
        TSL2591_Error = False
        TSL2591_Error_MSG = None
        Anemometer_Error = False
        Anemometer_Error_Msg = None
        BME680_Read = False
        BME680_Temperature = None
        BME680_Humidity = None
        BME680_Gas = None
        TSL2591_Read = False
        TSL2591_Lux = None
        TSL2591_Visible = None
        TSL2591_IR = None
        TSL2591_Full_Spectrum = None
        Anemometer_Read = False
        WindSpeedVoltage = None
        WindSpeed = None
        MCP3008_output = None
        Readings_start = None
        Data.clear()

        print(Node_Name + " : " + time.strftime(
            "%d-%m-%Y %H:%M:%S ") + " : " + "zeroValues" + " : " + "Zeroing values...")

        logger.info(Node_Name + " : " + time.strftime(
            "%d-%m-%Y %H:%M:%S ") + " : " + "zeroValues" + " : " + "Zeroing values...")

    except Exception as zerovalues:
        lcd.clear()
        lcd.color = [100, 0, 0] # red color
        lcd.message = "Error!!!\n(R)zeroValues"
        General_Error = True
        General_Error_MSG = str(zerovalues)
        print(Node_Name + " : " + time.strftime(
            "%d-%m-%Y %H:%M:%S ") + " : ERROR : " + "zeroValues" + " : " + General_Error_MSG)
        logger.info(Node_Name + " : " + time.strftime(
            "%d-%m-%Y %H:%M:%S ") + " : ERROR : " + "zeroValues" + " : " + General_Error_MSG)

    finally:
        pass


# Main
try:
    Data = {}
    Data.clear()
    # JsonDumpCounter = 0

    print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : " + "Main" + " : " + "Program started")
    logger.info(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : " + "Main" + " : " + "Program started")
    
    while True:
        if Readings_start == None:
            Readings_start = time.time()
            print(Node_Name + " : " + time.strftime(
            "%d-%m-%Y %H:%M:%S ") + " : " + "Main" + " : " + "Refreshing readings start timer!")
        
        print(Node_Name + " : " + time.strftime(
            "%d-%m-%Y %H:%M:%S ") + " : " + "Main" + " : " + "Getting BME680 readings!!")
        getBME680Data()
        time.sleep(2)
        
        if not BME680_Error:
            print(Node_Name + " : " + time.strftime(
                "%d-%m-%Y %H:%M:%S ") + " : " + "Main" + " : " + "Getting TSL2591 readings!!")
            getTSL2591Data()
            time.sleep(2)
        
        if not TSL2591_Error:
            if GPIO.input(4) == 0:
                print(Node_Name + " : " + time.strftime(
                    "%d-%m-%Y %H:%M:%S ") + " : " + "Main" + " : " + "Getting Anemometer readings!!")
                getAnemometerData()
                time.sleep(2)
            else:
                print(Node_Name + " : " + time.strftime(
                    "%d-%m-%Y %H:%M:%S ") + " : " + "Main" + " : " + "Skipping Anemometer readings!!")
                lcd.clear()
                lcd.color = [0, 100, 0]  # green color
                lcd.message = "Skippping Anemometer%\n" + time.strftime("%d-%m-%Y %H:%M:%S")
        
        Readings_now = time.time()
        
        print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : " + "Main" + " : " + "Timer: " + str(Readings_now - Readings_start))
        
        if General_Error or Anemometer_Error or BME680_Error or TSL2591_Error:
            print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : " + "Main" + " : " + "Json error dump!!")
            lcd.clear()
            lcd.color = [100, 0, 0]  # green color
            lcd.message = "JSON error dump\n" + time.strftime("%d-%m-%Y %H:%M:%S")
            writeJSON()
            print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : " + "Main" + " : " + "Zeroing values!!")
            zeroValues()
            time.sleep(1)
            
        
        if (Readings_now - Readings_start > 90) and Readings:
            print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : " + "Main" + " : " + "Json dump!!")
            lcd.clear()
            lcd.color = [0, 100, 0]  # green color
            lcd.message = "JSON dump\n" + time.strftime("%d-%m-%Y %H:%M:%S")
            writeJSON()
            print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : " + "Main" + " : " + "Zeroing values!!")
            zeroValues()
            time.sleep(1)
            
            # Data.clear()
            # Readings_start = None
            # JsonDumpCounter = 0

        print("*******************************")

        # JsonDumpCounter += 1

        time.sleep(0.1)

except Exception as mainerror:
    lcd.clear()
    lcd.color = [100, 0, 0] # red color
    lcd.message = "Error!!!\n(R)MainProgram"
    General_Error = True
    General_Error_MSG = str(mainerror)
    print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : ERROR : " + "Main" + " : " + General_Error_MSG)
    logger.info(
        Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : ERROR : " + "Main" + " : " + General_Error_MSG)

finally:
    GPIO.cleanup()
    lcd.clear()
    lcd.display = False


