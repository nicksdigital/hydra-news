/**
 * Sentiment view for the GDELT News Analysis Dashboard
 */
class SentimentView {
    constructor() {
        // Chart instances
        this.charts = {
            timeline: null,
            entitySentiment: null
        };
        
        // Data
        this.data = {
            sentiment: null
        };
    }
    
    /**
     * Initialize the sentiment view
     */
    async init() {
        try {
            // Update status
            utils.updateStatus('Loading sentiment data...', 25);
            
            // Load data
            await this.loadData();
            
            // Initialize charts
            this.initCharts();
            
            // Initialize heatmap
            this.initHeatmap();
            
            // Initialize distribution
            this.initDistribution();
            
            // Update status
            utils.updateStatus('Sentiment data loaded', 100, false);
        } catch (error) {
            console.error('Error initializing sentiment view:', error);
            utils.updateStatus('Error loading sentiment data', 0, false);
        }
    }
    
    /**
     * Load sentiment data
     */
    async loadData() {
        try {
            // Load sentiment data
            this.data.sentiment = await api.getSentiment();
        } catch (error) {
            console.error('Error loading sentiment data:', error);
            throw error;
        }
    }
    
    /**
     * Initialize charts
     */
    initCharts() {
        // Sentiment timeline chart
        this.initSentimentTimelineChart();
        
        // Entity sentiment chart
        this.initEntitySentimentChart();
    }
    
