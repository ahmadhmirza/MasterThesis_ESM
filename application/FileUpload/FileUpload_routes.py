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
# This script implements the web-service for uploading a file to the
# server.
# Base path for the service: /hyapi
# Service endpoint: /upload
#############################################################################
from flask import current_app as app
from flask import make_response,Blueprint
from flask import request, abort
from datetime import datetime
from werkzeug.utils import secure_filename
import os
import json
import uuid
import requests
###############################################################################

fileUpload_bp = Blueprint('fileUpload_bp', __name__,
                     template_folder='templates',
                     static_folder='static',
                     url_prefix='/hyapi')

""" 
Initialization of all the necessary paths required for the script to run.
"""
try:
    from application import HyApi_constants as CONSTANTS
    print("INFO: FILEUPLOAD: Imported configuration from package successfully.")
except:
    import HyApi_constants as CONSTANTS
    print("DEBUG: FILEUPLOAD: Running in Safe Mode: Imported alternative configuration.")
    
# Storage directory for uploaded files.
DB_PATH             = CONSTANTS.DB_DIR
WORKSPACE_DIR       = CONSTANTS.WORKSPACE_DIR

UPLOAD_IMG_PATH     = CONSTANTS.USER_UPLOADS_IMAGES_DIR
UPLOAD_ZIP_PATH     = CONSTANTS.USER_UPLOADS_ZIP_DIR
UPLOAD_ARXML_PATH   = CONSTANTS.USER_UPLOADS_ARXML_DIR
UPLOAD_XSLX_PATH    = CONSTANTS.USER_UPLOADS_XLSX_DIR
UPLOAD_JSON_PATH    = CONSTANTS.USER_UPLOADS_JSON_DIR
UPLOAD_A2L_PATH     = CONSTANTS.USER_UPLOADS_A2L_DIR
UPLOAD_TXT_PATH     = CONSTANTS.USER_UPLOADS_TEXT_DIR

SUPPORTED_EXTENSIONS = CONSTANTS.SUPPORTED_EXTENSIONS_UPLOAD
MAX_UPLOAD_FILE_SIZE = CONSTANTS.MAX_UPLOAD_FILE_SIZE
################################ Init Databases ##############################
try:
    from application import Data_Controller as dc 
    print("INFO: FILEUPLOAD: DB Controller initialized successfully.")
except:
    import Data_Controller as dc
    print("DEBUG: FILEUPLOAD: Safe Mode: Imported alternative DBC.")


API_KEY_DB      = dc.getApiKeysFromDb()
REQ_HISTORY     = dc.getRequestHistory()

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
Functions to check if the name of the uplaoded file is correct.
param : file's name
"""
def allowedFileName(fileName):
    if fileName=="":
        print("ERROR: FILEUPLOAD: No filename")
        return False
    if not "." in fileName:
        print("ERROR: FILEUPLOAD: File must have an associated extension")
        return False
    else:
        extension = fileName.rsplit(".",1)[1]
        if extension.upper() in SUPPORTED_EXTENSIONS:
            return True
        else:
            print("ERROR: FILEUPLOAD: Unsupported file type.") 
            return False

"""
Function to verify if the file size of the uploaded file is within the 
allowed threshold. using in-memory streaming
param   : file
return  : boolean    : True/False
""" 
def isAllowedSize(file):
    file.seek(0, os.SEEK_END)
    file_length = file.tell()
    print("Size of recieved file : " + str(file_length))
    if int(file_length) <=  MAX_UPLOAD_FILE_SIZE:
        return True
    else:
        print("ERROR: FILEUPLOAD: File is too large.")
        return False

"""
Function to generate a md5 hash
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
def createRequestDetails(fileName,md5Checksum,mStatus,mResponse,requestID):
    #fName = fileName.rsplit(".",1)[0]
    try:    
        ext = fileName.rsplit(".",1)[1].upper()
    except:
        print("ERROR: FILEUPLOAD: Could not extract file's extension.")
        ext = "-"
    #create a dictionary with details of the uploaded file
    requestDetails = {
        "FileName"      :fileName, 
        "FileType"      :ext,
        "FileID"        :str(fileNameToHash(requestID+getTimeStamp())),
        "RequestID"     :requestID, 
        "MD5"           :md5Checksum,
        "Status"        :mStatus,
        "HttpResponse"  :mResponse,
        "timeStamp"     :getTimeStamp()
        }
    
    if dc.updateHistory(requestDetails,requestID):
        print("INFO: FILEUPLOAD: History log updated.")
    else:
        print("ERROR: FILEUPLOAD: Request could not be added to history log.")
    
    return requestDetails

