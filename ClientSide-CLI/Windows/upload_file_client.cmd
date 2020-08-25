@echo off
rem ###########################################################################
rem #                                                                         #
rem #                            ROBERT BOSCH GMBH                            #
rem #                                STUTTGART                                #
rem #                                                                         #
rem #              Alle Rechte vorbehalten - All rights reserved              #
rem #                                                                         #
rem ###########################################################################
rem #                      ____   ____  _____  ______ __  __                  #
rem #                     / __ ) / __ \/ ___/ / ____// / / /                  #
rem #                    / __  |/ / / /\__ \ / /    / /_/ /                   #
rem #                   / /_/ // /_/ /___/ // /___ / __  /                    #
rem #                  /_____/ \____//____/ \____//_/ /_/                     #
rem #                                                                         #
rem ###########################################################################
rem Script to demo file upload service with server handshake and authentication

setlocal
rem  Set paths to the requried tools specific to the client side computer.
set /p PYTHON_PATH=<.\config\python_path.cfg

rem path to the directory containing utility scripts
set SCRIPT_PATH=%~dp0\helper_scripts

rem The base URL for the server is to be set here.
rem set API_URL=http://localhost:5000/hyapi
set /p API_URL=<.\config\base_url.cfg
rem The end-point of the upload service:
set uploadURL=!API_URL!/upload?

rem USER SPECIFIC ACCESS CREDENTIALS- These should have been provided
rem by the system administrator as part of the on-boarding of a new user/client
rem Generated via generate_AccessID.cmd script
set /p ACCESS_ID=<.\config\cred_access_id.cfg
set /p ENCODING_KEY=<.\config\cred_encoding_key.cfg

goto :MAIN

rem This function informs the user if any of the required arguments are missing from the command
:EXIT_INPUT_ISSUE
	echo Not enough parameters: Please provide the correct input arguments
	endlocal
	exit /b 1

rem This function is called if the script execution failes due to any reason.
:EXIT_SCRIPT_ERROR
	echo Error detected in Python Script
	endlocal
	exit /b 1

rem Main funciton 
:MAIN
rem This script only takes in one argument, that is the path to the 
rem file that is to be uploaded to the server.
if "%~1"=="" (goto EXIT_INPUT_ISSUE) else (set File_To_Upload="%1")

rem =========== Script starts from here ===========

rem This variable will be updated with the value received from the server.
set serverStatus=1

rem STEP-1 : Check if the service for file upload is available or not by calling the
rem respective end-point.
rem ToDo: Implement server hand-shake

rem for /f "tokens=1,2 delims=:{}, " %%a in ('curl -k !API_URL!/uploadServiceStatus ') do (
rem 	if %%~a==StatusCode (
rem 		set serverStatus=%%~b
rem 		echo "Server Status Received"
rem 	)
rem )


rem If the server is available then proceed with request
if !serverStatus!==1 (
	rem generate the signature for the file to be uploaded
	rem A signature for the provided file is also generated on the server side, and compared with the
	rem one provided by the client, The request only proceeds if the two signatures match.
	rem This verification process if name as 2-Tier verification in this thesis.
	rem The signature is generated using, the file contents and the personal encoding key of the client.
	rem The script to generate this is "util_Generate_Signature.py"
	Call %PYTHON_PATH%\python.exe %SCRIPT_PATH%\util_Generate_Signature.py %File_To_Upload% %ENCODING_KEY% > temp.txt
	for /f "tokens=*" %%a in (temp.txt) do (
		set FILE_SIGNATURE=%%a
		goto :got_signature
	)
	:got_signature
	echo %FILE_SIGNATURE%
	rem delete the temporary file
	DEL temp.txt

	rem Use curl to access the upload service.
	curl -i -k -v -F hyapifile=@%File_To_Upload% "%uploadURL%access-id=%ACCESS_ID%&signature=%FILE_SIGNATURE%"
) else echo Service is not available at the moment.


if !errorlevel! neq 0 goto EXIT_SCRIPT_ERROR

echo "Script executed successfully".

endlocal
exit /b 0