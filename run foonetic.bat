@echo off
title Foonetic KittenBot

echo Starting bot...

:start
python kittenbot_foonetic.py
echo Bot stopped.

echo.
echo.
choice /c YN /m "Restart bot" /t 3 /d Y
if %errorlevel% == 1 (
	echo Restarting bot...
	goto:start
)
