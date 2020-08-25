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
from flask import request,render_template
from datetime import datetime
import subprocess,os,shutil
import uuid
import json
from .static.utils import file_handling as fh  
from . import ML_constants as MLC
from . import ML_Data_Controller as MLDC
from . import ML_ObjectDetection as ml_od
from . import ML_Training as ML_Training
from . import DockerInterface
from pathlib import Path
import zipfile

from .static.utils import file_handling as fh 
from .static.utils import generate_tfrecord 
from .static.utils import xml_to_csv

###############################################################################
machineLearning_bp = Blueprint('machineLearning_bp', __name__,
                     template_folder='templates',
                     static_folder='static',
                     url_prefix='/hyapi/service/ML')

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
#output images will initially be generated here before being moved.
OUTPUT_DIR = os.path.join(STATIC_PATH,"_out/")
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
FGB             = MLC.FROZEN_GRAPH_BASE
LMB             = MLC.LABEL_MAPS_BASE

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




"""
END_POINT : /service/process-image"
Use-Case : Customer uploads the files seperatly and provides the 
uploaded-file's IDs

This Function gets the files from the provided file-ids and runs the
ML_Object_Detection.

The generated image with bounding box is moved to the downloads folder in 
the database.

A file id is provided in the http response which can be used to download the 
resulting image.
"""
@machineLearning_bp.route("/process-image",methods =['POST'])
def detectStopSign():
    # declare as global to update the original variable.
    global REQUEST_ID 
    # generate a new id for each request.
    REQUEST_ID = str(uuid.uuid4())
    accessID = getAccessId()
    if fh.isAccessIdAuthentic(accessID):
        #Get the File IDs from the request parameters
        inputFileID = request.json
        #This is the folder in workspace where all the files generated by services shoudl be stored.
        userFilesDir = dc.getUserFilesDir(accessID)
        inputFilePath = dc.getImageUploadPath((accessID))
        try:
            inputFile_ID = inputFileID["InputFileID"]
        except Exception as e:
            print("ERROR: HyAPI_ML: " + str(e))
            inputFile_ID = "x"
        print("INFO: HyAPI_ML: "+ inputFile_ID)
        # File IDs to FileName translation
        inputFileName = dc.translateFileidToFilename(inputFile_ID)
        if inputFileName != False:
            print("INFO: HyAPI_ML FileName on Server: "+ inputFileName)
            inputFile = os.path.join(inputFilePath,inputFileName)
        else:
            print("ERROR: HyAPI_ML: Input image with the given FileID parameter not found")
            status = "Input image with the given FileID parameter not found"
            httpCode = MLC.HTTP_NOT_FOUND
            res = createRequestDetails(inputFile_ID,"N/A",status,httpCode,REQUEST_ID)
            return res

        #procStatus holds the filename
        procStatus = ml_od.detectStopSign(inputFile, FGB, LMB,userFilesDir)
        if procStatus != False:
            outputFileID = str(fh.generateHash(REQUEST_ID+fh.getTimeStamp()))
            status = "Object detection process successful"
            httpCode = MLC.HTTP_CREATED
            res = createRequestDetails(inputFileName,outputFileID,status,httpCode,REQUEST_ID)
            if dc.createFileDetails(outputFileID,procStatus,accessID) :
                print("INFO: HyAPI_ML: Object detection process successful")
                res = make_response(res,httpCode)
                return res    
            else: #Internal server error
                print("ERROR: HyAPI_ML: Error Saving file to server")
                status = "[ERR] Error saving file to disk."
                httpCode = MLC.HTTP_SERVER_ERROR
                res["Status"] = status
                res["HttpResponse"] = httpCode
                res = make_response(res,httpCode)
                #abort(500, "Error saving file to disk")
                return res
    else:
        print("ERROR: HyAPI_ML: Invalid Access-ID, request denied.")
        status = "[ERR] Invalid Access-ID, request denied."
        httpCode = MLC.HTTP_FORBIDDEN
        res = createRequestDetails("N/A","N/A",status,httpCode,REQUEST_ID)  
        res = make_response(res,httpCode)
    return res

