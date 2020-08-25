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
# This script implements the web-service for signing up to the HyAPI 
# services
# Base path for the service: /hyapi/signup
# Service endpoint: /cli  # Sign up from cli using cURL
#                   /     # For web-page
#############################################################################
"""
Created on Mon, March 23 13:13:13 2020
@author: Ahmad H. Mirza
scriptVersion = 1.0..0
"""
from flask import current_app as app
from flask import Blueprint, render_template,url_for
from flask import request,redirect,make_response,abort
import uuid
import os
import json
from pathlib import Path
from threading import Thread
###############################################################################

signup_bp = Blueprint('signup_bp', __name__,
                     template_folder='templates',
                     static_folder='static',
                     url_prefix='/hyapi/signup')
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
# Storage directories for different file types.
UPLOAD_IMG_PATH     = CONSTANTS.UPLOAD_IMG_PATH
UPLOAD_ZIP_PATH     = CONSTANTS.UPLOAD_ZIP_PATH
UPLOAD_ARXML_PATH   = CONSTANTS.UPLOAD_ARXML_PATH
UPLOAD_XSLX_PATH    = CONSTANTS.UPLOAD_XSLX_PATH
UPLOAD_JSON_PATH    = CONSTANTS.UPLOAD_JSON_PATH
UPLOAD_A2L_PATH     = CONSTANTS.UPLOAD_A2L_PATH
UPLOAD_TXT_PATH     = CONSTANTS.UPLOAD_TXT_PATH
# Storage Path for generated files that will be made available to user for download
USER_DOWNLOADS  = CONSTANTS.USER_DOWNLOADS

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
 
##############################################################################

"""
Create a URL route in the application for "/"
Implementation only for web applications
Not implemented at the moment
TODO : implement web app
"""

#try:
#     from application import forms
#     print("INFO: Signup: Imported configuration from package successfully.")
# except:
#     import forms
#     print("DEBUG: Signup: Running in Safe Mode: Imported alternative configuration.")

"""
This function unzips the template of the workspace to the new
workspace. This function in meant to run in a thread.
#TODO: Move paths to the constants configuration file
@param : WorkspaceID: should be the same as the API-key
"""
import zipfile
def prepareWorkSpace(workspaceID):
    path_to_zip_file = CONSTANTS.WORKFLOW_TEMPLATE_ZIP
    try:
        with zipfile.ZipFile(path_to_zip_file, 'r') as zip_ref:
            print("INFO: SIGNUP: Extracting Template to user workspace.")
            directory_to_extract_to=os.path.join(CONSTANTS.DB_DIR, str("Workspaces/"+ workspaceID))
            zip_ref.extractall(directory_to_extract_to)
            print("INFO: SIGNUP: Extraction complete.") 
            return True
    except Exception as e:
        print("INFO: SIGNUP:" + str(e))
        return False 

"""
Function to create a db entry for the current file upload
writes the entry to the json db defined in the script
return : Boolean - indicating the status of write to json operation
"""
def createRequestDetails(mStatus,mResponse,requestID):
    #create a dictionary with details of the uploaded file
    requestDetails = {
        "Service"      :"New User Registration",
        "RequestID"     :requestID, 
        "Status"        :mStatus,
        "HttpResponse"  :mResponse,
        "timeStamp"     :dc.getTimeStamp()
        }
    
    if dc.updateHistory(requestDetails,requestID):
        print("INFO: SIGNUP: History log updated.")
    else:
        print("ERROR: SIGNUP: Request could not be added to history log.")
    return requestDetails

# @signup_bp.route('/',methods=['POST'])
# def signup_WebPage():
#     if isInitSuccessful():
#         signupForm = forms.SignupForm()
#         if request.method == 'POST':
#             if signupForm.validate_on_submit():
#                 print("INFO: Signup: Form Data Validated.")
#                 print("INFO: Signup: new user registration, LastName: " + signupForm.lName.data)
#                 #TODO: Hash the password
#                 #TODO: verification email.
#                 newUserData = {
#                     "fName"       :   signupForm.fName.data,
#                     "lName"       :   signupForm.lName.data,
#                     "fullName"    :   signupForm.fName.data + " " + signupForm.lName.data,
#                     "company"     :   signupForm.company.data,
#                     "department"  :   signupForm.department.data,
#                     "emailAddr"   :   signupForm.emailAddr.data,
#                     "userName"    :   signupForm.userName.data,
#                     "password"    :   signupForm.password.data
#                 }
#                 newUserData = json.dumps(newUserData)

