/**
 * Themes view for the GDELT News Analysis Dashboard
 */
class ThemesView {
    constructor() {
        // Chart instances
        this.charts = {
            distribution: null,
            trends: null
        };
        
        // Data
        this.data = {
            themes: null
        };
    }
    
    /**
     * Initialize the themes view
     */
    async init() {
        try {
            // Update status
            utils.updateStatus('Loading theme data...', 25);
            
            // Load data
            await this.loadData();
            
            // Initialize charts
            this.initCharts();
            
            // Initialize correlation matrix
            this.initCorrelationMatrix();
            
            // Initialize theme table
            this.initThemeTable();
            
            // Update status
            utils.updateStatus('Theme data loaded', 100, false);
        } catch (error) {
            console.error('Error initializing themes view:', error);
            utils.updateStatus('Error loading theme data', 0, false);
        }
    }
    
    /**
     * Load theme data
     */
    async loadData() {
        try {
            // Load theme data
            this.data.themes = await api.getThemes();
        } catch (error) {
            console.error('Error loading theme data:', error);
            throw error;
        }
    }
    
    /**
     * Initialize charts
     */
    initCharts() {
        // Theme distribution chart
        this.initThemeDistributionChart();
        
        // Theme trends chart
        this.initThemeTrendsChart();
    }
    
