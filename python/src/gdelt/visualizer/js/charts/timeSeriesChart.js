/**
 * Time series chart for the GDELT News Analysis Dashboard
 */
class TimeSeriesChart {
    /**
     * Create a time series chart
     * @param {string} elementId - Element ID
     * @param {Object} options - Chart options
     */
    constructor(elementId, options = {}) {
        this.elementId = elementId;
        this.options = {
            ...CONFIG.chartDefaults,
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'day',
                        displayFormats: {
                            day: 'MMM D'
                        }
                    },
                    title: {
                        display: true,
                        text: 'Date'
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
     * @param {string} xKey - X-axis key
     * @param {string} yKey - Y-axis key
     * @param {string} label - Dataset label
     * @param {string} color - Dataset color
     */
    init(data, xKey, yKey, label, color) {
        const ctx = document.getElementById(this.elementId);
        if (!ctx) return;
        
        // Prepare data
        const labels = data.map(item => item[xKey]);
        const values = data.map(item => item[yKey]);
        
        // Create chart
        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: label,
                    data: values,
                    borderColor: color || CONFIG.colors.primary,
                    backgroundColor: `${color || CONFIG.colors.primary}33`,
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: this.options
        });
    }
    
    /**
     * Update the chart
     * @param {Array} data - Chart data
     * @param {string} xKey - X-axis key
     * @param {string} yKey - Y-axis key
     */
    update(data, xKey, yKey) {
        if (!this.chart) return;
        
        // Update data
        this.chart.data.labels = data.map(item => item[xKey]);
        this.chart.data.datasets[0].data = data.map(item => item[yKey]);
        
        // Update chart
        this.chart.update();
    }
    
    /**
     * Add a dataset to the chart
     * @param {Array} data - Dataset data
     * @param {string} xKey - X-axis key
     * @param {string} yKey - Y-axis key
     * @param {string} label - Dataset label
     * @param {string} color - Dataset color
     */
    addDataset(data, xKey, yKey, label, color) {
        if (!this.chart) return;
        
        // Create dataset
        const dataset = {
            label: label,
            data: data.map(item => item[yKey]),
            borderColor: color,
            backgroundColor: `${color}33`,
            borderWidth: 2,
            fill: false,
            tension: 0.4
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