def createReqDetails_newWorkflow(wfName,wfID,baseModel,requestID,mStatus,httpCode):
    #create a dictionary with details of the uploaded file
    requestDetails = {
        "WorkFlowName"  :str(wfName),
        "WorkFlowID"    :str(wfID),
        "BaseModel"     :baseModel,
        "RequestID"     :requestID,
        "Status"        :mStatus,
        "HttpResponse"  :httpCode,
        "timeStamp"     :fh.getTimeStamp()
        }
    
    if dc.updateHistory(requestDetails,requestID):
        print("INFO: HyAPI_ML: History log updated.")
    else:
        print("ERROR: HyAPI_ML: Request could not be added to history log.")
    return requestDetails

def extractZip(fileToExtract,directory_to_extract_to):
    try:
        templateFile = MLC.TF_WORKSPACE_TEMPLATE
        with zipfile.ZipFile(fileToExtract, 'r') as zip_ref:
            print("INFO: HyAPI_ML: Extracting file.")
            zip_ref.extractall(directory_to_extract_to)
            print("INFO: HyAPI_ML: Extraction complete.")
        return True
    except Exception as e:
        print("INFO: HyAPI_ML:" + str(e))
        return False

#TODO: CREATE A DB FILE TO HOLD WORKFLOWS INFORMATION
@machineLearning_bp.route("/create-new-workflow",methods =['POST'])
def createNewWorkflow():   
    # declare as global to update the original variable.
    global REQUEST_ID 
    # generate a new id for each request.
    REQUEST_ID = str(uuid.uuid4())
    accessID = getAccessId()
    if fh.isAccessIdAuthentic(accessID):
        #This is the folder in workspace where all the files generated by services shoudl be stored.
        #userTfDir = dc.getUserTfDir(accessID)
        #Get the File IDs from the request parameters
        newWorkFlowDetails = request.json
        #Get the data from the json included in the request.
        try:
            workFlowName = newWorkFlowDetails["WorkflowName"]
            try:
                #TODO: Provision for multiple base models
                #baseModel = newWorkFlowDetails["BaseModel"]
                #baseModelID = baseModel
                baseModel = "01"
                baseModelID = "01"
                # 01,02,03,04
            except Exception as e:
                print("ERROR: HyAPI_ML: " + str(e))
                baseModel = "x"
        except Exception as e:
            print("ERROR: HyAPI_ML: " + str(e))
            workFlowName = "x"
        #######################################################
        if baseModel != "x" and workFlowName !="x":
            userWorkflows = MLC.USER_WORKFLOWS_PATH
            workflowID = dc.encryptWithSecretKey(workFlowName)
            # STEP-1 Create new workspace.
            try:
                if not os.path.exists("./"+ userWorkflows+"/"+str(accessID)+"/"+str(workflowID)):
                    Path("./"+ userWorkflows+"/"+str(accessID)+"/"+str(workflowID)).mkdir(parents=True, exist_ok=True)
                else:
                    pass
            except Exception as e:
                print(str(e))
                status = "Error creating new workflow directory."
                print("ERROR: HyAPI_ML: "+ status)
                httpCode=MLC.HTTP_SERVER_ERROR
                res = createReqDetails_newWorkflow(workFlowName,workflowID,baseModelID,REQUEST_ID,status,httpCode)
                return make_response(res,httpCode)
                
            # STEP-2 Populate workspace with template
            templateFile = MLC.TF_WORKSPACE_TEMPLATE
            #print(templateFile)
            userTfWorkflow = MLDC.getUserTF_workflow(accessID,workflowID)
            #The template will be extracted to the newly created User's Tensoflow workflow directory
            if extractZip(templateFile,userTfWorkflow):
                print("INFO: HyAPI_ML: New workflow directory clone successful.")
            else:
                status = "Error cloning new workflow from template."
                print("ERROR: HyAPI_ML: "+ status)
                httpCode=MLC.HTTP_SERVER_ERROR
                res = createReqDetails_newWorkflow(workFlowName,workflowID,baseModelID,REQUEST_ID,status,httpCode)
                return make_response(res,httpCode)

            # STEP-3 Extract selected model in the "pre-trained-model" folder
            if str(baseModel) == "01":
                baseModel = MLC.MODEL_1_ZIP_PATH
                baseModelName = MLC.MODEL_NAME_1
                usrBaseModelPath = MLDC.getBaseModelDirectory(accessID,workflowID)
                if extractZip(baseModel,usrBaseModelPath):
                    print(usrBaseModelPath)
                    print("INFO: HyAPI_ML: Pre-Trained-Model copied successfully.")
                else:
                    status = "Error copying pre-trained-model to new workflow."
                    print("ERROR: HyAPI_ML: "+ status)
                    httpCode=MLC.HTTP_SERVER_ERROR
                    res = createReqDetails_newWorkflow(workFlowName,workflowID,baseModelID,REQUEST_ID,status,httpCode)
                    return make_response(res,httpCode)

                # STEP-4 create and return response to client
                status = "New workflow created successfuly."
                print("INFO: HyAPI_ML: "+ status)
                httpCode = MLC.HTTP_CREATED
                #create workflow details as a dict to add in the json db
                workflowDetails = {
                    "workflow_Name"     :workFlowName, 
                    "workflow_ID"       :workflowID,
                    "process_ID"        :"Never Run",
                    "process_Status"    :"Never Run",
                    "baseModel"         :baseModelName,
                    "timeStamp"         :fh.getTimeStamp()
                }
                if MLDC.saveWorkflowDetails(accessID,workflowID,workflowDetails):
                    res = createReqDetails_newWorkflow(workFlowName,workflowID,baseModelID,REQUEST_ID,status,httpCode)
                    return make_response(res,httpCode)
                else:
                    status = "Error saving workflow details to db."
                    print("ERROR: HyAPI_ML: "+ status)
                    httpCode=MLC.HTTP_SERVER_ERROR
                    res = createReqDetails_newWorkflow(workFlowName,workflowID,baseModelID,REQUEST_ID,status,httpCode)
                    return make_response(res,httpCode)
            else:
                status = "Wrong parameter for baseModel(acceptable values are 01 & 02)"
                print("ERROR: HyAPI_ML: "+ status)
                httpCode=MLC.HTTP_BAD_REQUEST
                res = createReqDetails_newWorkflow(workFlowName,workflowID,baseModelID,REQUEST_ID,status,httpCode)
                return make_response("Error",400)
        else:
            status = "WorkflowName & BaseModel values are required in input json. One or both are missing in the request."
            print("ERROR: HyAPI_ML: "+ status)
            httpCode=MLC.HTTP_BAD_REQUEST
            res = createReqDetails_newWorkflow("N/A","N/A","N/A",REQUEST_ID,status,httpCode)
            return make_response(res,httpCode)

