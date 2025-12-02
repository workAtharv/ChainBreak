import json
import networkx as nx
import community.community_louvain as community_louvain
import matplotlib.pyplot as plt
import graphs from data.graph as graphs

# 1. Your Data (Fixed JSON format for the script)

json_data = """
{
  "nodes": [
    {"id": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh", "label": "bc1qxy2kgdyg", "type": "address"},
    {"id": "7242385e142a5902c6de8f2324ef7e43acb7e9aa765642b197756b1000460c5a", "label": "7242385e142a", "type": "transaction"},
    {"id": "bc1ql4y9tzsyhavaw689tv45wa4f8hckm69uf7xk0c", "label": "bc1ql4y9tzsy", "type": "address"},
    {"id": "bc1qgcp2xfsp5g5ksuqqv5kh5lqwfd8nrtsq03ky4h", "label": "bc1qgcp2xfsp5g5ksuqqv5kh5lqwfd8nrtsq03ky4h", "type": "address"},
    {"id": "bc1qm4jggrp3qkh9hkh5qvmjw7rr9td649w45m3agh", "label": "bc1qm4jggrp3qkh9hkh5qvmjw7rr9td649w45m3agh", "type": "address"}
  ],
  "edges": [
    {
      "source": "bc1ql4y9tzsyhavaw689tv45wa4f8hckm69uf7xk0c",
      "target": "7242385e142a5902c6de8f2324ef7e43acb7e9aa765642b197756b1000460c5a",
      "value": 51467
    },
    {
      "source": "bc1qgcp2xfsp5g5ksuqqv5kh5lqwfd8nrtsq03ky4h",
      "target": "7242385e142a5902c6de8f2324ef7e43acb7e9aa765642b197756b1000460c5a",
      "value": 23150
    },
    {
      "source": "7242385e142a5902c6de8f2324ef7e43acb7e9aa765642b197756b1000460c5a",
      "target": "bc1qm4jggrp3qkh9hkh5qvmjw7rr9td649w45m3agh",
      "value": 69969
    }
  ]
}
"""

# Load data
data = json.loads(json_data)

# 2. Build the Graph
G = nx.Graph() # Louvain works best with undirected graphs

# Add Nodes
for node in data['nodes']:
    # We store the 'type' (address/transaction) as an attribute to use later
    G.add_node(node['id'], label=node['label'], node_type=node['type'])

# Add Edges
for edge in data['edges']:
    # We use the transaction value as the WEIGHT
    # Higher value = Stronger connection
    G.add_edge(edge['source'], edge['target'], weight=edge['value'])

# 3. Apply Louvain Algorithm
# The resolution parameter controls the size of communities. 
# 1.0 is standard. >1.0 = smaller communities, <1.0 = larger communities.
partition = community_louvain.best_partition(G, weight='value')

# 4. Process and Display Results
# The partition is a dictionary {node_id: community_id}

# Organize nodes by community
communities = {}
for node, comm_id in partition.items():
    if comm_id not in communities:
        communities[comm_id] = []
    communities[comm_id].append(node)

print(f"Total Communities Found: {len(communities)}\n")

for comm_id, members in communities.items():
    print(f"--- Community {comm_id} ---")
    for member in members:
        # Fetch node type to distinguish Address from Transaction
        n_type = G.nodes[member]['node_type']
        label = G.nodes[member].get('label', member[:10])
        print(f"  [{n_type.upper()}] {label}...")
    print("\n")

# 5. Visualization (Optional)


#[Image of Graph Network Visualization]

# We color code the nodes based on their assigned community
pos = nx.spring_layout(G)
cmap = plt.cm.get_cmap('viridis', max(partition.values()) + 1)

plt.figure(figsize=(10, 6))
nx.draw_networkx_nodes(G, pos, partition.keys(), node_size=300, 
                       cmap=cmap, node_color=list(partition.values()))
nx.draw_networkx_edges(G, pos, alpha=0.5)
nx.draw_networkx_labels(G, pos, labels=nx.get_node_attributes(G, 'label'), font_size=8)
plt.title("Bitcoin Transaction Communities (Louvain)")
plt.show()