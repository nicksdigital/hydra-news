/**
 * Bar chart for the GDELT News Analysis Dashboard
 */
class BarChart {
    /**
     * Create a bar chart
     * @param {string} elementId - Element ID
     * @param {Object} options - Chart options
     */
    constructor(elementId, options = {}) {
        this.elementId = elementId;
        this.options = {
            ...CONFIG.chartDefaults,
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Category'
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Value'
                    }
                }
            },
            ...options
        };
        
        this.chart = null;
    }
    
    /**
     * Initialize the chart
     * @param {Array} data - Chart data
     * @param {string} labelKey - Label key
     * @param {string} valueKey - Value key
     * @param {string} label - Dataset label
     * @param {string} color - Dataset color
     * @param {boolean} horizontal - Whether to use horizontal bars
     */
    init(data, labelKey, valueKey, label, color, horizontal = false) {
        const ctx = document.getElementById(this.elementId);
        if (!ctx) return;
        
        // Prepare data
        const labels = data.map(item => item[labelKey]);
        const values = data.map(item => item[valueKey]);
        
        // Update options for horizontal bars
        if (horizontal) {
            this.options.indexAxis = 'y';
        }
        
        // Create chart
        this.chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: label,
                    data: values,
                    backgroundColor: color || CONFIG.colors.primary
                }]
            },
            options: this.options
        });
    }
    
    /**
     * Update the chart
     * @param {Array} data - Chart data
     * @param {string} labelKey - Label key
     * @param {string} valueKey - Value key
     */
    update(data, labelKey, valueKey) {
        if (!this.chart) return;
        
        // Update data
        this.chart.data.labels = data.map(item => item[labelKey]);
        this.chart.data.datasets[0].data = data.map(item => item[valueKey]);
        
        // Update chart
        this.chart.update();
    }
    
    /**
     * Add a dataset to the chart
     * @param {Array} data - Dataset data
     * @param {string} valueKey - Value key
     * @param {string} label - Dataset label
     * @param {string} color - Dataset color
     */
    addDataset(data, valueKey, label, color) {
        if (!this.chart) return;
        
        // Create dataset
        const dataset = {
            label: label,
            data: data.map(item => item[valueKey]),
            backgroundColor: color
        };
        
        // Add dataset
        this.chart.data.datasets.push(dataset);
        
        // Update chart
        this.chart.update();
    }
    
    /**
     * Remove a dataset from the chart
     * @param {number} index - Dataset index
     */
    removeDataset(index) {
        if (!this.chart) return;
        
        // Remove dataset
        this.chart.data.datasets.splice(index, 1);
        
        // Update chart
        this.chart.update();
    }
    
    /**
     * Destroy the chart
     */
    destroy() {
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
    }
}
