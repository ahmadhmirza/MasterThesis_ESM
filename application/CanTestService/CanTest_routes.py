# -*- coding: utf-8 -*-
#############################################################################
#                                                                           #
#                            ROBERT BOSCH GMBH                              #
#                                STUTTGART                                  #
#                                                                           #
#              Alle Rechte vorbehalten - All rights reserved                #
#                                                                           #
#############################################################################
#                      ____   ____  _____  ______ __  __                    #
#                     / __ ) / __ \/ ___/ / ____// / / /                    #
#                    / __  |/ / / /\__ \ / /    / /_/ /                     #
#                   / /_/ // /_/ /___/ // /___ / __  /                      #
#                  /_____/ \____//____/ \____//_/ /_/                       #
#                                                                           #
#############################################################################
# This script implements the web-service for performing CAN-Configuration
# test
# Base path for the service: /hyapi/service/
# Service endpoint: /can-config-test
###############################################################################

from flask import current_app as app
from flask import make_response,Blueprint
from flask import request
from datetime import datetime
import subprocess,os,shutil
import uuid
import json
###############################################################################

canTest_bp = Blueprint('canTest_bp', __name__,
                     template_folder='templates',
                     static_folder='static',
                     url_prefix='/hyapi/service')

""" 
Initialization of all the necessary paths required for the script to run.
"""
try:
    from application import HyApi_constants as CONSTANTS
    print("INFO: GEN_UML: Imported configuration from package successfully.")
except:
    import HyApi_constants as CONSTANTS
    print("DEBUG: GEN_UML: Running in Safe Mode: Imported alternative configuration.")
  
  
""" 
Initialization of all the necessary paths required for the script to run.
"""
# Paths specific to the service.
PYTHON_PATH=CONSTANTS.PYTHON_PATH
TOOL_NAME = CONSTANTS.CAN_CONFIG_TEST

SCRIPT_PATH = os.path.dirname(__file__)

STATIC_PATH = os.path.join(os.path.dirname(__file__),"static")
TOOL_DIR    = os.path.join(STATIC_PATH+ "/CanConfigTest/")
TOOL_PATH   = os.path.join(STATIC_PATH+ TOOL_NAME)

OUTPUT_FILE = "\CAN_config_validation.log"
OUTPUT_DIR = os.path.join(STATIC_PATH,"_out/")

# Storage directory for uploaded files.
DB_PATH             = CONSTANTS.DB_DIR
WORKSPACE_DIR       = CONSTANTS.WORKSPACE_DIR
# Storage directories for different file types.
#TODO: Support for uploading zip archives.
UPLOAD_ZIP_PATH     = CONSTANTS.UPLOAD_ZIP_PATH
UPLOAD_XSLX_PATH    = CONSTANTS.UPLOAD_XSLX_PATH
UPLOAD_A2L_PATH     = CONSTANTS.UPLOAD_A2L_PATH


REQUEST_ID = str(uuid.uuid4())

################################ Init Databases ##############################
try:
    from application import Data_Controller as dc 
    print("INFO: CAN_TEST: DB Controller initialized successfully.")
except:
    import Data_Controller as dc
    print("DEBUG: CAN_TEST: Safe Mode: Imported alternative DBC.")


API_KEY_DB      = dc.getApiKeysFromDb()
REQ_HISTORY     = dc.getRequestHistory()
FILES_ON_SERVER = dc.getFilesOnServer()

def isInitSuccessful():
    if API_KEY_DB == False:
        return False
    if REQ_HISTORY == False:
        return False   
    return True
 

"""
Returns timeStamp at the time of function call
"""
def getTimeStamp():
    return datetime.now().strftime(("%Y-%m-%d %H:%M:%S"))

"""
Function to generate an md5 hash
param 	: file name : String
return 	: Hash value in Hex
"""
import hashlib
def fileNameToHash(fileName):   
    hashName = hashlib.md5(fileName.encode())
    return hashName.hexdigest()
    
