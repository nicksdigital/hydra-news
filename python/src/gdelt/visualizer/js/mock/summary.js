/**
 * Mock summary data for the GDELT News Analysis Dashboard
 */
const MOCK_SUMMARY = {
    article_count: 5000,
    entity_count: 1200,
    themes: [
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
        { country: 'China', count: 450 },
        { country: 'Russia', count: 400 },
        { country: 'Japan', count: 350 },
        { country: 'India', count: 300 },
        { country: 'Brazil', count: 250 },
        { country: 'Canada', count: 200 }
    ],
    sentiment: {
        positive: 2000,
        neutral: 2500,
        negative: 500
    }
};

// Add to window for testing
window.MOCK_SUMMARY = MOCK_SUMMARY;
