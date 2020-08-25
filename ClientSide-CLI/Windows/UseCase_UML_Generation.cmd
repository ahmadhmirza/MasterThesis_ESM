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
rem Script to demo UML Diagram Generation Service.
rem Simulates client side CLI implementation.

setlocal
rem  Set paths to the requried tools specific to the client side computer.
set /p PYTHON_PATH=<.\config\python_path.cfg

rem path to the directory containing utility scripts
set SCRIPT_PATH=%~dp0\helper_scripts

rem The base URL for the server is to be set here.
set /p API_URL=<.\config\base_url.cfg

rem ==== URLs for File Upload services ======
set uploadURL=!API_URL!/upload?
rem ==== URLs for Service : CAN_CONF_CHECK ====
set ccService_URL=!API_URL!/service/can-config-test?
rem ==== URLs for File Download services ======
set fileID=NA

rem ToDo : end point to check the status of file on the server (available/not available)
rem set chkFileStatus_URL=!API_URL!/checkFileStatus/
set download_URL=!API_URL!/download

rem ==== URLs for the service ======
set Service_URL=!API_URL!/service/generate-uml?

rem ==== USER SPECIFIC ACCESS CREDENTIALS ====
set /p ACCESS_ID=<.\config\cred_access_id.cfg
set /p ENCODING_KEY=<.\config\cred_encoding_key.cfg


rem ==== Output Files ==== 
set LogFile=%~dp0\example_outputs\UML_Gen.log
set tempFile=%~dp0\example_outputs\tmp.txt
set outFile=%~dp0\example_outputs\Generated_UML_Model.png
goto :MAIN

rem This function informs the user if any of the required arguments are missing from the command
:EXIT_INPUT_ISSUE
	echo Not enough parameters: Please provide the correct input arguments.
	endlocal
	exit /b 1

rem This function is called if any error occus while the file upload process.
:EXIT_FILEUPLOAD_ERROR
	echo Error(s) while uploading file to server.
	endlocal
	exit /b 2

rem This function is called if the script execution failes due to any reason.
:EXIT_CCC_ERROR
	echo Service did not execute properly.
	endlocal
	exit /b 3

rem This function is called if any error occus while the file download process.
:EXIT_RESULTDOWNLOAD_ERROR
	echo Error(s) while retrieving the results.
	endlocal
	exit /b 4

rem Main funciton 
:MAIN
rem One required input parameter = path to the source text file with uml description.
if "%~1"=="" (goto EXIT_INPUT_ISSUE) else (set UmlDia_Description="%1")

echo ":::::UML_DIAGRAM_GENERATION_DEMO:::::">!LogFile!
echo ::::UML_DIAGRAM_GENERATION_DEMO::::
rem =========== Script starts from here ===========
rem This variable will be updated with the value received from the server.
set serverStatus=1

rem Get the status of the server to check if it is availabel or not before proceeding
rem for /f "tokens=1,2 delims=:{}, " %%a in ('curl -k !API_URL!/uploadServiceStatus') do (
rem 	if %%~a==StatusCode (
rem 		set serverStatus=%%~b
rem 		echo "Server Status Received"
rem 		echo Server Status Received:!serverStatus!>>!LogFile!
rem 		echo *********************************************>>!LogFile!
rem 	)
rem )

rem if the server is available then proceed with request
if !serverStatus! neq 1 (
	echo Service is not available at the moment.>>!LogFile!
	echo Service is not available at the moment.
	goto :EOF
	) else (
	
	echo Generating Files' signatures.>>!LogFile!
	echo Generating Files' signatures
	rem generate the signature for the file to be uploaded
	Call %PYTHON_PATH%\python.exe %SCRIPT_PATH%\util_Generate_Signature.py %UmlDia_Description% %ENCODING_KEY%>!tempFile!
	for /f "tokens=*" %%a in (!tempFile!) do (
		set FILE_SIGNATURE=%%a
		goto :got_file_signature
	)
	:got_file_signature
	rem delete the temporary file
	DEL !tempFile!

	echo Signature generated.>>!LogFile!
	echo FILE_SIGNATURE:%FILE_SIGNATURE%>>!LogFile!
	echo *********************************************>>!LogFile!
	echo Signature generated.
	echo FILE_SIGNATURE:%FILE_SIGNATURE%
	echo *********************************************


	echo "Uploading diagram description file">>!LogFile!
	echo "Uploading diagram description file"
	curl -i -k -F hyapifile=@%UmlDia_Description% "%uploadURL%access-id=%ACCESS_ID%&signature=%FILE_SIGNATURE%">!tempFile!
	
	rem -----
	for /f "tokens=1,2 delims=:{}, " %%a in (!tempFile!) do (
		if %%~a==FileID (
			set up_FileID=%%~b
			echo "File uploaded successfully and FileID received from the server.">>!LogFile!
			echo "File uploaded successfully and FileID received from the server."
			goto :File_Upload_Success
		)
	)
	:File_Upload_Success
	DEL !tempFile!
	echo *********************************************>>!LogFile!
	echo FileID: !up_FileID!>>!LogFile!
	echo *********************************************>>!LogFile!
	echo *********************************************
	echo FileID: !up_FileID!
	echo *********************************************
	)
	
if !errorlevel! neq 0 goto EXIT_FILEUPLOAD_ERROR

echo Generating UML diagram.>>!LogFile!
echo Generating UML diagram.
curl -X POST %Service_URL%access-id=%ACCESS_ID% -H "Content-type:application/json" -d "{\"InputFileID\":\"!up_FileID!\"}">!tempFile!
for /f "tokens=1,2 delims=:{}, " %%x in (!tempFile!) do (
	if %%~x==FileID (
		set results_FileID=%%~y
		echo "Output FileID received from the server.">>!LogFile!
		echo "Output FileID received from the server."
		goto :service_execution_success
	)
)
:service_execution_success
DEL !tempFile!

echo Downloading generated file to local directory>>!LogFile!
echo Downloading generated file to local directory...
curl -X GET !download_URL!/!results_FileID!?access-id=!ACCESS_ID! -o !outFile!
echo Results saved in "Output.png" file.>>!LogFile!
echo Results saved in "Output.png" file.

:EOF
echo Script executed successfully.>>!LogFile!
echo *********************************************>>!LogFile!
echo Script executed successfully.
echo *********************************************
endlocal
exit /b 0