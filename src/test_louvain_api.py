"""
Test script to verify the Louvain API endpoint
Run this after starting the Flask server to test the /api/louvain endpoint
"""

import requests
import json
from pathlib import Path

# API endpoint
API_URL = "http://localhost:5001/api/louvain"

def test_louvain_endpoint():
    """Test the Louvain API endpoint with sample graph data"""
    
    # Load sample graph data
    graph_file = Path("data/graph/example1.json")
    
    if not graph_file.exists():
        print(f"❌ Graph file not found: {graph_file}")
        return
    
    with open(graph_file, 'r') as f:
        graph_data = json.load(f)
    
    print("=" * 60)
    print("TESTING LOUVAIN API ENDPOINT")
    print("=" * 60)
    print(f"Graph: {len(graph_data['nodes'])} nodes, {len(graph_data['edges'])} edges")
    print()
    
    # Prepare request data
    request_data = {
        "nodes": graph_data["nodes"],
        "edges": graph_data["edges"],
        "resolution": 1.0
    }
    
    try:
        print(f"Sending POST request to {API_URL}...")
        response = requests.post(
            API_URL,
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print()
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("success"):
                data = result["data"]
                
                print("✅ SUCCESS!")
                print("=" * 60)
                print(f"Number of Communities: {data['num_communities']}")
                print(f"Modularity Score: {data['modularity']:.4f}")
                print()
                
                print("Communities:")
                for comm_id, members in sorted(data["communities"].items(), key=lambda x: int(x[0])):
                    print(f"  Community {comm_id}: {len(members)} nodes")
                    for member in members[:3]:  # Show first 3 members
                        print(f"    - {member[:20]}...")
                    if len(members) > 3:
                        print(f"    ... and {len(members) - 3} more")
                
                print()
                print("Partition (first 5 nodes):")
                for i, (node_id, comm_id) in enumerate(list(data["partition"].items())[:5]):
                    print(f"  {node_id[:30]}... → Community {comm_id}")
                
                print("=" * 60)
                print("✅ API endpoint is working correctly!")
                
            else:
                print(f"❌ API returned error: {result.get('error')}")
        
        else:
            print(f"❌ HTTP Error {response.status_code}")
            print(f"Response: {response.text}")
    
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error!")
        print("Make sure the Flask server is running:")
        print("  python src/api.py")
        print("  OR")
        print("  flask run")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_louvain_endpoint()
