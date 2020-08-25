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
from flask import current_app as app
from flask import make_response,Blueprint,send_from_directory
from flask import request,render_template,url_for,redirect
import subprocess,os,shutil
import uuid
import json
from .static.utils import file_handling as fh
from . import ML_GUI_constants as MLC
from . import ML_GUI_Data_Controller as MLDC_GUI
from . import forms
from pathlib import Path
import zipfile
from werkzeug.utils import secure_filename

###############################################################################
mlGUI_bp = Blueprint('mlGUI_bp', __name__,
                     template_folder='templates',
                     static_folder='static',
                     url_prefix='/hyapi/AI/toolkit')

############################# Web-Service Tasks ##############################
""" 
Initialization of all the necessary paths required for the script to run.
"""
try:
    from application import HyApi_constants as CONSTANTS
    print("INFO: HyAPI_ML: Imported configuration from package successfully.")
except:
    import HyApi_constants as CONSTANTS
    print("DEBUG: HyAPI_ML: Running in Safe Mode: Imported alternative configuration.")

STATIC_PATH = os.path.join(os.path.dirname(__file__),"static")

# Storage directory for uploaded files.
DB_PATH             = CONSTANTS.DB_DIR
WORKSPACE_DIR       = CONSTANTS.WORKSPACE_DIR

# These are directory names NOT path strings.
UPLOAD_ZIP_PATH     = CONSTANTS.USER_UPLOADS_ZIP_DIR
UPLOAD_TXT_PATH     = CONSTANTS.USER_UPLOADS_TEXT_DIR

################################ Init Databases ##############################
try:
    from application import Data_Controller as dc 
    print("INFO: HyAPI_ML: DB Controller initialized successfully.")
except:
    import Data_Controller as dc
    print("DEBUG: HyAPI_ML: Safe Mode: Imported alternative DBC.")


API_KEY_DB      = dc.getApiKeysFromDb()
REQ_HISTORY     = dc.getRequestHistory()
FILES_ON_SERVER = dc.getFilesOnServer()

def isInitSuccessful():
    if API_KEY_DB == False:
        return False
    if REQ_HISTORY == False:
        return False   
    return True

global status_msg
status_msg = ""

"""
Function to create a db entry for the current file upload
writes the entry to the json db defined in the script
return : Boolean - indicating the status of write to json operation
"""
def createRequestDetails(inFileID,outFileID,mStatus,mResponse,requestID):
    #create a dictionary with details of the uploaded file
    requestDetails = {
        "In_FileName"   :str(inFileID),
        "Out_FileID"    :str(outFileID),
        "RequestID"     :requestID,
        "Status"        :mStatus,
        "HttpResponse"  :mResponse,
        "timeStamp"     :fh.getTimeStamp()
        }
    
    if dc.updateHistory(requestDetails,requestID):
        print("INFO: HyAPI_ML: History log updated.")
    else:
        print("ERROR: HyAPI_ML: Request could not be added to history log.")
    return requestDetails

def getAccessId():
    # get access-id and signature from the request.
    # if none provided set it to empty string.
    # an error will be raised subsequently.
    try:
        accessID    = request.args.get('access-id')
        print("INFO: HyAPI_ML: Access-id received: " + str(accessID))
    except:
        accessID = ""
        print("ERROR: HyAPI_ML: Access-id not available in the request.")
    return accessID

def isAccessIdAuthentic(accessID):
    API_KEY_DB = dc.getApiKeysFromDb()
    if API_KEY_DB != False:
        if accessID in API_KEY_DB.keys():
            customerDataDict = API_KEY_DB[accessID]
            print("INFO: UTILS: Access ID authenticated. Requester identified as: "+ customerDataDict["customer"])
            return customerDataDict
        else:
            return False
    else:
        print("ERROR: UTILS: Invalid AccessID, request denied.")
        return False

def authenticateCredentials(userName,password):
    accessID = dc.encryptWithSecretKey(userName)
    password = dc.encryptWithSecretKey(password)
    status = isAccessIdAuthentic(accessID)
    if status != False:
        dbPass = status["password"]
        if password==dbPass:
            return 0
        else:
            return 2
    else:
        return 1

def generateAccessToken(userName,password,accessID,encodingKey):
    password = dc.encryptWithSecretKey(password)
    credentials = userName+accessID+password+encodingKey
    accessToken = dc.encryptWithSecretKey(credentials)
    print(credentials)
    return accessToken

def isAccessTokenAuthentic(accessID,accessToken):
    accountDetails = isAccessIdAuthentic(accessID)
    if accountDetails != False:
        try:
            userName = accountDetails["userName"]
            password = accountDetails["password"]
            encodingKey =accountDetails["encodingKey"]

            credentials = userName+accessID+password+encodingKey
            internal_accessToken = dc.encryptWithSecretKey(credentials)
        except Exception as e:
            print(str(e))
            return False
        if internal_accessToken == accessToken :
            return True
        else:
            print(credentials)
            print(accessToken)
            print(internal_accessToken)
            return False


