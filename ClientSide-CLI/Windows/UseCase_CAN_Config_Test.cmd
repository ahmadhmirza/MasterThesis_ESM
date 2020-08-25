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

rem CAN_CONFIG_SERVICE = ccService
setlocal
rem  Set paths to the requried tools specific to the client side computer.
set /p PYTHON_PATH=<.\config\python_path.cfg

rem path to the directory containing utility scripts
set SCRIPT_PATH=%~dp0\helper_scripts

rem The base URL for the server is to be set here.
set /p API_URL=<.\config\base_url.cfg

set /p outputPath=<.\config\output_directory.cfg

echo !API_URL!
rem ==== URLs for File Upload services ======
set uploadURL=!API_URL!/upload?
rem ==== URLs for Service : CAN_CONF_CHECK ====
set ccService_URL=!API_URL!/service/can-config-test?
rem ==== URLs for File Download services ======
set fileID=NA
rem ToDo : end point to check the status of file on the server (availavle/not availabel)
rem set chkFileStatus_URL=!API_URL!/checkFileStatus/
set download_URL=!API_URL!/download

rem ==== USER SPECIFIC ACCESS CREDENTIALS ====
set /p ACCESS_ID=<.\config\cred_access_id.cfg
set /p ENCODING_KEY=<.\config\cred_encoding_key.cfg

rem Specify the path to where the output recieved from the server should be stored.
rem Client side paths:


rem ==== Output Files ==== 
set LogFile=%outputPath%\CCTEST_LOG.log
set tempFile=%outputPath%\tmp.txt
set outFile=%outputPath%\CC_TEST_RESULTS.txt
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
rem Can-Config-Test requires two input files:
rem 1 - A2L file, 2- XLSX file with can-configuration
if "%~1"=="" (goto EXIT_INPUT_ISSUE) else (set A2L_File_To_Upload="%1")
if "%~2"=="" (goto EXIT_INPUT_ISSUE) else (set EXL_File_To_Upload="%2")

echo "::::::CAN_CONFIG_SERVICE_WEB_APP_DEMO:::::">!LogFile!
rem =========== Script starts from here ===========
rem This variable will be updated with the value received from the server.
set serverStatus=1

rem ToDo: Implement server hand-shake
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
	echo Generating Files' signatures.
	rem generate the signature for the files to be uploaded
	Call %PYTHON_PATH%\python.exe %SCRIPT_PATH%\util_Generate_Signature.py %A2L_File_To_Upload% %ENCODING_KEY%>!tempFile!
	for /f "tokens=*" %%a in (!tempFile!) do (
		set A2L_FILE_SIGNATURE=%%a
		goto :got_signature_a2l
	)
	:got_signature_a2l
	rem delete the temporary file
	DEL !tempFile!
	Call %PYTHON_PATH%\python.exe %SCRIPT_PATH%\util_Generate_Signature.py %EXL_File_To_Upload% %ENCODING_KEY%>!tempFile!
	for /f "tokens=*" %%a in (!tempFile!) do (
		set EXL_FILE_SIGNATURE=%%a
		goto :got_signature_exl
	)
	DEL !tempFile!
	:got_signature_exl
	rem delete the temporary file
	DEL !tempFile!
	echo Signatures generated for both files.>>!LogFile!
	echo A2L_FILE_SIGNATURE:%A2L_FILE_SIGNATURE%>>!LogFile!
	echo EXL_FILE_SIGNATURE:%EXL_FILE_SIGNATURE%>>!LogFile!
	echo *********************************************>>!LogFile!
	echo Signatures generated for both files.
	echo A2L_FILE_SIGNATURE:%A2L_FILE_SIGNATURE%
	echo EXL_FILE_SIGNATURE:%EXL_FILE_SIGNATURE%
	echo *********************************************

	rem upload the a2l and the xlsx file to the server
	echo "Uploading a2l file">>!LogFile!
	echo "Uploading a2l file"
	curl -i -k -F hyapifile=@%A2L_File_To_Upload% "%uploadURL%access-id=%ACCESS_ID%&signature=%A2L_FILE_SIGNATURE%">!tempFile!
	
	for /f "tokens=1,2 delims=:{}, " %%a in (!tempFile!) do (
		if %%~a==FileID (
			set a2l_FileID=%%~b
			echo "A2L File uploaded successfully and FileID received from the server.">>!LogFile!
			echo "A2L File uploaded successfully and FileID received from the server."
			goto :a2l_Upload_Success
		)
	)
	:a2l_Upload_Success
	DEL !tempFile!
	echo "Uploading excel file">>!LogFile!
	echo "Uploading excel file"
	rem TODO: Exception handling for bad request
	curl -i -k -F hyapifile=@%EXL_File_To_Upload% "%uploadURL%access-id=%ACCESS_ID%&signature=%EXL_FILE_SIGNATURE%">!tempFile!
	for /f "tokens=1,2 delims=:{}, " %%x in (!tempFile!) do (
		if %%~x==FileID (
			set exl_FileID=%%~y
			echo "Excel File uploaded successfully and FileID received from the server.">>!LogFile!
			echo "Excel File uploaded successfully and FileID received from the server."
			goto :exl_Upload_Success
		)
	)
	:exl_Upload_Success
	DEL !tempFile!
	echo *********************************************>>!LogFile!
	echo a2l_FileID: !a2l_FileID!>>!LogFile!	
	echo exl_FileID: !exl_FileID!>>!LogFile!
	echo *********************************************>>!LogFile!
	echo *********************************************
	echo a2l_FileID: !a2l_FileID!	
	echo exl_FileID: !exl_FileID!
	echo *********************************************
	)
	
if !errorlevel! neq 0 goto EXIT_FILEUPLOAD_ERROR

echo Performing CAN Configuration Check on the given files.>>!LogFile!
echo Performing CAN Configuration Check on the given files.
rem curl -X POST -H "Content-Type: application/json" -d "{"a2l_FileID":"!a2l_FileID!", "xl_FileID":"!exl_FileID!"}" %ccService_URL%accessID=%ACCESS_ID%>!tempFile!
curl -X POST %ccService_URL%access-id=%ACCESS_ID% -H "Content-type:application/json" -d "{\"xlFileID\":\"!exl_FileID!\",\"a2lFileID\":\"!a2l_FileID!\"}">!tempFile!
for /f "tokens=1,2 delims=:{}, " %%x in (!tempFile!) do (
	if %%~x==FileID (
		set results_FileID=%%~y
		echo "Results FileID received from the server.">>!LogFile!
		goto :cc_test_success
	)
)
:cc_test_success
DEL !tempFile!

echo Downloading generated file to local directory>>!LogFile!
echo Downloading generated file to local directory
curl -X GET !download_URL!/!results_FileID!?access-id=!ACCESS_ID! -o !outFile!
echo Results saved in "CC_TEST_RESULTS.txt" file.>>!LogFile!
echo Results saved in "CC_TEST_RESULTS.txt" file.

:EOF
echo Script executed successfully.>>!LogFile!
echo *********************************************>>!LogFile!
echo Script executed successfully.
echo *********************************************
endlocal
exit /b 0