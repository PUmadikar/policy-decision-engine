@echo off
echo ============================================================
echo   Starting Policy-Aware RAG Claim Decision Engine
echo ============================================================
echo.

echo Running End-to-End Evaluation Suite...
python -m eval.evaluate
if %errorlevel% neq 0 (
    echo Evaluation encountered an error.
    pause
    exit /b %errorlevel%
)

echo.
echo Starting Streamlit Reviewer Dashboard...
streamlit run ui/app.py
