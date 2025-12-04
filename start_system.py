#!/usr/bin/env python3
"""
Startup Script for ChainBreak
Helps start the system with different configurations
"""

import subprocess
import sys
import os
import time
import argparse
from pathlib import Path

def check_docker():
    """Check if Docker is available"""
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def start_with_docker():
    """Start the system using Docker Compose"""
    print("🐳 Starting ChainBreak with Docker Compose...")
    
    if not check_docker():
        print("❌ Docker is not installed or not available")
        return False
    
    try:
        # Start the services
        subprocess.run(['docker-compose', 'up', '-d'], check=True)
        print("✅ Docker services started successfully")
        
        # Wait for services to be ready
        print("⏳ Waiting for services to be ready...")
        time.sleep(10)
        
        # Check status
        print("🔍 Checking service status...")
        subprocess.run(['docker-compose', 'ps'])
        
        print("\n🌐 Access points:")
        print("   • API: http://localhost:5001")
        print("   • Frontend: http://localhost:5001/frontend/index.html")
        print("   • Neo4j Browser: http://localhost:7474")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start Docker services: {e}")
        return False

def start_api_only():
    """Start only the API server (without Neo4j dependency)"""
    print("🚀 Starting ChainBreak API server only...")
    
    try:
        # Set environment variable to indicate Neo4j is not required
        env = os.environ.copy()
        env['CHAINBREAK_NO_NEO4J'] = '1'
        
        # Start the API server
        print("📡 Starting API server on http://localhost:5001")
        subprocess.run([sys.executable, 'app.py'], env=env, check=True)
        
    except KeyboardInterrupt:
        print("\n🛑 API server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start API server: {e}")
        return False
    
    return True

def start_full_system():
    """Start the full system with Neo4j"""
    print("🚀 Starting ChainBreak full system...")
    
    try:
        # Start the API server
        print("📡 Starting API server on http://localhost:5001")
        subprocess.run([sys.executable, 'app.py'], check=True)
        
    except KeyboardInterrupt:
        print("\n🛑 System stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start system: {e}")
        return False
    
    return True

def check_prerequisites():
    """Check if prerequisites are met"""
    print("🔍 Checking prerequisites...")
    
    # Check if config file exists
    if not Path('config.yaml').exists():
        print("⚠️  config.yaml not found, using default configuration")
    
    # Check if requirements are installed
    try:
        import flask
        import neo4j
        print("✅ Python dependencies are installed")
    except ImportError as e:
        print(f"❌ Missing Python dependency: {e}")
        print("   Run: pip install -r requirements.txt")
        return False
    
    return True

def main():
    parser = argparse.ArgumentParser(description='ChainBreak Startup Script')
    parser.add_argument('--mode', choices=['docker', 'api-only', 'full'], 
                       default='full', help='Startup mode')
    parser.add_argument('--check', action='store_true', 
                       help='Only check prerequisites')
    
    args = parser.parse_args()
    
    print("🔗 ChainBreak Startup Script")
    print("=" * 40)
    
    if args.check:
        check_prerequisites()
        return
    
    if not check_prerequisites():
        print("❌ Prerequisites check failed")
        sys.exit(1)
    
    success = False
    
    if args.mode == 'docker':
        success = start_with_docker()
    elif args.mode == 'api-only':
        success = start_api_only()
    elif args.mode == 'full':
        success = start_full_system()
    
    if success:
        print("\n✅ System started successfully!")
        print("\n💡 Tips:")
        print("   • Use Ctrl+C to stop the server")
        print("   • Run 'python health_check.py' to check system status")
        print("   • Check logs in chainbreak.log for detailed information")
    else:
        print("\n❌ Failed to start system")
        sys.exit(1)

if __name__ == "__main__":
    main()
