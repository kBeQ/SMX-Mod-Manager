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

REM --- Step 2: Kill any running instances of the app ---
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
ECHO  LAUNCHING FINAL APPLICATION
ECHO =======================================
ECHO.

REM --- Step 4: CRITICAL FIX - Delete the useless wrapper executable ---
REM PyInstaller in one-folder mode creates a bootstrap .exe in the root of dist/.
REM We must delete it to avoid confusion and ensure we run the correct one.
del "dist\smx_mod_manager.exe"

REM --- Step 5: Launch the correct .exe from INSIDE the final application folder ---
start "" "dist\smx_mod_manager\smx_mod_manager.exe"

REM Success, exit the script
exit /b 0

:build_failed
ECHO.
ECHO =======================================
ECHO  BUILD FAILED!
ECHO =======================================
ECHO An error occurred. Please review the messages above.
ECHO.
pause
exit /b 1