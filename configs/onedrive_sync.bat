@echo off

REM ADD CUSTOM FOLDER TO ONE DRIVE
set /p "onedrivefolder=One drive folder name: "
set /p "customfolder=Path to folder: "

REM set sync folder 
mklink /j "%UserProfile%\OneDrive\%onedrivefolder%" "%customfolder%"