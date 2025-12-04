#!/bin/bash

echo "🚀 Setting up ChainBreak React Frontend..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16+ first."
    echo "   Visit: https://nodejs.org/"
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 16 ]; then
    echo "❌ Node.js version 16+ is required. Current version: $(node -v)"
    echo "   Please upgrade Node.js and try again."
    exit 1
fi

echo "✅ Node.js version: $(node -v)"

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm first."
    exit 1
fi

echo "✅ npm version: $(npm -v)"

# Install dependencies
echo "📦 Installing dependencies..."
npm install

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully!"
else
    echo "❌ Failed to install dependencies. Please check the error messages above."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "🔧 Creating .env file..."
    cat > .env << EOF
REACT_APP_API_URL=http://localhost:5001
EOF
    echo "✅ .env file created with default API URL"
else
    echo "✅ .env file already exists"
fi

# Check if backend is running
echo "🔍 Checking backend connection..."
if curl -s http://localhost:5001/api/status > /dev/null 2>&1; then
    echo "✅ Backend is running on http://localhost:5001"
else
    echo "⚠️  Backend is not running on http://localhost:5001"
    echo "   Please start the ChainBreak backend first:"
    echo "   python app.py --api"
fi

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "To start the development server:"
echo "  npm start"
echo ""
echo "To build for production:"
echo "  npm run build"
echo ""
echo "The application will be available at:"
echo "  http://localhost:3000"
echo ""
echo "Happy coding! 🚀"
