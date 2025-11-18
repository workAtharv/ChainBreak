#!/usr/bin/env python3
"""
ChainBreak Main Application
Blockchain Forensic Analysis Tool

Usage:
    python app.py                    # Run standalone analysis
    python app.py --api             # Start API server
    python app.py --analyze <addr>  # Analyze specific address
"""

from src.utils import DataValidator
from src.utils import LogManager
from src.api import create_app
from src.chainbreak import ChainBreak
import argparse
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


logger = logging.getLogger(__name__)


def run_standalone_analysis(address: str = None):
    """Run standalone ChainBreak analysis"""
    try:
        print("🔗 ChainBreak - Blockchain Forensic Analysis Tool")
        print("=" * 60)

        # Initialize ChainBreak
        print("Initializing ChainBreak...")
        chainbreak = ChainBreak()

        # Check system status
        print("\nChecking system status...")
        status = chainbreak.get_system_status()
        print(f"System Status: {status['system_status']}")
        print(f"Neo4j Connection: {status['neo4j_connection']}")

        if status['system_status'] != 'operational':
            print(
                "❌ System not operational. Please check configuration and Neo4j connection.")
            return

        # If no address provided, use a default test address
        if not address:
            address = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"  # Genesis block address
            print(f"\nNo address provided, using test address: {address}")

        # Validate address
        if not DataValidator.validate_bitcoin_address(address):
            print(f"❌ Invalid Bitcoin address: {address}")
            return

        # Run analysis
        print(f"\n🚀 Starting analysis of address: {address}")
        print("This may take several minutes depending on transaction volume...")

        results = chainbreak.analyze_address(
            address, generate_visualizations=True)

        if 'error' in results:
            print(f"❌ Analysis failed: {results['error']}")
            return

        # Display results
        print("\n✅ Analysis completed successfully!")
        print("\n📊 Analysis Summary:")
        print(f"  Address: {results['address']}")
        print(f"  Blockchain: {results['blockchain']}")
        print(f"  Risk Level: {results['risk_score']['risk_level']}")
        print(f"  Risk Score: {results['risk_score']['total_risk_score']:.3f}")
        print(f"  Total Anomalies: {results['summary']['total_anomalies']}")
        print(f"  Layering Patterns: {results['summary']['layering_count']}")
        print(f"  Smurfing Patterns: {results['summary']['smurfing_count']}")
        print(
            f"  Volume Anomalies: {results['summary']['volume_anomaly_count']}")

        # Display recommendations
        if results['summary']['recommendations']:
            print("\n💡 Recommendations:")
            for rec in results['summary']['recommendations']:
                print(f"  • {rec}")

        # Export to Gephi if requested
        export_choice = input(
            "\n📤 Export network to Gephi format? (y/n): ").lower().strip()
        if export_choice in ['y', 'yes']:
            print("Exporting to Gephi...")
            export_file = chainbreak.export_network_to_gephi(address)
            if export_file:
                print(f"✅ Network exported to: {export_file}")
            else:
                print("❌ Export failed")

        print("\n🎉 Analysis complete! Check the generated visualizations and log files.")

    except KeyboardInterrupt:
        print("\n\n⚠️  Analysis interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during analysis: {str(e)}")
        logger.error(f"Standalone analysis error: {str(e)}")
    finally:
        if 'chainbreak' in locals():
            chainbreak.close()


def run_api_server():
    """Start the Flask API server with WebSocket support"""
    try:
        print("🔗 Starting ChainBreak API Server...")
        print("=" * 50)

        from src.api import run_app

        print("✅ API server initialized successfully!")
        print("📖 API Documentation: http://localhost:5000/")
        print("🔌 API Endpoints:")
        print("  GET  /api/status          - System status")
        print("  POST /api/analyze         - Analyze single address")
        print("  POST /api/analyze/batch   - Analyze multiple addresses")
        print("  GET  /api/export/gephi    - Export to Gephi")
        print("  POST /api/report/risk     - Generate risk report")
        print("  POST /api/community-detection/detect  - Community detection")
        print("  WS   /socket.io           - Real-time WebSocket")
        print("\n🚀 Server running on http://localhost:5000")
        print("Press Ctrl+C to stop the server")

        run_app(debug=False, host='0.0.0.0', port=5000)

    except KeyboardInterrupt:
        print("\n\n⚠️  API server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting API server: {str(e)}")
        logger.error(f"API server error: {str(e)}")


def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(
        description="ChainBreak - Blockchain Forensic Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python app.py                           # Run standalone analysis
  python app.py --api                     # Start API server
  python app.py --analyze 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa
  python app.py --config custom_config.yaml
        """
    )

    parser.add_argument(
        '--api',
        action='store_true',
        help='Start the Flask API server'
    )

    parser.add_argument(
        '--analyze',
        metavar='ADDRESS',
        help='Analyze a specific Bitcoin address'
    )

    parser.add_argument(
        '--config',
        metavar='CONFIG_FILE',
        default='config.yaml',
        help='Configuration file path (default: config.yaml)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Setup logging
    LogManager()
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('chainbreak.log'),
            logging.StreamHandler()
        ]
    )

    # Check if config file exists
    if not Path(args.config).exists():
        print(
            f"⚠️  Configuration file {args.config} not found, using defaults")

    # Run appropriate mode
    if args.api:
        run_api_server()
    elif args.analyze:
        run_standalone_analysis(args.analyze)
    else:
        run_standalone_analysis()


if __name__ == '__main__':
    main()
