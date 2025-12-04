@echo off
echo 🚀 Setting up ChainBreak React Frontend...

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js is not installed. Please install Node.js 16+ first.
    echo    Visit: https://nodejs.org/
    pause
    exit /b 1
)

REM Check Node.js version
for /f "tokens=1,2 delims=." %%a in ('node --version') do set NODE_VERSION=%%a
set NODE_VERSION=%NODE_VERSION:~1%
if %NODE_VERSION% lss 16 (
    echo ❌ Node.js version 16+ is required. Current version: 
    node --version
    echo    Please upgrade Node.js and try again.
    pause
    exit /b 1
)

echo ✅ Node.js version: 
node --version

REM Check if npm is installed
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ npm is not installed. Please install npm first.
    pause
    exit /b 1
)

echo ✅ npm version: 
npm --version

REM Install dependencies
echo 📦 Installing dependencies...
npm install

if %errorlevel% equ 0 (
    echo ✅ Dependencies installed successfully!
) else (
    echo ❌ Failed to install dependencies. Please check the error messages above.
    pause
    exit /b 1
)

REM Create .env file if it doesn't exist
if not exist .env (
    echo 🔧 Creating .env file...
    echo REACT_APP_API_URL=http://localhost:5001 > .env
    echo ✅ .env file created with default API URL
) else (
    echo ✅ .env file already exists
)

REM Check if backend is running
echo 🔍 Checking backend connection...
curl -s http://localhost:5001/api/status >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Backend is running on http://localhost:5001
) else (
    echo ⚠️  Backend is not running on http://localhost:5001
    echo    Please start the ChainBreak backend first:
    echo    python app.py --api
)

echo.
echo 🎉 Setup completed successfully!
echo.
echo To start the development server:
echo   npm start
echo.
echo To build for production:
echo   npm run build
echo.
echo The application will be available at:
echo   http://localhost:3000
echo.
echo Happy coding! 🚀
pause
