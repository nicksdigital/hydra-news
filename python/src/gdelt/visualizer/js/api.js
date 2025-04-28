/**
 * API service for the GDELT News Analysis Dashboard
 */
class ApiService {
    /**
     * Fetch data from the API
     * @param {string} endpoint - API endpoint
     * @param {Object} params - Query parameters
     * @returns {Promise<Object>} - API response
     */
    async fetch(endpoint, params = {}) {
        try {
            // Build URL with query parameters
            const url = new URL(endpoint, window.location.origin);
            Object.keys(params).forEach(key => {
                if (params[key] !== undefined && params[key] !== null) {
                    url.searchParams.append(key, params[key]);
                }
            });

            // Fetch data
            const response = await fetch(url);

            // Check if response is OK
            if (!response.ok) {
                throw new Error(`API error: ${response.status} ${response.statusText}`);
            }

            // Parse JSON response
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('API fetch error:', error);
            throw error;
        }
    }

    /**
     * Get summary data
     * @returns {Promise<Object>} - Summary data
     */
    async getSummary() {
        try {
            return this.fetch(CONFIG.api.summary);
        } catch (error) {
            console.warn('Error fetching summary data, using mock data:', error);
            // Return mock data for testing
            return window.MOCK_SUMMARY || {
                article_count: 5000,
                entity_count: 1200,
                themes: [
                    { theme: 'ECON', description: 'Economy', count: 850 },
                    { theme: 'ENV', description: 'Environment', count: 720 },
                    { theme: 'TECH', description: 'Technology', count: 650 },
                    { theme: 'HEALTH', description: 'Health', count: 580 },
                    { theme: 'CONFLICT', description: 'Conflict', count: 520 }
                ],
                timeSeries: (() => {
                    const data = [];
                    const today = new Date();
                    for (let i = 29; i >= 0; i--) {
                        const date = new Date(today);
                        date.setDate(date.getDate() - i);
                        data.push({
                            date: date.toISOString().split('T')[0],
                            count: Math.floor(Math.random() * 200) + 100
                        });
                    }
                    return data;
                })(),
                countries: [
                    { country: 'United States', count: 1200 },
                    { country: 'United Kingdom', count: 800 },
                    { country: 'Germany', count: 600 },
                    { country: 'France', count: 500 },
                    { country: 'China', count: 450 }
                ],
                sentiment: {
                    positive: 2000,
                    neutral: 2500,
                    negative: 500
                }
            };
        }
    }

    /**
     * Get entity data
     * @param {string} entity - Entity name (optional)
     * @returns {Promise<Object>} - Entity data
     */
    async getEntities(entity = null) {
        try {
            const params = entity ? { entity } : {};
            return this.fetch(CONFIG.api.entities, params);
        } catch (error) {
            console.warn('Error fetching entity data, using mock data:', error);
            // Return mock data for testing
            if (entity) {
                return {
                    entity: {
                        id: 1,
                        text: entity,
                        type: 'PERSON',
                        mention_count: 150
                    },
                    articles: Array(20).fill(0).map((_, i) => ({
                        id: i + 1,
                        title: `Article about ${entity} #${i + 1}`,
                        url: `https://example.com/article${i + 1}`,
                        domain: 'example.com',
                        seendate: new Date(Date.now() - i * 86400000).toISOString(),
                        sourcecountry: 'United States',
                        theme_id: 'POLITICAL',
                        theme_description: 'Politics'
                    }))
                };
            } else {
                return Array(50).fill(0).map((_, i) => ({
                    entity: `Entity ${i + 1}`,
                    type: ['PERSON', 'ORGANIZATION', 'LOCATION', 'EVENT'][Math.floor(Math.random() * 4)],
                    count: Math.floor(Math.random() * 500) + 50
                }));
            }
        }
    }

