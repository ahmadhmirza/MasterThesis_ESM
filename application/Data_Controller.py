# -*- coding: utf-8 -*-
"""
Created on Mon, March 30 10:10:10 2020
@author: Ahmad H. Mirza
scriptVersion = 1.0..0
"""

#TODO: Add API Key generation to this script as well.
from flask import current_app as app
import json
from datetime import datetime
import secrets
import os
""" 
Initialization of all the necessary paths required for the script to run.
"""
try:
    from application import HyApi_constants as CONSTANTS
    print("Imported configuration from package successfully.")
except:
    import SC_constants as CONSTANTS
    print("Running in Safe Mode: Imported alternative configuration.")

# Storage directory for uploaded files.
DB_PATH                     = CONSTANTS.DB_DIR
WORKSPACE_DIR               = CONSTANTS.WORKSPACE_DIR
USER_UPLOADS_DIR            = CONSTANTS.USER_UPLOADS_DIR_NAME
USER_FILES_DIR              = CONSTANTS.USER_FILES_DIR_NAME
TEMP_DIR                    = CONSTANTS.TMP_DIR_NAME
USER_TF_DIR                 = CONSTANTS.USER_TF_DIR_NAME

API_KEY_DB_json             = CONSTANTS.API_DB_JSON
REQUESTS_HISTORY_JSON       = CONSTANTS.REQUESTS_HISTORY_JSON
FILES_ON_SERVER_JSON        = CONSTANTS.FILES_ON_SERVER_JSON

BYTESIZE = 16 # for generating Api Key string using secrets module
####################################################################

def writeJson(filePath,pyDictionary):
    try:
        with open(filePath,"w") as outFile:
            json.dump(pyDictionary, outFile, indent=4)
        return True
    except Exception as e:
        print(str(e))
        return False
    
def getTimeStamp():
    return datetime.now().strftime(("%Y-%m-%d %H:%M:%S"))

"""
Function to generate a md5 hash
param 	: file name : String
return 	: Hash value in Hex
"""
import hashlib
def generateHash(stringToHash):   
    hashName = hashlib.md5(stringToHash.encode())
    return hashName.hexdigest()

"""
Function to generate signature from file and encoding key
"""
import hmac
from hashlib import md5    
def generateSignature(apiKey,encodingKey):
     #h = hashlib.md5()
    h = hmac.new(encodingKey.encode(),msg = None,digestmod=md5)
    h.update(apiKey.encode())
    signature= h.hexdigest()
    return signature


"""
To generate the API-key
Uses use-name and the APP's secret key to generate the API-Key
"""
def encryptWithSecretKey(StringToEncrypt):
    secretKey = app.config['SECRET_KEY']
    #apiKey = secrets.token_hex(BYTESIZE)  # old way to generate api key
    h = hmac.new(secretKey.encode(),msg = None,digestmod=md5)
    h.update(StringToEncrypt.encode())
    apiKey= h.hexdigest()
    return apiKey

"""
Function to read API-Keys Database 
return: dictionary of the json file / False
"""
def getApiKeysFromDb():
    API_KEY_DB={}
    try:
        with open(API_KEY_DB_json,"r") as apiDb_jsonFile:
            API_KEY_DB=json.load(apiDb_jsonFile)
        return API_KEY_DB
    except Exception as e:
        print(str(e))
        return False
        #logger.error(str(e))
