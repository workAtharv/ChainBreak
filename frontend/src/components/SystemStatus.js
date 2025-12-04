import React from 'react';
import { motion } from 'framer-motion';
import { Activity, Database, FileText, CheckCircle, AlertCircle, Clock, Settings } from 'lucide-react';

const SystemStatus = ({ backendMode, systemStatus }) => {
  const getStatusIcon = () => {
    if (!backendMode) return <Clock className="w-5 h-5 text-gray-400" />;

    if (backendMode.backend_mode === 'neo4j') {
      return backendMode.neo4j_available ?
        <Database className="w-5 h-5 text-green-500" /> :
        <Database className="w-5 h-5 text-red-500" />;
    } else {
      return <FileText className="w-5 h-5 text-yellow-500" />;
    }
  };

  const getStatusColor = () => {
    if (!backendMode) return 'text-gray-400';

    if (backendMode.backend_mode === 'neo4j') {
      return backendMode.neo4j_available ? 'text-green-400' : 'text-red-400';
    } else {
      return 'text-yellow-400';
    }
  };

  const getStatusText = () => {
    if (!backendMode) return 'Unknown';

    if (backendMode.backend_mode === 'neo4j') {
      return backendMode.neo4j_available ? 'Neo4j Connected' : 'Neo4j Unavailable';
    } else {
      return 'JSON Mode';
    }
  };

  return (
    <div className="bg-gray-800/50 backdrop-blur-sm rounded-lg border border-gray-700/50 p-6">
      <div className="flex items-center space-x-3 mb-4">
        <Activity className="w-6 h-6 text-green-500" />
        <h3 className="text-lg font-semibold text-white">System Status</h3>
      </div>

      <div className="space-y-4">
        {/* Backend Mode */}
        <div className="flex items-center justify-between p-3 bg-gray-700/30 rounded-lg">
          <div className="flex items-center space-x-3">
            {getStatusIcon()}
            <span className="text-gray-300">Backend Mode</span>
          </div>
          <span className={`font-medium ${getStatusColor()}`}>
            {getStatusText()}
          </span>
        </div>

        {/* System Status */}
        {systemStatus && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-3"
          >
            <div className="flex items-center justify-between p-3 bg-gray-700/30 rounded-lg">
              <div className="flex items-center space-x-3">
                <CheckCircle className="w-5 h-5 text-green-500" />
                <span className="text-gray-300">System Status</span>
              </div>
              <span className="text-green-400 font-medium">
                {systemStatus.system_status || 'Operational'}
              </span>
            </div>

            {systemStatus.data_ingestor_status && (
              <div className="flex items-center justify-between p-3 bg-gray-700/30 rounded-lg">
                <div className="flex items-center space-x-3">
                  <Database className="w-5 h-5 text-blue-500" />
                  <span className="text-gray-300">Data Ingestor</span>
                </div>
                <span className="text-blue-400 font-medium">
                  {systemStatus.data_ingestor_status}
                </span>
              </div>
            )}

            {systemStatus.configuration && (
              <div className="p-3 bg-gray-700/30 rounded-lg">
                <div className="flex items-center space-x-3 mb-2">
                  <Settings className="w-5 h-5 text-purple-500" />
                  <span className="text-gray-300">Configuration</span>
                </div>
                <div className="text-sm text-gray-400 space-y-1">
                  <div>Neo4j URI: {systemStatus.configuration.neo4j_uri || 'Not configured'}</div>
                  <div>JSON Backend: {systemStatus.configuration.use_json_backend ? 'Enabled' : 'Disabled'}</div>
                </div>
              </div>
            )}
          </motion.div>
        )}

        {/* Connection Info */}
        <div className="p-3 bg-blue-900/20 border border-blue-500/30 rounded-lg">
          <div className="flex items-center space-x-2 mb-2">
            <Activity className="w-4 h-4 text-blue-400" />
            <span className="text-sm font-medium text-blue-300">Connection Info</span>
          </div>
          <div className="text-xs text-blue-200 space-y-1">
            <div>Backend: http://localhost:5001</div>
            <div>Frontend: http://localhost:3000</div>
            <div>Data Directory: Data/graph</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemStatus;