    /**
     * Get theme data
     * @param {string} theme - Theme ID (optional)
     * @returns {Promise<Object>} - Theme data
     */
    async getThemes(theme = null) {
        try {
            const params = theme ? { theme } : {};
            return this.fetch(CONFIG.api.themes, params);
        } catch (error) {
            console.warn('Error fetching theme data, using mock data:', error);
            // Return mock data for testing
            const themes = [
                { theme: 'ECON', description: 'Economy', count: 850 },
                { theme: 'ENV', description: 'Environment', count: 720 },
                { theme: 'TECH', description: 'Technology', count: 650 },
                { theme: 'HEALTH', description: 'Health', count: 580 },
                { theme: 'CONFLICT', description: 'Conflict', count: 520 },
                { theme: 'POLITICAL', description: 'Politics', count: 480 },
                { theme: 'SOCIAL', description: 'Social Issues', count: 420 },
                { theme: 'EDUCATION', description: 'Education', count: 380 },
                { theme: 'SECURITY', description: 'Security', count: 350 },
                { theme: 'ENERGY', description: 'Energy', count: 320 }
            ];

            if (theme) {
                const themeData = themes.find(t => t.theme === theme);
                if (!themeData) {
                    throw new Error(`Theme not found: ${theme}`);
                }

                return {
                    theme: themeData,
                    articles: Array(20).fill(0).map((_, i) => ({
                        id: i + 1,
                        title: `Article about ${themeData.description} #${i + 1}`,
                        url: `https://example.com/article${i + 1}`,
                        domain: 'example.com',
                        seendate: new Date(Date.now() - i * 86400000).toISOString(),
                        sourcecountry: 'United States',
                        theme_id: theme,
                        theme_description: themeData.description
                    }))
                };
            } else {
                return themes;
            }
        }
    }

    /**
     * Get timeline data
     * @param {string} entity - Entity name
     * @param {string} type - Timeline type (entity, event, sentiment)
     * @returns {Promise<Object>} - Timeline data
     */
    async getTimeline(entity, type = 'entity') {
        try {
            return this.fetch(CONFIG.api.timelines, { entity, type });
        } catch (error) {
            console.warn('Error fetching timeline data, using mock data:', error);
            // Return mock data for testing
            const today = new Date();
            const data = [];

            for (let i = 29; i >= 0; i--) {
                const date = new Date(today);
                date.setDate(date.getDate() - i);

                if (type === 'entity') {
                    data.push({
                        date: date.toISOString().split('T')[0],
                        count: Math.floor(Math.random() * 50) + 10
                    });
                } else if (type === 'sentiment') {
                    data.push({
                        date: date.toISOString().split('T')[0],
                        sentiment: (Math.random() * 2 - 1) * 0.8
                    });
                } else if (type === 'event') {
                    // Only add events on some days
                    if (Math.random() > 0.7) {
                        data.push({
                            date: date.toISOString().split('T')[0],
                            title: `Event involving ${entity}`,
                            description: `This is a mock event about ${entity} that occurred on ${date.toISOString().split('T')[0]}.`,
                            source: 'Mock Data'
                        });
                    }
                }
            }

            return {
                entity,
                type,
                data
            };
        }
    }

    /**
     * Get sentiment data
     * @param {string} entity - Entity name (optional)
     * @param {string} theme - Theme ID (optional)
     * @returns {Promise<Object>} - Sentiment data
     */
    async getSentiment(entity = null, theme = null) {
        try {
            const params = {};
            if (entity) params.entity = entity;
            if (theme) params.theme = theme;
            return this.fetch(CONFIG.api.sentiment, params);
        } catch (error) {
            console.warn('Error fetching sentiment data, using mock data:', error);
            // Return mock data for testing
            const today = new Date();
            const overall = [];

            for (let i = 29; i >= 0; i--) {
                const date = new Date(today);
                date.setDate(date.getDate() - i);
                overall.push({
                    date: date.toISOString().split('T')[0],
                    sentiment: (Math.random() * 2 - 1) * 0.5
                });
            }

            if (entity) {
                return {
                    entity,
                    sentiment: overall
                };
            } else if (theme) {
                return {
                    theme,
                    sentiment: overall
                };
            } else {
                // Generate entity sentiment data
                const entities = Array(10).fill(0).map((_, i) => ({
                    entity: `Entity ${i + 1}`,
                    sentiment: (Math.random() * 2 - 1) * 0.8,
                    count: Math.floor(Math.random() * 500) + 50
                }));

                // Generate theme sentiment data
                const themes = [
                    { theme: 'ECON', description: 'Economy', sentiment: 0.3, count: 850 },
                    { theme: 'ENV', description: 'Environment', sentiment: 0.1, count: 720 },
                    { theme: 'TECH', description: 'Technology', sentiment: 0.5, count: 650 },
                    { theme: 'HEALTH', description: 'Health', sentiment: -0.2, count: 580 },
                    { theme: 'CONFLICT', description: 'Conflict', sentiment: -0.7, count: 520 },
                    { theme: 'POLITICAL', description: 'Politics', sentiment: -0.3, count: 480 },
                    { theme: 'SOCIAL', description: 'Social Issues', sentiment: 0.2, count: 420 },
                    { theme: 'EDUCATION', description: 'Education', sentiment: 0.6, count: 380 },
                    { theme: 'SECURITY', description: 'Security', sentiment: -0.4, count: 350 },
                    { theme: 'ENERGY', description: 'Energy', sentiment: 0.1, count: 320 }
                ];

                return {
                    overall,
                    entities,
                    themes
                };
            }
        }
    }

