@echo off
cd /d "C:\Users\Chaarvi D\Desktop\android\mobile_app"
echo Adding files...
git add main.py buildozer.spec BUILD_STATUS_FIXED.md
echo.
echo Committing...
git commit -m "Fix corrupted main.py and optimize dependencies"
echo.
echo Pushing to GitHub...
git push origin main
echo.
echo Done!
pause

