import time
import datetime
import logging
from logging.handlers import TimedRotatingFileHandler
import os
import socket
import shutil

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
logFilename = logDirectory + Node_Name + "_TransmitLog_" + timeLog + ".log"
# handler = logging.FileHandler(logFilename)
handler = TimedRotatingFileHandler(logFilename, when="midnight", interval=1)
handler.suffix = "%d-%m-%Y_%H-%M-%S.log".replace(" ", "-")
logger.addHandler(handler)

# set directories
JSONDirectoryNew = "/home/pi/NodePrograms/JSON_NEW_FILES/"
if not os.path.exists(JSONDirectoryNew):
    os.makedirs(JSONDirectoryNew)
    
JSONDirectoryOld = "/home/pi/NodePrograms/JSON_OLD_FILES/"
if not os.path.exists(JSONDirectoryOld):
    os.makedirs(JSONDirectoryOld)

PictureDirectoryNew = "/home/pi/NodePrograms/PICS_NEW_FILES/"
if not os.path.exists(PictureDirectoryNew):
    os.makedirs(PictureDirectoryNew)
    
PictureDirectoryOld = "/home/pi/NodePrograms/PICS_OLD_FILES/"
if not os.path.exists(PictureDirectoryOld):
    os.makedirs(PictureDirectoryOld)     
 
# Transmit time start
TransmitJSON_start = None
TransmitJSON_now = None
TransmitJPG_start = None
TransmitJPG_now = None

# Lists
j_file_names = []
p_file_names = []


# Method for sending JSON files to server
def transmitJSON():
    global j_file_names
    
    try:
        j_file_names.clear()
        service_success = False
        
        print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : " + "TransmitJSON" + " : " +
              "Checking for new JSON files...")
        logger.info(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : " + "TransmitJSON" + " : " +
                    "Checking for new JSON files...")
            
        for r, d, f in os.walk(JSONDirectoryNew):
            for files in f:
                j_file_names.append(os.path.join(r, files))
        
        if len(j_file_names) > 0:
            print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : " + "TransmitJSON" + " : " +
                  str(len(j_file_names)) + " JSON files found...")
            logger.info(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : " + "TransmitJSON" + " : " +
                        str(len(j_file_names)) + " JSON files found...")
            
            for f in j_file_names:
                with open(f, "r") as filescontent:
                    temp = filescontent.readlines()
                    # Call web service
                    service_success = True
                    if service_success:
                        print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : " + "TransmitJSON" +
                              " : " + "File send with name: " + f)
                        logger.info(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : " + "TransmitJSON" +
                                    " : " + "File send with name: " + f)
                        
                        shutil.move(f, JSONDirectoryOld)
                        print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : " + "TransmitJSON" +
                              " : " + "File moved with name: " + f)
                        logger.info(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : " + "TransmitJSON" +
                                    " : " + "File moved with name: " + f)
                        
                        service_success = False
                        
        else:
            print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : " + "TransmitJSON" + " : " +
                  "No JSON files found...")
            logger.info(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : " + "TransmitJSON" + " : " +
                        "No JSON files found...")
        
    except Exception as transmitjsonerror:    
        print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : ERROR : " + "TransmitJSON" + " : " +
              str(transmitjsonerror))
        logger.info(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : ERROR : " + "TransmitJSON" + " : " +
                    str(transmitjsonerror))

    finally:
        pass


# Method for sending picture files to server
def transmitJPG():
    global p_file_names
    
    try:
        p_file_names.clear()
        service_success = False
        
        print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : " + "transmitJPG" + " : " +
              "Checking for new picture files...")
        logger.info(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : " + "transmitJPG" + " : " +
                    "Checking for new picture files...")
            
        for r, d, f in os.walk(PictureDirectoryNew):
            for files in f:
                p_file_names.append(os.path.join(r, files))
        
        if len(p_file_names) > 0:
            print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : " + "transmitJPG" + " : " +
                  str(len(p_file_names)) + " Picture files found...")
            logger.info(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : " + "transmitJPG" + " : " +
                        str(len(p_file_names)) + " Picture files found...")
            
            for f in p_file_names:
                # Call web service
                service_success = True
                if service_success:
                    print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : " + "transmitJPG" +
                          " : " + "File send with name: " + f)
                    logger.info(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : " + "transmitJPG" +
                                " : " + "File send with name: " + f)
                    
                    shutil.move(f, PictureDirectoryOld)
                    print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : " + "transmitJPG" +
                          " : " + "File moved with name: " + f)
                    logger.info(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : " + "transmitJPG" +
                                " : " + "File moved with name: " + f)
                    
                    service_success = False
                        
        else:
            print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : " + "transmitJPG" + " : " +
                  "No Picture files found...")
            logger.info(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : " + "transmitJPG" + " : " +
                        "No Picture files found...")
        
    except Exception as transmitpicerror:    
        print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : ERROR : " + "transmitJPG" + " : " +
              str(transmitpicerror))
        logger.info(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : ERROR : " + "transmitJPG" + " : " +
                    str(transmitpicerror))

    finally:
        pass


# Main
try:
    print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : " + "Main" + " : " + "Program started")
    logger.info(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : " + "Main" + " : " + "Program started")

    while True:
        if TransmitJSON_start is None:
            TransmitJSON_start = time.time()
        if TransmitJPG_start is None:
            TransmitJPG_start = time.time()
            
        TransmitJSON_now = time.time()
        TransmitJPG_now = time.time()
        
        if TransmitJSON_now - TransmitJSON_start > 2:
            print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : " + "Main" + " : " +
                  "Checking for JSON files to send to server!!")
            transmitJSON()
            transmitJSON_start = None
            time.sleep(1)
        
        if TransmitJPG_now - TransmitJPG_start > 2:
            print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : " + "Main" + " : " +
                  "Checking for Picture files to send to server!!")
            transmitJPG()
            transmitJPG_start = None
            time.sleep(1)
        
        time.sleep(2)
            
except Exception as mainError:
    print(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : ERROR : " + "Main" + " : " + str(mainError))
    logger.info(Node_Name + " : " + time.strftime("%d-%m-%Y %H:%M:%S") + " : ERROR : " + "Main" + " : " +
                str(mainError))

finally:
    pass
