@echo off
echo ========================================================
echo   OmniGrab - Pushing Commits to GitHub
echo ========================================================
echo.
set "PATH=C:\Users\balak\AppData\Local\Programs\Git\cmd;C:\Users\balak\AppData\Local\Programs\Git\mingw64\bin;%PATH%"
cd /d "%~dp0"
echo Pushing local commits to origin main...
echo A browser window may open to authorize GitHub if needed.
echo.
git.exe push origin main
echo.
if %errorlevel% equ 0 (
    echo ========================================================
    echo   SUCCESS! Your code has been pushed to GitHub.
    echo ========================================================
) else (
    echo ========================================================
    echo   Push failed or was cancelled. Check above error.
    echo ========================================================
)
echo.
pause