def createFileDetails(fileID,fileName,accessId):
    try:    
        ext = fileName.rsplit(".",1)[1].upper()
    except:
        print("ERROR: FILEUPLOAD: Could not extract file's extension.")
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
        print("INFO: FILEUPLOAD: History log updated.")
        return True
    else:
        print("ERROR: FILEUPLOAD: Request could not be added to history log.")
        return False
    

"""
Function to generate signature from file and encoding key
"""
import hmac
from hashlib import md5    
def generateSignature(mfile,mEncodingKey):
    h = hmac.new(mEncodingKey.encode(),msg = None,digestmod=md5)
    for chunk in iter(lambda: mfile.read(4096), b""):
       h.update(chunk)
    signature= h.hexdigest()
    return signature
"""
Function to verify signature
"""
def isSignatureAuthentic(mfile,mEncodingKey,mSignature):
    signature= generateSignature(mfile,mEncodingKey)
    print("Server-Signature:")
    print(signature)
    if mSignature == signature:
        return True
    else:
        return False

"""
Function to get the correct path for saving the uploaded file
based on the file type.
"""
def getSavePath(fileName,accessID):
    extension = fileName.rsplit(".",1)[1].upper()

    userUploadsDir  = dc.getUserUploadsDir(accessID)

    if extension in ["JPEG","JPG","PNG"]:
        UPLOAD_IMG_PATH = os.path.join(userUploadsDir,CONSTANTS.USER_UPLOADS_IMAGES_DIR)
        savePath = os.path.join(UPLOAD_IMG_PATH,fileName)
    elif extension in ["ZIP"]:
        UPLOAD_ZIP_PATH = os.path.join(userUploadsDir,CONSTANTS.USER_UPLOADS_ZIP_DIR)
        savePath = os.path.join(UPLOAD_ZIP_PATH,fileName)
    elif extension in ["ARXML"]:
        UPLOAD_ARXML_PATH = os.path.join(userUploadsDir,CONSTANTS.USER_UPLOADS_ARXML_DIR)
        savePath = os.path.join(UPLOAD_ARXML_PATH,fileName)
    elif extension in ["JSON"]:
        UPLOAD_JSON_PATH = os.path.join(userUploadsDir,CONSTANTS.USER_UPLOADS_JSON_DIR)
        savePath = os.path.join(UPLOAD_JSON_PATH,fileName)
    elif extension in ["XLSX","XLS"]:
        UPLOAD_XSLX_PATH = os.path.join(userUploadsDir,CONSTANTS.USER_UPLOADS_XLSX_DIR)
        savePath = os.path.join(UPLOAD_XSLX_PATH,fileName)
    elif extension in ["A2L"]:
        UPLOAD_A2L_PATH = os.path.join(userUploadsDir,CONSTANTS.USER_UPLOADS_A2L_DIR)
        savePath = os.path.join(UPLOAD_A2L_PATH,fileName)
    elif extension in ["TXT",".C"]:
        UPLOAD_TXT_PATH = os.path.join(userUploadsDir,CONSTANTS.USER_UPLOADS_TEXT_DIR)
        savePath = os.path.join(UPLOAD_TXT_PATH,fileName)

    else:
        return False
    return savePath

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
            print("INFO: FILEUPLOAD: Access ID authenticated. Requester identified as: "+ customerDataDict["customer"])
            return True
    else:
        print("ERROR: FILEUPLOAD: Invalid AccessID, request denied.")
        return False