    /**
     * Initialize theme distribution chart
     */
    initThemeDistributionChart() {
        const ctx = document.getElementById('theme-distribution-chart');
        if (!ctx) return;
        
        // Prepare data
        const themesData = this.data.themes.slice(0, 10);
        const labels = themesData.map(theme => theme.description || theme.theme);
        const data = themesData.map(theme => theme.count);
        const colors = themesData.map((theme, index) => utils.getThemeColor(theme.theme, index));
        
        // Create chart
        this.charts.distribution = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors
                }]
            },
            options: {
                ...CONFIG.chartDefaults,
                plugins: {
                    legend: {
                        position: 'right'
                    }
                }
            }
        });
    }
    
    /**
     * Initialize theme trends chart
     */
    initThemeTrendsChart() {
        const ctx = document.getElementById('theme-trends-chart');
        if (!ctx) return;
        
        // For demonstration, we'll create some random trend data
        const themes = this.data.themes.slice(0, 5);
        const dates = [];
        
        // Generate dates for the last 30 days
        const today = new Date();
        for (let i = 29; i >= 0; i--) {
            const date = new Date(today);
            date.setDate(date.getDate() - i);
            dates.push(date.toISOString().split('T')[0]);
        }
        
        // Create datasets
        const datasets = themes.map((theme, index) => {
            // Generate random trend data
            const data = dates.map(() => Math.floor(Math.random() * 100));
            
            return {
                label: theme.description || theme.theme,
                data: data,
                borderColor: utils.getThemeColor(theme.theme, index),
                backgroundColor: `${utils.getThemeColor(theme.theme, index)}33`,
                borderWidth: 2,
                fill: false,
                tension: 0.4
            };
        });
        
        // Create chart
        this.charts.trends = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: datasets
            },
            options: {
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
                            text: 'Article Count'
                        }
                    }
                }
            }
        });
    }
    
    /**
     * Initialize correlation matrix
     */
    initCorrelationMatrix() {
        const container = document.getElementById('theme-correlation-container');
        if (!container) return;
        
        // Clear container
        container.innerHTML = '';
        
        // Get top themes
        const themes = this.data.themes.slice(0, 10);
        
        // For demonstration, we'll create a random correlation matrix
        const matrix = [];
        for (let i = 0; i < themes.length; i++) {
            const row = [];
            for (let j = 0; j < themes.length; j++) {
                if (i === j) {
                    row.push(1); // Perfect correlation with self
                } else {
                    // Random correlation between -1 and 1
                    row.push(Math.random() * 2 - 1);
                }
            }
            matrix.push(row);
        }
        
        // Create SVG
        const width = container.clientWidth;
        const height = container.clientHeight;
        const padding = 100; // Padding for labels
        
        const svg = d3.select(container)
            .append('svg')
            .attr('width', width)
            .attr('height', height);
        
        // Create color scale
        const colorScale = d3.scaleLinear()
            .domain([-1, 0, 1])
            .range(['#dc3545', '#f8f9fa', '#198754']);
        
        // Create cell size
        const cellSize = Math.min(
            (width - padding * 2) / themes.length,
            (height - padding * 2) / themes.length
        );
        
        // Create group for the matrix
        const matrixGroup = svg.append('g')
            .attr('transform', `translate(${padding}, ${padding})`);
        
        // Create cells
        matrixGroup.selectAll('rect')
            .data(matrix.flat())
            .enter()
            .append('rect')
            .attr('x', (d, i) => (i % themes.length) * cellSize)
            .attr('y', (d, i) => Math.floor(i / themes.length) * cellSize)
            .attr('width', cellSize)
            .attr('height', cellSize)
            .attr('fill', d => colorScale(d))
            .attr('stroke', '#fff')
            .append('title')
            .text((d, i) => {
                const row = Math.floor(i / themes.length);
                const col = i % themes.length;
                return `${themes[row].description || themes[row].theme} - ${themes[col].description || themes[col].theme}: ${d.toFixed(2)}`;
            });
        
        // Add row labels
        matrixGroup.selectAll('.row-label')
            .data(themes)
            .enter()
            .append('text')
            .attr('class', 'row-label')
            .attr('x', -5)
            .attr('y', (d, i) => i * cellSize + cellSize / 2)
            .attr('text-anchor', 'end')
            .attr('alignment-baseline', 'middle')
            .style('font-size', '10px')
            .text(d => d.description || d.theme);
        
        // Add column labels
        matrixGroup.selectAll('.col-label')
            .data(themes)
            .enter()
            .append('text')
            .attr('class', 'col-label')
            .attr('x', (d, i) => i * cellSize + cellSize / 2)
            .attr('y', -5)
            .attr('text-anchor', 'middle')
            .attr('alignment-baseline', 'bottom')
            .style('font-size', '10px')
            .style('transform', 'rotate(-45deg)')
            .style('transform-origin', (d, i) => `${i * cellSize + cellSize / 2}px -5px`)
            .text(d => d.description || d.theme);
    }
    
    /**
     * Initialize theme table
     */
    initThemeTable() {
        const table = document.getElementById('theme-table');
        if (!table) return;
        
        // Get table body
        const tbody = table.querySelector('tbody');
        if (!tbody) return;
        
        // Clear table body
        tbody.innerHTML = '';
        
        // Add themes to table
        this.data.themes.forEach(theme => {
            const row = document.createElement('tr');
            
            // Theme ID
            const idCell = document.createElement('td');
            idCell.textContent = theme.theme;
            row.appendChild(idCell);
            
            // Theme description
            const descriptionCell = document.createElement('td');
            descriptionCell.textContent = theme.description || '-';
            row.appendChild(descriptionCell);
            
            // Article count
            const countCell = document.createElement('td');
            countCell.textContent = utils.formatNumber(theme.count);
            row.appendChild(countCell);
            
            // Sentiment
            const sentimentCell = document.createElement('td');
            const sentiment = Math.random() * 2 - 1; // Placeholder
            sentimentCell.innerHTML = utils.formatSentiment(sentiment);
            row.appendChild(sentimentCell);
            
            tbody.appendChild(row);
        });
    }
    
    /**
     * Refresh the themes view
     */
    async refresh() {
        try {
            // Update status
            utils.updateStatus('Refreshing theme data...', 25);
            
            // Load data
            await this.loadData();
            
            // Update charts
            this.updateCharts();
            
            // Update correlation matrix
            this.initCorrelationMatrix();
            
            // Update theme table
            this.initThemeTable();
            
            // Update status
            utils.updateStatus('Theme data refreshed', 100, false);
        } catch (error) {
            console.error('Error refreshing themes view:', error);
            utils.updateStatus('Error refreshing theme data', 0, false);
        }
    }
    
    /**
     * Update charts with new data
     */
    updateCharts() {
        // Update theme distribution chart
        if (this.charts.distribution) {
            const themesData = this.data.themes.slice(0, 10);
            this.charts.distribution.data.labels = themesData.map(theme => theme.description || theme.theme);
            this.charts.distribution.data.datasets[0].data = themesData.map(theme => theme.count);
            this.charts.distribution.data.datasets[0].backgroundColor = themesData.map((theme, index) => utils.getThemeColor(theme.theme, index));
            this.charts.distribution.update();
        }
        
        // For the trends chart, we would need actual trend data
        // For now, we'll just recreate it with new random data
        if (this.charts.trends) {
            this.initThemeTrendsChart();
        }
    }
}
