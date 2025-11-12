:: This batch file converts a Python script into a Windows executable.
@echo off
setlocal

:: Determine if we have 'python' or 'python3' in the path. On Windows, the
:: Python executable is typically called 'python', so check that first.
where /q python
if ERRORLEVEL 1 goto python3
set PYTHON=python
goto build

:python3
where /q python3
if ERRORLEVEL 1 goto nopython
set PYTHON=python3

:: Verify the setup script has been run
:build
set VENV=.venv
set DIST_DIR=dist
set HA_DIR=%DIST_DIR%\home-assistant
if exist %VENV% (
	call %VENV%\Scripts\activate.bat

	:: Ensure subfolder exists
	if not exist "%HA_DIR%" mkdir "%HA_DIR%"

	pyinstaller --onefile --name home-assistant-plugin --distpath "%HA_DIR%" plugin.py
	if exist manifest.json (
		copy /y manifest.json "%HA_DIR%\manifest.json"
		echo manifest.json copied successfully.
	) else (
		echo {} > manifest.json
		echo Created a blank manifest.json file.	
		copy /y manifest.json "%HA_DIR%\manifest.json"
		echo manifest.json copied successfully.
	)
	copy /y manifest_template.json "%HA_DIR%\manifest_template.json"
	echo manifest_template.json copied successfully.
	copy /y config.json "%HA_DIR%\config.json"
	echo config.json copied successfully.

	call %VENV%\Scripts\deactivate.bat
	echo Plugin can be found in the "%HA_DIR%" directory
	exit /b 0
) else (
	echo Please run setup.bat before attempting to build
	exit /b 1
)

:nopython
echo Python needs to be installed and in your path
exit /b 1
