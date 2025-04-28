/**
 * Predictions view for the GDELT News Analysis Dashboard
 */
class PredictionsView {
    constructor() {
        // Chart instances
        this.charts = {
            entityPrediction: null,
            multiEntityPrediction: null,
            modelComparison: null,
            eventDetailChart: null
        };

        // Data
        this.data = {
            entities: null,
            predictions: {},
            selectedEntity: null,
            selectedEntities: [],
            daysToPredict: 14,
            showHighProbabilityOnly: true,
            eventModalInstance: null
        };
    }

    /**
     * Initialize the predictions view
     */
    async init() {
        try {
            // Update status
            utils.updateStatus('Loading prediction data...', 25);

            // Load data
            await this.loadData();

            // Initialize entity selector
            this.initEntitySelector();

            // Initialize prediction chart
            this.initPredictionChart();

            // Initialize model comparison chart
            this.initModelComparisonChart();

            // Initialize prediction metrics
            this.initPredictionMetrics();

            // Initialize prediction events
            this.initPredictionEvents();

            // Update status
            utils.updateStatus('Prediction data loaded', 100, false);
        } catch (error) {
            console.error('Error initializing predictions view:', error);
            utils.updateStatus('Error loading prediction data', 0, false);
        }
    }

    /**
     * Load prediction data
     */
    async loadData() {
        try {
            // Load entities
            this.data.entities = await api.getEntities();

            // Get top entities
            const topEntities = this.data.entities.slice(0, 20);

            if (topEntities.length > 0) {
                // Set selected entity
                this.data.selectedEntity = topEntities[0].entity;

                // Load predictions for selected entity
                await this.loadEntityPredictions(this.data.selectedEntity);
            }
        } catch (error) {
            console.error('Error loading prediction data:', error);
            throw error;
        }
    }

    /**
     * Load predictions for an entity
     * @param {string} entity - Entity name
     */
    async loadEntityPredictions(entity) {
        try {
            // Check if we already have predictions for this entity
            if (!this.data.predictions[entity]) {
                // Load predictions
                const predictions = await api.getPredictions(entity);

                // Store predictions for this entity
                this.data.predictions[entity] = predictions;
            }

            // Update selected entity
            this.data.selectedEntity = entity;
        } catch (error) {
            console.error(`Error loading predictions for entity '${entity}':`, error);
            throw error;
        }
    }

    /**
     * Initialize entity selector
     */
    initEntitySelector() {
        // Initialize single entity selector
        this.initSingleEntitySelector();

        // Initialize multi-entity selector
        this.initMultiEntitySelector();

        // Initialize days to predict selectors
        this.initDaysToPredictSelectors();

        // Initialize event filter
        this.initEventFilter();

        // Initialize compare button
        this.initCompareButton();
    }

    /**
     * Initialize single entity selector
     */
    initSingleEntitySelector() {
        const selector = document.getElementById('prediction-entity-selector');
        if (!selector) return;

        // Clear selector
        selector.innerHTML = '';

        // Group entities by type
        const entityGroups = {};
        this.data.entities.slice(0, 30).forEach(entity => {
            const type = entity.type || 'OTHER';
            if (!entityGroups[type]) {
                entityGroups[type] = [];
            }
            entityGroups[type].push(entity);
        });

        // Add entities to selector grouped by type
        Object.keys(entityGroups).sort().forEach(type => {
            // Create optgroup
            const optgroup = document.createElement('optgroup');
            optgroup.label = this.formatEntityType(type);

            // Add entities to optgroup
            entityGroups[type].forEach(entity => {
                const option = document.createElement('option');
                option.value = entity.entity;
                option.textContent = entity.entity;

                // Set selected option
                if (entity.entity === this.data.selectedEntity) {
                    option.selected = true;
                }

                optgroup.appendChild(option);
            });

            selector.appendChild(optgroup);
        });

        // Add change event listener
        selector.addEventListener('change', async (event) => {
            const entity = event.target.value;

            // Update status
            utils.updateStatus(`Loading predictions for '${entity}'...`, 25);

            try {
                // Load predictions for selected entity
                await this.loadEntityPredictions(entity);

                // Update charts
                this.updatePredictionChart();
                this.updateModelComparisonChart();

                // Update metrics
                this.updatePredictionMetrics();

                // Update events
                this.updatePredictionEvents();

                // Update status
                utils.updateStatus(`Predictions for '${entity}' loaded`, 100, false);
            } catch (error) {
                console.error(`Error loading predictions for entity '${entity}':`, error);
                utils.updateStatus(`Error loading predictions for '${entity}'`, 0, false);
            }
        });
    }

