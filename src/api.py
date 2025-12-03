from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import logging
import traceback
import json
from pathlib import Path
from .chainbreak import ChainBreak
from .api_frontend import bp as frontend_bp

logger = logging.getLogger(__name__)

app = Flask(__name__)

# Enable CORS before registering blueprints
CORS(app, resources={
    r"/api/*": {"origins": ["http://localhost:3000", "http://localhost:5000"]},
    r"/frontend/*": {"origins": ["http://localhost:3000", "http://localhost:5000"]}
})

app.register_blueprint(frontend_bp)

# Unified data directory - use data/graph (consistent with actual structure)
GRAPH_DIR = Path("data/graph")
GRAPH_DIR.mkdir(parents=True, exist_ok=True)

logger.info(f"Graph directory initialized: {GRAPH_DIR.resolve()}")


# Global ChainBreak instance for better performance
_chainbreak_instance = None
_chainbreak_initialized = False

def get_chainbreak():
    """Get or create ChainBreak instance with singleton pattern"""
    global _chainbreak_instance, _chainbreak_initialized

    if _chainbreak_instance is not None and _chainbreak_initialized:
        return _chainbreak_instance

    try:
        from .chainbreak import ChainBreak
        _chainbreak_instance = ChainBreak()
        _chainbreak_initialized = True
        logger.info("ChainBreak instance created successfully")
        return _chainbreak_instance
    except Exception as e:
        logger.error(f"Failed to initialize ChainBreak: {e}")
        _chainbreak_initialized = False
        return None

def reset_chainbreak():
    """Reset ChainBreak instance (useful for testing or reconfiguration)"""
    global _chainbreak_instance, _chainbreak_initialized
    if _chainbreak_instance is not None:
        try:
            _chainbreak_instance.close()
        except Exception as e:
            logger.warning(f"Error closing ChainBreak instance: {e}")

    _chainbreak_instance = None
    _chainbreak_initialized = False
    logger.info("ChainBreak instance reset")


@app.route("/")
def index_new():
    try:
        # Try to serve the React build index.html
        frontend_build = Path("frontend/build").resolve()
        if frontend_build.exists():
            logger.info(f"Serving React frontend from {frontend_build}")
            return send_from_directory(str(frontend_build), "index.html")
        else:
            logger.info(
                "React build not found, falling back to static frontend")
            static_frontend = Path("frontend").resolve()
            return send_from_directory(str(static_frontend), "index.html")
    except Exception as e:
        logger.error(f"Error serving frontend: {e}")
        return jsonify({"error": "Frontend not available"}), 404


@app.route("/static/<path:filename>")
def serve_static(filename):
    try:
        frontend_build = Path("frontend/build/static").resolve()
        if frontend_build.exists():
            logger.info(f"Serving static file from React build: {filename}")
            return send_from_directory(str(frontend_build), filename)
        else:
            logger.info(
                f"React static not found, falling back to static: {filename}")
            static_dir = Path("frontend/static").resolve()
            return send_from_directory(str(static_dir), filename)
    except Exception as e:
        logger.error(f"Error serving static file {filename}: {e}")
        return jsonify({"error": "Static file not found"}), 404


@app.route("/<path:filename>")
def serve_frontend_files(filename):
    try:
        # Skip API routes
        if filename.startswith('api/'):
            return jsonify({"error": "API endpoint not found"}), 404

        frontend_build = Path("frontend/build").resolve()
        if frontend_build.exists():
            file_path = frontend_build / filename
            if file_path.exists() and file_path.is_file():
                logger.info(f"Serving React file: {filename}")
                return send_from_directory(str(frontend_build), filename)

        # Fallback to old static files
        logger.info(
            f"React file not found, falling back to static: {filename}")
        static_dir = Path("frontend").resolve()
        return send_from_directory(str(static_dir), filename)
    except Exception as e:
        logger.error(f"Error serving frontend file {filename}: {e}")
        return jsonify({"error": "File not found"}), 404


@app.route("/api/mode", methods=["GET"])
def get_backend_mode():
    """Get current backend mode"""
    try:
        chainbreak = get_chainbreak()
        if chainbreak:
            return jsonify({
                "success": True,
                "data": {
                    "backend_mode": chainbreak.get_backend_mode(),
                    "neo4j_available": chainbreak.is_neo4j_available()
                }
            })
        else:
            return jsonify({
                "success": False,
                "error": "ChainBreak not initialized"
            }), 500
    except Exception as e:
        logger.error(f"Error getting backend mode: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/status", methods=["GET"])
