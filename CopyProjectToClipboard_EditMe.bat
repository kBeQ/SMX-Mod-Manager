@echo off
setlocal enabledelayedexpansion

:: =================================================================
:: ||                                                           ||
:: ||  EDIT THIS LIST: Add the filenames you want to copy here. ||
:: ||  Separate each filename with a space.                     ||
:: ||  **Use quotes and ^ to escape & for complex filenames**   ||
:: ||                                                           ||
:: =================================================================

set "fileList="build ^& run.bat" "build ^& zip ^& run.bat" requirements.txt smx_mod_manager.spec"

:: =================================================================
:: ||                                                           ||
:: ||          (You shouldn't need to edit below this line)       ||
:: ||                                                           ||
:: =================================================================

:: Create a temporary file to store the combined content
set "tempFile=%TEMP%\clipboard_temp.txt"

:: Clear the temporary file if it already exists to start fresh
if exist "%tempFile%" del "%tempFile%"

:: Loop through the list of files you defined above
for %%F in (%fileList%) do (
    if exist "%%~F" (
        :: Add a header with the filename to the temp file
        echo;============================================================ >> "%tempFile%"
        echo;==== FILENAME: %%~F                                      ==== >> "%tempFile%"
        echo;============================================================ >> "%tempFile%"
        echo. >> "%tempFile%"
        
        :: Append the content of the file to the temp file
        type "%%~F" >> "%tempFile%"
        
        :: Add newlines after the content for separation
        echo. >> "%tempFile%"
        echo. >> "%tempFile%"
        
    ) else (
        echo  - WARNING: Could not find [%%~F]. Skipping. >> "%tempFile%"
    )
)

:: Check if the temporary file was created (i.e., at least one file was found)
if not exist "%tempFile%" (
    echo.
    echo No valid files were found to copy. Please check the fileList in the script.
    pause
    exit /b
)

:: Copy the entire content of the temporary file to the clipboard
clip < "%tempFile%"

:: Clean up the temporary file
del "%tempFile%"

:: The script will now exit immediately upon success.
exit /b