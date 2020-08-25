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
# This script implements the web-service for performing Computation-methods'
# verification and generation. Returns a .zip file with results
# Base path for the service: /hyapi/service/
# Service endpoint: /validate-compu-methods
###############################################################################

from flask import current_app as app
from flask import make_response,Blueprint
from flask import request
from datetime import datetime
import subprocess,os,shutil
import uuid
import json
###############################################################################

compuMethod_bp = Blueprint('compuMethod_bp', __name__,
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
  
from . import CM_constants as CMConst
""" 
Initialization of all the necessary paths required for the script to run.
"""
# Paths specific to the service.
PYTHON_PATH=CONSTANTS.PYTHON_PATH
CM_TOOL = CMConst.CM_TOOL
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
        print("ERROR: CM_Validation: Could not extract file's extension.")
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
        print("INFO: CM_Validation: History log updated.")
    else:
        print("ERROR: CM_Validation: Request could not be added to history log.")
    
    return requestDetails

def createFileDetails(fileID,fileName,accessId):
    try:    
        ext = fileName.rsplit(".",1)[1].upper()
    except:
        print("ERROR: CM_Validation: Could not extract file's extension.")
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
        print("INFO: CM_Validation: History log updated.")
        return True
    else:
        print("ERROR: CM_Validation: Request could not be added to history log.")
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
import os
import zipfile
def createZip(src, ziph):
    try:
        # ziph is zipfile handle
        zipf = zipfile.ZipFile(ziph, 'w', zipfile.ZIP_DEFLATED)
        for root, dirs, files in os.walk(src):
            for file in files:
                zipf.write(os.path.join(src, file))
        zipf.close()
        print("zipped")
        return True
    except Exception as e:
        print(str(e))
        return False

import shutil
def postProcessing(userFilesDir):
    TOOL_DIR = CMConst.TOOL_DIR
    OUT_DIR = CMConst.OUTPUT_DIR
    newFileName = str(uuid.uuid4())

    zippedOutFile = os.path.join(userFilesDir,newFileName)
    print(zippedOutFile)
    try:
        shutil.make_archive(zippedOutFile, 'zip', OUT_DIR)
        newFileName = newFileName + ".zip"
        md5Checksum = generateMD5(zippedOutFile + ".zip")
        return newFileName, md5Checksum
    except Exception as e:
        print("ERROR: CM_Validation: Post Processing of the results Failed")
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
            print("INFO: CM_Validation: Access ID authenticated. Requester identified as: "+ customerDataDict["customer"])
            return True
    else:
        print("ERROR: CM_Validation: Invalid AccessID, request denied.")
        return False

def getAccessId():
    # get access-id and signature from the request.
    # if none provided set it to empty string.
    # an error will be raised subsequently.
    try:
        accessID    = request.args.get('access-id')
        print("INFO: CM_Validation: Access-id received: " + str(accessID))
    except:
        accessID = ""
        print("ERROR: CM_Validation: Access-id not available in the request.")

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
@compuMethod_bp.route("/validate-compu-methods",methods =['POST'])
def validateCompuMethods():
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
            xl_FileID   = inputFileID["xlFileID"]
        except Exception as e:
            print("ERROR: CM_Validation: " + str(e))
            xl_FileID = "x"
        try:
            a2l_FileID = inputFileID["a2lFileID"] 
        except Exception as e:
            print("ERROR: CM_Validation: " + str(e))
            a2l_FileID = "x"
#########File IDs to FileName translation#########
        fileName = dc.translateFileidToFilename(xl_FileID)
        if fileName != False:
            UPLOAD_XSLX_PATH = dc.getExcelUploadPath(accessID)
            xl_file = os.path.join(UPLOAD_XSLX_PATH,fileName)
            print(xl_file)
        else:
            print("ERROR: CM_Validation: Excel file with the given FileID parameter not found")
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
            print("ERROR: CM_Validation: a2l file with the given FileID parameter not found")
            status = "a2l file with the given FileID parameter not found"
            httpCode = 404
            res = createRequestDetails("404",a2l_FileID,"404",status,httpCode,REQUEST_ID)   
            return res
        OUT_DIR     = CMConst.OUTPUT_DIR
        # Call the service.
        tool = CMConst.CLI_INTERFACE
        PARAMS = tool+" "+a2l_file+" "+xl_file+" "+OUT_DIR+" "+OUT_DIR
        #cmd = PYTHON_PATH + " " + tool + " " + PARAMS
        
        try:
            #subprocess.Popen(cmd)
            subprocess.call([tool,a2l_file,xl_file,OUT_DIR,OUT_DIR])
        except Exception as e:
            print("ERROR: CM_Validation: " + str(e))
            status = "Error(s) encountered in executing the service."
            httpCode = 500
            res = createRequestDetails("404","404","404",status,httpCode,REQUEST_ID)
            return res
        
        fileName,md5chkSum = postProcessing(userFilesDir)
        if fileName != False :
            print("INFO: CM_Validation: Service executed successfully")
            status = "Service executed successfully."
            httpCode = 201
            Generated_fileID = str(fileNameToHash(REQUEST_ID+getTimeStamp()))
            res = createRequestDetails(fileName,Generated_fileID,md5chkSum,status,httpCode,REQUEST_ID)
            if createFileDetails(Generated_fileID,fileName,accessID):
                res = make_response(res,httpCode)
                return res
            else:
                print("ERROR: CM_Validation: Error Saving results to server")
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
        print("ERROR: CM_Validation: Invalid Access-ID, request denied.")
        status = "[ERR] Invalid Access-ID, request denied."
        httpCode = 403
        res = createRequestDetails("xxx","xxx","xxx",status,httpCode,REQUEST_ID)  
        res = make_response(res,httpCode)
    return res
    
#if __name__ == '__main__':
#   unitTest()

