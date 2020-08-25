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
def moveFile(fileName,destDir):
    try:
        destDir.encode('unicode_escape')
        shutil.move(fileName, destDir)
        return True
    except:
        return False

def unitTest():
    print("-----------------------------------")
      
#if __name__ == "__main__":
#    unitTest()

