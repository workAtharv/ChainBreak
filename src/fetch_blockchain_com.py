import os
import json
import logging
import time
import requests
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from functools import lru_cache
import hashlib

logger = logging.getLogger(__name__)

BLOCKCHAIN_BASE = "https://blockchain.info"
# Unified data directory - use data/graph (consistent with actual structure)
DATA_DIR = Path("data/graph")
DATA_DIR.mkdir(parents=True, exist_ok=True)

logger.info(f"BlockchainComFetcher using data directory: {DATA_DIR.resolve()}")


@dataclass
class GraphNode:
    """Represents a node in the transaction graph"""
    id: str
    label: str
    type: str


@dataclass
class GraphEdge:
    """Represents an edge in the transaction graph"""
    id: str
    source: str
    target: str
    type: str
    value: int


@dataclass
class GraphMeta:
    """Metadata for the transaction graph"""
    address: str
    tx_count: int
    node_count: int
    edge_count: int


@dataclass
class GraphData:
    """Complete graph data structure"""
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    meta: GraphMeta


class BlockchainAPIError(Exception):
    """Base exception for blockchain API errors"""
    pass


class RateLimitError(BlockchainAPIError):
    """Raised when API rate limit is exceeded"""
    pass


class InvalidAddressError(BlockchainAPIError):
    """Raised when an invalid address is provided"""
    pass


class TransactionNotFoundError(BlockchainAPIError):
    """Raised when a transaction is not found"""
    pass


class BlockNotFoundError(BlockchainAPIError):
    """Raised when a block is not found"""
    pass


@dataclass
class FetcherConfig:
    """Configuration for BlockchainComFetcher"""
    rate_limit_s: float = 0.2
    timeout: int = 20
    max_retries: int = 3
    backoff_factor: float = 0.3
    cache_enabled: bool = True
    cache_ttl: int = 300  # 5 minutes
    max_cache_size: int = 1000
    data_dir: Optional[Path] = None