@mlGUI_bp.route("/")
def mainPage():
    trainingServiceURL = url_for("mlGUI_bp.loginPage")
    objectDetectionURL = url_for("mlGUI_bp.loginPage")
    IasURL = url_for("mlGUI_bp.loginPage")
    return render_template("mainpage.html",
                    trainingServiceURL=trainingServiceURL,
                    objectDetectionURL=objectDetectionURL,
                    IasURL = IasURL)

@mlGUI_bp.route("/login",methods=('GET', 'POST'))
def loginPage():  
    loginForm = forms.LoginForm()
    if request.method == 'POST':
        if loginForm.validate_on_submit():
            print("INFO: ML_GUI: Form Data Validated.")
            userName = loginForm.userName.data
            password = loginForm.password.data
            status = authenticateCredentials(userName,password)
            if status == 0:
                print("Username/password combination validated.")
                accessID = dc.encryptWithSecretKey(userName)
                encodingKey = dc.generateHash(accessID)
                accessToken = generateAccessToken(userName,password,accessID,encodingKey)

                workspaces_url = url_for("mlGUI_bp.showWorkSpace",userName=userName,accessID=accessID,accessToken=accessToken)
                
                #workspaces_url = "192.168.0.192:5000" + workspaces_url
                #print(workspaces_url)
                return redirect(workspaces_url)

            elif status == 1:
                print("Invalid username.")
                return render_template('login.html',
                form = loginForm,
                status = "Invalid usename," + userName + " does not exist in database.")
            elif status == 2:
                print("Incorrect password.")
                return render_template('login.html',
                form = loginForm,
                status = "Incorrect password given for user: "+ userName)
    elif request.method == 'GET': 
        return render_template("login.html",
        form = loginForm)
    else:
        return make_response("Invalid http method", 404)

    
from ..ML_ClassificationService import ML_Data_Controller as MLDC
from ..ML_ClassificationService import ML_Internal_API as ml_api

@mlGUI_bp.route("/wokspace/<userName>/<accessID>/<accessToken>")
def showWorkSpace(userName,accessID,accessToken): 
    loginForm = forms.LoginForm()
    workflowForm = forms.newWorkflowForm()
    if fh.isAccessIdAuthentic(accessID):
        encodingKey = dc.generateHash(accessID)
        if isAccessTokenAuthentic(accessID,accessToken):
                userWorkspace = MLDC.getWorkspace(accessID)

                url = url_for("mlGUI_bp.showWorkSpace",userName=userName, accessID=accessID,accessToken=accessToken )

                return render_template('workspace.html',
                userName        = userName,
                apiKey          = accessID,
                encKey          = encodingKey,
                accessToken     = accessToken,
                workflowsList   = userWorkspace,
                workflowUrl     = url,
                status_message  = status_msg,
                form            = workflowForm)
        else:
            print("couldn't login")
            return render_template('login.html',
            form = loginForm,
            status = "login-failed.")


@mlGUI_bp.route("/wokspace/<userName>/<accessID>/<accessToken>/<workflowID>")
def showWorkflow(userName,accessID,accessToken,workflowID): 
    loginForm = forms.LoginForm()
    if fh.isAccessIdAuthentic(accessID):
        encodingKey = dc.generateHash(accessID)
        if isAccessTokenAuthentic(accessID,accessToken):
                userWorkspace = MLDC.getWorkspace(accessID)
                workflow = userWorkspace[workflowID]
                return render_template('workflow.html',
                workflowName    = workflow["workflow_Name"],
                workflowID      = workflow["workflow_ID"],
                baseModel       = workflow["baseModel"],
                processID       = workflow["process_ID"],
                userName        = userName,
                accessID        = accessID,
                accessToken     = accessToken,
                encodingKey     = encodingKey,
                status_message = status_msg
                )
        else:
            print("couldn't login")
            return render_template('login.html',
            form = loginForm,
            status = "Not sure")

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
        if extension.upper() == "ZIP":
            return True
        else:
            print("ERROR: FILEUPLOAD: Unsupported file type.") 
            return False


def errorReturn(msg,userName,accessID,accessToken,workflowID):
    global status_msg
    status_msg = msg
    redirect_url = url_for("mlGUI_bp.showWorkflow",userName=userName,accessID=accessID,accessToken=accessToken,workflowID=workflowID)
    return redirect_url

import shutil
def clearDataset(datasetPath):
    
    testPath = os.path.join(datasetPath,"test")
    trainPath = os.path.join(datasetPath,"train")
    try:
        shutil.rmtree(testPath)
        shutil.rmtree(trainPath)
        return True
    except OSError as e:
        pass

