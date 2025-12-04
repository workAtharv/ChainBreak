// frontend/src/utils/api.js
import axios from 'axios';
import logger from './logger';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config) => {
    const startTime = performance.now();
    config.metadata = { startTime };

    logger.debug(`API Request: ${config.method?.toUpperCase()} ${config.url}`, {
      method: config.method,
      url: config.url,
      data: config.data,
      params: config.params
    });

    return config;
  },
  (error) => {
    logger.error('API Request Error', error);
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => {
    const endTime = performance.now();
    const duration = endTime - response.config.metadata.startTime;

    logger.logAPIRequest(
      response.config.method,
      response.config.url,
      response.status,
      duration,
      { data: response.data }
    );

    return response;
  },
  (error) => {
    const endTime = performance.now();
    const duration = error.config?.metadata?.startTime ?
      endTime - error.config.metadata.startTime : 0;

    logger.logAPIRequest(
      error.config?.method || 'UNKNOWN',
      error.config?.url || 'UNKNOWN',
      error.response?.status || 0,
      duration,
      {
        error: error.message,
        response: error.response?.data
      }
    );

    return Promise.reject(error);
  }
);

export const apiService = {
  async get(endpoint, config = {}) {
    try {
      const response = await api.get(endpoint, config);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'GET', endpoint);
    }
  },

  async post(endpoint, data = {}, config = {}) {
    try {
      const response = await api.post(endpoint, data, config);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'POST', endpoint);
    }
  },

  async put(endpoint, data = {}, config = {}) {
    try {
      const response = await api.put(endpoint, data, config);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'PUT', endpoint);
    }
  },

  async delete(endpoint, config = {}) {
    try {
      const response = await api.delete(endpoint, config);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'DELETE', endpoint);
    }
  },

  handleError(error, method, endpoint) {
    let errorMessage = 'An unexpected error occurred';
    let errorDetails = {};

    if (error.response) {
      const { status, data } = error.response;

      switch (status) {
        case 400:
          errorMessage = data.error || 'Bad request';
          break;
        case 401:
          errorMessage = 'Unauthorized access';
          break;
        case 403:
          errorMessage = 'Access forbidden';
          break;
        case 404:
          errorMessage = 'Resource not found';
          break;
        case 429:
          errorMessage = 'Too many requests. Please try again later.';
          break;
        case 500:
          errorMessage = 'Internal server error';
          break;
        case 502:
          errorMessage = 'Bad gateway';
          break;
        case 503:
          errorMessage = 'Service unavailable';
          break;
        default:
          errorMessage = data.error || `HTTP ${status} error`;
      }

      errorDetails = {
        status,
        data,
        method,
        endpoint
      };
    } else if (error.request) {
      errorMessage = 'No response received from server';
      errorDetails = {
        method,
        endpoint,
        request: error.request
      };
    } else {
      errorMessage = error.message || 'Network error';
      errorDetails = {
        method,
        endpoint,
        message: error.message
      };
    }

    const apiError = new Error(errorMessage);
    apiError.isApiError = true;
    apiError.details = errorDetails;
    apiError.originalError = error;

    logger.error(`API Error: ${errorMessage}`, apiError, errorDetails);

    return apiError;
  }
};

export const chainbreakAPI = {
  async getBackendMode() {
    return apiService.get('/api/mode');
  },

  async getSystemStatus() {
    return apiService.get('/api/status');
  },

  async listGraphs() {
    return apiService.get('/api/graph/list');
  },

  async getGraph(name) {
    return apiService.get('/api/graph/get', { params: { name } });
  },

  async fetchAndSaveGraph(address, txLimit = 50) {
    return apiService.post('/api/graph/address', { address, tx_limit: txLimit });
  },

  async analyzeAddress(address, blockchain = 'btc', generateVisualizations = true) {
    return apiService.post('/api/analyze', {
      address,
      blockchain,
      generate_visualizations: generateVisualizations
    });
  },

  async analyzeMultipleAddresses(addresses, blockchain = 'btc') {
    return apiService.post('/api/analyze/batch', {
      addresses,
      blockchain
    });
  },

  async exportToGephi(address, outputFile = null) {
    const params = { address };
    if (outputFile) params.output_file = outputFile;
    return apiService.get('/api/export/gephi', { params });
  },

  async generateRiskReport(addresses, outputFile = null) {
    return apiService.post('/api/report/risk', {
      addresses,
      output_file: outputFile
    });
  },

  async getAnalyzedAddresses() {
    return apiService.get('/api/addresses');
  },

  async getStatistics() {
    return apiService.get('/api/statistics');
  }
};

export default apiService;
