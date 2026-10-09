@echo off
title PDF 4-in-1 Offline Converter
echo ===================================================
echo         PDF 4-in-1 Handout Offline Converter
echo ===================================================
cd /d "%~dp0"

if "%~1"=="" (
    echo Drag and drop any PDF or folder onto this file, or enter path below:
    set /p USER_PATH="Enter PDF file or Folder path: "
) else (
    set USER_PATH=%~1
)

python pdf_converter.py "%USER_PATH%"
echo.
echo Conversion complete!
pause
