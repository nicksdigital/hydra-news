/**
 * Configuration settings for the GDELT News Analysis Dashboard
 */
const CONFIG = {
    // API endpoints
    api: {
        base: '/api',
        summary: '/api/summary',
        entities: '/api/entities',
        themes: '/api/themes',
        timelines: '/api/timelines',
        sentiment: '/api/sentiment',
        events: '/api/events',
        articles: '/api/articles',
        predictions: '/api/predictions'
    },

    // Data refresh interval in milliseconds (1 minute)
    refreshInterval: 1 * 60 * 1000,

    // Chart colors
    colors: {
        primary: '#0d6efd',
        secondary: '#6c757d',
        success: '#198754',
        danger: '#dc3545',
        warning: '#ffc107',
        info: '#0dcaf0',
        light: '#f8f9fa',
        dark: '#212529',

        // Theme colors
        themes: [
            '#4e79a7', '#f28e2c', '#e15759', '#76b7b2', '#59a14f',
            '#edc949', '#af7aa1', '#ff9da7', '#9c755f', '#bab0ab'
        ],

        // Entity colors
        entities: [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ],

        // Sentiment colors
        sentiment: {
            positive: '#198754',
            neutral: '#6c757d',
            negative: '#dc3545'
        }
    },

    // Default chart options
    chartDefaults: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'bottom'
            },
            tooltip: {
                mode: 'index',
                intersect: false
            }
        }
    },

    // Maximum number of items to display in various charts and lists
    limits: {
        topEntities: 10,
        topThemes: 10,
        topCountries: 10,
        recentEvents: 5,
        timelineEvents: 20
    }
};
