@echo off
setlocal

if "%1"=="" (
    echo Usage: tell ^<question^>    or    tell "do ^<task^>"
    echo.
    echo   tell ^<question^>           -- Answer queries (no system actions)
    echo   tell "do ^<task^>"          -- System/coding tasks
    echo.
    echo Examples:
    echo   tell "what is python?"
    echo   tell "do create a flask app"
    echo   tell "do check disk usage"
    exit /b 1
)

if "%NVIDIA_API_KEY%"=="" (
    echo Error: NVIDIA_API_KEY is not set.
    echo Get a key: https://build.nvidia.com/explore
    echo Then: set NVIDIA_API_KEY="nvapi-..."
    exit /b 1
)

python "%~dp0main.py" --inline %*