"""
Generate and add a new API key to the database.
Next step should be to add the user profile data to the
relevant db
param : json object containing user's data
return
"""   
def addNewApiKey(newUserData):
    #Read the DB containing API_Keys
    API_KEY_DB = getApiKeysFromDb()
    print(API_KEY_DB)
    if API_KEY_DB != False: #If read operation is successful
        username = str(newUserData["userName"])
        password = str(newUserData["password"])
        print("user name =" + username + " password: "+ password)

        apiKey = encryptWithSecretKey(username)   # generate a new API key
        password = encryptWithSecretKey(password)

        print("user name =" + username + " password: "+ password)
        encodingKey = generateHash(apiKey)
        print("encodingKey: " + encodingKey)
        API_KEY_DB[apiKey] = {      # write new key to the read db
            "customer"	  : newUserData["fullName"],
            "company"     : newUserData["company"],
            "department"  : newUserData["department"],
            "emailAddr"   : newUserData["emailAddr"],
            "userName"    : newUserData["userName"],
            "password"    : password,
            "encodingKey" : encodingKey
            }

        if writeJson(API_KEY_DB_json,API_KEY_DB): # write operation successful?
            print("New API-Key generated successfully!")
            print(apiKey)
            print("-----------------------------------")
            return apiKey
        else:
            print("Error(s) encountered in API-Key generation.")
            return False
    else:
        print("Error(s) encountered in API-Key generation.")
        return False



"""
Function to read User profile database
return: dictionary of user profiles / False
"""    
def getRequestHistory():
    try:
        with open(REQUESTS_HISTORY_JSON,"r") as history_json:
            REQUESTS_HISTORY=json.load(history_json)
        return REQUESTS_HISTORY
    except Exception as e:
        print(str(e))
        #logger.error(str(e))
        return False  
 
"""
Generate and add new user data to the database.
param : requestDetails object , requestID
return: True/false depending on the operation results.
"""         
def updateHistory(requestDetails,requestID):
    # read the user database
    REQUESTS_HISTORY = getRequestHistory()
    if REQUESTS_HISTORY != False: # if read operation successful
        # write the request to history json
        REQUESTS_HISTORY[requestID] = requestDetails
     
        if writeJson(REQUESTS_HISTORY_JSON,REQUESTS_HISTORY): # write operation successful?
            print("Request details added to history file.")
            print("-----------------------------------")
            return True
        else:
            print("Error(s) encountered while updating history with request ID: " + requestID )
            return False
    else:
        print("Error(s) encountered in reading Requests History db.")
        return False
 

"""
Function to read User profile database
return: dictionary of user profiles / False
"""    
def getFilesOnServer():
    try:
        with open(FILES_ON_SERVER_JSON,"r") as files_json:
            FILES_ON_SERVER=json.load(files_json)
        return FILES_ON_SERVER
    except Exception as e:
        print(str(e))
        #logger.error(str(e))
        return False  
 
"""
Generate and add new user data to the database.
param : fileDetails object , requestID
return: True/false depending on the operation results.
"""         
def updateFilesOnServer(fileDetails,fileID):
    # read the user database
    FILES_ON_SERVER = getFilesOnServer()
    if FILES_ON_SERVER != False: # if read operation successful
        # write the request to history json
        FILES_ON_SERVER[fileID] = fileDetails
     
        if writeJson(FILES_ON_SERVER_JSON,FILES_ON_SERVER): # write operation successful?
            print("Details of new file added to file.")
            print("-----------------------------------")
            return True
        else:
            print("Error(s) encountered while updating files details with file ID: " + fileID )
            return False
    else:
        print("Error(s) encountered in reading FILES_ON_SERVER db.")
        return False

"""
This Function translates a given file-ID to its corresponding file-Name
by comparing it in the database.
"""
def translateFileidToFilename(fileID):
    #FILES_ON_SERVER should be fetched again to get the most recent data.
    FILES_ON_SERVER = getFilesOnServer()
    try:
        if fileID in FILES_ON_SERVER:
            print("INFO: DC: Requested file found on server.")
            fileName = FILES_ON_SERVER[fileID]["FileName"]
            return fileName
        else:
            print("INFO: DC: Requested file not found on server.")
            return False
    except Exception as e:
        print("ERROR: DC: "+ str(e))
        return False

def getUserWorkspace(accessID):
    userWorkspace = os.path.join(WORKSPACE_DIR,accessID)
    return userWorkspace

def getUserUploadsDir(accessID):
    userWorkspace   = os.path.join(WORKSPACE_DIR,accessID)
    userUploadsDir  = os.path.join(userWorkspace,USER_UPLOADS_DIR)
    return userUploadsDir

