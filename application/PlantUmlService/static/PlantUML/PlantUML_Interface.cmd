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
rem # Author  : Ahmad Hassan Mirza, Mir6si, PS-EC/ECC   #
rem # Created : Feb, 2020                               #
rem ####################################################
rem The script interfaces with PlantUML Binary file
rem Parameters : Path to the input file and Path to the Output directory.
rem This script is called from the Flask App (python script) Service_GenerateUML.py

setlocal
rem Declare all path constants
set PYTHON_PATH=C:\toolbase\python\3.6.6.2.2\python-3.6.6.amd64
set JAVA_PATH=c:\toolbase\java_jre\1.8.0_141_64\bin

set SCRIPT_PATH=C:\Users\MIR6SI\Documents\HyAPI\3_Services\PlantUML
set IN_PATH=%SCRIPT_PATH%\_in
set OUT_PATH=%SCRIPT_PATH%\_out
set LICENSE_PATH=%SCRIPT_PATH%\_license
goto MAIN

:EXIT_INPUT_ISSUE
	echo Not enough parameters: Please provide the correct input arguments.
	endlocal
	exit /b 1

:EXIT_CCC_ERROR
	echo Service did not execute properly.
	endlocal
	exit /b 2


:MAIN
if "%~1"=="" (goto EXIT_INPUT_ISSUE) else (set IN_PATH="%1")
if "%~2"=="" (goto EXIT_INPUT_ISSUE) else (set OUT_PATH="%2")


java -jar %SCRIPT_PATH%\plantuml.jar "%IN_PATH%" -o "%OUT_PATH%"

set umlGenStatus=!errorlevel!

if !umlGenStatus! neq 0 (
	echo "Error(s) in generating the UML model."
	goto EXIT_CCC_ERROR
	) else ( 
	echo "UML model generated successfully."
	endlocal
	exit /b 0)