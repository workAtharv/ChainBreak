import React, { useState, useEffect, useMemo } from 'react';
import { Search, Copy, Download, ChevronDown, ChevronRight, Check } from 'lucide-react';

const JsonViewer = ({ data, onClose }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedPaths, setExpandedPaths] = useState(new Set(['root']));
  const [copiedPath, setCopiedPath] = useState(null);
  const [viewMode, setViewMode] = useState('tree'); // 'tree' or 'raw'

  // Pretty print JSON with syntax highlighting
  const prettyJson = useMemo(() => {
    if (!data) return '';
    return JSON.stringify(data, null, 2);
  }, [data]);

  const handleCopy = (text, path) => {
    navigator.clipboard.writeText(text);
    setCopiedPath(path);
    setTimeout(() => setCopiedPath(null), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([prettyJson], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `graph-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const toggleExpand = (path) => {
    const newExpanded = new Set(expandedPaths);
    if (newExpanded.has(path)) {
      newExpanded.delete(path);
    } else {
      newExpanded.add(path);
    }
    setExpandedPaths(newExpanded);
  };

  const expandAll = () => {
    const allPaths = new Set();
    const traverse = (obj, path) => {
      allPaths.add(path);
      if (typeof obj === 'object' && obj !== null) {
        Object.keys(obj).forEach(key => {
          traverse(obj[key], `${path}.${key}`);
        });
      }
    };
    traverse(data, 'root');
    setExpandedPaths(allPaths);
  };

  const collapseAll = () => {
    setExpandedPaths(new Set(['root']));
  };

  const renderValue = (value, path, key) => {
    const isExpanded = expandedPaths.has(path);
    const matchesSearch = !searchTerm ||
      (key && key.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (typeof value === 'string' && value.toLowerCase().includes(searchTerm.toLowerCase()));

    if (value === null) {
      return <span className="text-gray-500">null</span>;
    }

    if (value === undefined) {
      return <span className="text-gray-500">undefined</span>;
    }

    if (typeof value === 'boolean') {
      return <span className={value ? "text-green-600" : "text-red-600"}>{String(value)}</span>;
    }

    if (typeof value === 'number') {
      return <span className="text-blue-600">{value}</span>;
    }

    if (typeof value === 'string') {
      return (
        <span className="text-orange-600">
          "{value.length > 100 ? value.substring(0, 100) + '...' : value}"
        </span>
      );
    }

    if (Array.isArray(value)) {
      return (
        <div className={matchesSearch ? 'bg-yellow-50' : ''}>
          <div className="flex items-center gap-2">
            <button
              onClick={() => toggleExpand(path)}
              className="hover:bg-gray-200 rounded p-1"
            >
              {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
            </button>
            <span className="text-gray-600">Array[{value.length}]</span>
            <button
              onClick={() => handleCopy(JSON.stringify(value, null, 2), path)}
              className="ml-2 text-gray-400 hover:text-gray-600"
              title="Copy array"
            >
              {copiedPath === path ? <Check size={14} className="text-green-600" /> : <Copy size={14} />}
            </button>
          </div>
          {isExpanded && (
            <div className="ml-6 mt-1 border-l-2 border-gray-200 pl-3">
              {value.slice(0, 100).map((item, index) => (
                <div key={index} className="mb-2">
                  <span className="text-gray-500 mr-2">[{index}]:</span>
                  {renderValue(item, `${path}[${index}]`, index)}
                </div>
              ))}
              {value.length > 100 && (
                <div className="text-gray-500 italic">... {value.length - 100} more items</div>
              )}
            </div>
          )}
        </div>
      );
    }

    if (typeof value === 'object') {
      const keys = Object.keys(value);
      return (
        <div className={matchesSearch ? 'bg-yellow-50' : ''}>
          <div className="flex items-center gap-2">
            <button
              onClick={() => toggleExpand(path)}
              className="hover:bg-gray-200 rounded p-1"
            >
              {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
            </button>
            <span className="text-gray-600">Object {`{${keys.length}}`}</span>
            <button
              onClick={() => handleCopy(JSON.stringify(value, null, 2), path)}
              className="ml-2 text-gray-400 hover:text-gray-600"
              title="Copy object"
            >
              {copiedPath === path ? <Check size={14} className="text-green-600" /> : <Copy size={14} />}
            </button>
          </div>
          {isExpanded && (
            <div className="ml-6 mt-1 border-l-2 border-gray-200 pl-3">
              {keys.map(objKey => (
                <div key={objKey} className="mb-2">
                  <span className="text-purple-600 font-medium mr-2">{objKey}:</span>
                  {renderValue(value[objKey], `${path}.${objKey}`, objKey)}
                </div>
              ))}
            </div>
          )}
        </div>
      );
    }

    return <span>{String(value)}</span>;
  };

  // Syntax highlighting for raw JSON
  const syntaxHighlight = (json) => {
    json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, (match) => {
      let cls = 'text-orange-600';
      if (/^"/.test(match)) {
        if (/:$/.test(match)) {
          cls = 'text-purple-600 font-medium';
        } else {
          cls = 'text-orange-600';
        }
      } else if (/true|false/.test(match)) {
        cls = /true/.test(match) ? 'text-green-600' : 'text-red-600';
      } else if (/null/.test(match)) {
        cls = 'text-gray-500';
      } else {
        cls = 'text-blue-600';
      }
      return `<span class="${cls}">${match}</span>`;
    });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-2xl w-full max-w-6xl h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-t-lg">
          <div>
            <h2 className="text-xl font-bold">JSON Viewer</h2>
            <p className="text-sm text-indigo-100 mt-1">
              Explore and analyze graph data structure
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-white hover:bg-white hover:bg-opacity-20 rounded px-3 py-1 transition"
          >
            Close
          </button>
        </div>

        {/* Toolbar */}
        <div className="flex items-center gap-3 p-3 border-b bg-gray-50">
          <div className="flex gap-2">
            <button
              onClick={() => setViewMode('tree')}
              className={`px-3 py-1.5 rounded ${
                viewMode === 'tree'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-white text-gray-700 border hover:bg-gray-100'
              }`}
            >
              Tree View
            </button>
            <button
              onClick={() => setViewMode('raw')}
              className={`px-3 py-1.5 rounded ${
                viewMode === 'raw'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-white text-gray-700 border hover:bg-gray-100'
              }`}
            >
              Raw JSON
            </button>
          </div>

          {viewMode === 'tree' && (
            <>
              <button
                onClick={expandAll}
                className="px-3 py-1.5 bg-white border rounded hover:bg-gray-100 text-sm"
              >
                Expand All
              </button>
              <button
                onClick={collapseAll}
                className="px-3 py-1.5 bg-white border rounded hover:bg-gray-100 text-sm"
              >
                Collapse All
              </button>
            </>
          )}

          <div className="flex-1 flex items-center gap-2">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
              <input
                type="text"
                placeholder="Search keys and values..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-1.5 border rounded focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
            </div>
          </div>

          <button
            onClick={handleDownload}
            className="flex items-center gap-2 px-3 py-1.5 bg-green-600 text-white rounded hover:bg-green-700"
          >
            <Download size={16} />
            Download
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-4 bg-gray-50">
          {viewMode === 'tree' ? (
            <div className="bg-white p-4 rounded-lg shadow font-mono text-sm">
              {renderValue(data, 'root', 'root')}
            </div>
          ) : (
            <div className="bg-gray-900 p-4 rounded-lg shadow overflow-auto">
              <pre
                className="font-mono text-sm text-gray-100"
                dangerouslySetInnerHTML={{ __html: syntaxHighlight(prettyJson) }}
              />
            </div>
          )}
        </div>

        {/* Footer Stats */}
        <div className="flex items-center justify-between p-3 border-t bg-gray-50 text-sm">
          <div className="flex gap-6 text-gray-600">
            {data?.nodes && <span>Nodes: <strong>{data.nodes.length}</strong></span>}
            {data?.edges && <span>Edges: <strong>{data.edges.length}</strong></span>}
            <span>Size: <strong>{(JSON.stringify(data).length / 1024).toFixed(2)} KB</strong></span>
          </div>
          <div className="text-gray-500">
            Press ESC to close
          </div>
        </div>
      </div>
    </div>
  );
};

// Hook for ESC key to close
const useEscapeKey = (callback) => {
  useEffect(() => {
    const handleEsc = (event) => {
      if (event.key === 'Escape') {
        callback();
      }
    };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [callback]);
};

const JsonViewerWithEscape = (props) => {
  useEscapeKey(props.onClose);
  return <JsonViewer {...props} />;
};

export default JsonViewerWithEscape;
