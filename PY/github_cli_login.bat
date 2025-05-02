@echo off
echo Checking GitHub CLI login status...

REM Check if logged in. gh auth status exits with 1 if not logged in.
gh auth status > nul 2>&1

if errorlevel 1 (
    echo You are not logged into GitHub CLI.
    echo Please follow the prompts in your browser to log in.
    gh auth login
    echo.
    echo Press any key once you have completed the login process...
    pause > nul
) else (
    echo Already logged into GitHub CLI.
)

echo.
echo Starting GitHub Manager...
echo.

REM Run your Python script (adjust python command if needed, or use the .exe)
REM python "c:\Users\Dizzy\Desktop\GitHub Automation\PY\github_manager.py"
REM Alternatively, if you want to run the compiled .exe:
"dist\GitHub_Manager\github_manager.exe"

echo.
echo Script finished. Press any key to close this window.
pause > nul