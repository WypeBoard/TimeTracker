@echo off
REM Manual startup launcher for the TimeTracker standalone web app.
REM Per features/standalone-web-app.md Requirements: startup is manual for
REM now (a .bat file or Startup-folder shortcut is acceptable). This does
REM not auto-launch a browser — open http://127.0.0.1:8765/ manually and
REM pin the tab.
cd /d "%~dp0"
".venv\Scripts\python.exe" -m webapp
