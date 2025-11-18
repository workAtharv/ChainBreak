"""
Community Detection Algorithms for ChainBreak
Implements Louvain, Leiden, and Label Propagation algorithms for graph analysis
"""

import logging
from typing import Dict, Any, List, Set, Tuple, Optional
import networkx as nx
from collections import defaultdict, Counter
import random
import math
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)


class CommunityDetector:
    """Implements multiple community detection algorithms for blockchain graph analysis"""

    def __init__(self, neo4j_driver=None):
        self.driver = neo4j_driver

    def detect_communities(self, graph_data: Dict[str, Any], algorithm: str = 'louvain') -> Dict[str, Any]:
        """
        Main entry point for community detection

        Args:
            graph_data: Dictionary with 'nodes' and 'edges' lists
            algorithm: One of 'louvain', 'leiden', 'label_propagation'

        Returns:
            Dictionary with community assignments and statistics
        """
        try:
            logger.info(f"Starting community detection with {algorithm} algorithm")

            # Build NetworkX graph from data
            G = self._build_networkx_graph(graph_data)

            if len(G.nodes()) == 0:
                logger.warning("Empty graph provided")
                return self._empty_result()

            # Run selected algorithm
            if algorithm.lower() == 'louvain':
                communities = self._louvain_algorithm(G)
            elif algorithm.lower() == 'leiden':
                communities = self._leiden_algorithm(G)
            elif algorithm.lower() == 'label_propagation':
                communities = self._label_propagation_algorithm(G)
            else:
                logger.error(f"Unknown algorithm: {algorithm}")
                return self._empty_result()

            # Calculate statistics
            stats = self._calculate_community_stats(G, communities)

            result = {
                'algorithm': algorithm,
                'communities': communities,
                'statistics': stats,
                'node_count': len(G.nodes()),
                'edge_count': len(G.edges()),
                'community_count': len(set(communities.values()))
            }

            logger.info(f"Community detection complete: {result['community_count']} communities found")
            return result

        except Exception as e:
            logger.error(f"Error in community detection: {str(e)}")
            return self._empty_result()

    def _build_networkx_graph(self, graph_data: Dict[str, Any]) -> nx.Graph:
        """Convert graph data to NetworkX graph"""
        G = nx.Graph()

        # Add nodes
        nodes = graph_data.get('nodes', [])
        for node in nodes:
            node_id = node.get('id') or node.get('address')
            if node_id:
                G.add_node(node_id, **node)

        # Add edges with weights
        edges = graph_data.get('edges', [])
        for edge in edges:
            source = edge.get('source')
            target = edge.get('target')
            weight = edge.get('value', 1.0) or 1.0

            if source and target:
                # Normalize weight (convert satoshis to BTC for better scaling)
                normalized_weight = float(weight) / 100000000.0 if weight > 1000 else float(weight)
                G.add_edge(source, target, weight=normalized_weight)

        logger.info(f"Built NetworkX graph: {len(G.nodes())} nodes, {len(G.edges())} edges")
        return G

    def _louvain_algorithm(self, G: nx.Graph, resolution: float = 1.0) -> Dict[str, int]:
        """
        Implementation of the Louvain algorithm for community detection

        The Louvain method is a greedy optimization algorithm that optimizes modularity.
        It works in two phases that are repeated iteratively:
        1. Local moving: Each node is moved to the community that maximizes modularity gain
        2. Aggregation: Communities are aggregated into super-nodes
        """
        logger.info("Running Louvain algorithm")

        # Initialize: each node in its own community
        communities = {node: idx for idx, node in enumerate(G.nodes())}

        # Calculate initial modularity
        m = G.number_of_edges()
        if m == 0:
            return communities

        improved = True
        iteration = 0
        max_iterations = 100

        while improved and iteration < max_iterations:
            improved = False
            iteration += 1

            # Phase 1: Local moving
            nodes = list(G.nodes())
            random.shuffle(nodes)  # Random order for better results

            for node in nodes:
                current_community = communities[node]

                # Get neighboring communities
                neighbor_communities = self._get_neighbor_communities(G, node, communities)

                if not neighbor_communities:
                    continue

                # Calculate modularity gain for each neighbor community
                best_community = current_community
                best_gain = 0.0

                for neighbor_comm in neighbor_communities:
                    gain = self._modularity_gain(G, node, current_community, neighbor_comm, communities, resolution)

                    if gain > best_gain:
                        best_gain = gain
                        best_community = neighbor_comm

                # Move node if improvement found
                if best_community != current_community and best_gain > 1e-10:
                    communities[node] = best_community
                    improved = True

            logger.debug(f"Louvain iteration {iteration}: {len(set(communities.values()))} communities")

        # Renumber communities to be consecutive
        communities = self._renumber_communities(communities)

        logger.info(f"Louvain algorithm complete after {iteration} iterations")
        return communities

    def _leiden_algorithm(self, G: nx.Graph, resolution: float = 1.0) -> Dict[str, int]:
        """
        Implementation of the Leiden algorithm for community detection

        The Leiden algorithm improves upon Louvain by:
        1. Moving nodes to different communities (like Louvain)
        2. Refining partitions by exploring all possible moves
        3. Aggregating communities based on refined partition

        This ensures well-connected communities and faster convergence.
        """
        logger.info("Running Leiden algorithm")

        # Initialize: each node in its own community
        communities = {node: idx for idx, node in enumerate(G.nodes())}

        m = G.number_of_edges()
        if m == 0:
            return communities

        improved = True
        iteration = 0
        max_iterations = 100

        while improved and iteration < max_iterations:
            improved = False
            iteration += 1

            # Phase 1: Local moving (similar to Louvain)
            nodes = list(G.nodes())
            random.shuffle(nodes)

            moved_nodes = set()

            for node in nodes:
                current_community = communities[node]
                neighbor_communities = self._get_neighbor_communities(G, node, communities)

                if not neighbor_communities:
                    continue

                best_community = current_community
                best_gain = 0.0

                for neighbor_comm in neighbor_communities:
                    gain = self._modularity_gain(G, node, current_community, neighbor_comm, communities, resolution)

                    if gain > best_gain:
                        best_gain = gain
                        best_community = neighbor_comm

                if best_community != current_community and best_gain > 1e-10:
                    communities[node] = best_community
                    moved_nodes.add(node)
                    improved = True

            # Phase 2: Refinement (unique to Leiden)
            # Refine partition by considering sub-communities
            if moved_nodes:
                communities = self._refine_partition(G, communities, moved_nodes, resolution)

            logger.debug(f"Leiden iteration {iteration}: {len(set(communities.values()))} communities")

        # Renumber communities
        communities = self._renumber_communities(communities)

        logger.info(f"Leiden algorithm complete after {iteration} iterations")
        return communities

    def _label_propagation_algorithm(self, G: nx.Graph) -> Dict[str, int]:
        """
        Implementation of Label Propagation algorithm for community detection

        Label Propagation is a fast algorithm where:
        1. Each node is initialized with a unique label (community ID)
        2. Iteratively, each node adopts the label most common among its neighbors
        3. Process continues until convergence or max iterations

        It's faster than Louvain/Leiden but may be less accurate.
        """
        logger.info("Running Label Propagation algorithm")

        # Initialize: each node gets its own label
        labels = {node: idx for idx, node in enumerate(G.nodes())}

        if len(labels) == 0:
            return labels

        converged = False
        iteration = 0
        max_iterations = 100

        while not converged and iteration < max_iterations:
            iteration += 1
            converged = True

            # Process nodes in random order
            nodes = list(G.nodes())
            random.shuffle(nodes)

            for node in nodes:
                # Get labels of neighbors
                neighbor_labels = []
                for neighbor in G.neighbors(node):
                    # Weight by edge weight if available
                    weight = G[node][neighbor].get('weight', 1.0)
                    neighbor_labels.extend([labels[neighbor]] * max(1, int(weight)))

                if not neighbor_labels:
                    continue

                # Find most common label
                label_counts = Counter(neighbor_labels)
                most_common_label = label_counts.most_common(1)[0][0]

                # Update if different
                if labels[node] != most_common_label:
                    labels[node] = most_common_label
                    converged = False

            logger.debug(f"Label Propagation iteration {iteration}: {len(set(labels.values()))} communities")

        # Renumber communities
        labels = self._renumber_communities(labels)

        logger.info(f"Label Propagation complete after {iteration} iterations")
        return labels

    def _get_neighbor_communities(self, G: nx.Graph, node: str, communities: Dict[str, int]) -> Set[int]:
        """Get set of communities that are neighbors of the given node"""
        neighbor_communities = set()

        for neighbor in G.neighbors(node):
            neighbor_communities.add(communities[neighbor])

        # Also consider current community
        neighbor_communities.add(communities[node])

        return neighbor_communities

    def _modularity_gain(self, G: nx.Graph, node: str, from_comm: int, to_comm: int,
                        communities: Dict[str, int], resolution: float = 1.0) -> float:
        """
        Calculate modularity gain from moving node from one community to another

        Modularity measures the quality of a partition:
        Q = (1/2m) * Σ[A_ij - (k_i * k_j)/2m] * δ(c_i, c_j)

        Where:
        - m is the number of edges
        - A_ij is the adjacency matrix
        - k_i is the degree of node i
        - δ(c_i, c_j) is 1 if nodes i and j are in the same community
        """
        if from_comm == to_comm:
            return 0.0

        m = G.number_of_edges()
        if m == 0:
            return 0.0

        # Calculate edge weights to communities
        k_i = G.degree(node, weight='weight')
        k_i_in_from = 0.0
        k_i_in_to = 0.0

        for neighbor in G.neighbors(node):
            weight = G[node][neighbor].get('weight', 1.0)

            if communities[neighbor] == from_comm:
                k_i_in_from += weight
            elif communities[neighbor] == to_comm:
                k_i_in_to += weight

        # Calculate community degrees
        sigma_from = sum(G.degree(n, weight='weight') for n in communities if communities[n] == from_comm)
        sigma_to = sum(G.degree(n, weight='weight') for n in communities if communities[n] == to_comm)

        # Modularity gain calculation
        gain = (k_i_in_to - k_i_in_from) / (2 * m) - resolution * k_i * (sigma_to - sigma_from - k_i) / (4 * m * m)

        return gain

    def _refine_partition(self, G: nx.Graph, communities: Dict[str, int],
                         moved_nodes: Set[str], resolution: float) -> Dict[str, int]:
        """
        Refine partition by exploring sub-communities (Leiden-specific)

        This phase ensures well-connected communities by checking if moved nodes
        should form sub-communities.
        """
        # Create subgraph of moved nodes
        refined_communities = communities.copy()

        # Group moved nodes by their current community
        community_nodes = defaultdict(list)
        for node in moved_nodes:
            community_nodes[communities[node]].append(node)

        # For each community with moved nodes, check connectivity
        for comm_id, nodes in community_nodes.items():
            if len(nodes) < 2:
                continue

            # Create subgraph
            subgraph = G.subgraph(nodes)

            # Check if subgraph is connected
            if not nx.is_connected(subgraph):
                # Split into connected components
                components = list(nx.connected_components(subgraph))

                if len(components) > 1:
                    # Assign new community IDs to components
                    max_comm_id = max(refined_communities.values())

                    for idx, component in enumerate(components[1:], start=1):
                        new_comm_id = max_comm_id + idx
                        for node in component:
                            refined_communities[node] = new_comm_id

        return refined_communities

    def _renumber_communities(self, communities: Dict[str, int]) -> Dict[str, int]:
        """Renumber communities to be consecutive starting from 0"""
        unique_communities = sorted(set(communities.values()))
        community_map = {old_id: new_id for new_id, old_id in enumerate(unique_communities)}

        return {node: community_map[comm_id] for node, comm_id in communities.items()}

    def _calculate_community_stats(self, G: nx.Graph, communities: Dict[str, int]) -> Dict[str, Any]:
        """Calculate statistics about detected communities"""

        # Group nodes by community
        community_groups = defaultdict(list)
        for node, comm_id in communities.items():
            community_groups[comm_id].append(node)

        # Calculate statistics for each community
        community_stats = []

        for comm_id, nodes in community_groups.items():
            subgraph = G.subgraph(nodes)

            # Calculate internal edges
            internal_edges = subgraph.number_of_edges()

            # Calculate external edges
            external_edges = 0
            for node in nodes:
                for neighbor in G.neighbors(node):
                    if communities[neighbor] != comm_id:
                        external_edges += 1

            # Calculate total volume (sum of transaction values)
            total_volume = sum(G[u][v].get('weight', 1.0) for u, v in subgraph.edges())

            # Density
            possible_edges = len(nodes) * (len(nodes) - 1) / 2
            density = internal_edges / possible_edges if possible_edges > 0 else 0.0

            community_stats.append({
                'community_id': comm_id,
                'size': len(nodes),
                'internal_edges': internal_edges,
                'external_edges': external_edges,
                'density': density,
                'total_volume': total_volume,
                'nodes': nodes[:10]  # Sample of nodes
            })

        # Sort by size
        community_stats.sort(key=lambda x: x['size'], reverse=True)

        # Calculate modularity
        modularity = self._calculate_modularity(G, communities)

        return {
            'modularity': modularity,
            'num_communities': len(community_groups),
            'largest_community_size': community_stats[0]['size'] if community_stats else 0,
            'smallest_community_size': community_stats[-1]['size'] if community_stats else 0,
            'average_community_size': sum(c['size'] for c in community_stats) / len(community_stats) if community_stats else 0,
            'communities': community_stats
        }

    def _calculate_modularity(self, G: nx.Graph, communities: Dict[str, int]) -> float:
        """
        Calculate modularity of the partition

        Modularity Q ranges from -1 to 1:
        - Q > 0.3 indicates significant community structure
        - Q > 0.7 indicates very strong community structure
        """
        m = G.number_of_edges()
        if m == 0:
            return 0.0

        Q = 0.0

        for edge in G.edges():
            u, v = edge
            weight = G[u][v].get('weight', 1.0)

            if communities[u] == communities[v]:
                k_u = G.degree(u, weight='weight')
                k_v = G.degree(v, weight='weight')

                Q += weight - (k_u * k_v) / (2 * m)

        Q = Q / (2 * m)

        return Q

    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result structure"""
        return {
            'algorithm': 'none',
            'communities': {},
            'statistics': {
                'modularity': 0.0,
                'num_communities': 0,
                'largest_community_size': 0,
                'smallest_community_size': 0,
                'average_community_size': 0,
                'communities': []
            },
            'node_count': 0,
            'edge_count': 0,
            'community_count': 0
        }

    def compare_algorithms(self, graph_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run all three algorithms and compare results

        Returns comparison metrics including modularity scores and runtime
        """
        import time

        results = {}

        for algorithm in ['louvain', 'leiden', 'label_propagation']:
            start_time = time.time()
            result = self.detect_communities(graph_data, algorithm)
            end_time = time.time()

            results[algorithm] = {
                'result': result,
                'runtime': end_time - start_time,
                'modularity': result['statistics']['modularity'],
                'num_communities': result['community_count']
            }

        # Determine best algorithm by modularity
        best_algorithm = max(results.items(), key=lambda x: x[1]['modularity'])

        return {
            'results': results,
            'best_algorithm': best_algorithm[0],
            'comparison': {
                'louvain_modularity': results['louvain']['modularity'],
                'leiden_modularity': results['leiden']['modularity'],
                'label_propagation_modularity': results['label_propagation']['modularity'],
                'louvain_runtime': results['louvain']['runtime'],
                'leiden_runtime': results['leiden']['runtime'],
                'label_propagation_runtime': results['label_propagation']['runtime']
            }
        }
