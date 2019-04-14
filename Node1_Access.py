import time
import json
import logging
import RPi.GPIO as GPIO
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import sys
import socket
sys.path.insert(0, '/home/pi/MFRC522-python')
import SimpleMFRC522
import board
import digitalio
import adafruit_character_lcd.character_lcd as characterlcd

# Raspberry initialization
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(7, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(4, GPIO.OUT)

# Sensors - Protocols initialization
reader = SimpleMFRC522.SimpleMFRC522()

# Node information
Node_Name = socket.gethostname()
Node_Name = Node_Name.replace(" ", "-")

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
lcd.color = [0, 0, 100] # blue color

# Set logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
timeLog = time.strftime("%d-%m-%Y_%H-%M-%S")
timeLog = timeLog.replace(" ", "-")
logFilename = "/home/pi/Logs/" + Node_Name + "_AccessLog_" + timeLog + ".log"
handler = logging.FileHandler(logFilename)
logger.addHandler(handler)

# Errors
General_Error = False
General_Error_MSG = ""
MFRC522_Error = False
MFRC522_Error_MSG = ""

# Access into node
Access = False

# MFRC522 Reading
RFID_Timer = None
RFID_Read = False
RFID_Card_No = ""
RFID_Card_User = ""
RFID_Time = ""
RFID_Closed = True

# Door Contact
Door_Contact = False
Door_Open = False

# Card id's with access
Access_list_id = [291511417800, 539278603011]
## Access_list_id = [Kostas, Giorgos]


# Method for checking GPIO pin for door contact
def checkDoorContact():
    global Door_Contact
    global General_Error
    global General_Error_MSG
    global Access
    global Door_Open

    try:
        if GPIO.input(7) == 1 and not Door_Open:
            Door_Open = True
            Access = True
            Door_Contact = True
            print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : " + "checkDoorContact" + " : " + "Door #2 open! - Magnetic contact")
            logger.info(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : " + "checkDoorContact" + " : " + "Door #2 open! - Magnetic contact")
            lcd.clear()
            lcd.color = [0, 0, 100] # blue color
            lcd.message = "Door #2 open!\n" + time.strftime("%d-%m-%Y %H:%M:%S")
            
        if GPIO.input(7) == 0 and Door_Open:
            Door_Open = False
            Access = True
            Door_Contact = False
            print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : " + "checkDoorContact" + " : " + "Door # closed! - Magnetic contact")
            logger.info(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : " + "checkDoorContact" + " : " + "Door #2 closed! - Magnetic contact")
            lcd.clear()
            lcd.color = [0, 0, 100] # blue color
            lcd.message = "Door #2 closed!\n" + time.strftime("%d-%m-%Y %H:%M:%S")

    except Exception as e:
        lcd.clear()
        lcd.color = [100, 0, 0] # red color
        lcd.message = "Error!!!\ncheckDoorContact"
        General_Error = True
        General_Error_MSG = str(e)
        print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : ERROR : " + "checkDoorContact" + " : " + General_Error_MSG)
        logger.info(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : ERROR : " + "checkDoorContact" + " : " + General_Error_MSG)

    finally:
        pass


# Method for reading MFRC522 cards
def checkMFRC522():
    
    global Access
    global General_Error
    global General_Error_MSG
    global MFRC522_Error
    global MFRC522_Error_MSG
    global RFID_Card_No
    global RFID_Card_User
    global RFID_Time
    global RFID_Timer
    global RFID_Read
    global RFID_Closed

    try:
        print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : " + "checkMFRC522" + " : " + "Reading card...")
        id, text = reader.readInterval()
        
        if RFID_Timer is not None:
            if (time.time()- RFID_Timer > 5):
                print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : " + "checkMFRC522" + " : " + "Lock #1 closed!")
                logger.info(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : " + "checkMFRC522" + " : " + "Lock #1 closed!")
                RFID_Closed = not RFID_Closed
                RFID_Timer = None
                GPIO.output(4,GPIO.LOW)
                lcd.clear()
                lcd.color = [0, 0, 100] # blue color
                lcd.message = "Lock #1 closed!\n" + time.strftime("%d-%m-%Y %H:%M:%S")

        if id is not None:
            textremovespaces = text.rstrip()

            for x in Access_list_id:
                if x == id:
                    Access = True
                    
            RFID_Card_No = str(id)
            RFID_Card_User = textremovespaces
            RFID_Time = time.strftime("%d-%m-%Y %H:%M:%S ")
            RFID_Read = True
            if Access:
                RFID_Closed = not RFID_Closed
            
            if Access and not RFID_Closed:
                print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : " + "checkMFRC522" + " : " + "User: " + RFID_Card_User + " with ID: " + RFID_Card_No)
                logger.info(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : " + "checkMFRC522" + " : " + "User: " + RFID_Card_User + " with ID: " + RFID_Card_No)
                print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : " + "checkMFRC522" + " : " + "Lock #1 open for 5 seconds!")
                logger.info(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : " + "checkMFRC522" + " : " + "Lock #1 open for 5 seconds!")
                GPIO.output(4,GPIO.HIGH)
                lcd.clear()
                lcd.color = [0, 0, 100] # blue color
                lcd.message = "Lock #1 open!\n" + time.strftime("%d-%m-%Y %H:%M:%S")
                time.sleep(1)
                lcd.clear()
                lcd.color = [0, 0, 100] # blue color
                lcd.message = (RFID_Card_No + "\n" + RFID_Card_User) 
                RFID_Timer = time.time()
                               
            if not Access:
                print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : " + "checkMFRC522" + " : " + "User: " + RFID_Card_User + " with ID: " + RFID_Card_No + " does not have access!!!")
                logger.info(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : " + "checkMFRC522" + " : " + "User: " + RFID_Card_User + " with ID: " + RFID_Card_No + " does not have access!!!")
                lcd.clear()
                lcd.color = [0, 0, 100] # blue color
                lcd.message = RFID_Card_No + "\n" + "No Access!"
                time.sleep(1) 
                
        id=""
        text=""

    except Exception as e:
        lcd.clear()
        lcd.color = [100, 0, 0] # red color
        lcd.message = "Error!!!\ncheckMFRC522"
        General_Error = True
        MFRC522_Error = True
        General_Error_MSG = str(e)
        print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : ERROR : " + "checkMFRC522" + " : " + MFRC522_Error_MSG)
        logger.info(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : ERROR : " + "checkMFRC522" + " : " + MFRC522_Error_MSG)

    finally:
        pass


# Method for writing JSON dumps
def writeJSON():
    
    global Data
    global General_Error
    global General_Error_MSG

    try:
        if not General_Error:
            Data = {
                "Node_Name": Node_Name,
                "Date": time.strftime("%d-%m-%Y %H:%M:%S "),
                "General_Error": General_Error,
                "General_Error_Message": General_Error_MSG if General_Error is True else None,
                "Access": Access,
                "Access Data": [
                    {"RFID_Card_Number": RFID_Card_No} if RFID_Read is True else None,
                    {"RFID_Card_User": RFID_Card_User} if RFID_Read is True else None,
                    {"Door_contact": Door_Contact} if Door_Contact is True else None,
                ] if Access is True else None
            }
        elif General_Error:
            Data = {
                "Node_Name": Node_Name,
                "Date": time.strftime("%d-%m-%Y %H:%M:%S "),
                "General_Error": General_Error,
                "General_Error_Message": General_Error_MSG if General_Error is True else None,
                "Error Data": [
                    {"MFRC522_Error": MFRC522_Error},
                    {"MFRC522_Error_Message": MFRC522_Error_MSG},
                ] if MFRC522_Error is True else None
            }
            
        logger.info(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : " + "writeJSON" + " : " + "JSON dump")
        print(json.dumps(Data))
        logger.info(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : " + "writeJSON" + " : " + str(json.dumps(Data)))
        timeJSON = time.strftime("%d-%m-%Y_%H-%M-%S")
        timeJSON = timeJSON.replace(" ", "-")
        jsonpath = "/home/pi/JSON_NEW_FILES/" + Node_Name + "_AccessJSON_ "+ timeJSON + ".txt"
        with open(jsonpath, 'w') as outputfile:
            json.dump(Data, outputfile)
        timeJSON= ""
    except Exception as e:
        lcd.clear()
        lcd.color = [100, 0, 0] # red color
        lcd.message = "Error!!!\nwriteJSON"
        General_Error = True
        General_Error_MSG = str(e)
        print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : ERROR : " + "writeJSON" + " : " + General_Error_MSG)
        logger.info(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : ERROR : " + "writeJSON" + " : " + General_Error_MSG)

    finally:
        pass


# Method for zeroing values
def zeroValues():
    
    global General_Error
    global General_Error_MSG
    global MFRC522_Error
    global MFRC522_Error_MSG
    global Access
    global RFID_Read 
    global RFID_Card_No
    global RFID_Card_User
    global RFID_Time
    global Door_Contact
    global Data
    
    try:
        General_Error = False
        General_Error_MSG = ""
        MFRC522_Error = False
        MFRC522_Error_MSG = ""
        Access = False
        RFID_Read = False
        RFID_Card_No = ""
        RFID_Card_User = ""
        RFID_Time = ""
        Door_Contact = False
        Data.clear()

        logger.info(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : " + "zeroValues" + " : " + "Zeroing values...")
    
    except Exception as e:
        lcd.clear()
        lcd.color = [100, 0, 0] # red color
        lcd.message = "Error!!!\nzeroValues"
        General_Error = True
        General_Error_MSG = str(e)
        print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : ERROR : " + "zeroValues" + " : " + General_Error_MSG)
        logger.info(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : ERROR : " + + "zeroValues" + " : " + General_Error_MSG)
        
    finally:
        pass

# Main
try:
    Data = {}
    Data.clear()
    
    generalTimer= None
    
    print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : " + "Main" + " : " + "Program started")
    logger.info(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : " + "Main" + " : " + "Program started")
    while True:
        if generalTimer== None:
            generalTimer = time.time()
        
        print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : " + "Main" + " : " + "Checking for card ...")
        checkMFRC522()
        
        time.sleep(0.5)
        
        print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : " + "Main" + " : " + "Checking door contact...")
        checkDoorContact()
        
        time.sleep(0.5)
        
        print(time.time()- generalTimer)
        if time.time()- generalTimer > 120:
            generalTimer = None
            logger.info(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : " + "Main" + " : " + "No access to the node. Will log again in 120 seconds")

        if Access or General_Error:
            print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : " + "Main" + " : " + "Json dump!!")
            # lcd.clear()
            # lcd.color = [0, 0, 100] # blue color
            # lcd.message = "JSON dump\n" + time.strftime("%d-%m-%Y %H:%M:%S")
            writeJSON()
            # Data.clear()
            # Access = False
            
            print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : " + "Main" + " : " + "Zeroing values!!")
            zeroValues()      

        else:
            print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : " + "Main" + " : " + "No Json dump..")
            
        print("*******************************")    

        time.sleep(1)

except Exception as e:
    lcd.clear()
    lcd.color = [100, 0, 0] # red color
    lcd.message = "Error!!!\nMainProgram"
    General_Error = True
    General_Error_MSG = str(e)
    print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : ERROR : " + "Main" + " : " + General_Error_MSG)
    logger.info(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S ") + " : ERROR : " + "Main" + " : " + General_Error_MSG)

finally:
    GPIO.cleanup()
ngs