"""
Function to generate the MD5 hash of the file's contents
param : file name : string
return MD5 hash : string (hex)
"""
def generateMD5(fileName):
    hash_md5 = hashlib.md5()
    with open(fileName, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()
    
"""
Function to create a db entry for the current file upload
writes the entry to the json db defined in the script
return : Boolean - indicating the status of write to json operation
"""
def createRequestDetails(fileName,fileID,md5Checksum,mStatus,mResponse,requestID):
    try:    
        ext = fileName.rsplit(".",1)[1].upper()
    except:
        print("ERROR: CAN_TEST: Could not extract file's extension.")
        ext = "-"
    #create a dictionary with details of the uploaded file
    requestDetails = {
        "FileName"      :fileName, 
        "FileType"      :ext,
        "FileID"        :fileID,
        "RequestID"     :requestID, 
        "MD5"           :md5Checksum,
        "Status"        :mStatus,
        "HttpResponse"  :mResponse,
        "timeStamp"     :getTimeStamp()
        }
    
    if dc.updateHistory(requestDetails,requestID):
        print("INFO: CAN_TEST: History log updated.")
    else:
        print("ERROR: CAN_TEST: Request could not be added to history log.")
    
    return requestDetails

def createFileDetails(fileID,fileName,accessId):
    try:    
        ext = fileName.rsplit(".",1)[1].upper()
    except:
        print("ERROR: CAN_TEST: Could not extract file's extension.")
        ext = "-"

    #create a dictionary with details of the uploaded file
    fileDetails = {
        "FileName"      :fileName, 
        "FileType"      :ext,
        "FileID"        :fileID,
        "Access-id"     :accessId,
        "timeStamp"     :getTimeStamp()
        }

    if dc.updateFilesOnServer(fileDetails,fileID):
        print("INFO: CAN_TEST: History log updated.")
        return True
    else:
        print("ERROR: CAN_TEST: Request could not be added to history log.")
        return False
"""
Function to move files between directories
"""
def moveFile(fileName,destDir):
    try:
        destDir.encode('unicode_escape')
        shutil.move(fileName, destDir)
        return True
    except:
        return False
    
"""
This function renames the generated output file to a hashed value
and moves the file to downloads folder form where it can be served to user.
File is renamed to a generic hashed value to make the process simpler and
avoid unintentional overwriting of generated files.
"""    
def postProcessing(userFilesDir):
    outFile = os.path.join(TOOL_DIR,OUTPUT_FILE)
    newFileName = str(uuid.uuid4()) + ".log"
    try:
        os.rename(outFile,newFileName)
        moveFile(newFileName,userFilesDir)
        md5Checksum = generateMD5(os.path.join(userFilesDir,newFileName))
        return newFileName, md5Checksum
    except Exception as e:
        print("ERROR: CAN_TEST: Post Processing of the results Failed")
        print(str(e))
        return False,False
    

"""
apikeyInfoFunc
authenticates the apiKey passed in the request.
Passes user value directly to the function configured with the endpoint.
param : accessID : apiKey
returns: user corresponding to the apiKey.
""" 
def isAccessIdAuthentic(accessID):
    API_KEY_DB = dc.getApiKeysFromDb()
    if API_KEY_DB != False:
        if accessID in API_KEY_DB.keys():
            customerDataDict = API_KEY_DB[accessID]
            print("INFO: CAN_TEST: Access ID authenticated. Requester identified as: "+ customerDataDict["customer"])
            return True
    else:
        print("ERROR: CAN_TEST: Invalid AccessID, request denied.")
        return False

def getAccessId():
    # get access-id and signature from the request.
    # if none provided set it to empty string.
    # an error will be raised subsequently.
    try:
        accessID    = request.args.get('access-id')
        print("INFO: CAN_TEST: Access-id received: " + str(accessID))
    except:
        accessID = ""
        print("ERROR: CAN_TEST: Access-id not available in the request.")

    return accessID

"""
END_POINT : /service/generateUml
Use-Case : Customer uploads the files seperatly and provides the 
uploaded-file's IDs

This Function gets the files from the provided file-ids and runs the
UML Diagram Generation servicet employing PlantUML at back end.

The generated file is moved to the downloads folder in the database.

A file id is provided in the http response which can be used to download the 
generated file .
"""
@canTest_bp.route("/can-config-test",methods =['POST'])
def performCanTest():
    # declare as global to update the original variable.
    global REQUEST_ID 
    # generate a new id for each request.
    REQUEST_ID = str(uuid.uuid4())
    accessID = getAccessId()
    if isAccessIdAuthentic(accessID):
#########Get the File IDs from the request parameters#########
        inputFileID = request.json
        userFilesDir = dc.getUserFilesDir(accessID)
        try:
            #Get the File IDs from the request parameters
            xl_FileID = inputFileID["xlFileID"]
        except Exception as e:
            print("ERROR: CAN_TEST: " + str(e))
            xl_FileID = "x"
        try:
            a2l_FileID = inputFileID["a2lFileID"] 
        except Exception as e:
            print("ERROR: CAN_TEST: " + str(e))
            a2l_FileID = "x"
#########File IDs to FileName translation#########
        fileName = dc.translateFileidToFilename(xl_FileID)
        if fileName != False:
            UPLOAD_XSLX_PATH = dc.getExcelUploadPath(accessID)
            xl_file = os.path.join(UPLOAD_XSLX_PATH,fileName)
            print(xl_file)
        else:
            print("ERROR: CAN_TEST: Excel file with the given FileID parameter not found")
            status = "Excel file with the given FileID parameter not found"
            httpCode = 404
            res = createRequestDetails("404",xl_FileID,"404",status,httpCode,REQUEST_ID)
            return res
        
        fileName = dc.translateFileidToFilename(a2l_FileID)
        if fileName != False:
            UPLOAD_A2L_PATH = dc.getA2lUploadPath(accessID)
            a2l_file = os.path.join(UPLOAD_A2L_PATH,fileName)
            print(a2l_file)
        else:
            print("ERROR: CAN_TEST: a2l file with the given FileID parameter not found")
            status = "a2l file with the given FileID parameter not found"
            httpCode = 404
            res = createRequestDetails("404",a2l_FileID,"404",status,httpCode,REQUEST_ID)   
            return res
        
        # Call the service.
        tool = TOOL_PATH
        #PARAMS = TOOL_PATH+ " "+xl_file+" "+a2l_file
        #cmd = PYTHON_PATH + " " + tool + " " + PARAMS
        
        try:
            #subprocess.Popen(cmd)
            print(TOOL_PATH)
            subprocess.call(['python', tool,TOOL_DIR, xl_file, a2l_file])
        except Exception as e:
            print("ERROR: CAN_TEST: " + str(e))
            status = "Error(s) encountered in executing the service."
            httpCode = 500
            res = createRequestDetails("404","404","404",status,httpCode,REQUEST_ID)
            return res
        
        fileName,md5chkSum = postProcessing(userFilesDir)
        if fileName != False :
            print("INFO: CAN_TEST: Service executed successfully")
            status = "Service executed successfully."
            httpCode = 201
            Generated_fileID = str(fileNameToHash(REQUEST_ID+getTimeStamp()))
            res = createRequestDetails(fileName,Generated_fileID,md5chkSum,status,httpCode,REQUEST_ID)
            if createFileDetails(Generated_fileID,fileName,accessID):
                res = make_response(res,httpCode)
                return res
            else:
                print("ERROR: CAN_TEST: Error Saving results to server")
                status = "[ERR] Error saving file to disk."
                httpCode = 500
                res["Status"] = status
                res["HttpResponse"] = httpCode
                res = make_response(res,httpCode)
                #abort(500, "Error saving file to disk")
                return res
        else:
            status = "Error(s) encountered in post processing the results."
            httpCode = 500
            res = createRequestDetails("404","404","404",status,httpCode,REQUEST_ID)
            return res
    else:
        print("ERROR: CAN_TEST: Invalid Access-ID, request denied.")
        status = "[ERR] Invalid Access-ID, request denied."
        httpCode = 403
        res = createRequestDetails("xxx","xxx","xxx",status,httpCode,REQUEST_ID)  
        res = make_response(res,httpCode)
    return res

