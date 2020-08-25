# -*- coding: utf-8 -*-
"""
Created on Mon, March 23 13:13:13 2020
@author: Ahmad H. Mirza
scriptVersion = 1.0..0
"""
import os

"""
Directory Names
"""
DATABASE_DIR_NAME       = "Database"
WORKSPACE_DIR_NAME      = "Workspaces"
USER_UPLOADS_DIR_NAME   = "User_Uploads"
USER_FILES_DIR_NAME     = "User_Files"
USER_TF_DIR_NAME        = "tensorflow"
#obsolete:
USER_DOWNLOADS_DIR_NAME = "User_Downloads"
ASSETS_DIR_NAME         = "Assets"

USER_UPLOADS_IMAGES_DIR = "images"
USER_UPLOADS_ZIP_DIR    = "archives"
USER_UPLOADS_ARXML_DIR  = "arxml"
USER_UPLOADS_JSON_DIR   = "json"
USER_UPLOADS_XLSX_DIR   = "xlsx"  
USER_UPLOADS_A2L_DIR    = "a2l"
USER_UPLOADS_TEXT_DIR   = "text" 
  
#Directories under DATABASE directory:
TMP_DIR_NAME                    = "tmp"
API_DB_JSON_FILENAME            = "API_Keys_db.json"
REQUESTS_HISTORY_JSON_FILENAME  = "Requests_History.json"
FILES_ON_SERVER_FILENAME        = "Files_on_Server.json"
WORKFLOW_TEMPLATE_FILENAME      = "workflow_template.zip"

"""
Paths
"""
#get the path to the current script:
#This will facilitate in geting the rest of the path programatically.
SCRIPT_PATH = os.path.dirname(__file__)

DB_DIR          = os.path.join(SCRIPT_PATH,DATABASE_DIR_NAME)
WORKSPACE_DIR   = os.path.join(DB_DIR,WORKSPACE_DIR_NAME)

#obsolete
USER_UPLOADS    = os.path.join(DB_DIR,USER_UPLOADS_DIR_NAME)
USER_DOWNLOADS  = os.path.join(DB_DIR,USER_DOWNLOADS_DIR_NAME)
ASSETS = os.path.join(DB_DIR,ASSETS_DIR_NAME)

#Directories wehre files uploaded by the customer are stored
UPLOAD_A2L_PATH     = os.path.join(USER_UPLOADS,USER_UPLOADS_A2L_DIR)
UPLOAD_ZIP_PATH     = os.path.join(USER_UPLOADS,USER_UPLOADS_ZIP_DIR)
UPLOAD_ARXML_PATH   = os.path.join(USER_UPLOADS,USER_UPLOADS_ARXML_DIR)
UPLOAD_IMG_PATH     = os.path.join(USER_UPLOADS,USER_UPLOADS_IMAGES_DIR)
UPLOAD_JSON_PATH    = os.path.join(USER_UPLOADS,USER_UPLOADS_JSON_DIR)
UPLOAD_TXT_PATH     = os.path.join(USER_UPLOADS,USER_UPLOADS_TEXT_DIR)
UPLOAD_XSLX_PATH    = os.path.join(USER_UPLOADS,USER_UPLOADS_XLSX_DIR)
############################################################
API_DB_JSON             = os.path.join(DB_DIR,API_DB_JSON_FILENAME)
REQUESTS_HISTORY_JSON   = os.path.join(DB_DIR,REQUESTS_HISTORY_JSON_FILENAME)
FILES_ON_SERVER_JSON    = os.path.join(DB_DIR,FILES_ON_SERVER_FILENAME)
WORKFLOW_TEMPLATE_ZIP   = os.path.join(ASSETS,WORKFLOW_TEMPLATE_FILENAME)
#Directories for security certificates for HTTPs implementation
#SSL_CERTIFICATE     = CERT_DIR+ "/cert.pem"
#SSL_KEY             = CERT_DIR + "/key.pem"
############################################################

SUPPORTED_EXTENSIONS_UPLOAD=[  "JPEG","JPG","PNG",         #Images
                                "ZIP","JSON","ARXML",       #Docs
                                "XLS","XLSX",               #Excel
                                "A2L",
                                "TXT",".C"]

MAX_UPLOAD_FILE_SIZE = 10*1024*1024   #10MB

"""
Hard coded message strings go here.
"""
SERVER_ERROR_CODE = 500
SERVER_ERROR_STRING = "The cookie monster is loose at out HQ and we are trying to get him under control, please give us a moment and try again later."


"""
Tool Paths
"""
PYTHON_PATH         =r"C:/toolbase/python/3.6.6.2.2/python-3.6.6.amd64/python.exe"
JAVA_PATH           =r"c:/toolbase/java_jre/1.8.0_141_64/bin"

"""
***Services***
Base Directory for the tool should always be in the "static"
folder within the service componenet(blueprint module)
"""
UML_GEN_SERVICE     ="/PlantUML/plantuml.jar"
CAN_CONFIG_TEST = "/CanConfigTest/CAN_config_validation_tool.py"