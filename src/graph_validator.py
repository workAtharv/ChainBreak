"""
Graph Data Validator for ChainBreak
Validates and sanitizes graph data before processing
"""

import logging
from typing import Dict, Any, List, Tuple, Optional
import re

logger = logging.getLogger(__name__)


class GraphValidator:
    """Validates graph data structure and content"""

    @staticmethod
    def validate_graph_data(graph_data: Dict[str, Any], strict: bool = False) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Validate complete graph data structure

        Args:
            graph_data: Graph data dictionary with 'nodes' and 'edges'
            strict: If True, apply stricter validation rules

        Returns:
            Tuple of (is_valid, error_message, sanitized_data)
        """
        if not isinstance(graph_data, dict):
            return False, "Graph data must be a dictionary", {}

        # Check for required keys
        if 'nodes' not in graph_data and 'edges' not in graph_data:
            return False, "Graph data must contain 'nodes' or 'edges'", {}

        nodes = graph_data.get('nodes', [])
        edges = graph_data.get('edges', [])

        # Validate nodes
        valid_nodes, node_error, sanitized_nodes = GraphValidator.validate_nodes(nodes, strict)
        if not valid_nodes:
            return False, f"Node validation failed: {node_error}", {}

        # Validate edges
        valid_edges, edge_error, sanitized_edges = GraphValidator.validate_edges(
            edges, sanitized_nodes, strict
        )
        if not valid_edges:
            return False, f"Edge validation failed: {edge_error}", {}

        # Build sanitized graph
        sanitized_graph = {
            'nodes': sanitized_nodes,
            'edges': sanitized_edges,
            'meta': graph_data.get('meta', {})
        }

        logger.info(f"Graph validation successful: {len(sanitized_nodes)} nodes, {len(sanitized_edges)} edges")
        return True, None, sanitized_graph

    @staticmethod
    def validate_nodes(nodes: List[Dict], strict: bool = False) -> Tuple[bool, Optional[str], List[Dict]]:
        """
        Validate node list

        Args:
            nodes: List of node dictionaries
            strict: Apply stricter validation

        Returns:
            Tuple of (is_valid, error_message, sanitized_nodes)
        """
        if not isinstance(nodes, list):
            return False, "Nodes must be a list", []

        if len(nodes) == 0:
            if strict:
                return False, "Graph must contain at least one node", []
            else:
                return True, None, []

        # Check for maximum nodes
        max_nodes = 10000 if not strict else 5000
        if len(nodes) > max_nodes:
            return False, f"Too many nodes: {len(nodes)} (max: {max_nodes})", []

        sanitized_nodes = []
        node_ids = set()

        for idx, node in enumerate(nodes):
            if not isinstance(node, dict):
                return False, f"Node at index {idx} is not a dictionary", []

            # Validate node ID
            node_id = node.get('id') or node.get('address')
            if not node_id:
                return False, f"Node at index {idx} missing 'id' or 'address'", []

            if not isinstance(node_id, str):
                return False, f"Node ID at index {idx} must be a string", []

            if len(node_id) > 500:
                return False, f"Node ID at index {idx} too long (max: 500 chars)", []

            # Check for duplicate IDs
            if node_id in node_ids:
                logger.warning(f"Duplicate node ID found: {node_id}, skipping duplicate")
                continue

            node_ids.add(node_id)

            # Sanitize node data
            sanitized_node = {
                'id': node_id,
                'label': GraphValidator._sanitize_string(node.get('label', node_id)),
                'type': GraphValidator._sanitize_string(node.get('type', 'address'))
            }

            # Add optional fields with validation
            if 'balance' in node:
                sanitized_node['balance'] = GraphValidator._sanitize_number(node['balance'])

            if 'total_received' in node:
                sanitized_node['total_received'] = GraphValidator._sanitize_number(node['total_received'])

            if 'total_sent' in node:
                sanitized_node['total_sent'] = GraphValidator._sanitize_number(node['total_sent'])

            if 'n_tx' in node:
                sanitized_node['n_tx'] = GraphValidator._sanitize_number(node['n_tx'], is_int=True)

            if 'color' in node:
                sanitized_node['color'] = GraphValidator._sanitize_color(node['color'])

            if 'size' in node:
                sanitized_node['size'] = GraphValidator._sanitize_number(node['size'], min_val=1, max_val=100)

            # Copy other safe fields
            safe_fields = ['x', 'y', 'timestamp', 'block_height', 'confirmations']
            for field in safe_fields:
                if field in node:
                    sanitized_node[field] = node[field]

            sanitized_nodes.append(sanitized_node)

        logger.info(f"Validated {len(sanitized_nodes)} nodes")
        return True, None, sanitized_nodes

    @staticmethod
    def validate_edges(edges: List[Dict], nodes: List[Dict], strict: bool = False) -> Tuple[bool, Optional[str], List[Dict]]:
        """
        Validate edge list

        Args:
            edges: List of edge dictionaries
            nodes: List of validated nodes
            strict: Apply stricter validation

        Returns:
            Tuple of (is_valid, error_message, sanitized_edges)
        """
        if not isinstance(edges, list):
            return False, "Edges must be a list", []

        if len(edges) == 0:
            return True, None, []  # Empty edges list is valid

        # Check for maximum edges
        max_edges = 50000 if not strict else 25000
        if len(edges) > max_edges:
            return False, f"Too many edges: {len(edges)} (max: {max_edges})", []

        # Build node ID set for validation
        node_ids = {node['id'] for node in nodes}

        sanitized_edges = []
        seen_edges = set()

        for idx, edge in enumerate(edges):
            if not isinstance(edge, dict):
                return False, f"Edge at index {idx} is not a dictionary", []

            # Validate source and target
            source = edge.get('source')
            target = edge.get('target')

            if not source or not target:
                return False, f"Edge at index {idx} missing 'source' or 'target'", []

            if not isinstance(source, str) or not isinstance(target, str):
                return False, f"Edge at index {idx} source/target must be strings", []

            # Check if nodes exist
            if strict:
                if source not in node_ids:
                    return False, f"Edge at index {idx} references non-existent source: {source}", []
                if target not in node_ids:
                    return False, f"Edge at index {idx} references non-existent target: {target}", []

            # Check for self-loops
            if source == target:
                logger.warning(f"Self-loop detected at edge {idx}, skipping")
                continue

            # Check for duplicate edges
            edge_key = (source, target)
            if edge_key in seen_edges:
                logger.debug(f"Duplicate edge detected: {source} -> {target}, skipping")
                continue

            seen_edges.add(edge_key)

            # Sanitize edge data
            sanitized_edge = {
                'source': source,
                'target': target
            }

            # Add optional fields with validation
            if 'weight' in edge:
                sanitized_edge['weight'] = GraphValidator._sanitize_number(edge['weight'], min_val=0)

            if 'value' in edge:
                sanitized_edge['value'] = GraphValidator._sanitize_number(edge['value'], min_val=0)

            if 'color' in edge:
                sanitized_edge['color'] = GraphValidator._sanitize_color(edge['color'])

            if 'size' in edge:
                sanitized_edge['size'] = GraphValidator._sanitize_number(edge['size'], min_val=0.1, max_val=10)

            if 'type' in edge:
                sanitized_edge['type'] = GraphValidator._sanitize_string(edge['type'])

            if 'direction' in edge:
                sanitized_edge['direction'] = GraphValidator._sanitize_string(edge['direction'])

            # Copy timestamp if present
            if 'timestamp' in edge:
                sanitized_edge['timestamp'] = edge['timestamp']

            sanitized_edges.append(sanitized_edge)

        logger.info(f"Validated {len(sanitized_edges)} edges")
        return True, None, sanitized_edges

    @staticmethod
    def _sanitize_string(value: Any, max_length: int = 1000) -> str:
        """Sanitize string value"""
        if not isinstance(value, str):
            value = str(value)

        # Remove potentially dangerous characters
        value = re.sub(r'[<>"\']', '', value)

        # Truncate if too long
        if len(value) > max_length:
            value = value[:max_length]

        return value.strip()

    @staticmethod
    def _sanitize_number(value: Any, min_val: Optional[float] = None,
                        max_val: Optional[float] = None, is_int: bool = False) -> float:
        """Sanitize numeric value"""
        try:
            num = float(value)

            if is_int:
                num = int(num)

            # Check bounds
            if min_val is not None and num < min_val:
                num = min_val

            if max_val is not None and num > max_val:
                num = max_val

            return num

        except (ValueError, TypeError):
            return 0 if is_int else 0.0

    @staticmethod
    def _sanitize_color(value: Any) -> str:
        """Sanitize color value"""
        if not isinstance(value, str):
            return '#6366f1'  # Default color

        # Check if it's a valid hex color
        if re.match(r'^#[0-9A-Fa-f]{6}$', value):
            return value

        # Check if it's a valid CSS color name (basic check)
        if re.match(r'^[a-z]+$', value.lower()):
            return value.lower()

        return '#6366f1'  # Default color

    @staticmethod
    def validate_bitcoin_address(address: str) -> bool:
        """Validate Bitcoin address format"""
        if not isinstance(address, str):
            return False

        # Legacy address (P2PKH): starts with 1
        # P2SH address: starts with 3
        # Bech32 address: starts with bc1
        legacy_pattern = r'^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$'
        bech32_pattern = r'^bc1[a-z0-9]{39,59}$'

        return bool(re.match(legacy_pattern, address) or re.match(bech32_pattern, address))

    @staticmethod
    def get_graph_statistics(graph_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get statistics about the graph"""
        nodes = graph_data.get('nodes', [])
        edges = graph_data.get('edges', [])

        # Count node types
        node_types = {}
        for node in nodes:
            node_type = node.get('type', 'unknown')
            node_types[node_type] = node_types.get(node_type, 0) + 1

        # Count edge types
        edge_types = {}
        for edge in edges:
            edge_type = edge.get('type', 'unknown')
            edge_types[edge_type] = edge_types.get(edge_type, 0) + 1

        # Calculate average degree
        degree_map = {}
        for edge in edges:
            source = edge['source']
            target = edge['target']
            degree_map[source] = degree_map.get(source, 0) + 1
            degree_map[target] = degree_map.get(target, 0) + 1

        avg_degree = sum(degree_map.values()) / len(nodes) if nodes else 0

        return {
            'node_count': len(nodes),
            'edge_count': len(edges),
            'node_types': node_types,
            'edge_types': edge_types,
            'average_degree': avg_degree,
            'density': (2 * len(edges)) / (len(nodes) * (len(nodes) - 1)) if len(nodes) > 1 else 0
        }
