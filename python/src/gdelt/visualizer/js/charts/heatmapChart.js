/**
 * Heatmap chart for the GDELT News Analysis Dashboard
 */
class HeatmapChart {
    /**
     * Create a heatmap chart
     * @param {string} elementId - Element ID
     * @param {Object} options - Chart options
     */
    constructor(elementId, options = {}) {
        this.elementId = elementId;
        this.options = {
            margin: { top: 50, right: 50, bottom: 100, left: 100 },
            cellSize: 30,
            colorRange: ['#dc3545', '#f8f9fa', '#198754'],
            ...options
        };
        
        this.svg = null;
    }
    
    /**
     * Initialize the chart
     * @param {Array} data - Matrix data
     * @param {Array} rowLabels - Row labels
     * @param {Array} colLabels - Column labels
     */
    init(data, rowLabels, colLabels) {
        const container = document.getElementById(this.elementId);
        if (!container) return;
        
        // Clear container
        container.innerHTML = '';
        
        // Create SVG
        const width = container.clientWidth;
        const height = container.clientHeight;
        
        this.svg = d3.select(container)
            .append('svg')
            .attr('width', width)
            .attr('height', height);
        
        // Calculate dimensions
        const margin = this.options.margin;
        const innerWidth = width - margin.left - margin.right;
        const innerHeight = height - margin.top - margin.bottom;
        
        // Calculate cell size
        const cellSize = Math.min(
            innerWidth / colLabels.length,
            innerHeight / rowLabels.length
        );
        
        // Create color scale
        const colorScale = d3.scaleLinear()
            .domain([-1, 0, 1])
            .range(this.options.colorRange);
        
        // Create group for the heatmap
        const heatmapGroup = this.svg.append('g')
            .attr('transform', `translate(${margin.left}, ${margin.top})`);
        
        // Create cells
        const rows = heatmapGroup.selectAll('.row')
            .data(data)
            .enter()
            .append('g')
            .attr('class', 'row')
            .attr('transform', (d, i) => `translate(0, ${i * cellSize})`);
        
        const cells = rows.selectAll('.cell')
            .data(d => d)
            .enter()
            .append('rect')
            .attr('class', 'cell')
            .attr('x', (d, i) => i * cellSize)
            .attr('width', cellSize)
            .attr('height', cellSize)
            .attr('fill', d => colorScale(d))
            .attr('stroke', '#fff')
            .append('title')
            .text((d, i, j) => {
                const rowIndex = d3.select(j[i].parentNode.parentNode).datum().index;
                return `${rowLabels[rowIndex]} - ${colLabels[i]}: ${d.toFixed(2)}`;
            });
        
        // Add row labels
        heatmapGroup.selectAll('.row-label')
            .data(rowLabels)
            .enter()
            .append('text')
            .attr('class', 'row-label')
            .attr('x', -5)
            .attr('y', (d, i) => i * cellSize + cellSize / 2)
            .attr('text-anchor', 'end')
            .attr('alignment-baseline', 'middle')
            .style('font-size', '10px')
            .text(d => d);
        
        // Add column labels
        heatmapGroup.selectAll('.col-label')
            .data(colLabels)
            .enter()
            .append('text')
            .attr('class', 'col-label')
            .attr('x', (d, i) => i * cellSize + cellSize / 2)
            .attr('y', -5)
            .attr('text-anchor', 'middle')
            .attr('alignment-baseline', 'bottom')
            .style('font-size', '10px')
            .style('transform', (d, i) => `rotate(-45deg) translate(-${cellSize / 2}px, -${cellSize / 2}px)`)
            .style('transform-origin', (d, i) => `${i * cellSize + cellSize / 2}px -5px`)
            .text(d => d);
    }
    
    /**
     * Update the chart
     * @param {Array} data - Matrix data
     * @param {Array} rowLabels - Row labels
     * @param {Array} colLabels - Column labels
     */
    update(data, rowLabels, colLabels) {
        // Reinitialize the chart
        this.init(data, rowLabels, colLabels);
    }
    
    /**
     * Destroy the chart
     */
    destroy() {
        if (this.svg) {
            this.svg.selectAll('*').remove();
        }
    }
}
