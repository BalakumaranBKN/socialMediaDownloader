@echo off
echo ========================================================
echo   OmniGrab Android APK Build Helper
echo ========================================================
echo.

cd /d "%~dp0frontend"

echo [1/3] Compiling Angular production bundle...
call npm.cmd run build
if %errorlevel% neq 0 (
    echo Error: Angular build failed.
    pause
    exit /b %errorlevel%
)

echo [2/3] Syncing assets to native Android project...
call npx.cmd cap sync android
if %errorlevel% neq 0 (
    echo Error: Capacitor sync failed.
    pause
    exit /b %errorlevel%
)

echo [3/3] Android project is ready!
echo.
echo Opening Android Studio...
call npx.cmd cap open android

echo.
echo ========================================================
echo To generate the APK in Android Studio:
echo  1. Wait for Gradle sync to finish.
echo  2. Go to: Build -^> Build Bundle(s) / APK(s) -^> Build APK(s)
echo  3. Click "locate" to get your app-debug.apk!
echo ========================================================
pause
