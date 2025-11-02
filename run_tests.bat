@echo off
REM Windows batch script to run tests
REM Usage: run_tests.bat [pytest|cypress|all]

setlocal

echo 🧪 Running Tests
echo ==================

if "%1"=="pytest" goto pytest
if "%1"=="cypress" goto cypress
if "%1"=="all" goto all
goto usage

:pytest
echo.
echo 📋 Running Pytest Tests...
echo ---------------------------
pytest -v --tb=short
goto end

:cypress
echo.
echo 🌲 Running Cypress Tests...
echo ---------------------------
REM Check if server is running
curl -s http://localhost:4000 >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Server is not running
    echo Please start the server first:
    echo   python -m uvicorn api.app:app --reload
    exit /b 1
)
if exist "node_modules\cypress" (
    npx cypress run
) else (
    echo ❌ Cypress is not installed. Run: npm install
    exit /b 1
)
goto end

:all
echo.
echo 🚀 Running All Tests...
echo ========================
call :pytest
if errorlevel 1 (
    echo ❌ Pytest tests failed. Skipping Cypress tests.
    exit /b 1
)
call :cypress
goto end

:usage
echo Usage: %0 [pytest^|cypress^|all]
exit /b 1

:end
echo.
echo ✅ Tests completed!
endlocal

