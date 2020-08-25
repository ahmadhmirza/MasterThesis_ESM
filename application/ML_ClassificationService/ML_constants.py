# -*- coding: utf-8 -*-
"""
Created on Mon, March 23 13:13:13 2020
@author: Ahmad H. Mirza
scriptVersion = 1.0..0
"""
import os

TENSOR_FLOW_OBJECT_DETECTION_API_DIRECTORY = "/home/ahmad/Desktop/ObjectDetection/tensorflow/models/research/"

STATIC_DIR                  = "static"
ASSETS_DIR                  = "assets"
STATUS_ICON_DIR             = "status_images"
BASE_GRAPH_DIR              = "base_inference_graph"
BASE_FROZEN_GRAPH_FILE_NAME = "frozen_inference_graph.pb"
BASE_LABEL_MAP_FILE_NAME    = "label_map.pbtxt"
OUT_DIR                     = "_out"

#PROGRESS IMAGES NAMES:
RUNNING_ICON_FILE       = "running.png"
IDLE_ICON_FILE          = "idle.png"
NEVER_RUN_ICON_FILE     = "never_run.png"
ERROR_ICON_FILE         = "error.png"
#WORK_FLOW_SPECIFIC_DETAILS:
TF_WORKSPACE_TEMPLATE_FILE      = "tf_workspace_template.zip"
TF_MODELS_DIR                   = "tf_models"
USER_WORKFLOWS_DIR              = "UserWorkflows"
USER_WORKFLOWS_DB_FILE          = "user_workflows_db.json"
#DIRECTORIES INSIDE THE TEMPLATE
USR_WRKFLOW_SCRIPTS_DIR         = "preprocessing"
USR_WRKFLOW_TRAIN_DIR           = "training"
###
USR_WRKFLOW_ANNOTATIONS_DIR     ="annotations"
USR_WRKFLOW_DATASET_DIR         ="dataset"
USR_WRKFLOW_PRE_TR_MODEL_DIR    ="pre-trained-model"
USR_WRKFLOW_INF_GRAPH_DIR       ="trained-inference-graphs"
USR_WRKFLOW_TRAINING_OP_DIR     ="training"
USR_WRKFLOW_TMP_DIR             ="tmp"
## INPUT FILES
USR_INPUT_TEST_IMAGES_DIR       ="test"
USR_INPUT_TRAIN_IMAGES_DIR      ="train"
USR_INPUT_LABEL_MAP_FILE        ="label_map.pbtxt"
USR_INPUT_PIPELINE_FILE         ="pipeline.config"
## OUTPUT_FILES
USR_OUTPUT_TRAIN_CSV            = "train_labels.csv"
USR_OUTPUT_TEST_CSV             = "test_labels.csv"
USR_OUTPUT_TRAIN_RECORD         = "train.record"
USR_OUTPUT_TEST_RECORD          = "test.record"

#get the path to the current script:
#This will facilitate in geting the rest of the path programatically.
SCRIPT_PATH             = os.path.dirname(__file__)
STATIC_PATH             = os.path.join(SCRIPT_PATH,STATIC_DIR)
OUTPUT_DIR              = os.path.join(STATIC_PATH,OUT_DIR)
ASSETS_PATH             = os.path.join(STATIC_PATH,ASSETS_DIR)
ICON_PATH               = os.path.join(ASSETS_PATH,STATUS_ICON_DIR)
USER_WORKFLOWS_PATH     = os.path.join(SCRIPT_PATH,USER_WORKFLOWS_DIR)
USER_WORKFLOWS_DB_JSON  = os.path.join(USER_WORKFLOWS_PATH,USER_WORKFLOWS_DB_FILE)

#Icon assets:
icon_running    = os.path.join(ICON_PATH,RUNNING_ICON_FILE)
icon_idle       = os.path.join(ICON_PATH,IDLE_ICON_FILE)
icon_never_run  = os.path.join(ICON_PATH,NEVER_RUN_ICON_FILE)
icon_error      = os.path.join(ICON_PATH,ERROR_ICON_FILE)

BASE_GRAPH_PATH = os.path.join(ASSETS_PATH,BASE_GRAPH_DIR)
TF_MODEL_PATH   = os.path.join(ASSETS_PATH,TF_MODELS_DIR)
TF_WORKSPACE_TEMPLATE = os.path.join(ASSETS_PATH,TF_WORKSPACE_TEMPLATE_FILE)
# BASE FROZEN_GRAPH
# Base model is trained to identify the stop sign
FROZEN_GRAPH_BASE   = os.path.join(BASE_GRAPH_PATH, BASE_FROZEN_GRAPH_FILE_NAME)
LABEL_MAPS_BASE     = os.path.join(BASE_GRAPH_PATH, BASE_LABEL_MAP_FILE_NAME)
OUTPUT_DIR          = os.path.join(STATIC_PATH,OUT_DIR)

# MODEL DETAILS:
MODEL_NAME_1 = 'ssd_inception_v2_coco.zip'
MODEL_1_ZIP_PATH = os.path.join(TF_MODEL_PATH,MODEL_NAME_1)

# DOCKER CONSTANTS
containerVolume="/datavol"
trainingDockerImage = "ahmadhmirza/train-tf-model:1.0"
exportModelDockerImage = "ahmadhmirza/export-tf-inferencegraph:1.0"

#HTTP_CODES.
HTTP_OK                     = 200
HTTP_CREATED                = 201
HTTP_ACCEPTED               = 202
HTTP_MOVED_PERMANENTLY      = 301
HTTP_BAD_REQUEST            = 400
HTTP_UNAUTHORIZED           = 401
HTTP_PAYMENT_REQUIRED       = 402
HTTP_FORBIDDEN              = 403
HTTP_NOT_FOUND              = 404
HTTP_PAYLOAD_TOO_LARGE      = 413
HTTP_IM_A_TEAPOT            = 418
HTTP_TOO_MANY_REQUESTS      = 429 #Rate limiting
HTTP_SERVER_ERROR           = 500
HTTP_NOT_IMPLEMENTED        = 501
HTTP_SERVICE_UNAVAILABLE    = 503
