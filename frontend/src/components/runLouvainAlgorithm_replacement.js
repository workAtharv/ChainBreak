// Replacement for runLouvainAlgorithm function in GraphRenderer.js
// Lines 280-291

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
        const response = await fetch('http://localhost:5000/api/louvain', {
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
            { duration: 5000 }
        );

        setIsLoading(false);

    } catch (err) {
        logger.error('Louvain algorithm failed:', err);
        setError(`Community detection failed: ${err.message}`);
        toast.error(`Failed to detect communities: ${err.message}`);
        setIsLoading(false);
    }
}, []);
