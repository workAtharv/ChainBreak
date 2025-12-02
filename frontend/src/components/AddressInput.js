import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Bitcoin, Search, Settings } from 'lucide-react';

const AddressInput = ({ onSubmit, isLoading }) => {
  const [address, setAddress] = useState('');
  const [txLimit, setTxLimit] = useState(50);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (address.trim()) {
      onSubmit(address.trim(), txLimit);
    }
  };

  const handleTxLimitChange = (e) => {
    const value = parseInt(e.target.value) || 50;
    setTxLimit(Math.max(1, Math.min(1000, value)));
  };

  return (
    <div className="bg-gray-800/50 backdrop-blur-sm rounded-lg border border-gray-700/50 p-6">
      <div className="flex items-center space-x-3 mb-4">
        <Bitcoin className="w-6 h-6 text-blue-500" />
        <h3 className="text-lg font-semibold text-white">Fetch Transaction Data</h3>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="address" className="block text-sm font-medium text-gray-300 mb-2">
            Bitcoin Address
          </label>
          <div className="relative">
            <input
              type="text"
              id="address"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder="Enter Bitcoin address "
              className="w-full px-4 py-3 bg-gray-700/50 border border-gray-600/50 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={isLoading}
            />
            <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
              <Bitcoin className="w-5 h-5 text-gray-400" />
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center space-x-2 text-sm text-gray-400 hover:text-gray-300 transition-colors"
          >
            <Settings className="w-4 h-4" />
            <span>Advanced Options</span>
          </button>
        </div>

        {showAdvanced && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="space-y-3"
          >
            <div>
              <label htmlFor="txLimit" className="block text-sm font-medium text-gray-300 mb-2">
                Transaction Limit
              </label>
              <input
                type="number"
                id="txLimit"
                value={txLimit}
                onChange={handleTxLimitChange}
                min="1"
                max="1000"
                className="w-full px-3 py-2 bg-gray-700/50 border border-gray-600/50 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={isLoading}
              />
              <p className="text-xs text-gray-400 mt-1">
                Maximum number of transactions to fetch (1-1000)
              </p>
            </div>
          </motion.div>
        )}

        <motion.button
          type="submit"
          disabled={!address.trim() || isLoading}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className="w-full flex items-center justify-center space-x-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
        >
          {isLoading ? (
            <>
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              <span>Fetching...</span>
            </>
          ) : (
            <>
              <Search className="w-5 h-5" />
              <span>Fetch Transactions</span>
            </>
          )}
        </motion.button>
      </form>

      <div className="mt-4 p-3 bg-blue-900/20 border border-blue-500/30 rounded-lg">
        <p className="text-sm text-blue-300">
          <strong>Tip:</strong> Use a valid Bitcoin address to fetch transaction data and visualize the network graph.
        </p>
      </div>
    </div>
  );
};

export default AddressInput;
