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
import os,shutil

try:
    from application import Data_Controller as dc 
    print("INFO: GEN_UML: DB Controller initialized successfully.")
except:
    import Data_Controller as dc
    print("DEBUG: GEN_UML: Safe Mode: Imported alternative DBC.")

def writeJson(filePath,pyDictionary):
    try:
        with open(filePath,"w") as outFile:
            json.dump(pyDictionary, outFile, indent=4)
        return True
    except Exception as e:
        print(str(e))
        return False
    
"""
Returns timeStamp at the time of function call
"""
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
Function to move files between directories
"""
def moveFile(file_path,destDir):
    try:
        destDir.encode('unicode_escape')
        shutil.move(file_path, destDir)
        return True
    except Exception as e:
        print("ERROR:FILE_HANDLER: "+ str(e))
        return False

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
            print("INFO: UTILS: Access ID authenticated. Requester identified as: "+ customerDataDict["customer"])
            return True
        else:
            return False
    else:
        print("ERROR: UTILS: Invalid AccessID, request denied.")
        return False

def unitTest():
    print("-----------------------------------")
      
#if __name__ == "__main__":
#    unitTest()

