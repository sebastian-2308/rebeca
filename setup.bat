@echo off
title Rebeca - Setup
cd /d "%~dp0"

echo ============================================
echo  Rebeca AI Coding Assistant - Setup
echo ============================================
echo.

REM ---- Check Python ----
py --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no esta instalado.
    echo Instalalo desde: https://www.python.org/downloads/
    echo Asegurate de marcar "Add Python to PATH"
    pause
    exit /b 1
)
py --version

REM ---- Create virtual environment ----
if not exist venv\ (
    echo [1/3] Creando entorno virtual...
    py -m venv venv
) else (
    echo [1/3] Entorno virtual ya existe.
)

REM ---- Install dependencies ----
echo [2/3] Instalando dependencias...
call venv\Scripts\pip.exe install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Fallo al instalar dependencias.
    pause
    exit /b 1
)

REM ---- Create desktop shortcut ----
echo [3/3] Creando lanzador en el escritorio...
set DESKTOP=%USERPROFILE%\Desktop
set SHORTCUT=%DESKTOP%\Rebeca.bat

>"%SHORTCUT%" (
    echo @echo off
    echo title Rebeca - AI Coding Assistant
    echo cd /d "%~dp0"
    echo call venv\Scripts\python.exe -m rebeca.cli --provider ollama --model qwen2.5-coder:7b %%*
    echo if errorlevel 1 (
    echo     echo.
    echo     echo Rebeca cerro con error. Presione una tecla para cerrar.
    echo     pause
    echo )
)

echo.
echo ============================================
echo  Setup completado!
echo ============================================
echo.
echo Para ejecutar Rebeca:
echo   1. Asegurate de tener Ollama instalado y corriendo
echo   2. Ejecuta: python -m rebeca.cli --provider ollama --model qwen2.5-coder:7b
echo.
echo O usa el acceso directo en el Escritorio: Rebeca.bat
echo.
pause
