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
"""
Created on Mon Feb 10 10:10:10 2020
@author: Ahmad H. Mirza(PS-EC/ECC) [Mir6si]
--------------------------------------------
Utility script to generate API-Keys 
Also maintain the db in JSON format for 
the list of API-Keys in use.

python util_AccessId_Generator.py <CustomerName> <RequestedAPI-Endpoint>
--------------------------------------------
scriptVersion = 1.0.0
"""
#from flask import make_response,abort
#from flask import request
from datetime import datetime
#import os
import json
import secrets
from optparse import OptionParser
""" 
Initialization of all the necessary paths required for the script to run.
"""
import HyApiConstants as CONSTANTS
apiDB_json = CONSTANTS.API_CALL_HISTORY_DB_JSON

API_KEY_SIZE = 16

"""
Read the API_keys_db to get the existing API-Keys
"""
API_KEY_DB = {}
try:
    with open(apiDB_json,"r") as apiDb_jsonFile:
        API_KEY_DB=json.load(apiDb_jsonFile)
except:
#    with open(apiDB_json,"w") as apiDb_jsonFile:
#        json.dump(API_KEY_DB,apiDb_jsonFile,indent=4)
        API_KEY_DB={}

"""
Function to write a python dictionary to a json file
param   : python dictionary
return  : boolean : status of write operation
"""
def writeJson(pyDict):
    try:
        with open(apiDB_json,"w") as outFile:
            json.dump(pyDict,outFile,indent=4)
        return True
    except:
        return False

"""
Returns timeStamp at the time of function call
"""
def getTimeStamp():
    return datetime.now().strftime(("%Y-%m-%d %H:%M:%S"))

"""
Generates AccessID for a new user
Concatnates two strings -> encodes to byte -> generates Hash.
param : string1, string2 -> recomended CustomerName+EndPoint
return : hash digest
"""
def generateAccessID(string1,string2):
    key = str(string1)+str(string2)
    key_as_byte = str.encode(key)
    hashName = hashlib.md5(key_as_byte)
    return hashName.hexdigest()
"""
Function to generate an Apikey
param: byteSize : INT : size in bytes for the ApiKey
return : HEX string for ApiKey
"""
def generateApiKey(byteSize):    
    apiKey = secrets.token_hex(byteSize)
    return apiKey

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
Main function
"""
def main():
    isHashed="true"
    usage = "usage: %prog arg1<CustomerName> arg2<Api-EndPoint> [options]"
    parser = OptionParser(usage=usage)
    parser.add_option("-e", "--encrypt",dest="isHashed",
                      help="should the API-Key be encrypted", metavar="Boolean",
                      default="true")
 
    (options, args)         = parser.parse_args()
    isHashed          = options.isHashed.lower()


    if len(args) != 2:
        print("Incorrect number of arguments provided!")
    else:
        apiCustomer = str(args[0])
        apiEndPoint = str(args[1])
     
    apiKey = generateApiKey(API_KEY_SIZE)
    accessID = generateAccessID(apiCustomer,apiEndPoint)
    if isHashed == "true" :
        hashed_apiKey = generateHash(apiKey)       
        # Create the DB entry:
        API_KEY_DB[accessID] = {
                "customer"      : apiCustomer,
                "encodingKey"   : hashed_apiKey,
                "authorization" : apiEndPoint,
                "timeStamp"     : getTimeStamp()
                }
    else: 
        API_KEY_DB[accessID] = {
                "customer"      : apiCustomer,
                "encodingKey"   : apiKey,
                "authorization" : apiEndPoint,
                "timeStamp"     : getTimeStamp()
                }
        
    if writeJson(API_KEY_DB):
        print("New Api-Key generated successfully for Service : " + str(apiEndPoint))
        print(API_KEY_DB[accessID])
    else:
        print("Error(s) occured in Api-Key generation.")
        
if __name__ == '__main__':
    main()