class BlockchainComFetcher:
    def __init__(
        self,
        config: Optional[FetcherConfig] = None,
        session: Optional[requests.Session] = None
    ):
        self.config = config or FetcherConfig()
        self.session = session or self._create_session(
            self.config.max_retries,
            self.config.backoff_factor
        )

        # Initialize cache
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timestamps: Dict[str, float] = {}

        # Update data directory if specified in config
        if self.config.data_dir:
            global DATA_DIR
            DATA_DIR = self.config.data_dir
            DATA_DIR.mkdir(parents=True, exist_ok=True)

        self._last_request_time = 0.0

    @classmethod
    def from_config_file(cls, config_path: Union[str, Path]) -> "BlockchainComFetcher":
        """Create instance from configuration file"""
        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        config = FetcherConfig(**config_data)
        return cls(config=config)

    def _get_cache_key(self, url: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Generate cache key for URL and parameters"""
        key_data = f"{url}|{json.dumps(params or {}, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is still valid"""
        if not self.config.cache_enabled:
            return False

        if cache_key not in self._cache_timestamps:
            return False

        age = time.time() - self._cache_timestamps[cache_key]
        return age < self.config.cache_ttl

    def _get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached response if valid"""
        if self._is_cache_valid(cache_key):
            logger.debug(f"Cache hit for key: {cache_key}")
            return self._cache.get(cache_key)
        return None

    def _cache_response(self, cache_key: str, data: Dict[str, Any]) -> None:
        """Cache response data"""
        if not self.config.cache_enabled:
            return

        # Implement LRU-style cache eviction
        if len(self._cache) >= self.config.max_cache_size:
            # Remove oldest entry
            oldest_key = min(self._cache_timestamps, key=self._cache_timestamps.get)
            del self._cache[oldest_key]
            del self._cache_timestamps[oldest_key]

        self._cache[cache_key] = data
        self._cache_timestamps[cache_key] = time.time()
        logger.debug(f"Cached response for key: {cache_key}")

    def clear_cache(self) -> None:
        """Clear all cached data"""
        self._cache.clear()
        self._cache_timestamps.clear()
        logger.info("Cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "cache_enabled": self.config.cache_enabled,
            "cache_size": len(self._cache),
            "max_cache_size": self.config.max_cache_size,
            "cache_ttl": self.config.cache_ttl,
            "oldest_entry_age": min(self._cache_timestamps.values()) if self._cache_timestamps else 0,
            "newest_entry_age": max(self._cache_timestamps.values()) if self._cache_timestamps else 0
        }

    def _create_session(self, max_retries: int, backoff_factor: float) -> requests.Session:
        """Create a session with retry strategy and connection pooling"""
        session = requests.Session()

        # Use allowed_methods instead of deprecated method_whitelist for newer requests versions
        retry_kwargs = {
            "total": max_retries,
            "status_forcelist": [429, 500, 502, 503, 504],
            "backoff_factor": backoff_factor
        }

        # Check if allowed_methods is supported (newer requests versions)
        try:
            retry_strategy = Retry(
                allowed_methods=["HEAD", "GET", "OPTIONS"],
                **retry_kwargs
            )
        except TypeError:
            # Fallback to method_whitelist for older requests versions
            retry_strategy = Retry(
                method_whitelist=["HEAD", "GET", "OPTIONS"],
                **retry_kwargs
            )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _validate_address(self, address: str) -> None:
        """Validate Bitcoin address format"""
        if not address or not isinstance(address, str):
            raise InvalidAddressError(f"Invalid address: {address}")

        # Basic validation for Bitcoin addresses (P2PKH, P2SH, Bech32)
        if not re.match(r'^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$|^bc1[a-z0-9]{39,59}$', address):
            raise InvalidAddressError(f"Invalid Bitcoin address format: {address}")

    def _validate_tx_hash(self, tx_hash: str) -> None:
        """Validate transaction hash format"""
        if not tx_hash or not isinstance(tx_hash, str):
            raise TransactionNotFoundError(f"Invalid transaction hash: {tx_hash}")

        if not re.match(r'^[a-fA-F0-9]{64}$', tx_hash):
            raise TransactionNotFoundError(f"Invalid transaction hash format: {tx_hash}")

    def _validate_block_hash(self, block_hash: str) -> None:
        """Validate block hash format"""
        if not block_hash or not isinstance(block_hash, str):
            raise BlockNotFoundError(f"Invalid block hash: {block_hash}")

        if not re.match(r'^[a-fA-F0-9]{64}$', block_hash):
            raise BlockNotFoundError(f"Invalid block hash format: {block_hash}")

    def _rate_limit_wait(self) -> None:
        """Enforce rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time

        if time_since_last < self.config.rate_limit_s:
            sleep_time = self.config.rate_limit_s - time_since_last
            time.sleep(sleep_time)

        self._last_request_time = time.time()

    def _get(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make HTTP GET request with caching, error handling and rate limiting"""
        cache_key = self._get_cache_key(url, params)

        # Try to get from cache first
        cached_data = self._get_cached_response(cache_key)
        if cached_data is not None:
            return cached_data

        try:
            self._rate_limit_wait()
            logger.debug(f"Making request to {url} with params {params}")

            response = self.session.get(url, params=params, timeout=self.config.timeout)
            response.raise_for_status()

            data = response.json()
            logger.debug(f"Successfully fetched data from {url}")

            # Cache the response
            self._cache_response(cache_key, data)

            return data

        except requests.exceptions.HTTPError as e:
            if hasattr(response, 'status_code') and response.status_code == 429:
                raise RateLimitError(f"Rate limit exceeded for {url}") from e
            elif hasattr(response, 'status_code') and response.status_code == 404:
                if "rawtx" in url:
                    raise TransactionNotFoundError(f"Transaction not found: {url.split('/')[-1]}") from e
                elif "rawblock" in url:
                    raise BlockNotFoundError(f"Block not found: {url.split('/')[-1]}") from e
                else:
                    raise BlockchainAPIError(f"Resource not found: {url}") from e
            else:
                status_code = getattr(response, 'status_code', 'unknown')
                raise BlockchainAPIError(f"HTTP error {status_code} for {url}: {e}") from e

        except requests.exceptions.Timeout as e:
            raise BlockchainAPIError(f"Request timeout for {url}") from e

        except requests.exceptions.ConnectionError as e:
            raise BlockchainAPIError(f"Connection error for {url}") from e

        except json.JSONDecodeError as e:
            raise BlockchainAPIError(f"Invalid JSON response from {url}") from e

        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}")
            raise BlockchainAPIError(f"Unexpected error: {e}") from e

    def fetch_tx(self, tx_hash: str) -> Dict[str, Any]:
        """Fetch transaction data by hash"""
        self._validate_tx_hash(tx_hash)
        url = f"{BLOCKCHAIN_BASE}/rawtx/{tx_hash}"
        return self._get(url)

    def fetch_address(self, address: str, limit: int = 50) -> Dict[str, Any]:
        """Fetch address data with transaction history"""
        self._validate_address(address)
        if limit < 1 or limit > 1000:
            raise ValueError(f"Limit must be between 1 and 1000, got {limit}")

        url = f"{BLOCKCHAIN_BASE}/rawaddr/{address}"
        params = {"limit": limit}
        return self._get(url, params=params)

    def fetch_block(self, block_hash: str) -> Dict[str, Any]:
        """Fetch block data by hash"""
        self._validate_block_hash(block_hash)
        url = f"{BLOCKCHAIN_BASE}/rawblock/{block_hash}"
        return self._get(url)

    def build_graph_for_address(self, address: str, tx_limit: int = 50) -> Dict[str, Any]:
        """Build optimized graph data for an address with better performance"""
        logger.info(f"Building graph for address {address} with limit {tx_limit}")

        data = self.fetch_address(address, limit=tx_limit)
        transactions = data.get("txs", [])

        if not transactions:
            logger.warning(f"No transactions found for address {address}")
            return self._create_empty_graph(address)

        # Use sets for O(1) lookups and deduplication
        nodes_set = set()
        edges_list = []

        # Pre-allocate collections for better performance
        nodes_dict = {}
        edges_dict = {}  # For deduplication

        # Add the main address node
        main_node = GraphNode(id=address, label=address[:12], type="address")
        nodes_dict[address] = main_node
        nodes_set.add(address)

        processed_txs = 0
        total_inputs = 0
        total_outputs = 0

        for tx in transactions:
            txid = tx.get("hash")
            if not txid:
                continue

            processed_txs += 1

            # Add transaction node
            if txid not in nodes_set:
                tx_node = GraphNode(id=txid, label=txid[:12], type="transaction")
                nodes_dict[txid] = tx_node
                nodes_set.add(txid)

            # Process inputs
            for vin in tx.get("inputs", []):
                prev_out = vin.get("prev_out") or {}
                src_addr = prev_out.get("addr")
                if not src_addr:
                    continue

                total_inputs += 1

                # Add source address node
                if src_addr not in nodes_set:
                    src_node = GraphNode(id=src_addr, label=src_addr[:12], type="address")
                    nodes_dict[src_addr] = src_node
                    nodes_set.add(src_addr)

                # Create edge with deduplication
                edge_id = f"{src_addr}->{txid}"
                if edge_id not in edges_dict:
                    edge = GraphEdge(
                        id=edge_id,
                        source=src_addr,
                        target=txid,
                        type="SENT_FROM",
                        value=prev_out.get("value", 0)
                    )
                    edges_list.append(edge)
                    edges_dict[edge_id] = edge

            # Process outputs
            for vout in tx.get("out", []):
                dst_addr = vout.get("addr")
                if not dst_addr:
                    continue

                total_outputs += 1

                # Add destination address node
                if dst_addr not in nodes_set:
                    dst_node = GraphNode(id=dst_addr, label=dst_addr[:12], type="address")
                    nodes_dict[dst_addr] = dst_node
                    nodes_set.add(dst_addr)

                # Create edge with deduplication
                edge_id = f"{txid}->{dst_addr}"
                if edge_id not in edges_dict:
                    edge = GraphEdge(
                        id=edge_id,
                        source=txid,
                        target=dst_addr,
                        type="SENT_TO",
                        value=vout.get("value", 0)
                    )
                    edges_list.append(edge)
                    edges_dict[edge_id] = edge

        # Convert to final format
        graph_data = GraphData(
            nodes=list(nodes_dict.values()),
            edges=edges_list,
            meta=GraphMeta(
                address=address,
                tx_count=len(transactions),
                node_count=len(nodes_dict),
                edge_count=len(edges_list)
            )
        )

        logger.info(
            f"Graph built: {len(nodes_dict)} nodes, {len(edges_list)} edges, "
            f"{processed_txs} transactions processed"
        )

        # Return dict format for backward compatibility
        return {
            "nodes": [{"id": n.id, "label": n.label, "type": n.type} for n in graph_data.nodes],
            "edges": [{"id": e.id, "source": e.source, "target": e.target, "type": e.type, "value": e.value} for e in graph_data.edges],
            "meta": {
                "address": graph_data.meta.address,
                "tx_count": graph_data.meta.tx_count,
                "node_count": graph_data.meta.node_count,
                "edge_count": graph_data.meta.edge_count
            }
        }

    def _create_empty_graph(self, address: str) -> Dict[str, Any]:
        """Create an empty graph structure"""
        return {
            "nodes": [{"id": address, "label": address[:12], "type": "address"}],
            "edges": [],
            "meta": {
                "address": address,
                "tx_count": 0,
                "node_count": 1,
                "edge_count": 0
            }
        }

    def save_graph(self, graph: Dict[str, Any], filename: Optional[str] = None) -> str:
        """Save graph to file with sanitized filename"""
        data_dir = self.config.data_dir or DATA_DIR
        data_dir.mkdir(parents=True, exist_ok=True)

        if not filename:
            base = graph.get("meta", {}).get("address", "graph")
            # Sanitize filename - only allow alphanumeric, underscore, hyphen
            safe_base = re.sub(r'[^A-Za-z0-9_\-]', '_', base)
            filename = f"graph_{safe_base[:12]}.json"

        path = data_dir / filename

        # Use temporary file for atomic write
        tmp = str(path) + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(graph, f, ensure_ascii=False, indent=2)

        os.replace(tmp, path)

        logger.info(
            f"Graph saved: path={path} nodes={len(graph.get('nodes', []))} edges={len(graph.get('edges', []))}"
        )
        return str(path)