    /**
     * Initialize multi-entity selector
     */
    initMultiEntitySelector() {
        const selector = document.getElementById('multi-entity-selector');
        if (!selector) return;

        // Clear selector
        selector.innerHTML = '';

        // Group entities by type
        const entityGroups = {};
        this.data.entities.slice(0, 30).forEach(entity => {
            const type = entity.type || 'OTHER';
            if (!entityGroups[type]) {
                entityGroups[type] = [];
            }
            entityGroups[type].push(entity);
        });

        // Add entities to selector grouped by type
        Object.keys(entityGroups).sort().forEach(type => {
            // Create optgroup
            const optgroup = document.createElement('optgroup');
            optgroup.label = this.formatEntityType(type);

            // Add entities to optgroup
            entityGroups[type].forEach(entity => {
                const option = document.createElement('option');
                option.value = entity.entity;
                option.textContent = entity.entity;

                // Set selected options
                if (this.data.selectedEntities.includes(entity.entity)) {
                    option.selected = true;
                }

                optgroup.appendChild(option);
            });

            selector.appendChild(optgroup);
        });

        // Add change event listener
        selector.addEventListener('change', () => {
            // Get selected entities
            const selectedOptions = Array.from(selector.selectedOptions);

            // Limit to 5 entities
            if (selectedOptions.length > 5) {
                alert('You can select up to 5 entities for comparison');

                // Deselect the last selected option
                selector.options[selector.options.length - 1].selected = false;
                return;
            }

            // Update selected entities
            this.data.selectedEntities = selectedOptions.map(option => option.value);
        });
    }

    /**
     * Initialize days to predict selectors
     */
    initDaysToPredictSelectors() {
        // Single entity view
        const daysSelector = document.getElementById('prediction-days-selector');
        if (daysSelector) {
            // Set initial value
            daysSelector.value = this.data.daysToPredict.toString();

            // Add change event listener
            daysSelector.addEventListener('change', async () => {
                // Update days to predict
                this.data.daysToPredict = parseInt(daysSelector.value);

                // Update prediction chart
                this.updatePredictionChart();
            });
        }

        // Multi-entity view
        const multiDaysSelector = document.getElementById('multi-prediction-days-selector');
        if (multiDaysSelector) {
            // Set initial value
            multiDaysSelector.value = this.data.daysToPredict.toString();

            // Add change event listener
            multiDaysSelector.addEventListener('change', () => {
                // Update days to predict
                this.data.daysToPredict = parseInt(multiDaysSelector.value);
            });
        }
    }

    /**
     * Initialize event filter
     */
    initEventFilter() {
        const checkbox = document.getElementById('show-high-probability-only');
        if (checkbox) {
            // Set initial value
            checkbox.checked = this.data.showHighProbabilityOnly;

            // Add change event listener
            checkbox.addEventListener('change', () => {
                // Update filter
                this.data.showHighProbabilityOnly = checkbox.checked;

                // Update events
                this.updatePredictionEvents();
            });
        }
    }

    /**
     * Initialize compare button
     */
    initCompareButton() {
        const button = document.getElementById('compare-entities-btn');
        if (button) {
            // Add click event listener
            button.addEventListener('click', async () => {
                // Check if entities are selected
                if (this.data.selectedEntities.length === 0) {
                    alert('Please select at least one entity to compare');
                    return;
                }

                // Update status
                utils.updateStatus(`Loading predictions for ${this.data.selectedEntities.length} entities...`, 25);

                try {
                    // Load predictions for all selected entities
                    for (const entity of this.data.selectedEntities) {
                        if (!this.data.predictions[entity]) {
                            await this.loadEntityPredictions(entity);
                        }
                    }

                    // Initialize multi-entity chart
                    this.initMultiEntityPredictionChart();

                    // Update status
                    utils.updateStatus(`Predictions loaded for ${this.data.selectedEntities.length} entities`, 100, false);
                } catch (error) {
                    console.error('Error loading predictions for multiple entities:', error);
                    utils.updateStatus('Error loading predictions', 0, false);
                }
            });
        }
    }