#                 # 1- Generate a new API-key for the user.
#                 genApiKey = dc.addNewApiKey(newUserData)

#                 #2- Create a dedicated workspace for the new user on server.
#                 Path("../"+CONSTANTS.DATABASE_DIR_NAME+"/"+str(genApiKey)).mkdir(parents=True, exist_ok=True)
#                 #2.1 - Unzip template workspace
#                 thread = Thread(target = prepareWorkSpace,args = (genApiKey, ))
#                 thread.start()
#                 #3- Send a confirmation email with details.

#                 #4- Redirect to "Success" URL/workspace
#                 thread.join()
#                 print("INFO: Signup: New workspace prepared successfuly.")
#                 #return redirect(url_for('signup_bp.home'))
#             else:
#                 print("ERROR: Signup: Form data validation failed.")
#         return render_template("form.html",form = signupForm,
#                                 home_addr=url_for("home_bp.home"),
#                                 signin_addr= url_for("home_bp.home"),
#                                 signup_addr= url_for("signup_bp.home")
#                                 )
#     else:
#         welcomeString = "ERROR : INIT FAILED : SignUp "
#         res = make_response(welcomeString,500)
#         return res

"""
Access signup functionality from cli by passing a 
json file will the required fields
"""
@signup_bp.route('/cli',methods=['POST'])
def signup_cli():
    # declare as global to update the original variable.
    global REQUEST_ID 
    # generate a new id for each request.
    REQUEST_ID = str(uuid.uuid4())

    if isInitSuccessful():
        try:
            userData = request.json
        except Exception as e:
            print("ERROR: Signup: " + str(e))
            status = "[ERR] Bad request, json file not found in request"
            httpCode = 400
            res = createRequestDetails(status,httpCode,REQUEST_ID)
            return res
        if request.method == 'POST':
            #TODO: verification email.
            try:
                newUserData = {
                    "fName"       :   userData["fName"],
                    "lName"       :   userData["lName"],
                    "fullName"    :   userData["fName"] + " " + userData["lName"],
                    "company"     :   userData["company"],
                    "department"  :   userData["department"],
                    "emailAddr"   :   userData["emailAddr"],
                    "userName"    :   userData["userName"],
                    "password"    :   userData["password"]
                }
            except Exception as e:
                print("ERROR: Signup: " + str(e))
                status = "[ERR] Bad request, missing/in-valid data in json file"
                httpCode = 400
                res = createRequestDetails(status,httpCode,REQUEST_ID)
                return res

            # 1- Generate a new API-key for the user.
            try:
                genApiKey = dc.addNewApiKey(newUserData)
            except Exception as e:
                print(str(e))
                abort(500,"ERROR")

            #2- Create a dedicated workspace for the new user on server.
            Path("../"+CONSTANTS.DATABASE_DIR_NAME+"/"+str(genApiKey)).mkdir(parents=True, exist_ok=True)
            #2.1 - Unzip template workspace
            thread = Thread(target = prepareWorkSpace,args = (genApiKey, ))
            thread.start()
            #3- Send a confirmation email with details.

            #4- Redirect to "Success" URL/workspace
            thread.join()
            print("INFO: Signup: New workspace prepared successfuly.")
            print("INFO: Signup: Registration Complete")
            
            status = "Registration process complete,New user's API Key: " + str(genApiKey)
            httpCode = 201
            res = createRequestDetails(status,httpCode,REQUEST_ID)
            return res
            #return redirect(url_for('signup_bp.home'))
    else:
        welcomeString = "ERROR : INIT FAILED : SignUp "
        res = make_response(welcomeString,500)
        return res
################################ END OF SCRIPT ################################ 

