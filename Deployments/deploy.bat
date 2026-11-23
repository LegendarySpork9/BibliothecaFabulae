@echo off
setlocal

echo === BibliothecaFabulae Windows Deployment ===

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH.
    exit /b 1
)

:: Check Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Node.js is not installed or not in PATH.
    exit /b 1
)

:: Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

:: Activate and install dependencies
echo Installing backend dependencies...
call .venv\Scripts\activate.bat
pip install -r requirements.txt

:: Build frontend
echo Installing frontend dependencies...
cd frontend
call npm ci
echo Building frontend...
call npm run build
cd ..

:: Run database migrations
echo Running database migrations...
set PYTHONPATH=.
alembic upgrade head

:: Generate .env if needed
if not exist ".env" (
    echo Generating .env file...
    for /f %%a in ('python -c "import secrets; print(secrets.token_hex(32))"') do set SECRET_KEY=%%a
    for /f %%a in ('python -c "import secrets; print(secrets.token_hex(32))"') do set ENCRYPTION_KEY=%%a

    (
        echo SECRET_KEY=%SECRET_KEY%
        echo ENCRYPTION_KEY=%ENCRYPTION_KEY%
        echo DATABASE_URL=sqlite+aiosqlite:///./data/bibliothecafabulae.db
        echo CORS_ORIGINS=["http://localhost"]
        echo ENVIRONMENT=production
    ) > .env

    echo .env file created.
)

:: Create data directories
if not exist "data" mkdir data
if not exist "logs" mkdir logs

echo.
echo === Build complete ===
echo.
echo To run the backend manually:
echo   .venv\Scripts\uvicorn.exe backend.main:app --host 127.0.0.1 --port 8000
echo.
echo To install as a Windows service using NSSM:
echo   nssm install BibliothecaFabulae "%cd%\.venv\Scripts\uvicorn.exe" "backend.main:app --host 127.0.0.1 --port 8000"
echo   nssm set BibliothecaFabulae AppDirectory "%cd%"
echo   nssm start BibliothecaFabulae
echo.
echo Then configure IIS using the web.config in the iis\ directory.

endlocal
