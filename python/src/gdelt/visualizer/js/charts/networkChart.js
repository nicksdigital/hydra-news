/**
 * Network chart for the GDELT News Analysis Dashboard
 */
class NetworkChart {
    /**
     * Create a network chart
     * @param {string} elementId - Element ID
     * @param {Object} options - Chart options
     */
    constructor(elementId, options = {}) {
        this.elementId = elementId;
        this.options = {
            nodeRadius: 5,
            linkDistance: 100,
            chargeStrength: -300,
            ...options
        };
        
        this.svg = null;
        this.simulation = null;
        this.nodes = [];
        this.links = [];
    }
    
    /**
     * Initialize the chart
     * @param {Array} nodes - Nodes
     * @param {Array} links - Links
     */
    init(nodes, links) {
        const container = document.getElementById(this.elementId);
        if (!container) return;
        
        // Clear container
        container.innerHTML = '';
        
        // Store data
        this.nodes = nodes;
        this.links = links;
        
        // Create SVG
        const width = container.clientWidth;
        const height = container.clientHeight;
        
        this.svg = d3.select(container)
            .append('svg')
            .attr('width', width)
            .attr('height', height);
        
        // Create simulation
        this.simulation = d3.forceSimulation(this.nodes)
            .force('link', d3.forceLink(this.links).id(d => d.id).distance(this.options.linkDistance))
            .force('charge', d3.forceManyBody().strength(this.options.chargeStrength))
            .force('center', d3.forceCenter(width / 2, height / 2));
        
        // Create links
        const link = this.svg.append('g')
            .selectAll('line')
            .data(this.links)
            .enter()
            .append('line')
            .attr('class', 'link')
            .style('stroke', '#999')
            .style('stroke-opacity', 0.6)
            .style('stroke-width', d => Math.sqrt(d.value));
        
        // Create nodes
        const node = this.svg.append('g')
            .selectAll('circle')
            .data(this.nodes)
            .enter()
            .append('circle')
            .attr('class', 'node')
            .attr('r', d => this.options.nodeRadius + Math.sqrt(d.value / 5))
            .style('fill', d => d.color)
            .style('stroke', '#fff')
            .style('stroke-width', 1.5)
            .call(d3.drag()
                .on('start', this.dragstarted.bind(this))
                .on('drag', this.dragged.bind(this))
                .on('end', this.dragended.bind(this)));
        
        // Add node labels
        const label = this.svg.append('g')
            .selectAll('text')
            .data(this.nodes)
            .enter()
            .append('text')
            .text(d => d.name)
            .style('font-size', '10px')
            .style('text-anchor', 'middle')
            .style('pointer-events', 'none')
            .attr('dy', 15);
        
        // Add tooltips
        node.append('title')
            .text(d => `${d.name}: ${d.value}`);
        
        // Update positions on tick
        this.simulation.on('tick', () => {
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);
            
            node
                .attr('cx', d => d.x)
                .attr('cy', d => d.y);
            
            label
                .attr('x', d => d.x)
                .attr('y', d => d.y);
        });
    }
    
    /**
     * Handle drag start
     * @param {Object} event - Drag event
     * @param {Object} d - Node data
     */
    dragstarted(event, d) {
        if (!event.active) this.simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }
    
    /**
     * Handle drag
     * @param {Object} event - Drag event
     * @param {Object} d - Node data
     */
    dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }
    
    /**
     * Handle drag end
     * @param {Object} event - Drag event
     * @param {Object} d - Node data
     */
    dragended(event, d) {
        if (!event.active) this.simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }
    
    /**
     * Update the chart
     * @param {Array} nodes - Nodes
     * @param {Array} links - Links
     */
    update(nodes, links) {
        // Store data
        this.nodes = nodes;
        this.links = links;
        
        // Reinitialize the chart
        this.init(nodes, links);
    }
    
    /**
     * Destroy the chart
     */
    destroy() {
        if (this.simulation) {
            this.simulation.stop();
        }
        
        if (this.svg) {
            this.svg.selectAll('*').remove();
        }
    }
}