"""
function for handling secureUpload.
param : user - passed internally.
"""
@fileUpload_bp.route('/upload',methods=['POST'])    
def secureUpload():
    # declare as global to update the original variable.
    global REQUEST_ID 
    # generate a new id for each request.
    REQUEST_ID = str(uuid.uuid4())

    # get access-id and signature from the request.
    # if none provided set it to empty string.
    # an error will be raised subsequently.
    try:
        accessID    = request.args.get('access-id')
    except:
        accessID = ""
    try:
        custSignature  = request.args.get('signature')
    except:
        custSignature = ""

    if request.method == 'POST':
        # Check if a file is attached with the request for upload.
        if request.files:
            print("INFO: FILEUPLOAD: " + accessID)
            print("INFO: FILEUPLOAD: File Upload Initiated.")
            if isAccessIdAuthentic(accessID):
                customerDataDict = API_KEY_DB[accessID]
                #get encoding-key used to generate signature
                encodingKey = customerDataDict["encodingKey"]
                try:
                    #get file from the request 
                    rFile = request.files["hyapifile"]
                    rFile_tmp = rFile
                except:
                    print("ERROR: FILEUPLOAD: File could not be extracted from the request")
                    status = "[ERR] Bad request, please check that the file label is correct(hyapifile)"
                    httpCode = 400
                    res = createRequestDetails("N/A","N/A",status,httpCode,REQUEST_ID)  
                    res = make_response(res,httpCode)
                    return res

                #Get a secure filename
                secureFileName = secure_filename(rFile.filename)

                #verify the signature in the request vs the one generated on the server.
                if isSignatureAuthentic(rFile,encodingKey,custSignature):        
                    # Check the filename for inconsistencies
                    if allowedFileName(rFile.filename):
                        #File size check
                        if isAllowedSize(rFile_tmp):
                            #get corresponding path to save the file to.
                            savePath = getSavePath(secureFileName,accessID)
                            rFile.seek(0)
                            print("INFO: FILEUPLOAD: Save path: " + savePath)
                            try:
                                rFile.save(savePath)
                            except:
                                print("ERROR: FILEUPLOAD: Error Saving file to disk")
                                status = "[ERR] Error saving file to disk."
                                httpCode = 500
                                res = createRequestDetails(rFile.filename,"N/A",status,httpCode,REQUEST_ID)  
                                res = make_response(res,httpCode)
                                #abort(500, "Error saving file to disk")
                                return res 
                            print("INFO: FILEUPLOAD: File Saved.")
                            
                            #Generate md5checksum for the saved file.
                            md5Checksum = generateMD5(savePath)
                            #TODO: MOVE TO CONSTANTS SCRIPT
                            status = "File Upload Successful."
                            httpCode = 201
                            res = createRequestDetails(secureFileName,md5Checksum,status,httpCode,REQUEST_ID)
                            fileID = res["FileID"]
                            if createFileDetails(fileID,secureFileName,accessID):
                                res = make_response(res,httpCode)
                                return res
                            else:
                                print("ERROR: FILEUPLOAD: Error while updating db with new file metadata")
                                status = "[ERR] Error saving file to disk."
                                httpCode = 500
                                res["Status"] = status
                                res["HttpResponse"] = httpCode
                                res = make_response(res,httpCode)
                                #abort(500, "Error saving file to disk")
                                return res
                        else:
                            print("ERROR: FILEUPLOAD: File size is larger than the allowed threshold.")
                            status = "[ERR] File size is larger than the allowed threshold: " + str(CONSTANTS.MAX_UPLOAD_FILE_SIZE) + " bytes"
                            httpCode = 400
                            res = createRequestDetails(secureFileName,"N/A",status,httpCode,REQUEST_ID)  
                            res = make_response(res,httpCode)
                            return res                
                    else:
                        print("ERROR: FILEUPLOAD: Invalid filename")
                        status = "[ERR] Invalid filename"
                        httpCode = 400
                        res = createRequestDetails(secureFileName,"N/A",status,httpCode,REQUEST_ID)  
                        res = make_response(res,httpCode)
                        #abort(400, "file name associated with the selected file is not allowed.")          
                        return res               
                else:
                    print("ERROR: FILEUPLOAD: Invalid Signature, request denied.")
                    status = "[ERR] Invalid Signature, request denied."
                    httpCode = 403
                    res = createRequestDetails(secureFileName,"N/A",status,httpCode,REQUEST_ID)  
                    res = make_response(res,httpCode)
                    #return res
                    #abort(403, res)
            else:
                print("ERROR: FILEUPLOAD: Invalid Access-ID, request denied.")
                status = "[ERR] Invalid Access-ID, request denied."
                httpCode = 403
                res = createRequestDetails("N/A","N/A",status,httpCode,REQUEST_ID)  
                res = make_response(res,httpCode)
        else:
            print("ERROR: FILEUPLOAD: No/invalid file selected")
            status = "[ERR] No/invalid file selected"
            httpCode = 400
            res = createRequestDetails("N/A","N/A",status,httpCode,REQUEST_ID)  
            res = make_response(res,httpCode)
            #abort(400, "No/invalid file selected")
        return res 
