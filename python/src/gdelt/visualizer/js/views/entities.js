/**
 * Entities view for the GDELT News Analysis Dashboard
 */
class EntitiesView {
    constructor() {
        // Data
        this.data = {
            entities: null
        };
        
        // Network
        this.network = null;
    }
    
    /**
     * Initialize the entities view
     */
    async init() {
        try {
            // Update status
            utils.updateStatus('Loading entity data...', 25);
            
            // Load data
            await this.loadData();
            
            // Initialize entity network
            this.initEntityNetwork();
            
            // Initialize entity stats
            this.initEntityStats();
            
            // Initialize entity table
            this.initEntityTable();
            
            // Update status
            utils.updateStatus('Entity data loaded', 100, false);
        } catch (error) {
            console.error('Error initializing entities view:', error);
            utils.updateStatus('Error loading entity data', 0, false);
        }
    }
    
    /**
     * Load entity data
     */
    async loadData() {
        try {
            // Load entity data
            this.data.entities = await api.getEntities();
        } catch (error) {
            console.error('Error loading entity data:', error);
            throw error;
        }
    }
    
    /**
     * Initialize entity network
     */
    initEntityNetwork() {
        const container = document.getElementById('entity-network-large');
        if (!container) return;
        
        // Clear container
        container.innerHTML = '';
        
        // Get entity data
        const entities = this.data.entities.slice(0, 30);
        
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
                // Add a link with 30% probability
                if (Math.random() > 0.7) {
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
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(width / 2, height / 2));
        
        // Create links
        const link = svg.append('g')
            .selectAll('line')
            .data(links)
            .enter()
            .append('line')
            .attr('class', 'link')
            .style('stroke', '#999')
            .style('stroke-opacity', 0.6)
            .style('stroke-width', d => Math.sqrt(d.value));
        
        // Create nodes
        const node = svg.append('g')
            .selectAll('circle')
            .data(nodes)
            .enter()
            .append('circle')
            .attr('class', 'node')
            .attr('r', d => 5 + Math.sqrt(d.value / 5))
            .style('fill', d => d.color)
            .style('stroke', '#fff')
            .style('stroke-width', 1.5)
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
        
        // Add tooltips
        node.append('title')
            .text(d => `${d.name}: ${d.value} mentions`);
        
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
        
        // Store network
        this.network = {
            simulation,
            svg,
            nodes,
            links
        };
    }
    
    /**
     * Initialize entity stats
     */
    initEntityStats() {
        const container = document.getElementById('entity-stats');
        if (!container) return;
        
        // Clear container
        container.innerHTML = '';
        
        // Calculate stats
        const totalEntities = this.data.entities.length;
        const totalMentions = this.data.entities.reduce((sum, entity) => sum + entity.count, 0);
        const entityTypes = {};
        
        this.data.entities.forEach(entity => {
            if (entity.type) {
                entityTypes[entity.type] = (entityTypes[entity.type] || 0) + 1;
            }
        });
        
        // Create stats
        const stats = document.createElement('div');
        
        // Total entities
        const totalEntitiesDiv = document.createElement('div');
        totalEntitiesDiv.className = 'dashboard-stat';
        totalEntitiesDiv.innerHTML = `
            <div class="dashboard-stat-value">${utils.formatNumber(totalEntities)}</div>
            <div class="dashboard-stat-label">Total Entities</div>
        `;
        stats.appendChild(totalEntitiesDiv);
        
        // Total mentions
        const totalMentionsDiv = document.createElement('div');
        totalMentionsDiv.className = 'dashboard-stat';
        totalMentionsDiv.innerHTML = `
            <div class="dashboard-stat-value">${utils.formatNumber(totalMentions)}</div>
            <div class="dashboard-stat-label">Total Mentions</div>
        `;
        stats.appendChild(totalMentionsDiv);
        
        // Entity types
        const entityTypesDiv = document.createElement('div');
        entityTypesDiv.className = 'mt-4';
        entityTypesDiv.innerHTML = '<h5>Entity Types</h5>';
        
        const typesList = document.createElement('ul');
        typesList.className = 'list-group';
        
        Object.entries(entityTypes)
            .sort((a, b) => b[1] - a[1])
            .forEach(([type, count]) => {
                const item = document.createElement('li');
                item.className = 'list-group-item d-flex justify-content-between align-items-center';
                
                const nameSpan = document.createElement('span');
                nameSpan.textContent = type;
                
                const badge = document.createElement('span');
                badge.className = 'badge bg-primary rounded-pill';
                badge.textContent = count;
                
                item.appendChild(nameSpan);
                item.appendChild(badge);
                typesList.appendChild(item);
            });
        
        entityTypesDiv.appendChild(typesList);
        stats.appendChild(entityTypesDiv);
        
        // Add stats to container
        container.appendChild(stats);
    }
    
    /**
     * Initialize entity table
     */
    initEntityTable() {
        const table = document.getElementById('entity-table');
        if (!table) return;
        
        // Get table body
        const tbody = table.querySelector('tbody');
        if (!tbody) return;
        
        // Clear table body
        tbody.innerHTML = '';
        
        // Add entities to table
        this.data.entities.slice(0, 100).forEach(entity => {
            const row = document.createElement('tr');
            
            // Entity name
            const nameCell = document.createElement('td');
            nameCell.textContent = entity.entity;
            row.appendChild(nameCell);
            
            // Entity type
            const typeCell = document.createElement('td');
            typeCell.textContent = entity.type || 'Unknown';
            row.appendChild(typeCell);
            
            // Mentions
            const mentionsCell = document.createElement('td');
            mentionsCell.textContent = utils.formatNumber(entity.count);
            row.appendChild(mentionsCell);
            
            // Sources
            const sourcesCell = document.createElement('td');
            sourcesCell.textContent = utils.formatNumber(Math.floor(entity.count * 0.7)); // Placeholder
            row.appendChild(sourcesCell);
            
            // Trust score
            const trustCell = document.createElement('td');
            const trustScore = Math.random() * 0.5 + 0.5; // Placeholder
            trustCell.textContent = trustScore.toFixed(2);
            row.appendChild(trustCell);
            
            // Sentiment
            const sentimentCell = document.createElement('td');
            const sentiment = Math.random() * 2 - 1; // Placeholder
            sentimentCell.innerHTML = utils.formatSentiment(sentiment);
            row.appendChild(sentimentCell);
            
            tbody.appendChild(row);
        });
    }
    
    /**
     * Refresh the entities view
     */
    async refresh() {
        try {
            // Update status
            utils.updateStatus('Refreshing entity data...', 25);
            
            // Load data
            await this.loadData();
            
            // Update entity network
            this.initEntityNetwork();
            
            // Update entity stats
            this.initEntityStats();
            
            // Update entity table
            this.initEntityTable();
            
            // Update status
            utils.updateStatus('Entity data refreshed', 100, false);
        } catch (error) {
            console.error('Error refreshing entities view:', error);
            utils.updateStatus('Error refreshing entity data', 0, false);
        }
    }
}
