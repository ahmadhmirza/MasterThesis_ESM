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
from flask import make_response,Blueprint, url_for
from flask import request,render_template,send_from_directory
from datetime import datetime
import subprocess,os,shutil
import uuid
import json
###############################################################################

imgIntegration_bp = Blueprint('imgIntegration_bp', __name__,
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
ASSET_PATH = os.path.join(STATIC_PATH,"assets")
IMG1 = os.path.join(ASSET_PATH,"1.jpg")
IMG2 = os.path.join(ASSET_PATH,"2.png")
IMG3 = os.path.join(ASSET_PATH,"3.jpg")
IMG4 = os.path.join(ASSET_PATH,"error.png")

# Storage directory for uploaded files.
DB_PATH             = CONSTANTS.DB_DIR

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
@imgIntegration_bp.route("/showImages")
def imageIntegration():
    # declare as global to update the original variable.
    global REQUEST_ID 
    # generate a new id for each request.
    REQUEST_ID = str(uuid.uuid4())
    accessID = getAccessId()
    return render_template('ImageIntegration.html',
                img1 =  url_for("imgIntegration_bp.getImage",imageID=1),
                img2 = url_for("imgIntegration_bp.getImage",imageID=2),
                img3 = url_for("imgIntegration_bp.getImage",imageID=3),
                )

@imgIntegration_bp.route("/showImages/<imageID>")
def getImage(imageID):
    print(imageID)
    if imageID == "1":
        fileName = "1.jpg"

    elif imageID =="2":
        fileName = "2.png"

    elif imageID =="3":
        fileName = "3.jpg"

    else: 
        fileName = "error.png"

    print(fileName)
    return send_from_directory(ASSET_PATH, filename=fileName)