def get_system_status():
    """Get system status"""
    try:
        chainbreak = get_chainbreak()
        if chainbreak:
            status = chainbreak.get_system_status()
            return jsonify({
                "success": True,
                "data": status
            })
        else:
            return jsonify({
                "success": False,
                "error": "ChainBreak not initialized"
            }), 500
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/graph/list", methods=["GET"])
def list_graphs():
    """List available graph files"""
    try:
        files = [f.name for f in GRAPH_DIR.glob("*.json")]
        return jsonify({"success": True, "files": files})
    except Exception as e:
        logger.error(f"Error listing graphs: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/graph/address", methods=["POST"])
def fetch_graph_address():
    """Fetch and save graph for an address with enhanced error handling"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Invalid JSON data"}), 400

        address = data.get("address", "").strip()
        tx_limit = data.get("tx_limit", 50)

        # Validate inputs
        if not address:
            return jsonify({"success": False, "error": "Address is required"}), 400

        if not isinstance(tx_limit, int) or tx_limit < 1 or tx_limit > 200:
            return jsonify({"success": False, "error": "Transaction limit must be between 1 and 200"}), 400

        # Validate Bitcoin address format
        import re
        if not re.match(r'^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$|^bc1[a-z0-9]{39,59}$', address):
            return jsonify({"success": False, "error": "Invalid Bitcoin address format"}), 400

        chainbreak = get_chainbreak()
        if not chainbreak:
            return jsonify({"success": False, "error": "ChainBreak not initialized"}), 500

        logger.info(f"Fetching graph for address: {address[:10]}... with limit {tx_limit}")

        # Import here to avoid circular imports
        from .fetch_blockchain_com import BlockchainComFetcher, BlockchainAPIError, RateLimitError

        try:
            fetcher = BlockchainComFetcher()
            graph = fetcher.build_graph_for_address(address, tx_limit=tx_limit)
        except RateLimitError as e:
            logger.warning(f"Rate limit exceeded for address {address}: {e}")
            return jsonify({"success": False, "error": "API rate limit exceeded. Please try again later."}), 429
        except BlockchainAPIError as e:
            logger.error(f"Blockchain API error for address {address}: {e}")
            return jsonify({"success": False, "error": f"Blockchain API error: {str(e)}"}), 502
        except Exception as e:
            logger.error(f"Unexpected error fetching graph for {address}: {e}")
            return jsonify({"success": False, "error": "Failed to fetch blockchain data"}), 500

        # Validate graph data
        if not graph or not isinstance(graph, dict):
            return jsonify({"success": False, "error": "Invalid graph data received"}), 500

        nodes = graph.get("nodes", [])
        if len(nodes) == 0:
            return jsonify({"success": False, "error": "No transaction data found for this address"}), 404

        # Sanitize filename - only allow alphanumeric, underscore, hyphen
        safe_address = re.sub(r'[^A-Za-z0-9_\-]', '_', address)
        filename = f"graph_{safe_address[:12]}_{tx_limit}.json"

        try:
            file_path = GRAPH_DIR / filename
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(graph, f, indent=2, ensure_ascii=False)

            logger.info(f"Graph saved: {filename} with {len(nodes)} nodes, {len(graph.get('edges', []))} edges")

            return jsonify({
                "success": True,
                "file": filename,
                "meta": graph.get("meta", {}),
                "stats": {
                    "nodes": len(nodes),
                    "edges": len(graph.get("edges", [])),
                    "tx_limit": tx_limit
                }
            })

        except Exception as e:
            logger.error(f"Error saving graph file {filename}: {e}")
            return jsonify({"success": False, "error": "Failed to save graph data"}), 500

    except Exception as e:
        logger.error(f"Unexpected error in fetch_graph_address: {traceback.format_exc()}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@app.route("/api/graph/get", methods=["GET"])
def get_graph():
    """Get a specific graph by name"""
    try:
        name = request.args.get("name")
        if not name:
            return jsonify({"success": False, "error": "Name parameter required"}), 400

        file_path = GRAPH_DIR / name
        if not file_path.exists():
            return jsonify({"success": False, "error": "Graph not found"}), 404

        with open(file_path, "r") as f:
            graph_json = json.load(f)

        return jsonify(graph_json)

    except Exception as e:
        logger.error(f"Error getting graph: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/analyze", methods=["POST"])
def analyze_address():
    """Analyze a single address"""
    try:
        data = request.get_json()
        address = data.get("address")
        blockchain = data.get("blockchain", "btc")
        generate_visualizations = data.get("generate_visualizations", True)

        if not address:
            return jsonify({"success": False, "error": "Address required"}), 400

        chainbreak = get_chainbreak()
        if not chainbreak:
            return jsonify({"success": False, "error": "ChainBreak not initialized"}), 500

        result = chainbreak.analyze_address(
            address, blockchain, generate_visualizations)
        return jsonify({"success": True, "data": result})

    except Exception as e:
        logger.error(f"Error analyzing address: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/analyze/batch", methods=["POST"])
def analyze_multiple_addresses():
    """Analyze multiple addresses"""
    try:
        data = request.get_json()
        addresses = data.get("addresses", [])
        blockchain = data.get("blockchain", "btc")

        if not addresses:
            return jsonify({"success": False, "error": "Addresses array required"}), 400

        chainbreak = get_chainbreak()
        if not chainbreak:
            return jsonify({"success": False, "error": "ChainBreak not initialized"}), 500

        result = chainbreak.analyze_multiple_addresses(addresses, blockchain)
        return jsonify({"success": True, "data": result})

    except Exception as e:
        logger.error(f"Error analyzing addresses: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/export/gephi", methods=["GET"])
def export_to_gephi():
    """Export network to Gephi format"""
    try:
        address = request.args.get("address")
        output_file = request.args.get("output_file")

        if not address:
            return jsonify({"success": False, "error": "Address parameter required"}), 400

        chainbreak = get_chainbreak()
        if not chainbreak:
            return jsonify({"success": False, "error": "ChainBreak not initialized"}), 500

        result = chainbreak.export_network_to_gephi(address, output_file)
        return jsonify({"success": True, "data": {"file": result}})

    except Exception as e:
        logger.error(f"Error exporting to Gephi: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/report/risk", methods=["POST"])
def generate_risk_report():
    """Generate risk report for addresses"""
    try:
        data = request.get_json()
        addresses = data.get("addresses", [])
        output_file = data.get("output_file")

        if not addresses:
            return jsonify({"success": False, "error": "Addresses array required"}), 400

        chainbreak = get_chainbreak()
        if not chainbreak:
            return jsonify({"success": False, "error": "ChainBreak not initialized"}), 500

        result = chainbreak.generate_risk_report(addresses, output_file)
        return jsonify({"success": True, "data": {"report": result}})

    except Exception as e:
        logger.error(f"Error generating risk report: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/addresses", methods=["GET"])
def get_analyzed_addresses():
    """Get list of analyzed addresses"""
    try:
        chainbreak = get_chainbreak()
        if not chainbreak:
            return jsonify({"success": False, "error": "ChainBreak not initialized"}), 500

        # This would need to be implemented in ChainBreak class
        return jsonify({"success": True, "data": {"addresses": []}})

    except Exception as e:
        logger.error(f"Error getting addresses: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/statistics", methods=["GET"])
def get_statistics():
    """Get system statistics"""
    try:
        chainbreak = get_chainbreak()
        if not chainbreak:
            return jsonify({"success": False, "error": "ChainBreak not initialized"}), 500

        # This would need to be implemented in ChainBreak class
        return jsonify({"success": True, "data": {"statistics": {}}})

    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/threat-intelligence/status", methods=["GET"])
def get_threat_intelligence_status():
    """Get threat intelligence system status"""
    try:
        chainbreak = get_chainbreak()
        if not chainbreak:
            return jsonify({"success": False, "error": "ChainBreak not initialized"}), 500

        status = chainbreak.get_threat_intelligence_status()
        return jsonify({"success": True, "data": status})

    except Exception as e:
        logger.error(f"Error getting threat intelligence status: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/threat-intelligence/check", methods=["POST"])
def check_address_threat_intelligence():
    """Check an address against threat intelligence sources"""
    try:
        data = request.get_json()
        address = data.get("address")

        if not address:
            return jsonify({"success": False, "error": "Address required"}), 400

        chainbreak = get_chainbreak()
        if not chainbreak:
            return jsonify({"success": False, "error": "ChainBreak not initialized"}), 500

        result = chainbreak.threat_intel_manager.check_address(address)
        return jsonify({"success": True, "data": result})

    except Exception as e:
        logger.error(f"Error checking address threat intelligence: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/threat-intelligence/check-graph", methods=["POST"])
def check_graph_illicit_addresses():
    """Check all addresses in a graph for illicit activity"""
    try:
        data = request.get_json()
        graph_data = data.get("graph_data")

        if not graph_data:
            return jsonify({"success": False, "error": "Graph data required"}), 400

        chainbreak = get_chainbreak()
        if not chainbreak:
            return jsonify({"success": False, "error": "ChainBreak not initialized"}), 500

        result = chainbreak.check_illicit_addresses_in_graph(graph_data)
        return jsonify({"success": True, "data": result})

    except Exception as e:
        logger.error(f"Error checking graph illicit addresses: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/louvain", methods=["POST"])
def run_louvain_community_detection():
    """
    Run Louvain community detection algorithm on graph data.
    
    Request body:
    {
        "nodes": [{"id": "...", "label": "...", "type": "..."}],
        "edges": [{"source": "...", "target": "...", "value": 123}],
        "resolution": 1.0  // optional, default 1.0
    }
    
    Response:
    {
        "success": true,
        "data": {
            "partition": {"node_id": community_id, ...},
            "communities": {"0": ["node1", "node2"], "1": [...]},
            "modularity": 0.4523,
            "num_communities": 3
        }
    }
    """
    try:
        data = request.get_json()
        
        # Validate input
        if not data:
            return jsonify({"success": False, "error": "Invalid JSON data"}), 400
        
        if "nodes" not in data or "edges" not in data:
            return jsonify({"success": False, "error": "Missing 'nodes' or 'edges' in request"}), 400
        
        nodes = data.get("nodes", [])
        edges = data.get("edges", [])
        
        if len(nodes) == 0:
            return jsonify({"success": False, "error": "Graph must have at least one node"}), 400
        
        if len(edges) == 0:
            return jsonify({"success": False, "error": "Graph must have at least one edge"}), 400
        
        resolution = data.get("resolution", 1.0)
        
        # Validate resolution parameter
        if not isinstance(resolution, (int, float)) or resolution <= 0:
            return jsonify({"success": False, "error": "Resolution must be a positive number"}), 400
        
        logger.info(f"Running Louvain algorithm on graph with {len(nodes)} nodes and {len(edges)} edges")
        
        # Import the Louvain function
        try:
            from .test_louvain_simple import run_louvain_algorithm
        except ImportError:
            logger.error("Failed to import run_louvain_algorithm - test_louvain_simple.py not found")
            return jsonify({"success": False, "error": "Louvain algorithm not available"}), 500
        
        # Prepare graph data
        graph_data = {
            "nodes": nodes,
            "edges": edges
        }
        
        # Run Louvain algorithm
        try:
            results = run_louvain_algorithm(graph_data, resolution=resolution)
        except Exception as e:
            logger.error(f"Louvain algorithm execution failed: {e}")
            logger.error(traceback.format_exc())
            return jsonify({"success": False, "error": f"Algorithm execution failed: {str(e)}"}), 500
        
        # Format response (remove NetworkX graph object)
        response_data = {
            "partition": results["partition"],
            "communities": {str(k): v for k, v in results["communities"].items()},
            "modularity": results["modularity"],
            "num_communities": results["num_communities"]
        }
        
        logger.info(f"Louvain completed: {results['num_communities']} communities, modularity={results['modularity']:.4f}")
        
        return jsonify({"success": True, "data": response_data}), 200
        
    except Exception as e:
        logger.error(f"Error in Louvain endpoint: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": "Internal server error"}), 500



@app.errorhandler(404)
def not_found(error):
    logger.warning(f"404 error: {request.url}")
    return jsonify({"error": "Not found", "path": request.path}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 error: {error}")
    return jsonify({"error": "Internal server error"}), 500


def get_current_timestamp():
    from datetime import datetime
    return datetime.now().isoformat()


def create_app(config=None):
    if config:
        app.config.update(config)
    return app


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
