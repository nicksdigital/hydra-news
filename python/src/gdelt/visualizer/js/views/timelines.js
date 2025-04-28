/**
 * Timelines view for the GDELT News Analysis Dashboard
 */
class TimelinesView {
    constructor() {
        // Chart instances
        this.charts = {};
        
        // Data
        this.data = {
            entities: null,
            selectedEntity: null,
            timeline: null,
            events: null
        };
    }
    
    /**
     * Initialize the timelines view
     */
    async init() {
        try {
            // Update status
            utils.updateStatus('Loading timeline data...', 25);
            
            // Load entity data
            await this.loadEntityData();
            
            // Initialize entity selection
            this.initEntitySelection();
            
            // If there are entities, select the first one
            if (this.data.entities && this.data.entities.length > 0) {
                this.selectEntity(this.data.entities[0].entity);
            } else {
                utils.updateStatus('No entities found', 100, false);
            }
        } catch (error) {
            console.error('Error initializing timelines view:', error);
            utils.updateStatus('Error loading timelines', 0, false);
        }
    }
    
    /**
     * Load entity data
     */
    async loadEntityData() {
        try {
            // Load entity data
            this.data.entities = await api.getEntities();
        } catch (error) {
            console.error('Error loading entity data:', error);
            throw error;
        }
    }
    
    /**
     * Initialize entity selection
     */
    initEntitySelection() {
        const container = document.getElementById('entity-selection');
        if (!container) return;
        
        // Clear container
        container.innerHTML = '';
        
        // Create entity badges
        this.data.entities.slice(0, 20).forEach(entity => {
            const badge = utils.createEntityBadge(
                entity.entity,
                false,
                (entityName) => this.selectEntity(entityName)
            );
            container.appendChild(badge);
        });
    }
    
    /**
     * Select an entity
     * @param {string} entityName - Entity name
     */
    async selectEntity(entityName) {
        try {
            // Update status
            utils.updateStatus(`Loading timeline for ${entityName}...`, 50);
            
            // Update selected entity
            this.data.selectedEntity = entityName;
            
            // Update entity badges
            const badges = document.querySelectorAll('.entity-badge');
            badges.forEach(badge => {
                if (badge.dataset.entity === entityName) {
                    badge.classList.add('active');
                } else {
                    badge.classList.remove('active');
                }
            });
            
            // Load timeline data
            await this.loadTimelineData(entityName);
            
            // Load event data
            await this.loadEventData(entityName);
            
            // Display entity details
            this.displayEntityDetails(entityName);
            
            // Display entity timeline
            this.displayEntityTimeline();
            
            // Display entity events
            this.displayEntityEvents();
            
            // Update status
            utils.updateStatus(`Timeline for ${entityName} loaded`, 100, false);
        } catch (error) {
            console.error(`Error selecting entity ${entityName}:`, error);
            utils.updateStatus(`Error loading timeline for ${entityName}`, 0, false);
        }
    }
    
    /**
     * Load timeline data for an entity
     * @param {string} entityName - Entity name
     */
    async loadTimelineData(entityName) {
        try {
            // Load entity timeline
            this.data.timeline = await api.getTimeline(entityName, 'entity');
        } catch (error) {
            console.error(`Error loading timeline data for ${entityName}:`, error);
            this.data.timeline = null;
        }
    }
    
    /**
     * Load event data for an entity
     * @param {string} entityName - Entity name
     */
    async loadEventData(entityName) {
        try {
            // Load entity events
            this.data.events = await api.getEvents(entityName, 20);
        } catch (error) {
            console.error(`Error loading event data for ${entityName}:`, error);
            this.data.events = [];
        }
    }
    
    /**
     * Display entity details
     * @param {string} entityName - Entity name
     */
    displayEntityDetails(entityName) {
        const container = document.getElementById('entity-details');
        if (!container) return;
        
        // Clear container
        container.innerHTML = '';
        
        // Find entity data
        const entityData = this.data.entities.find(e => e.entity === entityName);
        if (!entityData) {
            container.innerHTML = '<p class="text-center text-muted">Entity details not available</p>';
            return;
        }
        
        // Create entity details
        const details = document.createElement('div');
        
        // Entity name
        const name = document.createElement('h4');
        name.textContent = entityData.entity;
        details.appendChild(name);
        
        // Entity type
        const type = document.createElement('p');
        type.innerHTML = `<strong>Type:</strong> ${entityData.type || 'Unknown'}`;
        details.appendChild(type);
        
        // Entity mentions
        const mentions = document.createElement('p');
        mentions.innerHTML = `<strong>Mentions:</strong> ${utils.formatNumber(entityData.count)}`;
        details.appendChild(mentions);
        
        // Add details to container
        container.appendChild(details);
    }
    
    /**
     * Display entity timeline
     */
    displayEntityTimeline() {
        const container = document.getElementById('entity-timeline-container');
        if (!container) return;
        
        // Clear container
        container.innerHTML = '';
        
        // Check if timeline data is available
        if (!this.data.timeline || !this.data.timeline.data) {
            container.innerHTML = '<p class="text-center text-muted">Timeline data not available</p>';
            return;
        }
        
        // Create canvas for chart
        const canvas = document.createElement('canvas');
        canvas.id = 'entity-timeline-chart';
        canvas.height = 250;
        container.appendChild(canvas);
        
        // Prepare data
        const timelineData = this.data.timeline.data;
        const labels = timelineData.map(item => item.date);
        const data = timelineData.map(item => item.count);
        
        // Create chart
        this.charts.timeline = new Chart(canvas, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Mentions',
                    data: data,
                    borderColor: utils.getEntityColor(this.data.selectedEntity),
                    backgroundColor: `${utils.getEntityColor(this.data.selectedEntity)}33`,
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
                            text: 'Mention Count'
                        }
                    }
                }
            }
        });
    }
    
    /**
     * Display entity events
     */
    displayEntityEvents() {
        const container = document.getElementById('entity-events');
        if (!container) return;
        
        // Clear container
        container.innerHTML = '';
        
        // Check if event data is available
        if (!this.data.events || this.data.events.length === 0) {
            container.innerHTML = '<p class="text-center text-muted">No events available</p>';
            return;
        }
        
        // Create timeline items
        this.data.events.forEach(event => {
            const item = utils.createTimelineItem(event);
            container.appendChild(item);
        });
    }
    
    /**
     * Refresh the timelines view
     */
    async refresh() {
        try {
            // Update status
            utils.updateStatus('Refreshing timeline data...', 25);
            
            // Load entity data
            await this.loadEntityData();
            
            // Initialize entity selection
            this.initEntitySelection();
            
            // If there's a selected entity, refresh it
            if (this.data.selectedEntity) {
                await this.selectEntity(this.data.selectedEntity);
            } else if (this.data.entities && this.data.entities.length > 0) {
                // Otherwise, select the first entity
                await this.selectEntity(this.data.entities[0].entity);
            }
            
            // Update status
            utils.updateStatus('Timeline data refreshed', 100, false);
        } catch (error) {
            console.error('Error refreshing timelines view:', error);
            utils.updateStatus('Error refreshing timeline data', 0, false);
        }
    }
}