@mlGUI_bp.route("/wokspace/<userName>/<accessID>/<accessToken>/<workflowID>/upload-dataset",methods=['POST'])
def uploadDataset(userName,accessID,accessToken,workflowID):
    global status_msg
    if request.method == 'POST':
        if request.files:
            try:
                #get file from the request 
                dFile = request.files["hyapifile_dataset"]
                aFile = request.files["hyapifile_ann"]
                print("[Debug] Files extracted from the request")
                # Check the filename for inconsistencies
                if allowedFileName(dFile.filename) and allowedFileName(aFile.filename) :
                    #Get a secure filename
                    dSecureFileName = secure_filename(dFile.filename)
                    aSecureFileName = secure_filename(aFile.filename)

                    tempPath = MLDC.getUserTF_tmp_dir(accessID, workflowID)
                    tempDatasetPath = os.path.join(tempPath,dSecureFileName)
                    tempAnnotationsPath = os.path.join(tempPath,aSecureFileName)

                    savePath = MLDC.getDatasetDirectory(accessID,workflowID)
                    clearDataset(savePath)
                    dFile.seek(0)
                    aFile.seek(0)

                    try:
                        dFile.save(tempDatasetPath)
                        if ml_api.extractZip(tempDatasetPath,savePath):
                            try:
                                aFile.save(tempAnnotationsPath)
                                savePath = MLDC.getAnnotationsDirectory(accessID,workflowID)
                                if ml_api.extractZip(tempAnnotationsPath,savePath):
                                    try:
                                        os.remove(tempDatasetPath)
                                        os.remove(tempAnnotationsPath)
                                    except:
                                        pass
                                    status_msg = "Dataset & Annotations uploaded successfully."
                                    return redirect(errorReturn(status_msg, userName, accessID,accessToken, workflowID))
                                else:
                                    status_msg = "[ERR] Error saving file to disk."
                                    return redirect(errorReturn(status_msg, userName, accessID,accessToken, workflowID))
                            except Exception as e:
                                print(str(e))
                                status_msg = str(e)
                                return redirect(errorReturn(status_msg, userName, accessID,accessToken, workflowID))
                        else:
                            status_msg = "[ERR] Error saving file to disk."
                            return redirect(errorReturn(status_msg, userName, accessID,accessToken, workflowID))
                    except Exception as e:
                        print(str(e))
                        status_msg = "[ERR] Error saving file to disk."
                        return redirect(errorReturn(status_msg, userName, accessID,accessToken, workflowID))

                else:
                    return redirect(errorReturn("Bad request, illegal filename!", userName, accessID,accessToken, workflowID))
            except Exception as e:
                print(str(e))
                status_msg = "[ERR] Bad request, please check that the file label is correct(hyapifile)"
                return redirect(errorReturn(status_msg, userName, accessID,accessToken, workflowID))

        else: # no file attached
            status_msg = "Error uploading file."
            return redirect(errorReturn(status_msg, userName, accessID,accessToken, workflowID))

    return True

@mlGUI_bp.route("/wokspace/<userName>/<accessID>/<accessToken>/<workflowID>/start-training/<inputFileID>",methods =['POST'])
def startTraining(userName,accessID,accessToken,workflowID,inputFileID): 
    status = ml_api.trainModel(accessID,workflowID,inputFileID)
    if status == True:
        global status_msg
        status_msg = "Training process started."
        redirect_url = url_for("mlGUI_bp.showWorkflow",userName=userName,accessID=accessID,accessToken=accessToken,workflowID=workflowID)

        return redirect(redirect_url)
    else:
        userWorkspace = MLDC.getWorkspace(accessID)
        workflow = userWorkspace[workflowID]
        return render_template('workflow.html',
            workflowName    = workflow["workflow_Name"],
            workflowID      = workflow["workflow_ID"],
            baseModel       = workflow["baseModel"],
            processID       = workflow["process_ID"],
            accessID        = accessID,
            status_message = "Error"
            )


@mlGUI_bp.route("/wokspace/<userName>/<accessID>/<accessToken>/create-new-workflow",methods =['POST'])
def createNewWorkflow(userName,accessID,accessToken): 
    workflowForm = forms.newWorkflowForm()
    global status_msg
    if request.method == 'POST':
        if workflowForm.validate_on_submit():
            print("INFO: ML_GUI: Form Data Validated.")
            workflowName    = workflowForm.workflowName.data
            baseModel       = workflowForm.baseModel.data
            status = ml_api.createNewWorkflow(accessID,workflowName,baseModel)
            if status == True:
                status_msg = "New workflow created."
                redirect_url = url_for("mlGUI_bp.showWorkSpace",userName=userName, accessID=accessID,accessToken=accessToken )
                return redirect(redirect_url)
            else:
                status_msg = "Error creating new workflow."
                redirect_url = url_for("mlGUI_bp.showWorkSpace",userName=userName, accessID=accessID,accessToken=accessToken )
                return redirect(redirect_url)
    else:
        return make_response("Invalid http method", 404)