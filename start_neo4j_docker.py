#!/usr/bin/env python3
"""
ChainBreak Neo4j Docker Startup Script

This script helps users start ChainBreak with Neo4j using Docker containers.
It provides an easy way to manage the Neo4j database and ChainBreak application.
"""

import os
import sys
import subprocess
import time
import requests
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Neo4jDockerManager:
    """Manager for Neo4j Docker containers"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.docker_compose_file = self.project_root / "docker-compose-neo4j.yml"
        self.neo4j_url = "http://localhost:7474"
        self.neo4j_bolt_url = "bolt://localhost:7687"
        
    def check_docker_installed(self) -> bool:
        """Check if Docker is installed and running"""
        try:
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True, check=True)
            logger.info(f"Docker found: {result.stdout.strip()}")
            
            # Check if Docker daemon is running
            subprocess.run(['docker', 'info'], 
                          capture_output=True, text=True, check=True)
            logger.info("Docker daemon is running")
            return True
            
        except subprocess.CalledProcessError:
            logger.error("Docker is not installed or not running")
            return False
        except FileNotFoundError:
            logger.error("Docker command not found. Please install Docker Desktop")
            return False
    
    def check_docker_compose_file(self) -> bool:
        """Check if docker-compose file exists"""
        if not self.docker_compose_file.exists():
            logger.error(f"Docker compose file not found: {self.docker_compose_file}")
            return False
        logger.info(f"Docker compose file found: {self.docker_compose_file}")
        return True
    
    def start_neo4j(self) -> bool:
        """Start Neo4j container"""
        try:
            logger.info("Starting Neo4j container...")
            cmd = ['docker-compose', '-f', str(self.docker_compose_file), 'up', '-d', 'neo4j']
            result = subprocess.run(cmd, cwd=self.project_root, 
                                  capture_output=True, text=True, check=True)
            logger.info("Neo4j container started successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to start Neo4j container: {e.stderr}")
            return False
    
    def wait_for_neo4j(self, timeout: int = 120) -> bool:
        """Wait for Neo4j to be ready"""
        logger.info("Waiting for Neo4j to be ready...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.neo4j_url}/", timeout=5)
                if response.status_code == 200:
                    logger.info("✅ Neo4j is ready!")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            logger.info("Neo4j not ready yet, waiting...")
            time.sleep(5)
        
        logger.error(f"Neo4j did not become ready within {timeout} seconds")
        return False
    
    def test_neo4j_connection(self) -> bool:
        """Test Neo4j connection"""
        try:
            from neo4j import GraphDatabase
            
            driver = GraphDatabase.driver(self.neo4j_bolt_url, auth=("neo4j", "password"))
            with driver.session() as session:
                result = session.run("RETURN 1 as test")
                record = result.single()
                if record and record["test"] == 1:
                    logger.info("✅ Neo4j connection test successful!")
                    driver.close()
                    return True
            
            driver.close()
            return False
            
        except Exception as e:
            logger.error(f"Neo4j connection test failed: {e}")
            return False
    
    def start_chainbreak_app(self) -> bool:
        """Start ChainBreak application container"""
        try:
            logger.info("Starting ChainBreak application...")
            cmd = ['docker-compose', '-f', str(self.docker_compose_file), 
                   '--profile', 'app', 'up', '-d', 'chainbreak-app']
            result = subprocess.run(cmd, cwd=self.project_root, 
                                  capture_output=True, text=True, check=True)
            logger.info("ChainBreak application started successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to start ChainBreak application: {e.stderr}")
            return False
    
    def start_neo4j_browser(self) -> bool:
        """Start Neo4j Browser (optional)"""
        try:
            logger.info("Starting Neo4j Browser...")
            cmd = ['docker-compose', '-f', str(self.docker_compose_file), 
                   '--profile', 'browser', 'up', '-d', 'neo4j-browser']
            result = subprocess.run(cmd, cwd=self.project_root, 
                                  capture_output=True, text=True, text=True, check=True)
            logger.info("Neo4j Browser started successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to start Neo4j Browser: {e.stderr}")
            return False
    
    def stop_all_services(self) -> bool:
        """Stop all ChainBreak services"""
        try:
            logger.info("Stopping all ChainBreak services...")
            cmd = ['docker-compose', '-f', str(self.docker_compose_file), 'down']
            result = subprocess.run(cmd, cwd=self.project_root, 
                                  capture_output=True, text=True, check=True)
            logger.info("All services stopped successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to stop services: {e.stderr}")
            return False
    
    def get_service_status(self) -> dict:
        """Get status of all services"""
        try:
            cmd = ['docker-compose', '-f', str(self.docker_compose_file), 'ps']
            result = subprocess.run(cmd, cwd=self.project_root, 
                                  capture_output=True, text=True, check=True)
            
            status = {
                'neo4j': 'unknown',
                'chainbreak_app': 'unknown',
                'neo4j_browser': 'unknown'
            }
            
            lines = result.stdout.strip().split('\n')
            for line in lines[2:]:  # Skip header lines
                if 'neo4j' in line and 'Up' in line:
                    status['neo4j'] = 'running'
                elif 'chainbreak-app' in line and 'Up' in line:
                    status['chainbreak_app'] = 'running'
                elif 'neo4j-browser' in line and 'Up' in line:
                    status['neo4j_browser'] = 'running'
            
            return status
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get service status: {e.stderr}")
            return {'error': str(e.stderr)}
    
    def show_status(self):
        """Show current status and URLs"""
        status = self.get_service_status()
        
        print("\n" + "="*60)
        print("CHAINBREAK NEO4J DOCKER STATUS")
        print("="*60)
        
        print(f"Neo4j Database: {status.get('neo4j', 'unknown')}")
        print(f"ChainBreak App: {status.get('chainbreak_app', 'unknown')}")
        print(f"Neo4j Browser: {status.get('neo4j_browser', 'unknown')}")
        
        print("\nURLs:")
        print(f"Neo4j Browser: http://localhost:7474")
        print(f"Neo4j Bolt: bolt://localhost:7687")
        print(f"ChainBreak API: http://localhost:5001")
        print(f"ChainBreak Frontend: http://localhost:3000")
        
        print("\nCredentials:")
        print("Neo4j Username: neo4j")
        print("Neo4j Password: password")
        
        print("="*60)


def main():
    """Main function"""
    print("🔗 ChainBreak Neo4j Docker Manager")
    print("="*50)
    
    manager = Neo4jDockerManager()
    
    # Check prerequisites
    if not manager.check_docker_installed():
        print("\n❌ Please install Docker Desktop and ensure it's running")
        print("Download from: https://www.docker.com/products/docker-desktop")
        return
    
    if not manager.check_docker_compose_file():
        print("\n❌ Docker compose file not found")
        return
    
    while True:
        print("\nChoose an option:")
        print("1. Start Neo4j only")
        print("2. Start Neo4j + ChainBreak App")
        print("3. Start Neo4j + ChainBreak App + Browser")
        print("4. Stop all services")
        print("5. Show status")
        print("6. Test Neo4j connection")
        print("7. Exit")
        
        choice = input("\nEnter your choice (1-7): ").strip()
        
        if choice == "1":
            if manager.start_neo4j():
                if manager.wait_for_neo4j():
                    print("✅ Neo4j started successfully!")
                    manager.show_status()
                else:
                    print("❌ Neo4j failed to start properly")
        
        elif choice == "2":
            if manager.start_neo4j():
                if manager.wait_for_neo4j():
                    if manager.test_neo4j_connection():
                        if manager.start_chainbreak_app():
                            print("✅ Neo4j and ChainBreak App started successfully!")
                            manager.show_status()
                        else:
                            print("❌ Failed to start ChainBreak App")
                    else:
                        print("❌ Neo4j connection test failed")
                else:
                    print("❌ Neo4j failed to start properly")
        
        elif choice == "3":
            if manager.start_neo4j():
                if manager.wait_for_neo4j():
                    if manager.test_neo4j_connection():
                        if manager.start_chainbreak_app():
                            if manager.start_neo4j_browser():
                                print("✅ All services started successfully!")
                                manager.show_status()
                            else:
                                print("⚠️ Neo4j and ChainBreak App started, but Browser failed")
                        else:
                            print("❌ Failed to start ChainBreak App")
                    else:
                        print("❌ Neo4j connection test failed")
                else:
                    print("❌ Neo4j failed to start properly")
        
        elif choice == "4":
            if manager.stop_all_services():
                print("✅ All services stopped successfully!")
            else:
                print("❌ Failed to stop services")
        
        elif choice == "5":
            manager.show_status()
        
        elif choice == "6":
            if manager.test_neo4j_connection():
                print("✅ Neo4j connection test successful!")
            else:
                print("❌ Neo4j connection test failed")
        
        elif choice == "7":
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
