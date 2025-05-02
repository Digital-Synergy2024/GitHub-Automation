@echo off
echo Checking Python and PyInstaller...

python --version 2>NUL || (
    echo Python is not installed! Please install it first.
    exit /B
)

pip show pyinstaller >nul || (
    echo Installing PyInstaller...
    pip install pyinstaller
)

pip show CTkListbox >nul || (
    echo Installing CTkListbox package...
    pip install CTkListbox
)

pip show requests >nul || (
    echo Installing requests package...
    pip install requests
)

pip show customtkinter >nul || (
    echo Installing customtkinter package...
    pip install customtkinter
)

echo Building executable with icon and all dependencies...
pyinstaller github_manager.spec

mkdir "dist\GitHub_Manager" 2>NUL
move "dist\github_manager.exe" "dist\GitHub_Manager\"

echo Build complete! Your executable is in the 'dist\GitHub_Manager' folder.
pause