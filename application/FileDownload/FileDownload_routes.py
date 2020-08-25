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
# This script implements the web-service for downloading the files from the
# server.
# Base path for the service: /hyapi/download
# Service endpoint:  /<fileID>
#                    /fileStatus/<fileID>
#############################################################################

from flask import current_app as app
from flask import make_response,Blueprint
from flask import request,send_from_directory
from datetime import datetime
import os
import json
import uuid
import hashlib
##############################################################################

fileDownload_bp = Blueprint('fileDownload_bp', __name__,
                     template_folder='templates',
                     static_folder='static',
                     url_prefix='/hyapi/download')

""" 
Initialization of all the necessary paths required for the script to run.
"""
try:
    from application import HyApi_constants as CONSTANTS
    print("INFO: FILEDOWNLOAD: Imported configuration from package successfully.")
except:
    import HyApi_constants as CONSTANTS
    print("DEBUG: FILEDOWNLOAD: Running in Safe Mode: Imported alternative configuration.")
    
# Storage directory for uploaded files.
DB_PATH             = CONSTANTS.DB_DIR
WORKSPACE_DIR       = CONSTANTS.WORKSPACE_DIR
USER_FILES          = CONSTANTS.USER_FILES_DIR_NAME
# Storage directories for different file types.

#TODO : A seperate end-point to download files uploaded by the user 
#       these files are sorted into the directories as below:
# These are directory names NOT path strings.
UPLOAD_IMG_PATH     = CONSTANTS.USER_UPLOADS_IMAGES_DIR
UPLOAD_ZIP_PATH     = CONSTANTS.USER_UPLOADS_ZIP_DIR
UPLOAD_ARXML_PATH   = CONSTANTS.USER_UPLOADS_ARXML_DIR
UPLOAD_XSLX_PATH    = CONSTANTS.USER_UPLOADS_XLSX_DIR
UPLOAD_JSON_PATH    = CONSTANTS.USER_UPLOADS_JSON_DIR
UPLOAD_A2L_PATH     = CONSTANTS.USER_UPLOADS_A2L_DIR
UPLOAD_TXT_PATH     = CONSTANTS.USER_UPLOADS_TEXT_DIR
# Storage Path for generated files that will be made available to user for download
USER_DOWNLOADS  = CONSTANTS.USER_DOWNLOADS
# Configurations
SUPPORTED_EXTENSIONS = CONSTANTS.SUPPORTED_EXTENSIONS_UPLOAD
MAX_UPLOAD_FILE_SIZE = CONSTANTS.MAX_UPLOAD_FILE_SIZE
################################ Init Databases ##############################
try:
    from application import Data_Controller as dc 
    print("INFO: FILEDOWNLOAD: DB Controller initialized successfully.")
except:
    import Data_Controller as dc
    print("DEBUG: FILEDOWNLOAD: Safe Mode: Imported alternative DBC.")


API_KEY_DB      = dc.getApiKeysFromDb()
REQ_HISTORY     = dc.getRequestHistory()
FILES_ON_SERVER = dc.getFilesOnServer()

def isInitSuccessful():
    if API_KEY_DB == False:
        return False
    if REQ_HISTORY == False:
        return False   
    return True
###############################################################################
"""
Returns timeStamp at the time of function call
"""
def getTimeStamp():
    return datetime.now().strftime(("%Y-%m-%d %H:%M:%S"))

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
        print("ERROR: FILEDOWNLOAD: Could not extract file's extension.")
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
        print("INFO: FILEDOWNLOAD: History log updated.")
    else:
        print("ERROR: FILEDOWNLOAD: Request could not be added to history log.")
    
    return requestDetails

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
            print("INFO: FILEDOWNLOAD: Access ID authenticated. Requester identified as: "+ customerDataDict["customer"])
            return True
    else:
        print("ERROR: FILEDOWNLOAD: Invalid AccessID, request denied.")
        return False