    /**
     * Get event data
     * @param {string} entity - Entity name (optional)
     * @param {number} limit - Maximum number of events to return (optional)
     * @returns {Promise<Object>} - Event data
     */
    async getEvents(entity = null, limit = null) {
        try {
            const params = {};
            if (entity) params.entity = entity;
            if (limit) params.limit = limit;
            return this.fetch(CONFIG.api.events, params);
        } catch (error) {
            console.warn('Error fetching event data, using mock data:', error);
            // Return mock data for testing
            const today = new Date();
            const events = [];

            // Generate random events
            for (let i = 0; i < (limit || 10); i++) {
                const date = new Date(today);
                date.setDate(date.getDate() - Math.floor(Math.random() * 30));

                events.push({
                    id: i + 1,
                    title: entity ?
                        `Event involving ${entity} #${i + 1}` :
                        `Event #${i + 1}`,
                    url: `https://example.com/event${i + 1}`,
                    domain: 'example.com',
                    seendate: date.toISOString(),
                    date: date.toISOString().split('T')[0],
                    sourcecountry: 'United States',
                    theme_id: ['ECON', 'ENV', 'TECH', 'HEALTH', 'CONFLICT'][Math.floor(Math.random() * 5)],
                    theme_description: ['Economy', 'Environment', 'Technology', 'Health', 'Conflict'][Math.floor(Math.random() * 5)],
                    source: 'Mock Data',
                    description: entity ?
                        `This is a mock event about ${entity} that occurred on ${date.toISOString().split('T')[0]}.` :
                        `This is a mock event that occurred on ${date.toISOString().split('T')[0]}.`
                });
            }

            // Sort by date (newest first)
            events.sort((a, b) => new Date(b.seendate) - new Date(a.seendate));

            return events;
        }
    }

    /**
     * Get article data
     * @param {string} entity - Entity name (optional)
     * @param {string} theme - Theme ID (optional)
     * @param {number} limit - Maximum number of articles to return (optional)
     * @returns {Promise<Object>} - Article data
     */
    async getArticles(entity = null, theme = null, limit = null) {
        try {
            const params = {};
            if (entity) params.entity = entity;
            if (theme) params.theme = theme;
            if (limit) params.limit = limit;
            return this.fetch(CONFIG.api.articles, params);
        } catch (error) {
            console.warn('Error fetching article data, using mock data:', error);
            // Return mock data for testing
            const today = new Date();
            const articles = [];

            // Generate random articles
            for (let i = 0; i < (limit || 50); i++) {
                const date = new Date(today);
                date.setDate(date.getDate() - Math.floor(Math.random() * 30));

                const themeIndex = Math.floor(Math.random() * 5);
                const themeIds = ['ECON', 'ENV', 'TECH', 'HEALTH', 'CONFLICT'];
                const themeDescriptions = ['Economy', 'Environment', 'Technology', 'Health', 'Conflict'];

                articles.push({
                    id: i + 1,
                    title: entity ?
                        `Article about ${entity} #${i + 1}` :
                        theme ?
                            `Article about ${themeDescriptions[themeIds.indexOf(theme)]} #${i + 1}` :
                            `Article #${i + 1}`,
                    url: `https://example.com/article${i + 1}`,
                    domain: 'example.com',
                    seendate: date.toISOString(),
                    sourcecountry: 'United States',
                    theme_id: theme || themeIds[themeIndex],
                    theme_description: theme ?
                        themeDescriptions[themeIds.indexOf(theme)] :
                        themeDescriptions[themeIndex],
                    sentiment_polarity: (Math.random() * 2 - 1) * 0.8
                });
            }

            // Sort by date (newest first)
            articles.sort((a, b) => new Date(b.seendate) - new Date(a.seendate));

            return articles;
        }
    }

