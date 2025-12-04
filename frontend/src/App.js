import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Toaster } from 'react-hot-toast';
import { Bitcoin, Activity, BarChart3, Settings, Zap, AlertCircle, CheckCircle, XCircle } from 'lucide-react';
import logger from './utils/logger';
import { chainbreakAPI } from './utils/api';
import AddressInput from './components/AddressInput';
import GraphRenderer from './components/GraphRenderer';
import GraphList from './components/GraphList';
import NodeDetails from './components/NodeDetails';
import SystemStatus from './components/SystemStatus';
import ThreatIntelligencePanel from './components/ThreatIntelligencePanel';
import toast from 'react-hot-toast';

const App = () => {
  const [backendMode, setBackendMode] = useState(null);
  const [systemStatus, setSystemStatus] = useState(null);
  const [currentGraph, setCurrentGraph] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [availableGraphs, setAvailableGraphs] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('graph');
  const [threatIntelData, setThreatIntelData] = useState(null);

  const checkBackendMode = useCallback(async () => {
    try {
      logger.info('Checking backend mode...');
      const response = await chainbreakAPI.getBackendMode();

      if (response.success) {
        setBackendMode(response.data);
        logger.info('Backend mode retrieved', response.data);
        return true;
      } else {
        throw new Error(response.error || 'Failed to get backend mode');
      }
    } catch (err) {
      logger.error('Backend mode check failed', err);
      const errorMsg = err.response?.status === 404 ?
        'Backend not found (404) - check if server is running on http://localhost:5001' :
        `Backend mode check failed: ${err.message}`;

      setError(errorMsg);
      toast.error(errorMsg);
      return false;
    }
  }, []);

  const checkSystemStatus = useCallback(async () => {
    try {
      logger.info('Checking system status...');
      const response = await chainbreakAPI.getSystemStatus();

      if (response.success) {
        setSystemStatus(response.data);
        logger.info('System status retrieved', response.data);
        return true;
      } else {
        throw new Error(response.error || 'Failed to get system status');
      }
    } catch (err) {
      logger.error('System status check failed', err);
      const errorMsg = `System status check failed: ${err.message}`;
      toast.error(errorMsg);
      return false;
    }
  }, []);

  const loadAvailableGraphs = useCallback(async () => {
    try {
      logger.info('Loading available graphs...');
      const response = await chainbreakAPI.listGraphs();

      if (response.success) {
        setAvailableGraphs(response.files || []);
        logger.info('Available graphs loaded', { count: response.files?.length || 0 });
        return true;
      } else {
        throw new Error(response.error || 'Failed to load graphs');
      }
    } catch (err) {
      logger.error('Failed to load available graphs', err);
      const errorMsg = `Failed to load graphs: ${err.message}`;
      toast.error(errorMsg);
      return false;
    }
  }, []);

  const initializeApp = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    logger.info('Starting app initialization...');

    try {
      const modeCheck = await checkBackendMode();
      if (!modeCheck) {
        setIsLoading(false);
        return;
      }

      const statusCheck = await checkSystemStatus();
      if (!statusCheck) {
        logger.warn('System status check failed, continuing...');
      }

      const graphsCheck = await loadAvailableGraphs();
      if (!graphsCheck) {
        logger.warn('Graph loading failed, continuing...');
      }

      logger.info('App initialization completed successfully');
      toast.success('ChainBreak initialized successfully');

    } catch (err) {
      logger.error('App initialization failed', err);
      const errorMsg = `App initialization failed: ${err.message}`;
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setIsLoading(false);
    }
  }, [checkBackendMode, checkSystemStatus, loadAvailableGraphs]);

  const handleAddressSubmit = useCallback(async (address, txLimit = 50) => {
    try {
      setIsLoading(true);
      setError(null);

      logger.info('Fetching graph for address', { address, txLimit });
      toast.loading('Fetching transaction data...');

      const response = await chainbreakAPI.fetchAndSaveGraph(address, txLimit);

      if (response.success) {
        logger.info('Graph fetched successfully', {
          file: response.file,
          meta: response.meta
        });

        toast.dismiss();
        toast.success('Graph data fetched successfully!');

        await loadAvailableGraphs();

        if (response.file) {
          const graphResponse = await chainbreakAPI.getGraph(response.file);
          setCurrentGraph(graphResponse);
          setActiveTab('graph');
        }
      } else {
        throw new Error(response.error || 'Failed to fetch graph');
      }
    } catch (err) {
      logger.error('Address submission failed', err);
      const errorMsg = `Failed to fetch graph: ${err.message}`;
      setError(errorMsg);
      toast.dismiss();
      toast.error(errorMsg);
    } finally {
      setIsLoading(false);
    }
  }, [loadAvailableGraphs]);

  const handleGraphSelect = useCallback(async (graphName) => {
    try {
      setIsLoading(true);
      setError(null);

      logger.info('Loading selected graph', { graphName });

      const response = await chainbreakAPI.getGraph(graphName);
      setCurrentGraph(response);
      setActiveTab('graph');
      setSelectedNode(null);

      logger.info('Graph loaded successfully', {
        nodes: response.nodes?.length || 0,
        edges: response.edges?.length || 0
      });

      toast.success('Graph loaded successfully!');
    } catch (err) {
      logger.error('Failed to load selected graph', err);
      const errorMsg = `Failed to load graph: ${err.message}`;
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleNodeClick = useCallback((nodeData) => {
    setSelectedNode(nodeData);
    logger.debug('Node selected', nodeData);
  }, []);

  const handleRefresh = useCallback(async () => {
    await initializeApp();
  }, [initializeApp]);

  const handleThreatIntelUpdate = useCallback((data) => {
    setThreatIntelData(data);
    logger.info('Threat intelligence data updated', data);
  }, []);

  useEffect(() => {
    initializeApp();
  }, [initializeApp]);

  if (isLoading && !backendMode) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <h2 className="text-xl font-semibold text-white mb-2">Initializing ChainBreak</h2>
          <p className="text-gray-400">Connecting to backend...</p>
        </div>
      </div>
    );
  }

  if (error && !backendMode) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center">
        <div className="max-w-md mx-auto text-center p-6 bg-red-900/20 rounded-lg border border-red-500/30">
          <XCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-red-400 mb-2">Connection Failed</h2>
          <p className="text-red-300 mb-4">{error}</p>
          <div className="space-y-2 text-sm text-red-200">
            <p>• Ensure the backend server is running on http://localhost:5001</p>
            <p>• Check that all required dependencies are installed</p>
            <p>• Verify the backend configuration</p>
          </div>
          <button
            onClick={handleRefresh}
            className="mt-4 px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#1f2937',
            color: '#f9fafb',
            border: '1px solid #374151',
          },
        }}
      />

      <header className="bg-gray-800/50 backdrop-blur-sm border-b border-gray-700/50">
        <div className="max-w-[1600px] mx-auto px-0 sm:px-2 lg:px-4">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-3">
              <Bitcoin className="w-8 h-8 text-blue-500" />
              <h1 className="text-2xl font-bold text-white">ChainBreak</h1>
              {backendMode && (
                <div className="flex items-center space-x-2 ml-4">
                  <div className={`w-2 h-2 rounded-full ${backendMode.neo4j_available ? 'bg-green-500' : 'bg-yellow-500'
                    }`} />
                  <span className="text-sm text-gray-300">
                    {backendMode.backend_mode === 'neo4j' ? 'Neo4j' : 'JSON'} Mode
                  </span>
                </div>
              )}
            </div>


          </div>
        </div>
      </header>

      <main className="max-w-[1600px] mx-auto px-0 sm:px-2 lg:px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          <div className="lg:col-span-1 space-y-6">
            <AddressInput onSubmit={handleAddressSubmit} isLoading={isLoading} />

            <SystemStatus
              backendMode={backendMode}
              systemStatus={systemStatus}
            />

            <GraphList
              graphs={availableGraphs}
              onGraphSelect={handleGraphSelect}
              onRefresh={loadAvailableGraphs}
              isLoading={isLoading}
            />

            <ThreatIntelligencePanel
              graphData={currentGraph}
              onThreatIntelUpdate={handleThreatIntelUpdate}
            />
          </div>

          <div className="lg:col-span-3">
            <div className="bg-gray-800/50 backdrop-blur-sm rounded-lg border border-gray-700/50 overflow-hidden">
              <div className="bg-gray-700/50 px-6 py-4 border-b border-gray-600/50">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-white">Transaction Graph</h2>
                  <div className="flex items-center space-x-2">
                    {currentGraph && (
                      <span className="text-sm text-gray-400">
                        {currentGraph.nodes?.length || 0} nodes, {currentGraph.edges?.length || 0} edges
                      </span>
                    )}
                  </div>
                </div>
              </div>

              <div className="p-6 h-[750px]">
                {currentGraph ? (
                  <GraphRenderer
                    graphData={currentGraph}
                    onNodeClick={handleNodeClick}
                    className="w-full h-full"
                    illicitAddresses={threatIntelData?.illicitAddresses || []}
                  />
                ) : (
                  <div className="text-center flex flex-col items-center justify-center h-full">
                    <Bitcoin className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-400 mb-2">No Graph Selected</h3>
                    <p className="text-gray-500">Enter a Bitcoin address to fetch and visualize the transaction graph</p>
                  </div>
                )}
              </div>
            </div>

            {selectedNode && (
              <div className="mt-6">
                <NodeDetails node={selectedNode} onClose={() => setSelectedNode(null)} />
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default App;
