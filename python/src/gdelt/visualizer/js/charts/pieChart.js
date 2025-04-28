/**
 * Pie chart for the GDELT News Analysis Dashboard
 */
class PieChart {
    /**
     * Create a pie chart
     * @param {string} elementId - Element ID
     * @param {Object} options - Chart options
     */
    constructor(elementId, options = {}) {
        this.elementId = elementId;
        this.options = {
            ...CONFIG.chartDefaults,
            ...options
        };
        
        this.chart = null;
    }
    
    /**
     * Initialize the chart
     * @param {Array} data - Chart data
     * @param {string} labelKey - Label key
     * @param {string} valueKey - Value key
     * @param {Array} colors - Colors
     */
    init(data, labelKey, valueKey, colors = null) {
        const ctx = document.getElementById(this.elementId);
        if (!ctx) return;
        
        // Prepare data
        const labels = data.map(item => item[labelKey]);
        const values = data.map(item => item[valueKey]);
        
        // Use provided colors or generate colors
        const chartColors = colors || data.map((item, index) => {
            if (labelKey === 'theme') {
                return utils.getThemeColor(item[labelKey], index);
            } else {
                return CONFIG.colors.themes[index % CONFIG.colors.themes.length];
            }
        });
        
        // Create chart
        this.chart = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: chartColors
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
     * @param {Array} colors - Colors
     */
    update(data, labelKey, valueKey, colors = null) {
        if (!this.chart) return;
        
        // Update data
        this.chart.data.labels = data.map(item => item[labelKey]);
        this.chart.data.datasets[0].data = data.map(item => item[valueKey]);
        
        // Update colors if provided
        if (colors) {
            this.chart.data.datasets[0].backgroundColor = colors;
        } else {
            this.chart.data.datasets[0].backgroundColor = data.map((item, index) => {
                if (labelKey === 'theme') {
                    return utils.getThemeColor(item[labelKey], index);
                } else {
                    return CONFIG.colors.themes[index % CONFIG.colors.themes.length];
                }
            });
        }
        
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
