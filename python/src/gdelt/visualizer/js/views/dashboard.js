/**
 * Dashboard view for the GDELT News Analysis Dashboard
 */
class DashboardView {
    constructor() {
        // Chart instances
        this.charts = {
            newsVolume: null,
            sentiment: null,
            themes: null,
            countries: null
        };
        
        // Data
        this.data = {
            summary: null,
            entities: null,
            themes: null,
            events: null
        };
    }
    
    /**
     * Initialize the dashboard view
     */
    async init() {
        try {
            // Update status
            utils.updateStatus('Loading dashboard data...', 25);
            
            // Load data
            await this.loadData();
            
            // Initialize charts
            this.initCharts();
            
            // Initialize entity list
            this.initEntityList();
            
            // Initialize recent events
            this.initRecentEvents();
            
            // Initialize entity network
            this.initEntityNetwork();
            
            // Update status
            utils.updateStatus('Dashboard loaded', 100, false);
        } catch (error) {
            console.error('Error initializing dashboard:', error);
            utils.updateStatus('Error loading dashboard', 0, false);
        }
    }
    
    /**
     * Load dashboard data
     */
    async loadData() {
        try {
            // Load summary data
            this.data.summary = await api.getSummary();
            
            // Load entity data
            this.data.entities = await api.getEntities();
            
            // Load theme data
            this.data.themes = await api.getThemes();
            
            // Load recent events
            this.data.events = await api.getEvents(null, CONFIG.limits.recentEvents);
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            throw error;
        }
    }
    
    /**
     * Initialize charts
     */
    initCharts() {
        // News volume chart
        this.initNewsVolumeChart();
        
        // Sentiment chart
        this.initSentimentChart();
        
        // Themes chart
        this.initThemesChart();
        
        // Countries chart
        this.initCountriesChart();
    }
    
