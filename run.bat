@echo off
title Network Engineer Simulator 3D
echo Starting Network Engineer Simulator 3D...

where py >nul 2>nul
if %errorlevel% equ 0 (
    py -3.11 main.py
    if %errorlevel% neq 0 (
        python main.py
    )
) else (
    python main.py
)

if %errorlevel% neq 0 (
    echo.
    echo Game exited with error. Press any key to close.
    pause >nul
)
