/**
 * Utility functions for the GDELT News Analysis Dashboard
 */
const utils = {
    /**
     * Format a date string
     * @param {string|Date} date - Date to format
     * @param {string} format - Format string (default: 'YYYY-MM-DD')
     * @returns {string} - Formatted date string
     */
    formatDate(date, format = 'YYYY-MM-DD') {
        return moment(date).format(format);
    },

    /**
     * Format a relative time (e.g., "2 hours ago")
     * @param {string|Date} date - Date to format
     * @returns {string} - Relative time string
     */
    formatRelativeTime(date) {
        return moment(date).fromNow();
    },

    /**
     * Format a number with commas
     * @param {number} num - Number to format
     * @returns {string} - Formatted number string
     */
    formatNumber(num) {
        return num.toLocaleString();
    },

    /**
     * Format a percentage
     * @param {number} value - Value to format
     * @param {number} decimals - Number of decimal places (default: 1)
     * @returns {string} - Formatted percentage string
     */
    formatPercent(value, decimals = 1) {
        return `${(value * 100).toFixed(decimals)}%`;
    },

    /**
     * Format a sentiment score
     * @param {number} score - Sentiment score (-1 to 1)
     * @returns {string} - Formatted sentiment string with icon
     */
    formatSentiment(score) {
        if (score > 0.2) {
            return `<span class="sentiment-positive"><i class="bi bi-emoji-smile"></i> ${score.toFixed(2)}</span>`;
        } else if (score < -0.2) {
            return `<span class="sentiment-negative"><i class="bi bi-emoji-frown"></i> ${score.toFixed(2)}</span>`;
        } else {
            return `<span class="sentiment-neutral"><i class="bi bi-emoji-neutral"></i> ${score.toFixed(2)}</span>`;
        }
    },

    /**
     * Get a color for a sentiment score
     * @param {number} score - Sentiment score (-1 to 1)
     * @returns {string} - Color hex code
     */
    getSentimentColor(score) {
        if (score > 0.2) {
            return CONFIG.colors.sentiment.positive;
        } else if (score < -0.2) {
            return CONFIG.colors.sentiment.negative;
        } else {
            return CONFIG.colors.sentiment.neutral;
        }
    },

    /**
     * Get a color for an entity
     * @param {string} entity - Entity name
     * @param {number} index - Entity index
     * @returns {string} - Color hex code
     */
    getEntityColor(entity, index = 0) {
        // Use a hash function to get a consistent color for the same entity
        const hash = this.hashString(entity);
        const colorIndex = hash % CONFIG.colors.entities.length;
        return CONFIG.colors.entities[colorIndex];
    },

    /**
     * Get a color for a theme
     * @param {string} theme - Theme ID
     * @param {number} index - Theme index
     * @returns {string} - Color hex code
     */
    getThemeColor(theme, index = 0) {
        // Use a hash function to get a consistent color for the same theme
        const hash = this.hashString(theme);
        const colorIndex = hash % CONFIG.colors.themes.length;
        return CONFIG.colors.themes[colorIndex];
    },

    /**
     * Simple string hash function
     * @param {string} str - String to hash
     * @returns {number} - Hash value
     */
    hashString(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32bit integer
        }
        return Math.abs(hash);
    },

    /**
     * Create an entity badge element
     * @param {string} entity - Entity name
     * @param {boolean} active - Whether the badge is active
     * @param {Function} onClick - Click event handler
     * @returns {HTMLElement} - Badge element
     */
    createEntityBadge(entity, active = false, onClick = null) {
        const badge = document.createElement('div');
        badge.className = `entity-badge${active ? ' active' : ''}`;
        badge.textContent = entity;
        badge.dataset.entity = entity;

        if (onClick) {
            badge.addEventListener('click', () => onClick(entity));
        }

        return badge;
    },

    /**
     * Create a theme tag element
     * @param {string} theme - Theme ID
     * @param {string} description - Theme description
     * @returns {HTMLElement} - Tag element
     */
    createThemeTag(theme, description) {
        const tag = document.createElement('span');
        tag.className = 'theme-tag';
        tag.textContent = description || theme;
        tag.dataset.theme = theme;
        tag.style.backgroundColor = this.getThemeColor(theme);
        tag.style.color = '#fff';

        return tag;
    },

    /**
     * Create a timeline item element
     * @param {Object} event - Event data
     * @returns {HTMLElement} - Timeline item element
     */
    createTimelineItem(event) {
        const item = document.createElement('div');
        item.className = 'timeline-item';

        const date = document.createElement('div');
        date.className = 'timeline-date';
        date.textContent = this.formatDate(event.date, 'MMM D, YYYY');

        const content = document.createElement('div');
        content.className = 'timeline-content';

        const title = document.createElement('h6');
        title.textContent = event.title;

        const description = document.createElement('p');
        description.textContent = event.description;
        description.className = 'mb-1';

        const source = document.createElement('small');
        source.className = 'text-muted';
        source.textContent = event.source;

        content.appendChild(title);
        content.appendChild(description);
        content.appendChild(source);

        item.appendChild(date);
        item.appendChild(content);

        return item;
    },

    /**
     * Show a loading spinner
     * @param {string} elementId - Element ID
     */
    showLoading(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.innerHTML = `
                <div class="d-flex justify-content-center">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                </div>
            `;
        }
    },

    /**
     * Hide a loading spinner
     * @param {string} elementId - Element ID
     */
    hideLoading(elementId) {
        const element = document.getElementById(elementId);
        if (element && element.querySelector('.spinner-border')) {
            element.innerHTML = '';
        }
    },

    /**
     * Update the status bar
     * @param {string} text - Status text
     * @param {number} progress - Progress percentage (0-100)
     * @param {boolean} loading - Whether to show the loading spinner
     */
    updateStatus(text, progress = null, loading = true) {
        const statusText = document.getElementById('status-text');
        const statusProgress = document.getElementById('status-progress');
        const statusPercentage = document.getElementById('status-percentage');
        const statusIndicator = document.getElementById('status-indicator');

        if (statusText) {
            statusText.textContent = text;
        }

        if (statusProgress && progress !== null) {
            statusProgress.style.width = `${progress}%`;
        }

        if (statusPercentage && progress !== null) {
            statusPercentage.textContent = `${progress}%`;
        }

        if (statusIndicator) {
            statusIndicator.style.display = loading ? 'inline-block' : 'none';
        }
    },

    /**
     * Load HTML content from a template file
     * @param {string} url - Template URL
     * @returns {Promise<string>} - HTML content
     */
    async loadTemplate(url) {
        try {
            console.log(`Fetching template from URL: ${url}`);
            const response = await fetch(url);
            console.log(`Response status: ${response.status} ${response.statusText}`);

            if (!response.ok) {
                throw new Error(`Failed to load template: ${response.status} ${response.statusText}`);
            }

            const text = await response.text();
            console.log(`Template content length: ${text.length}`);

            if (text.length === 0) {
                console.warn('Warning: Empty template content');
            }

            return text;
        } catch (error) {
            console.error('Error loading template:', error);
            throw error;
        }
    }
};
