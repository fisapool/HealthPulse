@echo off
REM Startup script for backend development (Windows)

echo Starting HealthPulse Registry Backend...

REM Check if .env exists
if not exist .env (
    echo Creating .env from env.example...
    copy env.example .env
    echo Please edit .env with your database credentials
)

REM Initialize database if needed
echo Initializing database...
python init_db.py

REM Start the server
echo Starting FastAPI server...
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