    /**
     * Initialize prediction chart
     */
    initPredictionChart() {
        const ctx = document.getElementById('entity-prediction-chart');
        if (!ctx) return;

        // Check if predictions are available
        if (!this.data.predictions || !this.data.predictions.historical_data || !this.data.predictions.predictions) {
            ctx.innerHTML = '<div class="alert alert-warning">No prediction data available</div>';
            return;
        }

        // Prepare data
        const historicalData = this.data.predictions.historical_data;
        const ensemblePredictions = this.data.predictions.predictions.ensemble;

        // Create labels and datasets
        const labels = [];
        const historicalValues = [];
        const predictionValues = [];
        const upperBoundValues = [];
        const lowerBoundValues = [];

        // Add historical data
        for (const date in historicalData) {
            labels.push(date);
            historicalValues.push(historicalData[date]);
            predictionValues.push(null);
            upperBoundValues.push(null);
            lowerBoundValues.push(null);
        }

        // Add prediction data with confidence intervals
        for (const date in ensemblePredictions) {
            labels.push(date);
            historicalValues.push(null);

            const predictedValue = ensemblePredictions[date];
            predictionValues.push(predictedValue);

            // Calculate confidence intervals (±15% for upper/lower bounds)
            // In a real implementation, these would come from the model's uncertainty estimates
            const confidenceMargin = predictedValue * 0.15;
            upperBoundValues.push(predictedValue + confidenceMargin);
            lowerBoundValues.push(Math.max(0, predictedValue - confidenceMargin));
        }

        // Sort labels by date
        const sortedIndices = labels.map((date, index) => ({ date, index }))
            .sort((a, b) => new Date(a.date) - new Date(b.date))
            .map(item => item.index);

        const sortedLabels = sortedIndices.map(index => labels[index]);
        const sortedHistoricalValues = sortedIndices.map(index => historicalValues[index]);
        const sortedPredictionValues = sortedIndices.map(index => predictionValues[index]);
        const sortedUpperBoundValues = sortedIndices.map(index => upperBoundValues[index]);
        const sortedLowerBoundValues = sortedIndices.map(index => lowerBoundValues[index]);

        // Create chart
        this.charts.entityPrediction = new Chart(ctx, {
            type: 'line',
            data: {
                labels: sortedLabels,
                datasets: [
                    {
                        label: 'Historical Data',
                        data: sortedHistoricalValues,
                        borderColor: CONFIG.colors.primary,
                        backgroundColor: `${CONFIG.colors.primary}33`,
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4
                    },
                    {
                        label: 'Prediction (Ensemble)',
                        data: sortedPredictionValues,
                        borderColor: CONFIG.colors.secondary,
                        backgroundColor: `${CONFIG.colors.secondary}33`,
                        borderWidth: 2,
                        borderDash: [5, 5],
                        fill: false,
                        tension: 0.4
                    },
                    {
                        label: 'Upper Confidence Bound',
                        data: sortedUpperBoundValues,
                        borderColor: `${CONFIG.colors.secondary}88`,
                        backgroundColor: `${CONFIG.colors.secondary}22`,
                        borderWidth: 1,
                        borderDash: [3, 3],
                        pointRadius: 0,
                        fill: '+1',
                        tension: 0.4
                    },
                    {
                        label: 'Lower Confidence Bound',
                        data: sortedLowerBoundValues,
                        borderColor: `${CONFIG.colors.secondary}88`,
                        backgroundColor: `${CONFIG.colors.secondary}22`,
                        borderWidth: 1,
                        borderDash: [3, 3],
                        pointRadius: 0,
                        fill: false,
                        tension: 0.4
                    }
                ]
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
                            text: 'Mentions'
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.dataset.label || '';
                                const value = context.parsed.y;

                                if (label === 'Upper Confidence Bound' || label === 'Lower Confidence Bound') {
                                    return `${label}: ${value.toFixed(1)}`;
                                }

                                return `${label}: ${value}`;
                            }
                        }
                    }
                }
            }
        });
    }

    /**
     * Update prediction chart
     */
    updatePredictionChart() {
        try {
            if (!this.charts.entityPrediction) {
                this.initPredictionChart();
                return;
            }

            // Check if predictions are available for the selected entity
            const entityData = this.data.predictions[this.data.selectedEntity];
            if (!entityData || !entityData.historical_data || !entityData.predictions) {
                console.warn(`No prediction data available for entity: ${this.data.selectedEntity}`);
                return;
            }

            // Set the predictions data for the current entity
            this.data.predictions = entityData;

            // Prepare data
            const historicalData = this.data.predictions.historical_data;
            const ensemblePredictions = this.data.predictions.predictions.ensemble;

            // Create labels and datasets
            const labels = [];
            const historicalValues = [];
            const predictionValues = [];
            const upperBoundValues = [];
            const lowerBoundValues = [];

            // Add historical data
            for (const date in historicalData) {
                labels.push(date);
                historicalValues.push(historicalData[date]);
                predictionValues.push(null);
                upperBoundValues.push(null);
                lowerBoundValues.push(null);
            }

            // Add prediction data with confidence intervals
            for (const date in ensemblePredictions) {
                labels.push(date);
                historicalValues.push(null);

                const predictedValue = ensemblePredictions[date];
                predictionValues.push(predictedValue);

                // Calculate confidence intervals (±15% for upper/lower bounds)
                const confidenceMargin = predictedValue * 0.15;
                upperBoundValues.push(predictedValue + confidenceMargin);
                lowerBoundValues.push(Math.max(0, predictedValue - confidenceMargin));
            }

            // Sort labels by date
            const sortedIndices = labels.map((date, index) => ({ date, index }))
                .sort((a, b) => new Date(a.date) - new Date(b.date))
                .map(item => item.index);

            const sortedLabels = sortedIndices.map(index => labels[index]);
            const sortedHistoricalValues = sortedIndices.map(index => historicalValues[index]);
            const sortedPredictionValues = sortedIndices.map(index => predictionValues[index]);
            const sortedUpperBoundValues = sortedIndices.map(index => upperBoundValues[index]);
            const sortedLowerBoundValues = sortedIndices.map(index => lowerBoundValues[index]);

            // Update chart data
            this.charts.entityPrediction.data.labels = sortedLabels;
            this.charts.entityPrediction.data.datasets[0].data = sortedHistoricalValues;
            this.charts.entityPrediction.data.datasets[1].data = sortedPredictionValues;
            this.charts.entityPrediction.data.datasets[2].data = sortedUpperBoundValues;
            this.charts.entityPrediction.data.datasets[3].data = sortedLowerBoundValues;

            // Update chart
            this.charts.entityPrediction.update();
        } catch (error) {
            console.error('Error updating prediction chart:', error);
        }
    }

    /**
     * Initialize model comparison chart
     */
    initModelComparisonChart() {
        const ctx = document.getElementById('model-comparison-chart');
        if (!ctx) return;

        // Check if predictions are available
        if (!this.data.predictions || !this.data.predictions.predictions) {
            ctx.innerHTML = '<div class="alert alert-warning">No prediction data available</div>';
            return;
        }

        // Get prediction date (first date in ensemble predictions)
        const predictionDates = Object.keys(this.data.predictions.predictions.ensemble).sort();
        if (predictionDates.length === 0) {
            ctx.innerHTML = '<div class="alert alert-warning">No prediction dates available</div>';
            return;
        }

        const predictionDate = predictionDates[0];

        // Get model predictions for the first date
        const modelPredictions = {};
        for (const model in this.data.predictions.predictions) {
            if (this.data.predictions.predictions[model][predictionDate]) {
                modelPredictions[model] = this.data.predictions.predictions[model][predictionDate];
            }
        }

        // Create chart
        this.charts.modelComparison = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: Object.keys(modelPredictions),
                datasets: [
                    {
                        label: `Predictions for ${predictionDate}`,
                        data: Object.values(modelPredictions),
                        backgroundColor: Object.keys(modelPredictions).map((model, index) => {
                            return CONFIG.colors.themes[index % CONFIG.colors.themes.length];
                        })
                    }
                ]
            },
            options: {
                ...CONFIG.chartDefaults,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Predicted Mentions'
                        }
                    }
                }
            }
        });
    }

    /**
     * Update model comparison chart
     */
    updateModelComparisonChart() {
        if (!this.charts.modelComparison) {
            this.initModelComparisonChart();
            return;
        }

        // Check if predictions are available
        if (!this.data.predictions || !this.data.predictions.predictions) {
            return;
        }

        // Get prediction date (first date in ensemble predictions)
        const predictionDates = Object.keys(this.data.predictions.predictions.ensemble).sort();
        if (predictionDates.length === 0) {
            return;
        }

        const predictionDate = predictionDates[0];

        // Get model predictions for the first date
        const modelPredictions = {};
        for (const model in this.data.predictions.predictions) {
            if (this.data.predictions.predictions[model][predictionDate]) {
                modelPredictions[model] = this.data.predictions.predictions[model][predictionDate];
            }
        }

        // Update chart data
        this.charts.modelComparison.data.labels = Object.keys(modelPredictions);
        this.charts.modelComparison.data.datasets[0].data = Object.values(modelPredictions);
        this.charts.modelComparison.data.datasets[0].backgroundColor = Object.keys(modelPredictions).map((model, index) => {
            return CONFIG.colors.themes[index % CONFIG.colors.themes.length];
        });
        this.charts.modelComparison.data.datasets[0].label = `Predictions for ${predictionDate}`;

        // Update chart
        this.charts.modelComparison.update();
    }

    /**
     * Initialize multi-entity prediction chart
     */
    initMultiEntityPredictionChart() {
        try {
            const ctx = document.getElementById('multi-entity-prediction-chart');
            if (!ctx) {
                console.error('Multi-entity prediction chart canvas not found');
                return;
            }

            // Check if selected entities are available
            if (this.data.selectedEntities.length === 0) {
                ctx.innerHTML = '<div class="alert alert-warning">No entities selected for comparison</div>';
                return;
            }

            // Destroy existing chart if it exists
            if (this.charts.multiEntityPrediction) {
                try {
                    this.charts.multiEntityPrediction.destroy();
                } catch (error) {
                    console.error('Error destroying existing chart:', error);
                }
            }

            // Prepare datasets
            const datasets = [];
            const allDates = new Set();

            // Create a dataset for each entity
            for (const entity of this.data.selectedEntities) {
                // Check if predictions are available for this entity
                if (!this.data.predictions[entity] ||
                    !this.data.predictions[entity].historical_data ||
                    !this.data.predictions[entity].predictions) {
                    console.warn(`No prediction data available for entity: ${entity}`);
                    continue;
                }

                // Get data for this entity
                const entityData = this.data.predictions[entity];
                const historicalData = entityData.historical_data;
                const ensemblePredictions = entityData.predictions.ensemble;

                // Collect all dates
                Object.keys(historicalData).forEach(date => allDates.add(date));
                Object.keys(ensemblePredictions).forEach(date => allDates.add(date));

                // Create dataset
                const dataPoints = {};

                // Add historical data
                for (const date in historicalData) {
                    dataPoints[date] = historicalData[date];
                }

                // Add prediction data
                for (const date in ensemblePredictions) {
                    dataPoints[date] = ensemblePredictions[date];
                }

                // Get a color for this entity
                const colorIndex = this.data.selectedEntities.indexOf(entity);
                const color = CONFIG.colors.themes[colorIndex % CONFIG.colors.themes.length];

                // Add dataset
                datasets.push({
                    label: entity,
                    data: dataPoints,
                    borderColor: color,
                    backgroundColor: `${color}33`,
                    borderWidth: 2,
                    fill: false,
                    tension: 0.4
                });
            }

            // Check if we have any datasets
            if (datasets.length === 0) {
                ctx.innerHTML = '<div class="alert alert-warning">No prediction data available for selected entities</div>';
                return;
            }

            // Sort dates
            const sortedDates = Array.from(allDates).sort((a, b) => new Date(a) - new Date(b));

            // Create chart
            this.charts.multiEntityPrediction = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: sortedDates,
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
                                text: 'Mentions'
                            }
                        }
                    },
                    plugins: {
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const label = context.dataset.label || '';
                                    const value = context.parsed.y;
                                    return `${label}: ${value}`;
                                }
                            }
                        }
                    }
                }
            });

            console.log('Multi-entity prediction chart initialized successfully');
        } catch (error) {
            console.error('Error initializing multi-entity prediction chart:', error);
            const ctx = document.getElementById('multi-entity-prediction-chart');
            if (ctx) {
                ctx.innerHTML = `<div class="alert alert-danger">Error initializing chart: ${error.message}</div>`;
            }
        }
    }

    /**
     * Initialize prediction metrics
     */
    initPredictionMetrics() {
        const container = document.getElementById('prediction-metrics');
        if (!container) return;

        // Clear container
        container.innerHTML = '';

        // Check if predictions are available
        if (!this.data.predictions || !this.data.predictions.model_evaluation) {
            container.innerHTML = '<div class="alert alert-warning">No model evaluation data available</div>';
            return;
        }

        // Create metrics table
        const table = document.createElement('table');
        table.className = 'table table-striped table-sm';

        // Create table header
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');

        const headers = ['Model', 'MSE', 'MAE', 'R²'];
        headers.forEach(header => {
            const th = document.createElement('th');
            th.textContent = header;
            headerRow.appendChild(th);
        });

        thead.appendChild(headerRow);
        table.appendChild(thead);

        // Create table body
        const tbody = document.createElement('tbody');

        for (const model in this.data.predictions.model_evaluation) {
            const metrics = this.data.predictions.model_evaluation[model];

            const row = document.createElement('tr');

            // Model name
            const nameCell = document.createElement('td');
            nameCell.textContent = model.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
            row.appendChild(nameCell);

            // MSE
            const mseCell = document.createElement('td');
            mseCell.textContent = metrics.mse ? metrics.mse.toFixed(4) : 'N/A';
            row.appendChild(mseCell);

            // MAE
            const maeCell = document.createElement('td');
            maeCell.textContent = metrics.mae ? metrics.mae.toFixed(4) : 'N/A';
            row.appendChild(maeCell);

            // R²
            const r2Cell = document.createElement('td');
            r2Cell.textContent = metrics.r2 ? metrics.r2.toFixed(4) : 'N/A';
            row.appendChild(r2Cell);

            tbody.appendChild(row);
        }

        table.appendChild(tbody);
        container.appendChild(table);
    }

    /**
     * Update prediction metrics
     */
    updatePredictionMetrics() {
        // Simply reinitialize the metrics
        this.initPredictionMetrics();
    }

    /**
     * Initialize prediction events
     */
    initPredictionEvents() {
        const container = document.getElementById('prediction-events');
        if (!container) return;

        // Clear container
        container.innerHTML = '';

        // Check if predictions are available
        if (!this.data.predictions || !this.data.predictions.predicted_events) {
            container.innerHTML = '<div class="alert alert-info">No predicted events available</div>';
            return;
        }

        // Get predicted events
        let predictedEvents = this.data.predictions.predicted_events;

        if (predictedEvents.length === 0) {
            container.innerHTML = '<div class="alert alert-info">No events predicted for this entity</div>';
            return;
        }

        // Filter events based on probability if needed
        if (this.data.showHighProbabilityOnly) {
            predictedEvents = predictedEvents.filter(event => event.confidence >= 0.7);

            if (predictedEvents.length === 0) {
                container.innerHTML = '<div class="alert alert-info">No high-probability events predicted for this entity</div>';
                return;
            }
        }

        // Create events list
        const list = document.createElement('div');
        list.className = 'list-group';

        predictedEvents.forEach((event, index) => {
            const item = document.createElement('div');
            item.className = 'list-group-item';

            // Create event header
            const header = document.createElement('div');
            header.className = 'd-flex justify-content-between align-items-center';

            const title = document.createElement('h5');
            title.className = 'mb-1';
            title.textContent = `Predicted Event: ${event.date}`;

            // Create badge with appropriate color based on confidence
            const badge = document.createElement('span');
            let badgeClass = 'bg-secondary';
            if (event.confidence >= 0.8) {
                badgeClass = 'bg-success';
            } else if (event.confidence >= 0.6) {
                badgeClass = 'bg-primary';
            } else if (event.confidence >= 0.4) {
                badgeClass = 'bg-warning text-dark';
            } else {
                badgeClass = 'bg-danger';
            }
            badge.className = `badge ${badgeClass} rounded-pill`;
            badge.textContent = `Confidence: ${(event.confidence * 100).toFixed(0)}%`;

            header.appendChild(title);
            header.appendChild(badge);

            // Create event details
            const details = document.createElement('div');
            details.className = 'mb-2';

            // Add predicted mentions
            const mentions = document.createElement('p');
            mentions.className = 'mb-1';
            mentions.innerHTML = `<strong>Predicted mentions:</strong> ${event.predicted_mentions.toFixed(1)}`;
            details.appendChild(mentions);

            // Add description if available
            if (event.description) {
                const description = document.createElement('p');
                description.className = 'mb-1';
                description.innerHTML = `<strong>Description:</strong> ${event.description}`;
                details.appendChild(description);
            }

            // Add view details button
            const buttonRow = document.createElement('div');
            buttonRow.className = 'd-flex justify-content-end mt-2';

            const detailsButton = document.createElement('button');
            detailsButton.className = 'btn btn-sm btn-outline-primary';
            detailsButton.textContent = 'View Details';
            detailsButton.dataset.eventIndex = index;

            // Add click event listener
            detailsButton.addEventListener('click', () => {
                this.showEventDetails(event);
            });

            buttonRow.appendChild(detailsButton);

            // Add to item
            item.appendChild(header);
            item.appendChild(details);
            item.appendChild(buttonRow);

            // Add to list
            list.appendChild(item);
        });

        container.appendChild(list);

        // Initialize event modal if not already initialized
        if (!this.data.eventModalInstance) {
            const modalElement = document.getElementById('event-details-modal');
            if (modalElement) {
                this.data.eventModalInstance = new bootstrap.Modal(modalElement);
            }
        }
    }

    /**
     * Show event details in modal
     * @param {Object} event - Event data
     */
    showEventDetails(event) {
        // Get modal elements
        const dateElement = document.getElementById('event-detail-date');
        const entityElement = document.getElementById('event-detail-entity');
        const mentionsElement = document.getElementById('event-detail-mentions');
        const confidenceElement = document.getElementById('event-detail-confidence');

        // Set modal content
        if (dateElement) dateElement.textContent = event.date;
        if (entityElement) entityElement.textContent = this.data.selectedEntity;
        if (mentionsElement) mentionsElement.textContent = event.predicted_mentions.toFixed(1);

        // Set confidence with color coding
        if (confidenceElement) {
            confidenceElement.textContent = `${(event.confidence * 100).toFixed(0)}%`;

            // Add color based on confidence
            confidenceElement.className = '';
            if (event.confidence >= 0.8) {
                confidenceElement.className = 'text-success fw-bold';
            } else if (event.confidence >= 0.6) {
                confidenceElement.className = 'text-primary fw-bold';
            } else if (event.confidence >= 0.4) {
                confidenceElement.className = 'text-warning fw-bold';
            } else {
                confidenceElement.className = 'text-danger fw-bold';
            }
        }

        // Create event detail chart
        this.createEventDetailChart(event);

        // Show modal
        if (this.data.eventModalInstance) {
            this.data.eventModalInstance.show();
        }
    }

    /**
     * Create event detail chart
     * @param {Object} event - Event data
     */
    createEventDetailChart(event) {
        const ctx = document.getElementById('event-detail-chart');
        if (!ctx) return;

        // Destroy existing chart if it exists
        if (this.charts.eventDetailChart) {
            this.charts.eventDetailChart.destroy();
        }

        // Get historical data and predictions
        const historicalData = this.data.predictions[this.data.selectedEntity].historical_data;
        const predictions = this.data.predictions[this.data.selectedEntity].predictions.ensemble;

        // Create labels and datasets
        const labels = [];
        const values = [];

        // Add historical data
        for (const date in historicalData) {
            labels.push(date);
            values.push(historicalData[date]);
        }

        // Add prediction data
        for (const date in predictions) {
            labels.push(date);
            values.push(predictions[date]);
        }

        // Sort by date
        const sortedIndices = labels.map((date, index) => ({ date, index }))
            .sort((a, b) => new Date(a.date) - new Date(b.date))
            .map(item => item.index);

        const sortedLabels = sortedIndices.map(index => labels[index]);
        const sortedValues = sortedIndices.map(index => values[index]);

        // Find event date index
        const eventDateIndex = sortedLabels.findIndex(date => date === event.date);

        // Create point styles array (highlight the event date)
        const pointStyles = sortedLabels.map(date => date === event.date ? 'circle' : 'circle');
        const pointRadii = sortedLabels.map(date => date === event.date ? 8 : 3);
        const pointColors = sortedLabels.map(date => date === event.date ? 'red' : CONFIG.colors.primary);

        // Create chart
        this.charts.eventDetailChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: sortedLabels,
                datasets: [
                    {
                        label: 'Entity Mentions',
                        data: sortedValues,
                        borderColor: CONFIG.colors.primary,
                        backgroundColor: pointColors,
                        borderWidth: 2,
                        pointStyle: pointStyles,
                        pointRadius: pointRadii,
                        tension: 0.4
                    }
                ]
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
                        }
                    },
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Mentions'
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.dataset.label || '';
                                const value = context.parsed.y;
                                return `${label}: ${value}`;
                            }
                        }
                    },
                    // Only add annotation if the plugin is available
                    ...(window.Chart && window.Chart.Annotation ? {
                        annotation: {
                            annotations: {
                                eventLine: {
                                    type: 'line',
                                    xMin: event.date,
                                    xMax: event.date,
                                    borderColor: 'red',
                                    borderWidth: 2,
                                    label: {
                                        content: 'Predicted Event',
                                        enabled: true,
                                        position: 'top'
                                    }
                                }
                            }
                        }
                    } : {})
                }
            }
        });
    }

    /**
     * Update prediction events
     */
    updatePredictionEvents() {
        // Simply reinitialize the events
        this.initPredictionEvents();
    }

    /**
     * Refresh the predictions view
     */
    async refresh() {
        try {
            // Update status
            utils.updateStatus('Refreshing prediction data...', 25);

            // Load data
            await this.loadData();

            // Update entity selector
            this.initEntitySelector();

            // Update prediction chart
            this.updatePredictionChart();

            // Update model comparison chart
            this.updateModelComparisonChart();

            // Update prediction metrics
            this.updatePredictionMetrics();

            // Update prediction events
            this.updatePredictionEvents();

            // Update status
            utils.updateStatus('Prediction data refreshed', 100, false);
        } catch (error) {
            console.error('Error refreshing predictions view:', error);
            utils.updateStatus('Error refreshing prediction data', 0, false);
        }
    }

    /**
     * Format entity type for display
     * @param {string} type - Entity type
     * @returns {string} - Formatted entity type
     */
    formatEntityType(type) {
        // Handle common entity types
        switch (type.toUpperCase()) {
            case 'PERSON':
                return '👤 People';
            case 'ORGANIZATION':
            case 'ORG':
                return '🏢 Organizations';
            case 'LOCATION':
            case 'LOC':
            case 'GPE':
                return '📍 Locations';
            case 'EVENT':
                return '📅 Events';
            case 'PRODUCT':
            case 'WORK_OF_ART':
                return '📦 Products';
            case 'DATE':
            case 'TIME':
                return '⏰ Dates & Times';
            case 'MONEY':
            case 'PERCENT':
            case 'QUANTITY':
                return '💰 Quantities';
            case 'LANGUAGE':
                return '🗣️ Languages';
            case 'OTHER':
                return '❓ Other Entities';
            default:
                // Capitalize each word
                return type.split('_').map(word =>
                    word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
                ).join(' ');
        }
    }
}
