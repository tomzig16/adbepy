@echo off
REM # ARG SET #
set mypath=%~dp0
set adubpath=%mypath%/src/adbe.py

REM if you have installed python 2 on your machine try using python3 command below
python %adubpath% %*
