"""
WebSocket Manager for Real-time Streaming
Provides real-time updates for transaction monitoring and graph analysis
"""

from flask import Flask
from flask_socketio import SocketIO, emit, join_room, leave_room
import logging
import json
import time
from threading import Thread, Lock
from typing import Dict, Set, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections and real-time data streaming"""

    def __init__(self, app: Flask = None):
        self.socketio = None
        self.app = app
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.monitored_addresses: Dict[str, Set[str]] = {}  # address -> set of session_ids
        self.lock = Lock()
        self.monitoring_thread = None
        self.is_monitoring = False

        if app:
            self.init_app(app)

    def init_app(self, app: Flask):
        """Initialize WebSocket with Flask app"""
        self.app = app
        self.socketio = SocketIO(
            app,
            cors_allowed_origins=["http://localhost:3000", "http://localhost:5000"],
            async_mode='threading',
            logger=True,
            engineio_logger=True
        )

        self._register_handlers()
        logger.info("WebSocket Manager initialized")

    def _register_handlers(self):
        """Register WebSocket event handlers"""

        @self.socketio.on('connect')
        def handle_connect():
            session_id = self._get_session_id()
            with self.lock:
                self.active_sessions[session_id] = {
                    'connected_at': datetime.now().isoformat(),
                    'monitored_addresses': set()
                }

            logger.info(f"Client connected: {session_id}")
            emit('connection_established', {
                'session_id': session_id,
                'status': 'connected',
                'timestamp': datetime.now().isoformat()
            })

        @self.socketio.on('disconnect')
        def handle_disconnect():
            session_id = self._get_session_id()
            self._cleanup_session(session_id)
            logger.info(f"Client disconnected: {session_id}")

        @self.socketio.on('subscribe_address')
        def handle_subscribe_address(data):
            """Subscribe to real-time updates for an address"""
            session_id = self._get_session_id()
            address = data.get('address')

            if not address:
                emit('error', {'message': 'Address is required'})
                return

            with self.lock:
                if address not in self.monitored_addresses:
                    self.monitored_addresses[address] = set()

                self.monitored_addresses[address].add(session_id)

                if session_id in self.active_sessions:
                    self.active_sessions[session_id]['monitored_addresses'].add(address)

            join_room(f"address_{address}")

            logger.info(f"Session {session_id} subscribed to address {address}")
            emit('subscribed', {
                'address': address,
                'timestamp': datetime.now().isoformat()
            })

            # Start monitoring if not already running
            self._ensure_monitoring_running()

        @self.socketio.on('unsubscribe_address')
        def handle_unsubscribe_address(data):
            """Unsubscribe from address updates"""
            session_id = self._get_session_id()
            address = data.get('address')

            if not address:
                emit('error', {'message': 'Address is required'})
                return

            with self.lock:
                if address in self.monitored_addresses:
                    self.monitored_addresses[address].discard(session_id)

                    # Clean up if no one is monitoring
                    if not self.monitored_addresses[address]:
                        del self.monitored_addresses[address]

                if session_id in self.active_sessions:
                    self.active_sessions[session_id]['monitored_addresses'].discard(address)

            leave_room(f"address_{address}")

            logger.info(f"Session {session_id} unsubscribed from address {address}")
            emit('unsubscribed', {
                'address': address,
                'timestamp': datetime.now().isoformat()
            })

        @self.socketio.on('ping')
        def handle_ping():
            """Handle ping for connection keep-alive"""
            emit('pong', {'timestamp': datetime.now().isoformat()})

        @self.socketio.on('request_status')
        def handle_request_status():
            """Send current monitoring status"""
            session_id = self._get_session_id()

            with self.lock:
                session_info = self.active_sessions.get(session_id, {})
                monitored = list(session_info.get('monitored_addresses', set()))

            emit('status', {
                'session_id': session_id,
                'monitored_addresses': monitored,
                'total_monitored': len(monitored),
                'timestamp': datetime.now().isoformat()
            })

    def _get_session_id(self) -> str:
        """Get current session ID"""
        from flask import request
        return request.sid

    def _cleanup_session(self, session_id: str):
        """Clean up session data"""
        with self.lock:
            if session_id in self.active_sessions:
                # Remove from all monitored addresses
                for address in self.active_sessions[session_id].get('monitored_addresses', set()):
                    if address in self.monitored_addresses:
                        self.monitored_addresses[address].discard(session_id)

                        if not self.monitored_addresses[address]:
                            del self.monitored_addresses[address]

                del self.active_sessions[session_id]

    def _ensure_monitoring_running(self):
        """Ensure monitoring thread is running"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitoring_thread = Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_thread.start()
            logger.info("Monitoring thread started")

    def _monitoring_loop(self):
        """Main monitoring loop for real-time updates"""
        logger.info("Monitoring loop started")

        while self.is_monitoring:
            try:
                with self.lock:
                    addresses_to_check = list(self.monitored_addresses.keys())

                if not addresses_to_check:
                    time.sleep(5)
                    continue

                # Check for updates (in production, this would query blockchain APIs)
                for address in addresses_to_check:
                    self._check_address_updates(address)

                time.sleep(10)  # Check every 10 seconds

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)

    def _check_address_updates(self, address: str):
        """Check for updates to a monitored address"""
        try:
            # In production, this would make actual API calls to check for new transactions
            # For now, we'll emit periodic heartbeat updates

            update_data = {
                'address': address,
                'timestamp': datetime.now().isoformat(),
                'type': 'heartbeat',
                'status': 'monitoring'
            }

            self.socketio.emit(
                'address_update',
                update_data,
                room=f"address_{address}"
            )

        except Exception as e:
            logger.error(f"Error checking updates for {address}: {e}")

    def broadcast_transaction_update(self, address: str, transaction_data: Dict[str, Any]):
        """Broadcast new transaction to all subscribers of an address"""
        if not self.socketio:
            return

        with self.lock:
            if address not in self.monitored_addresses:
                return

        update_data = {
            'address': address,
            'transaction': transaction_data,
            'timestamp': datetime.now().isoformat(),
            'type': 'new_transaction'
        }

        self.socketio.emit(
            'address_update',
            update_data,
            room=f"address_{address}"
        )

        logger.info(f"Broadcast transaction update for {address}")

    def broadcast_analysis_update(self, address: str, analysis_data: Dict[str, Any]):
        """Broadcast analysis results to subscribers"""
        if not self.socketio:
            return

        with self.lock:
            if address not in self.monitored_addresses:
                return

        update_data = {
            'address': address,
            'analysis': analysis_data,
            'timestamp': datetime.now().isoformat(),
            'type': 'analysis_update'
        }

        self.socketio.emit(
            'address_update',
            update_data,
            room=f"address_{address}"
        )

        logger.info(f"Broadcast analysis update for {address}")

    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket statistics"""
        with self.lock:
            return {
                'active_sessions': len(self.active_sessions),
                'monitored_addresses': len(self.monitored_addresses),
                'is_monitoring': self.is_monitoring,
                'sessions': {
                    sid: {
                        'connected_at': info['connected_at'],
                        'monitored_count': len(info['monitored_addresses'])
                    }
                    for sid, info in self.active_sessions.items()
                }
            }

    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Run the WebSocket server"""
        if self.socketio and self.app:
            logger.info(f"Starting WebSocket server on {host}:{port}")
            self.socketio.run(self.app, host=host, port=port, debug=debug)
        else:
            logger.error("WebSocket not initialized with Flask app")


# Global instance
websocket_manager = WebSocketManager()


def init_websocket(app: Flask) -> WebSocketManager:
    """Initialize WebSocket with Flask app"""
    websocket_manager.init_app(app)
    return websocket_manager
