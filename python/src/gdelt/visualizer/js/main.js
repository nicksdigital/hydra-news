/**
 * Main JavaScript file for the GDELT News Analysis Dashboard
 */
class DashboardApp {
    constructor() {
        // Initialize views
        this.views = {
            dashboard: new DashboardView(),
            timelines: new TimelinesView(),
            sentiment: new SentimentView(),
            entities: new EntitiesView(),
            themes: new ThemesView(),
            predictions: new PredictionsView()
        };

        // Current view
        this.currentView = 'dashboard';

        // Data refresh timer
        this.refreshTimer = null;

        // Initialize the app
        this.init();
    }

    /**
     * Initialize the app
     */
    async init() {
        try {
            // Set up event listeners
            this.setupEventListeners();

            // Load the initial view
            await this.loadView(this.currentView);

            // Start the data refresh timer
            this.startRefreshTimer();

            // Update status
            utils.updateStatus('Dashboard ready', 100, false);
        } catch (error) {
            console.error('Error initializing app:', error);
            utils.updateStatus('Error initializing dashboard', 0, false);
        }
    }

    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // Navigation links
        document.querySelectorAll('.nav-link[data-view]').forEach(link => {
            link.addEventListener('click', (event) => {
                event.preventDefault();
                const view = event.target.dataset.view;
                this.loadView(view);
            });
        });

        // Refresh button
        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.refreshData();
            });
        }
    }

    /**
     * Load a view
     * @param {string} viewName - View name
     */
    async loadView(viewName) {
        try {
            // Update status
            utils.updateStatus(`Loading ${viewName} view...`, 25);

            // Hide all views
            document.querySelectorAll('.view-content').forEach(view => {
                view.classList.add('d-none');
            });

            // Deactivate all nav links
            document.querySelectorAll('.nav-link').forEach(link => {
                link.classList.remove('active');
            });

            // Activate the selected nav link
            const navLink = document.querySelector(`.nav-link[data-view="${viewName}"]`);
            if (navLink) {
                navLink.classList.add('active');
            }

            // Get the view container
            const viewContainer = document.getElementById(`${viewName}-view`);
            if (!viewContainer) {
                throw new Error(`View container not found: ${viewName}-view`);
            }

            // Load the view template if not already loaded
            if (viewContainer.children.length === 0) {
                console.log(`Loading template for view: ${viewName}`);
                const templateUrl = `../templates/${viewName}.html`;
                console.log(`Template URL: ${templateUrl}`);
                try {
                    const templateHtml = await utils.loadTemplate(templateUrl);
                    console.log(`Template loaded, length: ${templateHtml.length}`);
                    viewContainer.innerHTML = templateHtml;
                } catch (error) {
                    console.error(`Error loading template for ${viewName}:`, error);
                    viewContainer.innerHTML = `<div class="alert alert-danger">Error loading template: ${error.message}</div>`;
                }
            }

            // Show the view
            viewContainer.classList.remove('d-none');

            // Initialize the view
            if (this.views[viewName]) {
                await this.views[viewName].init();
            }

            // Update current view
            this.currentView = viewName;

            // Update status
            utils.updateStatus(`${viewName} view loaded`, 100, false);
        } catch (error) {
            console.error(`Error loading view ${viewName}:`, error);
            utils.updateStatus(`Error loading ${viewName} view`, 0, false);
        }
    }

    /**
     * Refresh data for the current view
     */
    async refreshData() {
        try {
            // Update status
            utils.updateStatus('Refreshing data...', 25);

            // Refresh the current view
            if (this.views[this.currentView]) {
                await this.views[this.currentView].refresh();
            }

            // Update status
            utils.updateStatus('Data refreshed', 100, false);
        } catch (error) {
            console.error('Error refreshing data:', error);
            utils.updateStatus('Error refreshing data', 0, false);
        }
    }

    /**
     * Start the data refresh timer
     */
    startRefreshTimer() {
        // Clear any existing timer
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
        }

        // Set up a new timer
        this.refreshTimer = setInterval(() => {
            this.refreshData();
        }, CONFIG.refreshInterval);
    }
}

// Initialize the app when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new DashboardApp();
});
