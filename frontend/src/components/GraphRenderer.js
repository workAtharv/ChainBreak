// src/components/GraphRenderer.js
import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as d3 from 'd3';
import { motion } from 'framer-motion';
import { Loader2, AlertCircle, Play, RotateCcw, Expand, Shrink, Image } from 'lucide-react';
import logger from '../utils/logger';
import { Plus, Minus } from 'lucide-react';
import { saveSvgAsPng } from 'save-svg-as-png';
import toast from 'react-hot-toast';

const GraphRenderer = ({ graphData, onNodeClick, className = '', illicitAddresses = [] }) => {
  const wrapperRef = useRef(null);
  const containerRef = useRef(null);
  const svgRef = useRef(null);
  const simulationRef = useRef(null);
  const graphRef = useRef({ nodes: [], edges: [] });
  const roRef = useRef(null);
  const resizeObserverRef = useRef(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [layoutRunning, setLayoutRunning] = useState(false);
  const [communities, setCommunities] = useState(null);
  const [containerReady, setContainerReady] = useState(false);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const initializeGraph = useCallback(() => {
    if (!graphData || !containerRef.current) return null;
    try {
      logger.debug('Initializing graph with data', {
        nodes: graphData.nodes?.length || 0,
        edges: graphData.edges?.length || 0
      });
      const nodes = (graphData.nodes || [])
        .filter(n => n && typeof n.id === 'string')
        .map(n => ({
          id: n.id,
          label: n.label || n.id,
          size: 8,
          color: n.color || '#6366f1',
          x: n.x ?? Math.random() * 1000,
          y: n.y ?? Math.random() * 1000,
          type: 'circle',
          ...Object.fromEntries(
            Object.entries(n).filter(([key, value]) => {
              const exclude = ['type', 'id', 'label', 'size', 'color', 'x', 'y'];
              return !exclude.includes(key) && value !== undefined && value !== null && typeof value !== 'function';
            })
          )
        }));
      const edges = (graphData.edges || [])
        .filter(e => e && e.source && e.target && e.source !== e.target)
        .map(e => ({
          source: e.source,
          target: e.target,
          weight: e.weight || 1,
          color: e.color || '#94a3b8',
          size: e.size || 1,
          type: 'line',
          ...Object.fromEntries(
            Object.entries(e).filter(([key, value]) => {
              const exclude = ['source', 'target', 'weight', 'color', 'size', 'type', 'id'];
              return !exclude.includes(key) && value !== undefined && value !== null && typeof value !== 'function';
            })
          )
        }));
      graphRef.current = { nodes, edges };
      logger.info('Graph initialized successfully', {
        nodeCount: nodes.length,
        edgeCount: edges.length
      });
      return graphRef.current;
    } catch (err) {
      logger.error('Failed to initialize graph', err);
      setError(`Graph initialization failed: ${err.message}`);
      return null;
    }
  }, [graphData]);

  const initializeD3 = useCallback((graph) => {
    if (!graph || !containerRef.current) return null;
    try {
      const container = containerRef.current;
      const width = container.clientWidth;
      const height = container.clientHeight;
      if (width === 0 || height === 0) {
        logger.warn('Container has zero dimensions, postponing D3 initialization');
        return null;
      }
      d3.select(container).selectAll('svg').remove();
      const svg = d3.select(container)
        .append('svg')
        .attr('width', '100%')
        .attr('height', '100%')
        .attr('viewBox', `0 0 ${width} ${height}`)
        .style('background', '#111827');
      svgRef.current = svg;
      const g = svg.append('g');

      // Add arrow markers for edges
      const defs = svg.append('defs');
      const arrowMarker = defs.append('marker')
        .attr('id', 'arrowhead')
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 8)
        .attr('refY', 0)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto');

      arrowMarker.append('path')
        .attr('d', 'M0,-5L10,0L0,5')
        .attr('fill', '#94a3b8');

      const linkGroup = g.append('g').attr('stroke', '#94a3b8').attr('stroke-opacity', 0.6);
      const nodeGroup = g.append('g');
      const zoom = d3.zoom()
        .scaleExtent([0.1, 10])
        .on('zoom', (event) => {
          g.attr('transform', event.transform);
          setZoomLevel(event.transform.k);
        });
      svg.call(zoom);
      const links = linkGroup.selectAll('line')
        .data(graph.edges)
        .join('line')
        .attr('stroke-width', d => Math.max(1, Math.min(5, (d.value || 0) / 100000000)) || 1)
        .attr('stroke', d => {
          if (d.direction === 'incoming') return '#10b981'; // green for incoming
          if (d.direction === 'outgoing') return '#ef4444'; // red for outgoing
          return d.color || '#94a3b8';
        })
        .attr('stroke-opacity', 0.8)
        .attr('marker-end', 'url(#arrowhead)');
      const nodes = nodeGroup.selectAll('circle')
        .data(graph.nodes)
        .join('circle')
        .attr('r', d => {
          if (d.type === 'address') return Math.max(6, Math.min(15, (d.balance || 0) / 1000000000 + 6));
          if (d.type === 'transaction') return Math.max(4, Math.min(12, (d.total_input_value || 0) / 1000000000 + 4));
          return d.size || 8;
        })
        .attr('fill', d => {
          // Check if address is illicit
          const isIllicit = illicitAddresses.some(illicit => illicit.address === d.id);
          if (isIllicit) {
            return '#ef4444'; // red for illicit addresses
          }

          if (d.type === 'address') {
            if (d.balance > 0) return '#10b981'; // green for addresses with balance
            return '#6b7280'; // gray for addresses without balance
          }
          if (d.type === 'transaction') return '#3b82f6'; // blue for transactions
          return d.color || '#6366f1';
        })
        .attr('stroke', d => {
          // Check if address is illicit
          const isIllicit = illicitAddresses.some(illicit => illicit.address === d.id);
          if (isIllicit) {
            return '#dc2626'; // darker red stroke for illicit addresses
          }

          if (d.type === 'address' && d.balance > 0) return '#059669';
          if (d.type === 'transaction') return '#1d4ed8';
          return '#111827';
        })
        .attr('stroke-width', 2)
        .style('cursor', 'pointer')
        .call(d3.drag()
          .on('start', (event, d) => {
            if (!event.active && simulationRef.current) simulationRef.current.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on('drag', (event, d) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on('end', (event, d) => {
            if (!event.active && simulationRef.current) simulationRef.current.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          })
        );

      // Add tooltips with rich information
      nodes.append('title').text(d => {
        const isIllicit = illicitAddresses.some(illicit => illicit.address === d.id);
        let tooltip = `${d.label || d.id}\n`;

        if (isIllicit) {
          const illicitData = illicitAddresses.find(illicit => illicit.address === d.id);
          tooltip += `🚨 ILLICIT ADDRESS 🚨\n`;
          tooltip += `Risk Level: ${illicitData.risk_level?.toUpperCase()}\n`;
          tooltip += `Confidence: ${(illicitData.confidence * 100).toFixed(1)}%\n`;
          tooltip += `Sources: ${illicitData.sources.join(', ')}\n`;

          if (illicitData.illicit_activity_analysis) {
            tooltip += `Primary Activity: ${illicitData.illicit_activity_analysis.primary_activity_type?.replace(/_/g, ' ').toUpperCase()}\n`;
            if (illicitData.illicit_activity_analysis.secondary_activities?.length > 0) {
              tooltip += `Secondary: ${illicitData.illicit_activity_analysis.secondary_activities.map(sa => sa.type.replace(/_/g, ' ')).join(', ')}\n`;
            }
            if (illicitData.illicit_activity_analysis.risk_indicators?.length > 0) {
              tooltip += `Evidence: ${illicitData.illicit_activity_analysis.risk_indicators.slice(0, 2).join(', ')}\n`;
            }
          }
        }

        if (d.type === 'address') {
          tooltip += `Type: Address\nBalance: ${(d.balance || 0) / 100000000} BTC\nTransactions: ${d.transaction_count || 0}`;
        } else if (d.type === 'transaction') {
          tooltip += `Type: Transaction\nValue: ${(d.total_input_value || 0) / 100000000} BTC\nFee: ${(d.fee || 0) / 100000000} BTC`;
        }

        return tooltip;
      });

      nodes.on('click', (_, d) => {
        if (onNodeClick) onNodeClick(d);
      });
      svg.on('click', (event) => {
        if (event.target.tagName === 'svg' && onNodeClick) onNodeClick(null);
      });
      const simulation = d3.forceSimulation(graph.nodes)
        .force('link', d3.forceLink(graph.edges).id(d => d.id).distance(60).strength(0.1))
        .force('charge', d3.forceManyBody().strength(-80))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(d => (d.size || 8) + 2));
      simulation.on('tick', () => {
        links
          .attr('x1', d => d.source.x)
          .attr('y1', d => d.source.y)
          .attr('x2', d => d.target.x)
          .attr('y2', d => d.target.y);
        nodes
          .attr('cx', d => d.x)
          .attr('cy', d => d.y);
      });
      simulationRef.current = simulation;
      setContainerReady(true);
      logger.info('D3 renderer initialized successfully');
      return svg;
    } catch (err) {
      logger.error('Failed to initialize D3 renderer', err);
      setError(`Renderer initialization failed: ${err.message}`);
      return null;
    }
  }, [onNodeClick]);

  const setupResizeObserver = useCallback(() => {
    if (!containerRef.current) return;
    if (resizeObserverRef.current) resizeObserverRef.current.disconnect();
    const observer = new ResizeObserver(() => {
      if (graphRef.current) initializeD3(graphRef.current);
    });
    observer.observe(containerRef.current);
    resizeObserverRef.current = observer;
  }, [initializeD3]);

  const runForceAtlas2 = useCallback(async () => {
    if (!simulationRef.current) return;
    try {
      setIsLoading(true);
      setLayoutRunning(true);
      logger.info('Restarting D3 force simulation');
      simulationRef.current.alpha(1).restart();
      setTimeout(() => {
        simulationRef.current.alphaTarget(0);
        setLayoutRunning(false);
        setIsLoading(false);
        logger.info('D3 force simulation stabilized');
      }, 500);
    } catch (err) {
      logger.error('D3 layout failed', err);
      setError(`Layout algorithm failed: ${err.message}`);
      setLayoutRunning(false);
      setIsLoading(false);
    }
  }, []);

  const runLouvainAlgorithm = useCallback(async () => {
    try {
      setIsLoading(true);
      logger.info('Running Louvain community detection...');

      // Prepare graph data from current graph
      const graphData = {
        nodes: graphRef.current.nodes.map(n => ({
          id: n.id,
          label: n.label || n.id,
          type: n.type || 'unknown'
        })),
        edges: graphRef.current.edges.map(e => ({
          source: typeof e.source === 'object' ? e.source.id : e.source,
          target: typeof e.target === 'object' ? e.target.id : e.target,
          value: e.weight || e.value || 1
        })),
        resolution: 1.0
      };

      // Validate graph has data
      if (graphData.nodes.length === 0 || graphData.edges.length === 0) {
        toast.error('Graph must have nodes and edges to run community detection');
        setIsLoading(false);
        return;
      }

      logger.info(`Sending graph data: ${graphData.nodes.length} nodes, ${graphData.edges.length} edges`);

      // Call backend API
      const response = await fetch('http://localhost:5001/api/louvain', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(graphData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `API error: ${response.status}`);
      }

      const result = await response.json();

      if (!result.success) {
        throw new Error(result.error || 'Unknown error from API');
      }

      const data = result.data;
      logger.info('Louvain results received:', {
        num_communities: data.num_communities,
        modularity: data.modularity
      });

      // Apply community colors to nodes
      if (svgRef.current && data.partition) {
        const partition = data.partition;
        const numCommunities = data.num_communities;

        // Create color scale based on number of communities
        const colorScale = numCommunities <= 10
          ? d3.scaleOrdinal(d3.schemeCategory10)
          : d3.scaleOrdinal(d3.schemePaired);

        // Update node colors with smooth transition
        svgRef.current.selectAll('circle')
          .transition()
          .duration(800)
          .attr('fill', d => {
            const communityId = partition[d.id];
            if (communityId !== undefined) {
              return colorScale(communityId);
            }
            // Keep original color if node not in partition
            return d.color || '#6366f1';
          })
          .attr('stroke', d => {
            const communityId = partition[d.id];
            if (communityId !== undefined) {
              const baseColor = colorScale(communityId);
              return d3.color(baseColor).darker(1);
            }
            return '#111827';
          })
          .attr('stroke-width', 2.5);

        logger.info('Applied community colors to nodes');
      }

      // Store results in state
      setCommunities(data);

      // Show success notification with modularity and community count
      const modularityText = data.modularity.toFixed(3);
      const qualityText = data.modularity > 0.3 ? '(Good structure)' : '(Weak structure)';

      toast.success(
        `Found ${data.num_communities} ${data.num_communities === 1 ? 'community' : 'communities'}! ` +
        `Modularity: ${modularityText} ${qualityText}`,
        { duration: 5001 }
      );

      setIsLoading(false);

    } catch (err) {
      logger.error('Louvain algorithm failed:', err);
      setError(`Community detection failed: ${err.message}`);
      toast.error(`Failed to detect communities: ${err.message}`);
      setIsLoading(false);
    }
  }, []);

  const resetGraph = useCallback(() => {
    try {
      logger.debug('Initializing graph with data', {
        nodes: graphData.nodes?.length || 0,
        edges: graphData.edges?.length || 0
      });
      const nodes = (graphData.nodes || [])
        .filter(n => n && typeof n.id === 'string')
        .map(n => ({
          id: n.id,
          label: n.label || n.id,
          size: 8,
          color: n.color || '#6366f1',
          x: n.x ?? Math.random() * 1000,
          y: n.y ?? Math.random() * 1000,
          type: 'circle',
          ...Object.fromEntries(
            Object.entries(n).filter(([key, value]) => {
              const exclude = ['type', 'id', 'label', 'size', 'color', 'x', 'y'];
              return !exclude.includes(key) && value !== undefined && value !== null && typeof value !== 'function';
            })
          )
        }));
      const edges = (graphData.edges || [])
        .filter(e => e && e.source && e.target && e.source !== e.target)
        .map(e => ({
          source: e.source,
          target: e.target,
          weight: e.weight || 1,
          color: e.color || '#94a3b8',
          size: e.size || 1,
          type: 'line',
          ...Object.fromEntries(
            Object.entries(e).filter(([key, value]) => {
              const exclude = ['source', 'target', 'weight', 'color', 'size', 'type', 'id'];
              return !exclude.includes(key) && value !== undefined && value !== null && typeof value !== 'function';
            })
          )
        }));
      graphRef.current = { nodes, edges };
      logger.info('Graph initialized successfully', {
        nodeCount: nodes.length,
        edgeCount: edges.length
      });
      return graphRef.current;
    } catch (err) {
      logger.error('Failed to initialize graph', err);
      setError(`Graph initialization failed: ${err.message}`);
      return null;
    }
  }, [graphData, initializeD3]);

  const exportAsImage = useCallback(() => {
    if (!svgRef.current) return;
    try {
      const svgElement = svgRef.current.node();
      if (!svgElement) {
        logger.warn('No SVG element found for export');
        return;
      }

      // Get the SVG element and save using saveSvgAsPng.js
      saveSvgAsPng(svgElement, "chainbreak_graph.png", {
        backgroundColor: '#111827', // Match the dark background
        scale: 2, // Higher resolution
        width: svgElement.clientWidth,
        height: svgElement.clientHeight
      });

      logger.info('Graph exported as PNG image successfully');
    } catch (err) {
      logger.error('Failed to export graph as image', err);
      setError(`Image export failed: ${err.message}`);
    }
  }, []);

  const zoomIn = useCallback(() => {
    if (!svgRef.current) return;
    try {
      const svg = svgRef.current;
      svg.transition().duration(300).call(d3.zoom().scaleBy, 1.2);
    } catch (err) {
      logger.warn('Zoom in failed', err);
    }
  }, []);

  const zoomOut = useCallback(() => {
    if (!svgRef.current) return;
    try {
      const svg = svgRef.current;
      svg.transition().duration(300).call(d3.zoom().scaleBy, 1 / 1.2);
    } catch (err) {
      logger.warn('Zoom out failed', err);
    }
  }, []);

  const resetZoom = useCallback(() => {
    if (!svgRef.current) return;
    try {
      const svg = svgRef.current;
      svg.transition().duration(300).call(d3.zoom().transform, d3.zoomIdentity);
    } catch (err) {
      logger.warn('Reset zoom failed', err);
    }
  }, []);

  const toggleFullscreen = useCallback(() => {
    if (!wrapperRef.current) return;

    if (!document.fullscreenElement) {
      wrapperRef.current.requestFullscreen().then(() => {
        setIsFullscreen(true);
        logger.info('Entered fullscreen mode');
      }).catch(err => {
        logger.error('Failed to enter fullscreen', err);
        toast.error('Failed to enter fullscreen mode');
      });
    } else {
      document.exitFullscreen().then(() => {
        setIsFullscreen(false);
        logger.info('Exited fullscreen mode');
      }).catch(err => {
        logger.error('Failed to exit fullscreen', err);
        toast.error('Failed to exit fullscreen mode');
      });
    }
  }, []);

  useEffect(() => {
    if (!graphData) return;
    setError(null);
    setContainerReady(false);
    const graph = initializeGraph();
    if (graph) {
      const svg = initializeD3(graph);
      if (svg) {
        setupResizeObserver();
        setTimeout(() => {
          if (simulationRef.current && containerRef.current && containerRef.current.clientWidth > 0 && containerRef.current.clientHeight > 0) {
            runForceAtlas2();
          }
        }, 300);
      }
    }
    return () => {
      if (roRef.current) {
        try { roRef.current.disconnect(); } catch (e) { /* ignore */ }
        roRef.current = null;
      }
      if (resizeObserverRef.current) {
        try { resizeObserverRef.current.disconnect(); } catch (e) { /* ignore */ }
        resizeObserverRef.current = null;
      }
      try { d3.select(containerRef.current).selectAll('svg').remove(); } catch (e) { /* ignore */ }
      if (simulationRef.current) {
        try { simulationRef.current.stop(); } catch (e) { /* ignore */ }
        simulationRef.current = null;
      }
      graphRef.current = { nodes: [], edges: [] };
    };
  }, [graphData, initializeGraph, initializeD3, runForceAtlas2, setupResizeObserver]);

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);

      if (svgRef.current) {
        setTimeout(() => {
          try {
            if (graphRef.current) initializeD3(graphRef.current);
          } catch (err) {
            logger.warn('D3 re-render failed after fullscreen change', err);
          }
        }, 300);
      }
    };

    const handleKeyDown = (event) => {
      if (event.key === 'Escape' && document.fullscreenElement) {
        document.exitFullscreen().then(() => {
          setIsFullscreen(false);
          logger.info('Exited fullscreen via ESC key');
        }).catch(err => {
          logger.error('Failed to exit fullscreen via ESC', err);
        });
      }
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  if (!graphData) {
    return (
      <div className={`flex items-center justify-center h-96 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300 ${className}`}>
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500 text-lg">No graph data available</p>
          <p className="text-gray-400 text-sm">Fetch a Bitcoin address to visualize the transaction graph</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`flex items-center justify-center h-96 bg-red-50 rounded-lg border-2 border-red-200 ${className}`}>
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
          <p className="text-red-600 text-lg font-medium">Graph Rendering Error</p>
          <p className="text-red-500 text-sm">{error}</p>
          <div className="mt-4 flex gap-2 justify-center">
            <button
              onClick={() => {
                setError(null);
                const graph = initializeGraph();
                if (graph) initializeD3(graph);
              }}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              Retry
            </button>
            <button
              onClick={() => {
                setError(null);
                if (graphRef.current) {
                  try {
                    graphRef.current.nodes = graphRef.current.nodes.map(n => ({ ...n, x: Math.random() * 1000, y: Math.random() * 1000 }));
                    initializeD3(graphRef.current);
                  } catch (e) {
                    logger.error('Fallback layout failed', e);
                    setError(`Fallback layout failed: ${e.message}`);
                  }
                }
              }}
              className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
            >
              Use Simple Layout
            </button>
          </div>
        </div>
      </div>
    );
  }

  const totalCommunities = communities?.num_communities || 0;
  const modularityScore = typeof communities?.modularity === 'number'
    ? communities.modularity.toFixed(3)
    : null;
  const largestCommunity = communities?.communities
    ? Object.values(communities.communities).reduce((max, community) => {
      return community.length > max ? community.length : max;
    }, 0)
    : null;

  return (
    <div ref={wrapperRef} className={`relative ${className}`}>
      {!isFullscreen && (
        <div className="absolute top-4 left-4 z-10 flex flex-col gap-2">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={runForceAtlas2}
            disabled={isLoading || layoutRunning || !containerReady}
            className="flex items-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading && layoutRunning ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4" />
            )}
            {layoutRunning ? 'Running...' : 'Run Layout'}
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={runLouvainAlgorithm}
            disabled={isLoading || !containerReady}
            className="flex items-center gap-2 px-3 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4" />
            )}
            Run Louvain
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={resetGraph}
            disabled={isLoading || !containerReady}
            className="flex items-center gap-2 px-3 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <RotateCcw className="w-4 h-4" />
            Reset
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={exportAsImage}
            disabled={isLoading || !containerReady}
            className="flex items-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Image className="w-4 h-4" />
            Export PNG
          </motion.button>

          {/* Zoom controls */}
          <div className="flex flex-col gap-1 mt-2 pt-2 border-t border-gray-700">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={zoomIn}
              disabled={!containerReady}
              className="flex items-center justify-center p-2 bg-gray-700 text-white rounded-lg hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Plus className="w-4 h-4" />
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={resetZoom}
              disabled={!containerReady}
              className="flex items-center justify-center p-2 bg-gray-700 text-white rounded-lg hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {Math.round(zoomLevel * 100)}%
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={zoomOut}
              disabled={!containerReady}
              className="flex items-center justify-center p-2 bg-gray-700 text-white rounded-lg hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Minus className="w-4 h-4" />
            </motion.button>
          </div>

          {/* Fullscreen toggle */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={toggleFullscreen}
            disabled={!containerReady}
            className={`flex items-center gap-2 px-3 py-2 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors mt-2 ${isFullscreen
              ? 'bg-red-600 hover:bg-red-700 border-2 border-red-400'
              : 'bg-indigo-600 hover:bg-indigo-700'
              }`}
          >
            {isFullscreen ? <Shrink className="w-4 h-4" /> : <Expand className="w-4 h-4" />}
            {isFullscreen ? 'Exit Fullscreen (ESC)' : 'Fullscreen'}
          </motion.button>
        </div>
      )}


      {communities && (
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="absolute top-4 right-4 z-10 w-64 bg-gray-900/90 border border-purple-500/40 rounded-xl p-4 shadow-xl backdrop-blur"
        >
          <p className="text-xs uppercase tracking-wide text-purple-300 mb-1">Louvain Results</p>
          <p className="text-sm text-gray-200 mb-4">
            Community detection completed successfully.
          </p>
          <div className="space-y-2 text-sm text-gray-100">
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Communities</span>
              <span className="font-semibold text-white">{totalCommunities}</span>
            </div>
            {modularityScore && (
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Modularity</span>
                <span className="font-semibold text-white">{modularityScore}</span>
              </div>
            )}
            {largestCommunity !== null && (
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Largest size</span>
                <span className="font-semibold text-white">{largestCommunity} nodes</span>
              </div>
            )}
          </div>
        </motion.div>
      )}




      <div
        ref={containerRef}
        className="w-full h-full bg-gray-900 rounded-lg overflow-hidden"
        style={{ minHeight: '400px' }}
      />

      {!containerReady && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-900/80 rounded-lg z-20">
          <div className="text-center">
            <Loader2 className="w-8 h-8 text-white animate-spin mx-auto mb-2" />
            <p className="text-white text-sm">Initializing graph renderer...</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default GraphRenderer;