def createReqDetails_training(wfID,containerID,baseModel,requestID,mStatus,httpCode):
    #create a dictionary with details of the uploaded file
    requestDetails = {
        "WorkFlowID"    :str(wfID),
        "ContainerID"   :containerID,
        "BaseModel"     :baseModel,
        "RequestID"     :requestID,
        "Status"        :mStatus,
        "HttpResponse"  :httpCode,
        "timeStamp"     :fh.getTimeStamp()
        }
    if dc.updateHistory(requestDetails,requestID):
        print("INFO: HyAPI_ML: History log updated.")
    else:
        print("ERROR: HyAPI_ML: Request could not be added to history log.")
    return requestDetails

#TODO: VALID RESPONSES
@machineLearning_bp.route("/train-user-model/<workflowID>/<inputFileID>",methods =['POST'])
def trainModel(workflowID,inputFileID):  
    # declare as global to update the original variable.
    global REQUEST_ID 
    # generate a new id for each request.
    REQUEST_ID = str(uuid.uuid4())
    accessID = getAccessId()
    if fh.isAccessIdAuthentic(accessID):
        InputFileID = inputFileID
        inputFilePath = dc.getArchiveUploadPath((accessID))
        #######################################################
        if workflowID != "" and InputFileID !="":

            print("INFO: HyAPI_ML: "+ InputFileID)
            # File IDs to FileName translation
            inputFileName = dc.translateFileidToFilename(InputFileID)
            if inputFileName != False:
                print("INFO: HyAPI_ML: FileName on Server: "+ inputFileName)
                inputFile = os.path.join(inputFilePath,inputFileName)
            else:
                print("ERROR: HyAPI_ML: Input image with the given FileID parameter not found")
                status = "Input image with the given FileID parameter not found"
                httpCode = MLC.HTTP_NOT_FOUND
                res = createReqDetails_training(workflowID,"NA","NI",REQUEST_ID,status,httpCode)
                return res

            # Get the path to the user's workspace and the specified workflow:
            # STEP-1: EXTRACT THE INPUT ZIP TO THE TEMP DIRECTORY.
            tempDirectory = MLDC.getUserTF_tmp_dir(accessID,workflowID)
            if extractZip(inputFile,tempDirectory):
                print("INFO: HyAPI_ML: Inputs extracted to temp directory.")
            else:
                status = "Error extracting input .zip file to workflow."
                print("ERROR: HyAPI_ML: "+ status)
                httpCode=MLC.HTTP_SERVER_ERROR
                res = createReqDetails_training(workflowID,"NA","NI",REQUEST_ID,status,httpCode)
                return make_response(res,httpCode)
            
            #STEP-2: MOVE THE FILES TO THE RELEVANT DIRECTORIES IN THE WORKFLOW STRUCTURE.
            userWorkflow            = MLDC.getUserTF_workflow(accessID,workflowID)
            workflow_Dataset        = MLDC.getDatasetDirectory(accessID,workflowID)
            workflow_Annotations    = MLDC.getAnnotationsDirectory(accessID,workflowID)
            workflow_Training       = MLDC.getTrainingDirectory(accessID,workflowID)
            try:
                testData_tmp = os.path.join(tempDirectory,MLC.USR_INPUT_TEST_IMAGES_DIR)
                testData_final = os.path.join(workflow_Dataset,MLC.USR_INPUT_TEST_IMAGES_DIR)

                trainData_tmp = os.path.join(tempDirectory,MLC.USR_INPUT_TRAIN_IMAGES_DIR)
                trainData_final = os.path.join(workflow_Dataset,MLC.USR_INPUT_TRAIN_IMAGES_DIR)

                labelMap_tmp = os.path.join(tempDirectory,MLC.USR_INPUT_LABEL_MAP_FILE)
                labelMap_final = os.path.join(workflow_Annotations,MLC.USR_INPUT_LABEL_MAP_FILE)

                pipeline_tmp = os.path.join(tempDirectory,MLC.USR_INPUT_PIPELINE_FILE)
                pipeline_final = os.path.join(workflow_Training,MLC.USR_INPUT_PIPELINE_FILE)
                # (source,destination)

                if fh.moveFile(testData_tmp,testData_final) and fh.moveFile(trainData_tmp,trainData_final) and fh.moveFile(labelMap_tmp,labelMap_final) and fh.moveFile(pipeline_tmp,pipeline_final): 
                    print("INFO: HyAPI_ML:Files moved successfully")
                else:
                    print("INFO: HyAPI_ML: Error moving files.")
                    status = "Error(s) while populating the workflow with new files"
                    httpCode = MLC.HTTP_SERVER_ERROR
                    res = createReqDetails_training(workflowID,"NA","NI",REQUEST_ID,status,httpCode)
                    return make_response(res,httpCode)
            except Exception as e:
                print(str(e))
                status = "Error(s) while populating the workflow with new files"
                httpCode = MLC.HTTP_SERVER_ERROR
                res = createReqDetails_training(workflowID,"NA","NI",REQUEST_ID,status,httpCode)
                return make_response(res,httpCode)

            #STEP-3-a: GENERATE UNIFIED CSV FILES FOR TEST AND TRAIN DATA.
            train_csv_path = os.path.join(workflow_Annotations,MLC.USR_OUTPUT_TRAIN_CSV)
            test_csv_path  = os.path.join(workflow_Annotations,MLC.USR_OUTPUT_TEST_CSV)
            try: 
                xml_to_csv.generateCsvFromXml(trainData_final,train_csv_path)
                xml_to_csv.generateCsvFromXml(testData_final,test_csv_path)
                print("Dataset XMLs converted to CSV files successfully.")
            except Exception as e:
                print(str(e))
                status = "Error(s) while generating annotaion CSV files from the dataset XMLs."
                httpCode = MLC.HTTP_SERVER_ERROR
                res = createReqDetails_training(workflowID,"NA","NI",REQUEST_ID,status,httpCode)
                return make_response(res,httpCode)

            #STEP-3-b: GENERATE TF-RECORDS FILES FOR TEST AND TRAIN DATA
            train_records_path = os.path.join(workflow_Annotations,MLC.USR_OUTPUT_TRAIN_RECORD)
            test_records_path  = os.path.join(workflow_Annotations,MLC.USR_OUTPUT_TEST_RECORD)
            try: 
                generate_tfrecord.generateTfRecords(train_records_path,trainData_final,train_csv_path)
                generate_tfrecord.generateTfRecords(test_records_path,testData_final,test_csv_path)
                print("TF-Records file generated successfully.")
            except Exception as e:
                print(str(e))
                status = "Error(s) occured while generating tf-records file."
                httpCode = MLC.HTTP_SERVER_ERROR
                res = createReqDetails_training(workflowID,"NA","NI",REQUEST_ID,status,httpCode)
                return make_response(res,httpCode)

            #STEP-4: START THE TRAINING JOB
            try:
                containerID = DockerInterface.startModelTraining(REQUEST_ID,userWorkflow)
                if containerID != False:
                    print("Training process started, Container ID: " + str(containerID))
                    status = "Training process started, Model will be available for export once this process finishes."
                    httpCode = MLC.HTTP_CREATED
                    res = createReqDetails_training(workflowID,containerID,"NI",REQUEST_ID,status,httpCode)
                    if MLDC.updateWorkflow(accessID,workflowID,status,containerID):
                        return make_response(res,httpCode)
                    else:
                        status = "Error saving workflow details to db."
                        print("ERROR: HyAPI_ML: "+ status)
                        httpCode=MLC.HTTP_SERVER_ERROR
                        res = createReqDetails_training(workflowID,containerID,"NI",REQUEST_ID,status,httpCode)
                        return make_response(res,httpCode)
                else:
                    status = "Error(s) encountered while starting the training job."
                    print(status)
                    httpCode = MLC.HTTP_SERVER_ERROR
                    res = createReqDetails_training(workflowID,"NA","NI",REQUEST_ID,status,httpCode)
                    return make_response(res,httpCode)
            except Exception as e:
                print(str(e))
                status = "Error(s) encountered while starting the training job."
                httpCode = MLC.HTTP_SERVER_ERROR
                res = createReqDetails_training(workflowID,"NA","NI",REQUEST_ID,status,httpCode)
                return make_response(res,httpCode)
            #test = DockerInterface.checkContainerStatus(containerID)
            #print(str(test))
        #If one of the required parameters in the request are missing.
        else:
            status = "WorkflowName & BaseModel values are required in input json. One or both are missing in the request."
            print("ERROR: HyAPI_ML: "+ status)
            httpCode=MLC.HTTP_BAD_REQUEST
            res = createReqDetails_newWorkflow("N/A","N/A","N/A",REQUEST_ID,status,httpCode)
            return make_response(res,httpCode)
    