    /**
     * Initialize news volume chart
     */
    initNewsVolumeChart() {
        const ctx = document.getElementById('news-volume-chart');
        if (!ctx) return;
        
        // Prepare data
        const timeSeriesData = this.data.summary.timeSeries || [];
        const labels = timeSeriesData.map(item => item.date);
        const data = timeSeriesData.map(item => item.count);
        
        // Create chart
        this.charts.newsVolume = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'News Articles',
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
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Article Count'
                        }
                    }
                }
            }
        });
        
        // Set up period buttons
        document.querySelectorAll('[data-period]').forEach(button => {
            button.addEventListener('click', (event) => {
                // Remove active class from all buttons
                document.querySelectorAll('[data-period]').forEach(btn => {
                    btn.classList.remove('active');
                });
                
                // Add active class to clicked button
                event.target.classList.add('active');
                
                // Get period
                const period = event.target.dataset.period;
                
                // Filter data based on period
                let filteredData = [...timeSeriesData];
                if (period === 'week') {
                    filteredData = timeSeriesData.slice(-7);
                } else if (period === 'month') {
                    filteredData = timeSeriesData.slice(-30);
                }
                
                // Update chart
                this.charts.newsVolume.data.labels = filteredData.map(item => item.date);
                this.charts.newsVolume.data.datasets[0].data = filteredData.map(item => item.count);
                this.charts.newsVolume.update();
            });
        });
    }
    
    /**
     * Initialize sentiment chart
     */
    initSentimentChart() {
        const ctx = document.getElementById('sentiment-chart');
        if (!ctx) return;
        
        // Prepare data
        const sentimentData = this.data.summary.sentiment || {
            positive: 0,
            neutral: 0,
            negative: 0
        };
        
        // Create chart
        this.charts.sentiment = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Positive', 'Neutral', 'Negative'],
                datasets: [{
                    data: [
                        sentimentData.positive,
                        sentimentData.neutral,
                        sentimentData.negative
                    ],
                    backgroundColor: [
                        CONFIG.colors.sentiment.positive,
                        CONFIG.colors.sentiment.neutral,
                        CONFIG.colors.sentiment.negative
                    ]
                }]
            },
            options: {
                ...CONFIG.chartDefaults,
                cutout: '70%'
            }
        });
    }
    
    /**
     * Initialize themes chart
     */
    initThemesChart() {
        const ctx = document.getElementById('themes-chart');
        if (!ctx) return;
        
        // Prepare data
        const themesData = this.data.themes.slice(0, CONFIG.limits.topThemes);
        const labels = themesData.map(theme => theme.description || theme.theme);
        const data = themesData.map(theme => theme.count);
        const colors = themesData.map((theme, index) => utils.getThemeColor(theme.theme, index));
        
        // Create chart
        this.charts.themes = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors
                }]
            },
            options: {
                ...CONFIG.chartDefaults
            }
        });
    }
    
    /**
     * Initialize countries chart
     */
    initCountriesChart() {
        const ctx = document.getElementById('countries-chart');
        if (!ctx) return;
        
        // Prepare data
        const countriesData = this.data.summary.countries || [];
        const topCountries = countriesData.slice(0, CONFIG.limits.topCountries);
        const labels = topCountries.map(country => country.country);
        const data = topCountries.map(country => country.count);
        
        // Create chart
        this.charts.countries = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Articles',
                    data: data,
                    backgroundColor: CONFIG.colors.info
                }]
            },
            options: {
                ...CONFIG.chartDefaults,
                indexAxis: 'y',
                scales: {
                    x: {
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
     * Initialize entity list
     */
    initEntityList() {
        const container = document.getElementById('top-entities-list');
        if (!container) return;
        
        // Clear container
        container.innerHTML = '';
        
        // Get top entities
        const topEntities = this.data.entities.slice(0, CONFIG.limits.topEntities);
        
        // Create entity list
        const list = document.createElement('ul');
        list.className = 'list-group';
        
        // Add entities to list
        topEntities.forEach(entity => {
            const item = document.createElement('li');
            item.className = 'list-group-item d-flex justify-content-between align-items-center';
            
            const nameSpan = document.createElement('span');
            nameSpan.textContent = entity.entity;
            
            const badge = document.createElement('span');
            badge.className = 'badge bg-primary rounded-pill';
            badge.textContent = entity.count;
            
            item.appendChild(nameSpan);
            item.appendChild(badge);
            list.appendChild(item);
        });
        
        // Add list to container
        container.appendChild(list);
    }
    
    /**
     * Initialize recent events
     */
    initRecentEvents() {
        const container = document.getElementById('recent-events');
        if (!container) return;
        
        // Clear container
        container.innerHTML = '';
        
        // Get recent events
        const recentEvents = this.data.events || [];
        
        // Create timeline items
        recentEvents.forEach(event => {
            const item = utils.createTimelineItem(event);
            container.appendChild(item);
        });
        
        // Show message if no events
        if (recentEvents.length === 0) {
            container.innerHTML = '<p class="text-center text-muted">No recent events</p>';
        }
    }
    
    /**
     * Initialize entity network
     */
    initEntityNetwork() {
        const container = document.getElementById('entity-network');
        if (!container) return;
        
        // Clear container
        container.innerHTML = '';
        
        // Get entity data
        const entities = this.data.entities.slice(0, 10);
        
        // Create network data
        const nodes = entities.map(entity => ({
            id: entity.entity,
            name: entity.entity,
            value: entity.count,
            color: utils.getEntityColor(entity.entity)
        }));
        
        // Create links (for demonstration, we'll create some random links)
        const links = [];
        for (let i = 0; i < nodes.length; i++) {
            for (let j = i + 1; j < nodes.length; j++) {
                // Add a link with 50% probability
                if (Math.random() > 0.5) {
                    links.push({
                        source: nodes[i].id,
                        target: nodes[j].id,
                        value: Math.floor(Math.random() * 10) + 1
                    });
                }
            }
        }
        
        // Create network chart
        const width = container.clientWidth;
        const height = container.clientHeight;
        
        const svg = d3.select(container)
            .append('svg')
            .attr('width', width)
            .attr('height', height);
        
        // Create simulation
        const simulation = d3.forceSimulation(nodes)
            .force('link', d3.forceLink(links).id(d => d.id).distance(100))
            .force('charge', d3.forceManyBody().strength(-200))
            .force('center', d3.forceCenter(width / 2, height / 2));
        
        // Create links
        const link = svg.append('g')
            .selectAll('line')
            .data(links)
            .enter()
            .append('line')
            .attr('class', 'link')
            .style('stroke-width', d => Math.sqrt(d.value));
        
        // Create nodes
        const node = svg.append('g')
            .selectAll('circle')
            .data(nodes)
            .enter()
            .append('circle')
            .attr('class', 'node')
            .attr('r', d => 5 + Math.sqrt(d.value))
            .style('fill', d => d.color)
            .call(d3.drag()
                .on('start', dragstarted)
                .on('drag', dragged)
                .on('end', dragended));
        
        // Add node labels
        const label = svg.append('g')
            .selectAll('text')
            .data(nodes)
            .enter()
            .append('text')
            .text(d => d.name)
            .style('font-size', '10px')
            .style('text-anchor', 'middle')
            .style('pointer-events', 'none')
            .attr('dy', 15);
        
        // Update positions on tick
        simulation.on('tick', () => {
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
        
        // Drag functions
        function dragstarted(event, d) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }
        
        function dragged(event, d) {
            d.fx = event.x;
            d.fy = event.y;
        }
        
        function dragended(event, d) {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }
    }
    
    /**
     * Refresh the dashboard view
     */
    async refresh() {
        try {
            // Update status
            utils.updateStatus('Refreshing dashboard...', 25);
            
            // Load data
            await this.loadData();
            
            // Update charts
            this.updateCharts();
            
            // Update entity list
            this.initEntityList();
            
            // Update recent events
            this.initRecentEvents();
            
            // Update entity network
            this.initEntityNetwork();
            
            // Update status
            utils.updateStatus('Dashboard refreshed', 100, false);
        } catch (error) {
            console.error('Error refreshing dashboard:', error);
            utils.updateStatus('Error refreshing dashboard', 0, false);
        }
    }
    
    /**
     * Update charts with new data
     */
    updateCharts() {
        // Update news volume chart
        if (this.charts.newsVolume) {
            const timeSeriesData = this.data.summary.timeSeries || [];
            this.charts.newsVolume.data.labels = timeSeriesData.map(item => item.date);
            this.charts.newsVolume.data.datasets[0].data = timeSeriesData.map(item => item.count);
            this.charts.newsVolume.update();
        }
        
        // Update sentiment chart
        if (this.charts.sentiment) {
            const sentimentData = this.data.summary.sentiment || {
                positive: 0,
                neutral: 0,
                negative: 0
            };
            this.charts.sentiment.data.datasets[0].data = [
                sentimentData.positive,
                sentimentData.neutral,
                sentimentData.negative
            ];
            this.charts.sentiment.update();
        }
        
        // Update themes chart
        if (this.charts.themes) {
            const themesData = this.data.themes.slice(0, CONFIG.limits.topThemes);
            this.charts.themes.data.labels = themesData.map(theme => theme.description || theme.theme);
            this.charts.themes.data.datasets[0].data = themesData.map(theme => theme.count);
            this.charts.themes.update();
        }
        
        // Update countries chart
        if (this.charts.countries) {
            const countriesData = this.data.summary.countries || [];
            const topCountries = countriesData.slice(0, CONFIG.limits.topCountries);
            this.charts.countries.data.labels = topCountries.map(country => country.country);
            this.charts.countries.data.datasets[0].data = topCountries.map(country => country.count);
            this.charts.countries.update();
        }
    }
}
