#!/usr/bin/env python3
"""
Health Check Script for ChainBreak
Monitors system components and provides status information
"""

import requests
import json
import sys
from datetime import datetime
import time

def check_api_status(base_url="http://localhost:5001"):
    """Check if the API is responding"""
    try:
        response = requests.get(f"{base_url}/api/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                "status": "online",
                "neo4j_available": not data.get("data", {}).get("mock_mode", False),
                "message": data.get("message", "API is responding"),
                "timestamp": data.get("timestamp")
            }
        else:
            return {
                "status": "error",
                "neo4j_available": False,
                "message": f"API returned status code {response.status_code}",
                "timestamp": datetime.now().isoformat()
            }
    except requests.exceptions.ConnectionError:
        return {
            "status": "offline",
            "neo4j_available": False,
            "message": "Cannot connect to API server",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "neo4j_available": False,
            "message": f"Error checking API: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

def check_neo4j_direct(uri="bolt://localhost:7687", username="neo4j", password="password"):
    """Check Neo4j connection directly"""
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(uri, auth=(username, password))
        with driver.session() as session:
            result = session.run("RETURN 1 as test")
            record = result.single()
            driver.close()
            if record and record["test"] == 1:
                return {
                    "status": "online",
                    "message": "Neo4j is responding",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "error",
                    "message": "Neo4j query failed",
                    "timestamp": datetime.now().isoformat()
                }
    except ImportError:
        return {
            "status": "error",
            "message": "Neo4j Python driver not installed",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "offline",
            "message": f"Neo4j connection failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

def check_frontend(base_url="http://localhost:5001"):
    """Check if frontend is accessible"""
    try:
        response = requests.get(f"{base_url}/frontend/index.html", timeout=10)
        if response.status_code == 200:
            return {
                "status": "online",
                "message": "Frontend is accessible",
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "error",
                "message": f"Frontend returned status code {response.status_code}",
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        return {
            "status": "offline",
            "message": f"Frontend check failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

def print_status(component, status_data):
    """Print formatted status information"""
    status = status_data["status"]
    message = status_data["message"]
    timestamp = status_data["timestamp"]
    
    if status == "online":
        color = "\033[92m"  # Green
        icon = "✓"
    elif status == "offline":
        color = "\033[91m"  # Red
        icon = "✗"
    else:
        color = "\033[93m"  # Yellow
        icon = "⚠"
    
    reset = "\033[0m"
    print(f"{color}{icon} {component}: {status}{reset}")
    print(f"   Message: {message}")
    print(f"   Time: {timestamp}")
    
    if "neo4j_available" in status_data:
        neo4j_status = "available" if status_data["neo4j_available"] else "unavailable"
        neo4j_color = "\033[92m" if status_data["neo4j_available"] else "\033[91m"
        print(f"   {neo4j_color}Neo4j: {neo4j_status}{reset}")
    print()

def main():
    """Main health check function"""
    print("🔍 ChainBreak Health Check")
    print("=" * 50)
    print()
    
    # Check API status
    api_status = check_api_status()
    print_status("API Server", api_status)
    
    # Check Neo4j directly
    neo4j_status = check_neo4j_direct()
    print_status("Neo4j Database", neo4j_status)
    
    # Check frontend
    frontend_status = check_frontend()
    print_status("Frontend", frontend_status)
    
    # Summary
    print("📊 Summary:")
    print("-" * 20)
    
    all_online = (
        api_status["status"] == "online" and
        neo4j_status["status"] == "online" and
        frontend_status["status"] == "online"
    )
    
    if all_online:
        print("\033[92m✓ All systems are online and operational!\033[0m")
    else:
        print("\033[93m⚠ Some systems are experiencing issues:\033[0m")
        if api_status["status"] != "online":
            print("  - API Server is not responding")
        if neo4j_status["status"] != "online":
            print("  - Neo4j Database is not accessible")
        if frontend_status["status"] != "online":
            print("  - Frontend is not accessible")
    
    # Recommendations
    print("\n💡 Recommendations:")
    print("-" * 20)
    
    if api_status["status"] != "online":
        print("• Start the ChainBreak API server: python app.py")
    
    if neo4j_status["status"] != "online":
        print("• Start Neo4j database")
        print("• Check Neo4j credentials in config.yaml")
        print("• Verify Neo4j is running on bolt://localhost:7687")
    
    if frontend_status["status"] != "online":
        print("• Ensure the API server is running")
        print("• Check if frontend files are in the correct location")
    
    if api_status["status"] == "online" and not api_status.get("neo4j_available", False):
        print("• API is running but Neo4j is unavailable")
        print("• Frontend will work in limited mode")
        print("• Some advanced features may not be available")

if __name__ == "__main__":
    main()