@machineLearning_bp.route("/freeze-model",methods =['POST'])
def exportInferenceGraph():
# declare as global to update the original variable.
    global REQUEST_ID 
    # generate a new id for each request.
    REQUEST_ID = str(uuid.uuid4())
    accessID = getAccessId()
    if fh.isAccessIdAuthentic(accessID):
        #This is the folder in workspace where all the files generated by services shoudl be stored.
        #userTfDir = dc.getUserTfDir(accessID)
        #Get the File IDs from the request parameters
        workflowDetails = request.json
        #Get the data from the json included in the request.
        try:
            workflowID = workflowDetails["WorkflowID"]
        except Exception as e:
            print("ERROR: HyAPI_ML: " + str(e))
            workflowID = "x"
        
        #######################################################
        if workflowID != "x":
            userWorkflow = MLDC.getUserTF_workflow(accessID,workflowID)
            try:
                containerID = DockerInterface.exportGraph(REQUEST_ID,userWorkflow)
                if containerID != False:
                    print("export process started, Container ID: " + str(containerID))
                    status = "Export process started. Model will be available once the process finishes."
                    httpCode = MLC.HTTP_CREATED
                    workflowDetails = {
                        "workflow_Name"     :workFlowName, 
                        "workflow_ID"       :workflowID,
                        "process_ID"        :containerID,
                        "process_Status"    :status,
                        "baseModel"         :baseModelName,
                        "timeStamp"         :fh.getTimeStamp()
                        }
                    if MLDC.saveWorkflowDetails(accessID,workflowID,workflowDetails):
                        res = createReqDetails_newWorkflow(workFlowName,workflowID,baseModelID,REQUEST_ID,status,httpCode)
                        return make_response(res,httpCode)
                    else:
                        status = "Error saving workflow details to db."
                        print("ERROR: HyAPI_ML: "+ status)
                        httpCode=MLC.HTTP_SERVER_ERROR
                        res = createReqDetails_newWorkflow(workFlowName,workflowID,baseModelID,REQUEST_ID,status,httpCode)
                        return make_response(res,httpCode)
                else:
                    status = "Error(s) encountered while starting the training job."
                    print(status)
                    httpCode = MLC.HTTP_SERVER_ERROR
                    res = createReqDetails_training(workflowID,"NA","NI",REQUEST_ID,status,httpCode)
                    return make_response(res,httpCode)
            except Exception as e:
                print(str(e))
                status = "Error(s) encountered while starting the export job."
                httpCode = MLC.HTTP_SERVER_ERROR
                res = createReqDetails_training(workflowID,"NA","NI",REQUEST_ID,status,httpCode)
                return make_response(res,httpCode)
                #If one of the required parameters in the request are missing.
        else:
            status = "Bad request: WorkflowID parameter missing in input json."
            print("ERROR: HyAPI_ML: "+ status)
            httpCode=MLC.HTTP_BAD_REQUEST
            res = createReqDetails_training("N/A","N/A","NI",REQUEST_ID,status,httpCode)
            return make_response(res,httpCode)

