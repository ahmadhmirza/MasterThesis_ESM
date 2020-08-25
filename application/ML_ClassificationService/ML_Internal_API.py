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

############################# Web-Service Tasks ##############################
""" 
Initialization of all the necessary paths required for the script to run.
"""
try:
    from application import HyApi_constants as CONSTANTS
except:
    import HyApi_constants as CONSTANTS

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
except:
    import Data_Controller as dc



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

def trainModel(accessID,workflowID,inputFileID):  
    isInitSuccessful()
    REQUEST_ID = str(uuid.uuid4())
    inputFileName = dc.translateFileidToFilename(inputFileID)
    inputFilePath = dc.getArchiveUploadPath((accessID))
    if inputFileName != False:
        print("INFO: HyAPI_ML_INTERNAL: FileName: "+ inputFileName)
        inputFile = os.path.join(inputFilePath,inputFileName)
    else:
        print("ERROR: HyAPI_ML_INTERNAL: Input image with the given FileID parameter not found")
        return False

    # Get the path to the user's workspace and the specified workflow:
    # STEP-1: EXTRACT THE INPUT ZIP TO THE TEMP DIRECTORY.
    tempDirectory = MLDC.getUserTF_tmp_dir(accessID,workflowID)
    if extractZip(inputFile,tempDirectory):
        print("INFO: HyAPI_ML_INTERNAL: Inputs extracted to temp directory.")
    else:
        print("ERROR: HyAPI_ML_INTERNAL: Error extracting input .zip file to workflow.")
        return False
    
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
            print("INFO: HyAPI_ML_INTERNAL:Files moved successfully")
        else:
            print("ERROR: HyAPI_ML_INTERNAL: Error moving files.")
            return False
    except Exception as e:
        print(str(e))
        return False

    #STEP-3-a: GENERATE UNIFIED CSV FILES FOR TEST AND TRAIN DATA.
    train_csv_path = os.path.join(workflow_Annotations,MLC.USR_OUTPUT_TRAIN_CSV)
    test_csv_path  = os.path.join(workflow_Annotations,MLC.USR_OUTPUT_TEST_CSV)
    try: 
        xml_to_csv.generateCsvFromXml(trainData_final,train_csv_path)
        xml_to_csv.generateCsvFromXml(testData_final,test_csv_path)
        print("INFO: HyAPI_ML_INTERNAL: Dataset XMLs converted to CSV files successfully.")
    except Exception as e:
        print(str(e))
        return False

    #STEP-3-b: GENERATE TF-RECORDS FILES FOR TEST AND TRAIN DATA
    train_records_path = os.path.join(workflow_Annotations,MLC.USR_OUTPUT_TRAIN_RECORD)
    test_records_path  = os.path.join(workflow_Annotations,MLC.USR_OUTPUT_TEST_RECORD)
    try: 
        generate_tfrecord.generateTfRecords(train_records_path,trainData_final,train_csv_path)
        generate_tfrecord.generateTfRecords(test_records_path,testData_final,test_csv_path)
        print("INFO: HyAPI_ML_INTERNAL: TF-Records file generated successfully.")
    except Exception as e:
        print(str(e))
        return False

    #STEP-4: START THE TRAINING JOB
    try:
        containerID = DockerInterface.startModelTraining(REQUEST_ID,userWorkflow)
        if containerID != False:
            print("INFO: HyAPI_ML_INTERNAL: Training process started, Container ID: " + str(containerID))
            status = "Training started."
            if MLDC.updateWorkflow(accessID,workflowID,status,containerID):
                return True
            else:
                print("ERROR: HyAPI_ML_INTERNAL: Error saving workflow details to db.")
                return False
        else:
            print("ERROR: HyAPI_ML_INTERNAL: Error(s) encountered while starting the training job.")
            return False
    except Exception as e:
        print(str(e))
        return False


def createNewWorkflow(accessID,workFlowName,baseModelID):   
    # declare as global to update the original variable.
    global REQUEST_ID 
    # generate a new id for each request.
    REQUEST_ID = str(uuid.uuid4())
    userWorkflows = MLC.USER_WORKFLOWS_PATH
    workflowID = dc.encryptWithSecretKey(workFlowName)
    # STEP-1 Create new workspace.
    try:
        if not os.path.exists("./"+ userWorkflows+"/"+str(accessID)+"/"+str(workflowID)):
            Path("./"+ userWorkflows+"/"+str(accessID)+"/"+str(workflowID)).mkdir(parents=True, exist_ok=True)
        else:
            pass
    except Exception as e:
        print("ERROR: HyAPI_ML_INTERNAL: "+ str(e))
        return False
        
    # STEP-2 Populate workspace with template
    templateFile = MLC.TF_WORKSPACE_TEMPLATE
    #print(templateFile)
    userTfWorkflow = MLDC.getUserTF_workflow(accessID,workflowID)
    #The template will be extracted to the newly created User's Tensoflow workflow directory
    if extractZip(templateFile,userTfWorkflow):
        print("INFO: HyAPI_ML_INTERNAL: New workflow directory clone successful.")
    else:
        print("ERROR: HyAPI_ML_INTERNAL: Error cloning new workflow from template.")
        return False

    #TODO: implement other models
    # STEP-3 Extract selected model in the "pre-trained-model" folder
    if str(baseModelID) == "01":
        baseModel = MLC.MODEL_1_ZIP_PATH
        baseModelName = MLC.MODEL_NAME_1
        usrBaseModelPath = MLDC.getBaseModelDirectory(accessID,workflowID)
        if extractZip(baseModel,usrBaseModelPath):
            print("INFO: HyAPI_ML_INTERNAL: Pre-Trained-Model copied successfully.")
        else:
            print("ERROR: HyAPI_ML_INTERNAL: Error copying pre-trained-model to new workflow.")
            return False
        # STEP-4 create and return response to client
        print("INFO: HyAPI_ML_INTERNAL: New workflow created successfuly.")
        #create workflow details as a dict to add in the json db
        workflowDetails = {
            "workflow_Name"     :workFlowName, 
            "workflow_ID"       :workflowID,
            "process_ID"        :"Never Run",
            "process_Status"    :"Never Run",
            "baseModel"         :baseModelName,
            "dataSet"           :"empty",
            "timeStamp"         :fh.getTimeStamp()
        }
        if MLDC.saveWorkflowDetails(accessID,workflowID,workflowDetails):
            return True
        else:
            print("ERROR: HyAPI_ML_INTERNAL: Error saving workflow details to db.")
            return False
    else:
        print("ERROR: HyAPI_ML_INTERNAL: Wrong parameter for baseModel(acceptable values are 01 & 02)")
        return False