    /**
     * Get prediction data for an entity
     * @param {string} entity - Entity name
     * @returns {Promise<Object>} - Prediction data
     */
    async getPredictions(entity) {
        try {
            return this.fetch(CONFIG.api.predictions, { entity });
        } catch (error) {
            console.warn('Error fetching prediction data, using mock data:', error);
            // Return mock data for testing
            const today = new Date();

            // Generate historical data (last 30 days)
            const historicalData = {};
            for (let i = 30; i >= 1; i--) {
                const date = new Date(today);
                date.setDate(date.getDate() - i);
                const dateStr = date.toISOString().split('T')[0];
                historicalData[dateStr] = Math.floor(Math.random() * 50) + 10;
            }

            // Generate predictions (next 14 days)
            const predictions = {
                linear: {},
                random_forest: {},
                svr: {},
                ensemble: {}
            };

            // Base value for predictions (last historical value)
            const lastDate = Object.keys(historicalData).sort().pop();
            const baseValue = historicalData[lastDate];

            // Generate predictions for each model
            for (let i = 1; i <= 14; i++) {
                const date = new Date(today);
                date.setDate(date.getDate() + i);
                const dateStr = date.toISOString().split('T')[0];

                // Different models have slightly different predictions
                predictions.linear[dateStr] = Math.max(0, baseValue + (Math.random() * 10 - 5));
                predictions.random_forest[dateStr] = Math.max(0, baseValue + (Math.random() * 15 - 7));
                predictions.svr[dateStr] = Math.max(0, baseValue + (Math.random() * 12 - 6));
                predictions.ensemble[dateStr] = Math.max(0, (
                    predictions.linear[dateStr] +
                    predictions.random_forest[dateStr] +
                    predictions.svr[dateStr]
                ) / 3);
            }

            // Generate model evaluation metrics
            const modelEvaluation = {
                linear: {
                    mse: Math.random() * 10 + 5,
                    mae: Math.random() * 5 + 2,
                    r2: Math.random() * 0.5 + 0.3
                },
                random_forest: {
                    mse: Math.random() * 8 + 4,
                    mae: Math.random() * 4 + 1.5,
                    r2: Math.random() * 0.6 + 0.4
                },
                svr: {
                    mse: Math.random() * 9 + 4.5,
                    mae: Math.random() * 4.5 + 1.8,
                    r2: Math.random() * 0.55 + 0.35
                },
                ensemble: {
                    mse: Math.random() * 7 + 3.5,
                    mae: Math.random() * 3.5 + 1.2,
                    r2: Math.random() * 0.65 + 0.45
                }
            };

            // Generate predicted events
            const predictedEvents = [];
            for (let i = 1; i <= 14; i++) {
                // Only add events with 20% probability
                if (Math.random() > 0.8) {
                    const date = new Date(today);
                    date.setDate(date.getDate() + i);
                    const dateStr = date.toISOString().split('T')[0];

                    predictedEvents.push({
                        date: dateStr,
                        predicted_mentions: predictions.ensemble[dateStr],
                        confidence: Math.random() * 0.5 + 0.5,
                        description: `Predicted spike in mentions for ${entity}`
                    });
                }
            }

            return {
                entity,
                historical_data: historicalData,
                predictions,
                model_evaluation: modelEvaluation,
                predicted_events: predictedEvents
            };
        }
    }

    /**
     * For development/testing: Load mock data from a JSON file
     * @param {string} filename - JSON file name
     * @returns {Promise<Object>} - Mock data
     */
    async loadMockData(filename) {
        try {
            const response = await fetch(`../mock/${filename}.json`);
            if (!response.ok) {
                throw new Error(`Failed to load mock data: ${response.status} ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Error loading mock data:', error);
            throw error;
        }
    }
}

// Create a singleton instance
const api = new ApiService();
