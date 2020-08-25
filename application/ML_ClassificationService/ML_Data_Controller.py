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
from . import ML_constants as MLC

#Imports from ML_CONSTANTS config file
userWorkflows           = MLC.USER_WORKFLOWS_PATH
wf_baseModel_dir        = MLC.USR_WRKFLOW_PRE_TR_MODEL_DIR # workflow basemodel directory
wf_tmp_dir              = MLC.USR_WRKFLOW_TMP_DIR
wf_dataset_dir          = MLC.USR_WRKFLOW_DATASET_DIR
wf_annotations_dir      = MLC.USR_WRKFLOW_ANNOTATIONS_DIR
wf_preprocessing_dir    = MLC.USR_WRKFLOW_SCRIPTS_DIR
wf_trainedInfGraph_dir  = MLC.USR_WRKFLOW_INF_GRAPH_DIR
wf_training_dir         = MLC.USR_WRKFLOW_TRAINING_OP_DIR
def getUserTF_workflow(accessID, workflowID):
    tf_workspace = os.path.join(userWorkflows,accessID)
    requested_dir = os.path.join(tf_workspace,workflowID)
    return requested_dir

def getBaseModelDirectory(accessID,workflowID):
    tf_workflow = getUserTF_workflow(accessID,workflowID)
    requested_dir = os.path.join(tf_workflow,wf_baseModel_dir)
    return requested_dir

def getUserTF_tmp_dir(accessID, workflowID):
    workflow_dir = getUserTF_workflow(accessID, workflowID)
    requested_dir = os.path.join(workflow_dir,wf_tmp_dir)
    return requested_dir

def getDatasetDirectory(accessID, workflowID):
    workflow_dir = getUserTF_workflow(accessID, workflowID)
    requested_dir  = os.path.join(workflow_dir,wf_dataset_dir)
    return requested_dir

def getAnnotationsDirectory(accessID, workflowID):
    workflow_dir = getUserTF_workflow(accessID, workflowID)
    requested_dir  = os.path.join(workflow_dir,wf_annotations_dir)
    return requested_dir

def getPreprocessingDirectory(accessID, workflowID):
    workflow_dir = getUserTF_workflow(accessID, workflowID)
    requested_dir  = os.path.join(workflow_dir,wf_preprocessing_dir)
    return requested_dir

def getTrainedInferenceGraphDirectory(accessID, workflowID):
    workflow_dir = getUserTF_workflow(accessID, workflowID)
    requested_dir  = os.path.join(workflow_dir,wf_trainedInfGraph_dir)
    return requested_dir

def getTrainingDirectory(accessID, workflowID):
    workflow_dir = getUserTF_workflow(accessID, workflowID)
    requested_dir  = os.path.join(workflow_dir,wf_training_dir)
    return requested_dir


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

WORKSPACE_DB_JSON = MLC.USER_WORKFLOWS_DB_JSON
"""
Function to read User profile database
return: dictionary of user profiles / False
"""    
def getWorkSpaceDb():
    try:
        with open(WORKSPACE_DB_JSON,"r") as files_json:
            USER_WORKFLOWS_DB=json.load(files_json)
        return USER_WORKFLOWS_DB
    except Exception as e:
        print(str(e))
        #logger.error(str(e))
        return False  

def saveWorkflowDetails(accessID,workflowID,workflowDetails):
    # read the user database
    USER_WORKFLOWS = getWorkSpaceDb()
    if USER_WORKFLOWS != False: # if read operation successful
        # write the request to history json
        try:
            userworkflow = USER_WORKFLOWS[accessID]
        except: 
            USER_WORKFLOWS[accessID]={}
            userworkflow = USER_WORKFLOWS[accessID]
        userworkflow[workflowID] = workflowDetails
        USER_WORKFLOWS[accessID] =userworkflow
        if writeJson(WORKSPACE_DB_JSON,USER_WORKFLOWS): # write operation successful?
            print("Details of new workflow added to workflows databse.")
            print("-----------------------------------")
            return True
        else:
            print("Error(s) encountered while updating user workflows db")
            return False
    else:
        print("Error(s) encountered in reading USER_WORKFLOWS db.")
        return False

def updateWorkflow(accessID,workflowID,processStatus,processID):
    # read the user database
    USER_WORKFLOWS = getWorkSpaceDb()
    if USER_WORKFLOWS != False: # if read operation successful
        # write the request to history json
        try:
            userWorkspace= USER_WORKFLOWS[accessID]
        except Exception as e:
            print(str(e))
            return False 

        userworkflow = userWorkspace[workflowID]
        userworkflow["process_Status"]  = processStatus
        userworkflow["process_ID"]      = processID

        USER_WORKFLOWS[accessID][workflowID] = userworkflow

        if writeJson(WORKSPACE_DB_JSON,USER_WORKFLOWS): # write operation successful?
            print("Details of new workflow added to workflows databse.")
            print("-----------------------------------")
            return True
        else:
            print("Error(s) encountered while updating user workflows db")
            return False
    else:
        print("Error(s) encountered in reading USER_WORKFLOWS db.")
        return False

#TODO:
def workflowExists(accessID,workflowID):
    return True
    
def getWorkspace(accessID):
    # read the user database
    USER_WORKFLOWS = getWorkSpaceDb()
    try:
        userWorkflow = USER_WORKFLOWS[accessID]
        return userWorkflow
    except:
        print(accessID + "not found in database.")
        return False

"""
function for unit tests.
"""    
def unitTest():
    print("-----------------------------------")
      
#if __name__ == "__main__":
#    unitTest()

