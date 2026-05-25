@echo off
title Bifrost News Getter

echo =========================================
echo  STEP 1: Fetching Announcements...
echo =========================================
cd /d ".\Bifrost-news"
python .\tahiti-scraper.py

echo.
echo =========================================
echo  STEP 2: Starting Bifrost Launcher...
echo =========================================
cd ..
start "" ".\Bifrost.exe"

echo.
echo SUCCESS: Launcher initialized. Closing console window.
timeout /t 2 >nul
exit