def getImageUploadPath(accessID):
    userWorkspace   = os.path.join(WORKSPACE_DIR,accessID)
    userUploadsDir  = os.path.join(userWorkspace,USER_UPLOADS_DIR)
    imageUploadPath = os.path.join(userUploadsDir,CONSTANTS.USER_UPLOADS_IMAGES_DIR)
    return imageUploadPath

def getImageUploadPath(accessID):
    userWorkspace   = os.path.join(WORKSPACE_DIR,accessID)
    userUploadsDir  = os.path.join(userWorkspace,USER_UPLOADS_DIR)
    imageUploadPath = os.path.join(userUploadsDir,CONSTANTS.USER_UPLOADS_IMAGES_DIR)
    return imageUploadPath
def getArchiveUploadPath(accessID):
    userWorkspace   = os.path.join(WORKSPACE_DIR,accessID)
    userUploadsDir  = os.path.join(userWorkspace,USER_UPLOADS_DIR)
    imageUploadPath = os.path.join(userUploadsDir,CONSTANTS.USER_UPLOADS_ZIP_DIR)
    return imageUploadPath
def getARXMLUploadPath(accessID):
    userWorkspace   = os.path.join(WORKSPACE_DIR,accessID)
    userUploadsDir  = os.path.join(userWorkspace,USER_UPLOADS_DIR)
    imageUploadPath = os.path.join(userUploadsDir,CONSTANTS.USER_UPLOADS_ARXML_DIR)
    return imageUploadPath
def getJSONUploadPath(accessID):
    userWorkspace   = os.path.join(WORKSPACE_DIR,accessID)
    userUploadsDir  = os.path.join(userWorkspace,USER_UPLOADS_DIR)
    imageUploadPath = os.path.join(userUploadsDir,CONSTANTS.USER_UPLOADS_JSON_DIR)
    return imageUploadPath
def getExcelUploadPath(accessID):
    userWorkspace   = os.path.join(WORKSPACE_DIR,accessID)
    userUploadsDir  = os.path.join(userWorkspace,USER_UPLOADS_DIR)
    imageUploadPath = os.path.join(userUploadsDir,CONSTANTS.USER_UPLOADS_XLSX_DIR)
    return imageUploadPath
def getA2lUploadPath(accessID):
    userWorkspace   = os.path.join(WORKSPACE_DIR,accessID)
    userUploadsDir  = os.path.join(userWorkspace,USER_UPLOADS_DIR)
    imageUploadPath = os.path.join(userUploadsDir,CONSTANTS.USER_UPLOADS_A2L_DIR)
    return imageUploadPath
def getTextUploadPath(accessID):
    userWorkspace   = os.path.join(WORKSPACE_DIR,accessID)
    userUploadsDir  = os.path.join(userWorkspace,USER_UPLOADS_DIR)
    imageUploadPath = os.path.join(userUploadsDir,CONSTANTS.USER_UPLOADS_TEXT_DIR)
    return imageUploadPath


def getUserFilesDir(accessID):
    userWorkspace = os.path.join(WORKSPACE_DIR,accessID)
    userFilesDir  = os.path.join(userWorkspace,USER_FILES_DIR)
    return userFilesDir

def getUserTempDir(accessID):
    userWorkspace = os.path.join(WORKSPACE_DIR,accessID)
    userTempDir  = os.path.join(userWorkspace,TEMP_DIR)
    return userTempDir

def getUserTfDir(accessID):
    userWorkspace = os.path.join(WORKSPACE_DIR,accessID)
    userTfDir  = os.path.join(userWorkspace,USER_TF_DIR)
    return userTfDir

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

    if updateFilesOnServer(fileDetails,fileID):
        print("INFO: DC: File details updated.")
        return True
    else:
        print("ERROR: DC: Request could not be added to history log.")
        return False
"""
function for unit tests.
"""    
def unitTest():
    print("-----------------------------------")
      
#if __name__ == "__main__":
#    unitTest()