def getAccessId():
    # get access-id and signature from the request.
    # if none provided set it to empty string.
    # an error will be raised subsequently.
    try:
        accessID    = request.args.get('access-id')
        print("INFO: FILEDOWNLOAD: Access-id received: " + str(accessID))
    except:
        accessID = ""
        print("ERROR: FILEDOWNLOAD: Access-id not available in the request.")
    return accessID

"""
END-POINT : /checkFileStatus/{fileID}
This function allows customer to check the status of the file on server.
Allowing for a handshake protocol before the file download. 
"""
@fileDownload_bp.route('/fileStatus/<fileID>',methods =['GET','POST'])
def checkFileStatus(fileID):
    # declare as global to update the original variable.
    global REQUEST_ID 
    # generate a new id for each request.
    REQUEST_ID = str(uuid.uuid4())
    accessID = getAccessId()
    if isAccessIdAuthentic(accessID):
        mfileID = fileID
        
        userWorkspace   = os.path.join(WORKSPACE_DIR,accessID)
        userFilesDir  = os.path.join(userWorkspace,USER_FILES)
        
        fileName = dc.translateFileidToFilename(mfileID)
        if fileName != False:
            md5Checksum = generateMD5(os.path.join(userFilesDir,fileName))
            status = "File with the given FileID found on server."
            httpCode = 200
            res = createRequestDetails(fileName,mfileID,md5Checksum,status,httpCode,REQUEST_ID)
            return res
        else:
            print("File with the given FileID parameter not found")
            status = "File with the given FileID parameter not found"
            httpCode = 404
            res = createRequestDetails("N/A",mfileID,"N/A",status,httpCode,REQUEST_ID)   
            return res

    else:
        print("Invalid Access-ID, request denied.")
        status = "[ERR] Invalid Access-ID, request denied."
        httpCode = 403
        res = createRequestDetails("N/A","N/A","N/A",status,httpCode,REQUEST_ID)  
        res = make_response(res,httpCode)
    return res

#TODO: DOWNLOAD capability for uploaded files.
"""
END-POINT : /getFile/{fileID}
function for sending the requested file back to the consumer.
param : user - passed internally.
fileID - For identifying the requested file.
"""
@fileDownload_bp.route('/<fileID>',methods =['GET','POST'])     
def getFile(fileID):
    # declare as global to update the original variable.
    global REQUEST_ID 
    # generate a new id for each request.
    REQUEST_ID = str(uuid.uuid4())
    accessID = getAccessId()
    mfileID = fileID
    if isAccessIdAuthentic(accessID):
        fileName = dc.translateFileidToFilename(mfileID)
        userFilesDir  = dc.getUserFilesDir(accessID)

        print("INFO: FILEDOWNLOAD: Requested File Name: " + str(fileName))
        if fileName != False: 
            try:
                md5Checksum = generateMD5(os.path.join(userFilesDir,fileName))
                print("INFO: FILEDOWNLOAD: File with the given FileID found on server.")
                status = "File with the given FileID found on server."
                httpCode = 200
                res = createRequestDetails(fileName,mfileID,md5Checksum,status,httpCode,REQUEST_ID)
                return send_from_directory(userFilesDir, filename=fileName, as_attachment=True)
            except Exception as e :
                print("ERROR: FILEDOWNLOAD: Error(s) encountered while transferring file.")
                print(str(e))
                status = "Error(s) encountered while transferring file."
                httpCode = 500
                res = createRequestDetails("N/A",mfileID,"N/A",status,httpCode,REQUEST_ID)   
                
        else:
            print("ERROR: FILEDOWNLOAD: File with the given FileID parameter not found")
            status = "File with the given FileID parameter not found"
            httpCode = 404
            res = createRequestDetails("N/A",mfileID,"N/A",status,httpCode,REQUEST_ID)   
                   
    else:
        print("ERROR: FILEDOWNLOAD: Invalid Access-ID, request denied.")
        status = "[ERR] Invalid Access-ID, request denied."
        httpCode = 403
        res = createRequestDetails("N/A","N/A","N/A",status,httpCode,REQUEST_ID)  
        res = make_response(res,httpCode)
    return res
############################ END OF SCRIPT ###################################