    /**
     * Initialize sentiment timeline chart
     */
    initSentimentTimelineChart() {
        const ctx = document.getElementById('sentiment-timeline-chart');
        if (!ctx) return;
        
        // Prepare data
        const timelineData = this.data.sentiment.overall || [];
        const labels = timelineData.map(item => item.date);
        const data = timelineData.map(item => item.sentiment);
        
        // Create chart
        this.charts.timeline = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Sentiment',
                    data: data,
                    borderColor: CONFIG.colors.primary,
                    backgroundColor: 'rgba(13, 110, 253, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
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
                        min: -1,
                        max: 1,
                        title: {
                            display: true,
                            text: 'Sentiment Score'
                        }
                    }
                }
            }
        });
    }
    
    /**
     * Initialize entity sentiment chart
     */
    initEntitySentimentChart() {
        const ctx = document.getElementById('entity-sentiment-chart');
        if (!ctx) return;
        
        // Prepare data
        const entityData = this.data.sentiment.entities || [];
        const labels = entityData.map(item => item.entity);
        const data = entityData.map(item => item.sentiment);
        const colors = entityData.map(item => utils.getSentimentColor(item.sentiment));
        
        // Create chart
        this.charts.entitySentiment = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Sentiment',
                    data: data,
                    backgroundColor: colors
                }]
            },
            options: {
                ...CONFIG.chartDefaults,
                scales: {
                    y: {
                        min: -1,
                        max: 1,
                        title: {
                            display: true,
                            text: 'Sentiment Score'
                        }
                    }
                }
            }
        });
    }
    
    /**
     * Initialize sentiment heatmap
     */
    initHeatmap() {
        const container = document.getElementById('sentiment-heatmap-container');
        if (!container) return;
        
        // Clear container
        container.innerHTML = '';
        
        // Check if entity data is available
        if (!this.data.sentiment.entities || this.data.sentiment.entities.length === 0) {
            container.innerHTML = '<p class="text-center text-muted">No entity sentiment data available</p>';
            return;
        }
        
        // Create heatmap
        const heatmap = document.createElement('div');
        heatmap.className = 'sentiment-heatmap';
        
        // Create heatmap cells
        this.data.sentiment.entities.forEach(entity => {
            const cell = document.createElement('div');
            cell.className = 'sentiment-heatmap-cell';
            cell.style.backgroundColor = utils.getSentimentColor(entity.sentiment);
            cell.style.opacity = Math.min(1, Math.abs(entity.sentiment) * 2);
            cell.title = `${entity.entity}: ${entity.sentiment.toFixed(2)}`;
            
            const label = document.createElement('div');
            label.className = 'sentiment-heatmap-label';
            label.textContent = entity.entity;
            
            cell.appendChild(label);
            heatmap.appendChild(cell);
        });
        
        // Add heatmap to container
        container.appendChild(heatmap);
        
        // Add CSS for heatmap
        const style = document.createElement('style');
        style.textContent = `
            .sentiment-heatmap {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
                grid-gap: 10px;
                width: 100%;
                height: 100%;
            }
            .sentiment-heatmap-cell {
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 10px;
                border-radius: 5px;
                color: white;
                font-weight: bold;
                text-align: center;
                cursor: pointer;
            }
            .sentiment-heatmap-label {
                text-shadow: 0 0 2px rgba(0, 0, 0, 0.5);
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }
        `;
        document.head.appendChild(style);
    }
    
    /**
     * Initialize sentiment distribution
     */
    initDistribution() {
        const container = document.getElementById('sentiment-distribution-container');
        if (!container) return;
        
        // Clear container
        container.innerHTML = '';
        
        // Check if entity data is available
        if (!this.data.sentiment.entities || this.data.sentiment.entities.length === 0) {
            container.innerHTML = '<p class="text-center text-muted">No entity sentiment data available</p>';
            return;
        }
        
        // Create canvas for chart
        const canvas = document.createElement('canvas');
        canvas.id = 'sentiment-distribution-chart';
        canvas.height = 300;
        container.appendChild(canvas);
        
        // Prepare data
        const sentiments = this.data.sentiment.entities.map(entity => entity.sentiment);
        
        // Create bins
        const bins = [
            { min: -1.0, max: -0.8, count: 0 },
            { min: -0.8, max: -0.6, count: 0 },
            { min: -0.6, max: -0.4, count: 0 },
            { min: -0.4, max: -0.2, count: 0 },
            { min: -0.2, max: 0.0, count: 0 },
            { min: 0.0, max: 0.2, count: 0 },
            { min: 0.2, max: 0.4, count: 0 },
            { min: 0.4, max: 0.6, count: 0 },
            { min: 0.6, max: 0.8, count: 0 },
            { min: 0.8, max: 1.0, count: 0 }
        ];
        
        // Count sentiments in bins
        sentiments.forEach(sentiment => {
            for (const bin of bins) {
                if (sentiment >= bin.min && sentiment < bin.max) {
                    bin.count++;
                    break;
                }
            }
        });
        
        // Create chart
        const chart = new Chart(canvas, {
            type: 'bar',
            data: {
                labels: bins.map(bin => `${bin.min.toFixed(1)} to ${bin.max.toFixed(1)}`),
                datasets: [{
                    label: 'Entities',
                    data: bins.map(bin => bin.count),
                    backgroundColor: bins.map(bin => {
                        const midpoint = (bin.min + bin.max) / 2;
                        return utils.getSentimentColor(midpoint);
                    })
                }]
            },
            options: {
                ...CONFIG.chartDefaults,
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Sentiment Score Range'
                        }
                    },
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Entities'
                        }
                    }
                }
            }
        });
    }
    
    /**
     * Refresh the sentiment view
     */
    async refresh() {
        try {
            // Update status
            utils.updateStatus('Refreshing sentiment data...', 25);
            
            // Load data
            await this.loadData();
            
            // Update charts
            this.updateCharts();
            
            // Update heatmap
            this.initHeatmap();
            
            // Update distribution
            this.initDistribution();
            
            // Update status
            utils.updateStatus('Sentiment data refreshed', 100, false);
        } catch (error) {
            console.error('Error refreshing sentiment view:', error);
            utils.updateStatus('Error refreshing sentiment data', 0, false);
        }
    }
    
    /**
     * Update charts with new data
     */
    updateCharts() {
        // Update sentiment timeline chart
        if (this.charts.timeline) {
            const timelineData = this.data.sentiment.overall || [];
            this.charts.timeline.data.labels = timelineData.map(item => item.date);
            this.charts.timeline.data.datasets[0].data = timelineData.map(item => item.sentiment);
            this.charts.timeline.update();
        }
        
        // Update entity sentiment chart
        if (this.charts.entitySentiment) {
            const entityData = this.data.sentiment.entities || [];
            this.charts.entitySentiment.data.labels = entityData.map(item => item.entity);
            this.charts.entitySentiment.data.datasets[0].data = entityData.map(item => item.sentiment);
            this.charts.entitySentiment.data.datasets[0].backgroundColor = entityData.map(item => utils.getSentimentColor(item.sentiment));
            this.charts.entitySentiment.update();
        }
    }
}