# This function return the status of a given container based on the containerID parameter.
# The function return a graphical representation of the status i.e. a jpg file.
# To be used in integration in the web app.
@machineLearning_bp.route("/proc-status-graphical/<containerID>",methods =['GET','POST'])
def getTrainingStatus(containerID):  
    assets_dir = MLC.ICON_PATH
    try:
        
        status = DockerInterface.checkContainerStatus(containerID)
        print("Container: "+ containerID + ", Status: " + str(status) )
        httpCode = 200
        #TODO: Move to constants 
        if status == "running":
            print("running")
            fileName = MLC.RUNNING_ICON_FILE
            return send_from_directory(assets_dir, filename=fileName, as_attachment=True)
        else:
            print("exited")
            fileName = MLC.IDLE_ICON_FILE
            return send_from_directory(assets_dir, filename=fileName, as_attachment=True)
    except Exception as e:
        status = str(e)
        print(status)
        httpCode = MLC.HTTP_SERVER_ERROR
        #return make_response(status,httpCode)
        fileName = MLC.NEVER_RUN_ICON_FILE
        return send_from_directory(assets_dir, filename=fileName, as_attachment=True)

# This function return the status of a given container based on the containerID parameter.
# The function return a string for the container's status.
# To be used in integration in the CLI implementations.
@machineLearning_bp.route("/proc-status/<containerID>")
def getTrainingStatusCLI(containerID):  
    try:
        status = DockerInterface.checkContainerStatus(containerID)
        print("Container: "+ containerID + ", Status: " + str(status) )
        res = {
            "ContainerID": containerID,
            "Status": str(status)
        }
        httpCode = MLC.HTTP_OK
        return make_response(res,httpCode)
    except Exception as e:
        status = str(e)
        httpCode = MLC.HTTP_SERVER_ERROR
        return make_response(status,httpCode)

#TODO: Move to UI script
# fucntion to render status page
@machineLearning_bp.route("/proc-status-page/")
def getTrainingStatusPage():  
    try:       
        return render_template('test.html')
    except Exception as e:
        status = str(e)
        httpCode = MLC.HTTP_SERVER_ERROR
        return make_response(status,httpCode)

@machineLearning_bp.route("/get-user-workspace/<accessID>")
def getUserWorkflows(accessID):  
    userWorkflow = MLDC.getWorkspace(accessID)
    return userWorkflow


#TODO: Function to download the exported inference graph