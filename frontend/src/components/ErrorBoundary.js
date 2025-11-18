import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import logger from '../utils/logger';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorCount: 0
    };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    this.setState(prevState => ({
      error,
      errorInfo,
      errorCount: prevState.errorCount + 1
    }));

    // Log error details
    logger.error('React Error Boundary caught an error:', {
      error: error.toString(),
      componentStack: errorInfo.componentStack,
      errorCount: this.state.errorCount + 1
    });

    // In production, you might want to send this to an error reporting service
    if (process.env.NODE_ENV === 'production') {
      // Example: reportErrorToService(error, errorInfo);
    }
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    });
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      const { error, errorInfo, errorCount } = this.state;

      return (
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center p-4">
          <div className="max-w-2xl w-full">
            <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-8">
              {/* Icon and Title */}
              <div className="flex items-center gap-4 mb-6">
                <div className="p-3 bg-red-500/20 rounded-full">
                  <AlertTriangle className="w-8 h-8 text-red-500" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-red-400">
                    Oops! Something went wrong
                  </h1>
                  <p className="text-red-300 text-sm mt-1">
                    The application encountered an unexpected error
                  </p>
                </div>
              </div>

              {/* Error Details */}
              <div className="space-y-4 mb-6">
                <div>
                  <h3 className="text-red-400 font-semibold mb-2">Error Details:</h3>
                  <div className="bg-gray-900/50 rounded p-4 overflow-auto">
                    <code className="text-red-300 text-sm font-mono break-all">
                      {error && error.toString()}
                    </code>
                  </div>
                </div>

                {errorInfo && process.env.NODE_ENV === 'development' && (
                  <details className="cursor-pointer">
                    <summary className="text-red-400 font-semibold mb-2 hover:text-red-300">
                      Component Stack (Development Only)
                    </summary>
                    <div className="bg-gray-900/50 rounded p-4 overflow-auto max-h-48 mt-2">
                      <pre className="text-red-300 text-xs font-mono whitespace-pre-wrap">
                        {errorInfo.componentStack}
                      </pre>
                    </div>
                  </details>
                )}

                {errorCount > 1 && (
                  <div className="bg-yellow-900/20 border border-yellow-500/30 rounded p-3">
                    <p className="text-yellow-400 text-sm">
                      ⚠️ This error has occurred {errorCount} times.
                      Consider reloading the page or checking your browser console for more details.
                    </p>
                  </div>
                )}
              </div>

              {/* Actions */}
              <div className="flex gap-3">
                <button
                  onClick={this.handleReset}
                  className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
                >
                  <RefreshCw className="w-4 h-4" />
                  Try Again
                </button>
                <button
                  onClick={this.handleReload}
                  className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
                >
                  <RefreshCw className="w-4 h-4" />
                  Reload Page
                </button>
                {process.env.NODE_ENV === 'development' && (
                  <button
                    onClick={() => {
                      console.clear();
                      this.handleReset();
                    }}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                  >
                    Clear Console
                  </button>
                )}
              </div>

              {/* Help Text */}
              <div className="mt-6 pt-6 border-t border-red-500/30">
                <h3 className="text-red-400 font-semibold mb-2">Troubleshooting:</h3>
                <ul className="text-red-300 text-sm space-y-1 list-disc list-inside">
                  <li>Check your browser console for additional error details</li>
                  <li>Ensure the backend server is running (http://localhost:5000)</li>
                  <li>Try clearing your browser cache and reloading</li>
                  <li>Verify your network connection is stable</li>
                  {process.env.NODE_ENV === 'development' && (
                    <li>Check the terminal for backend errors</li>
                  )}
                </ul>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
