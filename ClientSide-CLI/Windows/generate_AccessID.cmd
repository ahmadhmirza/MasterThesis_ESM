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
rem Script Interfacing with the python script to generate AccessID and EncodingKey

setlocal
rem  Set paths to the requried tools specific to the client side computer.
set /p PYTHON_PATH=<.\config\python_path.cfg

rem path to the directory containing utility scripts
set SCRIPT_PATH=%~dp0\HelperScripts

goto MAIN

rem This function informs the user if any of the required arguments are missing from the command
:EXIT_INPUT_ISSUE
echo Not enough parameters: Please provide the correct input arguments
ENDLOCAL
exit /b 1

rem This function is called if the script execution failes due to any reason.
:EXIT_SCRIPT_ERROR
echo Error detected in Python Script
ENDLOCAL
exit /b 1

rem Main funciton 
:MAIN
rem input arguments handling.
rem two arguments are required 
rem for the actual script, the intention is to generate a strong access ID by
rem generating a hash from two strings that can be selelcted by the user,
rem or for example the user's name and the current time

rem recommended usage, client's name and the name of the required service for
rem which the access-id is to be generated.
if "%~1"=="" (goto EXIT_INPUT_ISSUE) else (set STR_1=%1)
if "%~2"=="" (goto EXIT_INPUT_ISSUE) else (set STR_2=%2)

REM Call to python script
Call %PYTHON_PATH%\python.exe %SCRIPT_PATH%\util_AccessId_Generator.py %STR_1% %STR_2%

if %ERRORLEVEL% neq 0 goto EXIT_SCRIPT_ERROR
echo "Script executed successfully".

ENDLOCAL
exit /b 0


