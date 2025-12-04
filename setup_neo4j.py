#!/usr/bin/env python3
"""
Neo4j Setup and Connection Test Script
"""

import sys
import os
import logging
from neo4j import GraphDatabase
import yaml

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_config():
    """Load configuration from config.yaml"""
    try:
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return None

def test_neo4j_connection(uri, username, password):
    """Test Neo4j connection"""
    try:
        driver = GraphDatabase.driver(uri, auth=(username, password))
        
        with driver.session() as session:
            result = session.run("RETURN 1 as test")
            record = result.single()
            if record and record["test"] == 1:
                logger.info("✅ Neo4j connection successful!")
                return True
            else:
                logger.error("❌ Neo4j connection test failed")
                return False
                
    except Exception as e:
        logger.error(f"❌ Neo4j connection failed: {e}")
        return False
    finally:
        if 'driver' in locals():
            driver.close()

def setup_neo4j_database(uri, username, password):
    """Setup Neo4j database with constraints and indexes"""
    try:
        driver = GraphDatabase.driver(uri, auth=(username, password))
        
        with driver.session() as session:
            # Create constraints
            constraints = [
                "CREATE CONSTRAINT address_unique IF NOT EXISTS FOR (a:Address) REQUIRE a.address IS UNIQUE",
                "CREATE CONSTRAINT transaction_unique IF NOT EXISTS FOR (t:Transaction) REQUIRE t.tx_hash IS UNIQUE",
                "CREATE CONSTRAINT block_unique IF NOT EXISTS FOR (b:Block) REQUIRE b.block_hash IS UNIQUE"
            ]
            
            for constraint in constraints:
                try:
                    session.run(constraint)
                    logger.info(f"✅ Created constraint: {constraint.split()[2]}")
                except Exception as e:
                    logger.warning(f"⚠️ Constraint creation failed: {e}")
            
            # Create indexes
            indexes = [
                "CREATE INDEX address_balance IF NOT EXISTS FOR (a:Address) ON (a.balance)",
                "CREATE INDEX transaction_value IF NOT EXISTS FOR (t:Transaction) ON (t.value)",
                "CREATE INDEX address_risk_score IF NOT EXISTS FOR (a:Address) ON (a.risk_score)"
            ]
            
            for index in indexes:
                try:
                    session.run(index)
                    logger.info(f"✅ Created index: {index.split()[2]}")
                except Exception as e:
                    logger.warning(f"⚠️ Index creation failed: {e}")
        
        logger.info("✅ Neo4j database setup completed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Neo4j database setup failed: {e}")
        return False
    finally:
        if 'driver' in locals():
            driver.close()

def create_sample_data(uri, username, password):
    """Create sample data for testing"""
    try:
        driver = GraphDatabase.driver(uri, auth=(username, password))
        
        with driver.session() as session:
            # Create sample addresses
            sample_addresses = [
                {
                    "address": "13AM4VW2dhxYgXeQepoHkHSQuy6NgaEb94",
                    "balance": 0,
                    "risk_score": 0.95,
                    "is_illicit": True,
                    "illicit_type": "ransomware"
                },
                {
                    "address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
                    "balance": 5001000000,
                    "risk_score": 0.1,
                    "is_illicit": False,
                    "illicit_type": None
                }
            ]
            
            for addr_data in sample_addresses:
                session.run("""
                    MERGE (a:Address {address: $address})
                    SET a.balance = $balance,
                        a.risk_score = $risk_score,
                        a.is_illicit = $is_illicit,
                        a.illicit_type = $illicit_type,
                        a.created_at = datetime()
                """, **addr_data)
            
            logger.info("✅ Sample data created successfully!")
            return True
            
    except Exception as e:
        logger.error(f"❌ Sample data creation failed: {e}")
        return False
    finally:
        if 'driver' in locals():
            driver.close()

def main():
    """Main function"""
    print("=" * 80)
    print("NEO4J SETUP AND CONNECTION TEST")
    print("=" * 80)
    
    # Load configuration
    config = load_config()
    if not config:
        print("❌ Failed to load configuration")
        return
    
    neo4j_config = config.get('neo4j', {})
    uri = neo4j_config.get('uri', 'bolt://localhost:7687')
    username = neo4j_config.get('username', 'neo4j')
    password = neo4j_config.get('password', 'password')
    
    print(f"\nNeo4j Configuration:")
    print(f"  URI: {uri}")
    print(f"  Username: {username}")
    print(f"  Password: {'*' * len(password)}")
    
    # Test connection
    print(f"\n1. Testing Neo4j connection...")
    if test_neo4j_connection(uri, username, password):
        print("✅ Connection successful!")
        
        # Setup database
        print(f"\n2. Setting up Neo4j database...")
        if setup_neo4j_database(uri, username, password):
            print("✅ Database setup completed!")
            
            # Create sample data
            print(f"\n3. Creating sample data...")
            if create_sample_data(uri, username, password):
                print("✅ Sample data created!")
                
                print(f"\n🎉 Neo4j is ready for use!")
                print(f"\nNext steps:")
                print(f"  1. Run the ChainBreak application")
                print(f"  2. Test threat intelligence integration")
                print(f"  3. Verify graph visualization")
            else:
                print("❌ Sample data creation failed")
        else:
            print("❌ Database setup failed")
    else:
        print("❌ Connection failed!")
        print(f"\nTroubleshooting:")
        print(f"  1. Make sure Neo4j is running on {uri}")
        print(f"  2. Check username/password: {username}/{'*' * len(password)}")
        print(f"  3. Install Neo4j Desktop or use Docker")
        print(f"  4. Update config.yaml with correct connection details")

if __name__ == "__main__":
    main()
