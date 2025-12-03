"""
Quick test to check if python-louvain is installed
"""

try:
    import community.community_louvain as community_louvain
    print("✓ python-louvain is installed")
    print(f"  Version: {community_louvain.__version__ if hasattr(community_louvain, '__version__') else 'unknown'}")
except ImportError as e:
    print("✗ python-louvain is NOT installed")
    print(f"  Error: {e}")
    print("\nTo install, run:")
    print("  pip install python-louvain")
    exit(1)

try:
    import networkx as nx
    print("✓ networkx is installed")
    print(f"  Version: {nx.__version__}")
except ImportError as e:
    print("✗ networkx is NOT installed")
    print(f"  Error: {e}")
    exit(1)

print("\n✓ All dependencies are installed!")
print("You can now run test_louvain_simple.py")
