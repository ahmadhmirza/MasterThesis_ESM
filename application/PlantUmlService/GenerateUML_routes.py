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
# This script implements the web-service for generating UML diagrams from 
# text description.
# Base path for the service: /hyapi/service
# Service endpoint: /generate-uml
#############################################################################
from flask import current_app as app
from flask import make_response,Blueprint
from flask import request
from datetime import datetime
import subprocess,os,shutil
import uuid
import json
###############################################################################

plantUml_bp = Blueprint('plantUml_bp', __name__,
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

UML_TOOL_NAME = CONSTANTS.UML_GEN_SERVICE

STATIC_PATH = os.path.join(os.path.dirname(__file__),"static")
TOOL_PATH = os.path.join(STATIC_PATH+ UML_TOOL_NAME)
OUTPUT_DIR = os.path.join(STATIC_PATH,"_out/")

# Storage directory for uploaded files.
DB_PATH             = CONSTANTS.DB_DIR
WORKSPACE_DIR       = CONSTANTS.WORKSPACE_DIR

# These are directory names NOT path strings.
UPLOAD_ZIP_PATH     = CONSTANTS.USER_UPLOADS_ZIP_DIR
UPLOAD_TXT_PATH     = CONSTANTS.USER_UPLOADS_TEXT_DIR


REQUEST_ID = str(uuid.uuid4())

################################ Init Databases ##############################
try:
    from application import Data_Controller as dc 
    print("INFO: GEN_UML: DB Controller initialized successfully.")
except:
    import Data_Controller as dc
    print("DEBUG: GEN_UML: Safe Mode: Imported alternative DBC.")


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
        print("ERROR: GEN_UML: Could not extract file's extension.")
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
        print("INFO: GEN_UML: History log updated.")
    else:
        print("ERROR: GEN_UML: Request could not be added to history log.")
    
    return requestDetails

def createFileDetails(fileID,fileName,accessId):
    try:    
        ext = fileName.rsplit(".",1)[1].upper()
    except:
        print("ERROR: GEN_UML: Could not extract file's extension.")
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
        print("INFO: GEN_UML: History log updated.")
        return True
    else:
        print("ERROR: GEN_UML: Request could not be added to history log.")
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

TO BE NOTED: If cURL is used at customer side, then a desired file name should
be provided at client side with the -o option in cURL to save the file in the
local system with the desired name. 
"""    
def postProcessing(fileName, userFilesDir):
    OUTPUT_FILE_EXTENTION = ".png"
    try:
        fName = fileName.rsplit(".",1)[0]
    except Exception as e:
        print("ERROR: GEN_UML: " + str(e))
        fName = "xxx"
        
    fName = fName + OUTPUT_FILE_EXTENTION
    fName = os.path.join(OUTPUT_DIR,fName)
    newFileName = str(uuid.uuid4()) + OUTPUT_FILE_EXTENTION
    try:
        os.rename(fName,newFileName)
        moveFile(newFileName,userFilesDir)
        md5Checksum = generateMD5(os.path.join(userFilesDir,newFileName))
        return newFileName, md5Checksum
    except Exception as e:
        print("ERROR: GEN_UML: Post Processing of the results Failed!")
        print("ERROR: GEN_UML: " + str(e))
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
            print("INFO: GEN_UML: Access ID authenticated. Requester identified as: "+ customerDataDict["customer"])
            return True
    else:
        print("ERROR: GEN_UML: Invalid AccessID, request denied.")
        return False

def getAccessId():
    # get access-id and signature from the request.
    # if none provided set it to empty string.
    # an error will be raised subsequently.
    try:
        accessID    = request.args.get('access-id')
        print("INFO: GEN_UML: Access-id received: " + str(accessID))
    except:
        accessID = ""
        print("ERROR: GEN_UML: Access-id not available in the request.")

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
@plantUml_bp.route("/generate-uml",methods =['POST'])
def generateUmlDiagram():
    # declare as global to update the original variable.
    global REQUEST_ID 
    # generate a new id for each request.
    REQUEST_ID = str(uuid.uuid4())
    accessID = getAccessId()
    if isAccessIdAuthentic(accessID):
        #Get the File IDs from the request parameters
        inputFileID = request.json
        #This is the folder in workspace where all the files generated by services shoudl be stored.
        userFilesDir = dc.getUserFilesDir(accessID)
        sourceFilePath = dc.getTextUploadPath(accessID)
        try:
            inputFile_ID = inputFileID["InputFileID"]
        except Exception as e:
            print("ERROR: GEN_UML: " + str(e))
            inputFile_ID = "x"
        print("INFO_GEN_UML: "+ inputFile_ID)
        # File IDs to FileName translation
        sourceFileName = dc.translateFileidToFilename(inputFile_ID)
        print("INFO_GEN_UML: FileName on Server: "+ sourceFileName)
        if sourceFileName != False:
            sourcefile = os.path.join(sourceFilePath,sourceFileName)
        else:
            print("ERROR: GEN_UML: Configuration(source code) with the given FileID parameter not found")
            status = "Configuration(source code) with the given FileID parameter not found"
            httpCode = 404
            res = createRequestDetails("N/A",inputFile_ID,"N/A",status,httpCode,REQUEST_ID)
            return res
        
        # Call the service.
        tool = TOOL_PATH
        # the cmd script takes in two parameters Input .TXT file and the path to 
        # the output directory which in this case is the "USER FILES DIRECTORY"
        #PARAMS = sourcefile + " " + OUTPUT_DIR
        #cmd = tool + " " + PARAMS
        try:
            subprocess.call(['java', '-jar', tool,sourcefile,"-o", OUTPUT_DIR])
        except Exception as e:
            print("ERROR: GEN_UML: " + str(e))
            status = "Error(s) encountered in executing the service."
            httpCode = 500
            res = createRequestDetails("N/A",inputFile_ID,"N/A",status,httpCode,REQUEST_ID)
            return res
        
        #processing on generate file
        #Plant uml names the generated file the same as input source file.
        fileName,md5chkSum = postProcessing(sourceFileName,userFilesDir)
        if fileName != False :
            print("INFO: GEN_UML: Service executed successfully.")
            status = "UML diagram generated successfully."
            Generated_fileID = str(fileNameToHash(REQUEST_ID+getTimeStamp()))
            httpCode = 201
            res = createRequestDetails(fileName,Generated_fileID,md5chkSum,status,httpCode,REQUEST_ID)
            if createFileDetails(Generated_fileID,fileName,accessID):
                res = make_response(res,httpCode)
                return res
            else:
                print("ERROR: GEN_UML: Error Saving file to server")
                status = "[ERR] Error saving file to disk."
                httpCode = 500
                res["Status"] = status
                res["HttpResponse"] = httpCode
                res = make_response(res,httpCode)
                #abort(500, "Error saving file to disk")
                return res
        else:
            print("ERROR: GEN_UML: Error(s) encountered in post processing the results.")
            status = "Error(s) encountered in post processing the results."
            httpCode = 500
            res = createRequestDetails(fileName,inputFile_ID,"N/A",status,httpCode,REQUEST_ID)
            return res
    else:
        print("ERROR: GEN_UML: Invalid Access-ID, request denied.")
        status = "[ERR] Invalid Access-ID, request denied."
        httpCode = 403
        res = createRequestDetails("N/A","N/A","N/A",status,httpCode,REQUEST_ID)  
        res = make_response(res,httpCode)
    return res
    
"""
Only for debugging purposes.
"""
def unitTest():
 print("To be implemented...")
    
#if __name__ == '__main__':
#   unitTest()

