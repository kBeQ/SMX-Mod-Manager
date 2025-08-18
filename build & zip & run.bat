@echo off
setlocal

ECHO =======================================
ECHO  CLEANING UP PREVIOUS BUILDS
ECHO =======================================
ECHO.

REM --- Step 1: Forcefully remove old build artifacts for a 100% clean build ---
IF EXIST "dist" (
    ECHO Deleting old 'dist' folder...
    rmdir /s /q "dist"
)
IF EXIST "build" (
    ECHO Deleting old 'build' folder...
    rmdir /s /q "build"
)
ECHO Cleanup complete.

ECHO.
ECHO =======================================
ECHO  STOPPING ANY OLD VERSIONS
ECHO =======================================
ECHO.

REM --- Step 2: Kill any running instances of the app to prevent file locks ---
taskkill /F /IM smx_mod_manager.exe 2>nul

ECHO =======================================
ECHO  BUILDING SMX MOD MANAGER
ECHO =======================================
ECHO.

REM --- Step 3: Run PyInstaller using the spec file ---
pyinstaller --noconfirm smx_mod_manager.spec

REM Check if the build command was successful
if errorlevel 1 goto build_failed

ECHO.
ECHO =======================================
ECHO  BUILD SUCCESSFUL!
ECHO =======================================
ECHO.

ECHO =======================================
ECHO  CREATING ZIP ARCHIVE
ECHO =======================================
ECHO.

REM --- Step 4: Define the source folder and the output zip file name ---
SET "SOURCE_DIR=dist\smx_mod_manager"
SET "ZIP_FILE=dist\SMX_Mod_Manager_Build.zip"

REM --- Step 5: Delete old zip file if it exists ---
IF EXIST "%ZIP_FILE%" (
    ECHO Deleting old zip archive...
    del "%ZIP_FILE%"
)

ECHO Creating zip archive...
REM --- Step 6: Use PowerShell to create the zip. This is reliable on modern Windows. ---
powershell -Command "Compress-Archive -Path '%SOURCE_DIR%/*' -DestinationPath '%ZIP_FILE%'"

REM Check if zipping was successful
if errorlevel 1 goto zip_failed

ECHO Zip created at %ZIP_FILE%
ECHO.

ECHO =======================================
ECHO  LAUNCHING FINAL APPLICATION (FOR TESTING)
ECHO =======================================
ECHO.

REM --- Step 7: CRITICAL FIX - Delete the useless wrapper executable from the dist root ---
del "dist\smx_mod_manager.exe"

REM --- Step 8: Launch the .exe from the UNZIPPED build folder ---
ECHO NOTE: Running the application from the build folder, NOT the zip file.
start "" "dist\smx_mod_manager\smx_mod_manager.exe"

REM --- All steps complete, exit successfully ---
exit /b 0

:build_failed
ECHO.
ECHO ######################################
ECHO #           BUILD FAILED!            #
ECHO ######################################
ECHO An error occurred during the PyInstaller build.
ECHO Please review the messages above.
ECHO.
pause
exit /b 1

:zip_failed
ECHO.
ECHO ######################################
ECHO #       ZIP CREATION FAILED!         #
ECHO ######################################
ECHO An error occurred while creating the zip file.
ECHO Make sure PowerShell is available and you have write permissions.
ECHO.
pause
exit /b 1