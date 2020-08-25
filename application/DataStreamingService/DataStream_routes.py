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
# Service endpoint: /data-stream-gui : Demos data streaming on a simple 
#                                       web-page with a counter
#                   /data-stream-cli   : Streams data from a text file
#                   /data-stream-cli-2 : Streams data from an a2l file
###############################################################################

from flask import current_app as app
from flask import make_response,Blueprint
from flask import request
from flask import Flask, Response
import subprocess,os,shutil
import uuid
import json
import time
from datetime import datetime
###############################################################################

dataStream_bp = Blueprint('dataStream_bp', __name__,
                     template_folder='templates',
                     static_folder='static',
                     url_prefix='/hyapi/service')

""" 
Initialization of all the necessary paths required for the script to run.
"""
REQUEST_ID = str(uuid.uuid4())
""" 
Initialization of all the necessary paths required for the script to run.
"""
try:
    from application import HyApi_constants as CONSTANTS
    print("INFO: GEN_UML: Imported configuration from package successfully.")
except:
    import HyApi_constants as CONSTANTS
    print("DEBUG: GEN_UML: Running in Safe Mode: Imported alternative configuration.")
  
from . import DS_constants as Const
DEMO_TXT_FILE = Const.DEMO_TXT_FILE
DEMO_A2L_FILE = Const.DEMO_A2L_FILE
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

def stream_template(template_name, **context):
    # http://flask.pocoo.org/docs/patterns/streaming/#streaming-from-templates
    app.update_template_context(context)
    t = app.jinja_env.get_template(template_name)
    rv = t.stream(context)
    # uncomment if you don't need immediate reaction
    ##rv.enable_buffering(5)
    return rv

@dataStream_bp.route('/data-stream-gui')
def index():
    def g():
        for i in range(0,10000):
            time.sleep(.1)  # an artificial delay
            yield i
    return Response(stream_template('index.html', data=g()))

@dataStream_bp.route('/data-stream-cli')
def streamTxtFile():
    def generate():
        with open(DEMO_TXT_FILE) as file:
            for i in file:
                time.sleep(.1)  # an artificial delay
                yield i
    return Response(generate(), mimetype='text/csv')

@dataStream_bp.route('/data-stream-cli-2')
def streamA2LFile():
    def generate():
        with open(DEMO_A2L_FILE) as file:
            for i in file:
                time.sleep(.1)  # an artificial delay
                yield i
    return Response(generate(), mimetype='text/csv')