@echo off
echo ==============================================
echo   Syncing Malachi Daniel Website from GitHub
echo ==============================================
git pull --rebase origin main
echo.
echo Sync Complete! Your local library is up to date.
timeout /t 5
