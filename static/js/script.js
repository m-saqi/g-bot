class SearchBotApp {
    constructor() {
        this.currentSession = null;
        this.isProcessing = false;
        this.initializeEventListeners();
        this.checkHealth();
    }

    initializeEventListeners() {
        // Form submission
        document.getElementById('searchForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.startSearch();
        });

        // Real-time validation
        document.getElementById('searchQuery').addEventListener('input', this.validateForm.bind(this));
        document.getElementById('targetWebsite').addEventListener('input', this.validateForm.bind(this));

        // Enter key support
        document.querySelectorAll('.form-input').forEach(input => {
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !this.isProcessing) {
                    this.startSearch();
                }
            });
        });
    }

    validateForm() {
        const query = document.getElementById('searchQuery').value.trim();
        const website = document.getElementById('targetWebsite').value.trim();
        const button = document.getElementById('startBtn');
        
        const isValid = query.length > 0 && website.length > 0;
        button.disabled = !isValid;
        
        return isValid;
    }

    async checkHealth() {
        try {
            const response = await fetch('/health');
            const data = await response.json();
            
            const statusElement = document.getElementById('statusIndicator');
            if (statusElement) {
                statusElement.className = `status-indicator ${data.status === 'healthy' ? 'online' : 'offline'}`;
                statusElement.title = `Server: ${data.status}`;
            }
        } catch (error) {
            console.warn('Health check failed:', error);
        }
    }

    async startSearch() {
        if (this.isProcessing) return;

        const query = document.getElementById('searchQuery').value.trim();
        const website = document.getElementById('targetWebsite').value.trim();
        const scrollDuration = parseInt(document.getElementById('scrollDuration').value);

        if (!this.validateForm()) {
            this.showAlert('Please fill in all required fields', 'error');
            return;
        }

        this.isProcessing = true;
        this.currentSession = this.generateSessionId();
        
        this.showLoadingState();
        this.hideResults();
        this.hideAlerts();

        try {
            const startTime = Date.now();
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query,
                    website: website,
                    scroll_duration: scrollDuration
                })
            });

            const data = await response.json();
            const responseTime = Date.now() - startTime;

            if (!response.ok) {
                throw new Error(data.error || `HTTP ${response.status}`);
            }

            if (data.success) {
                this.showSuccessResults(data.data, responseTime);
                this.showAlert('Search completed successfully!', 'success');
            } else {
                throw new Error(data.error || 'Search failed');
            }

        } catch (error) {
            console.error('Search error:', error);
            this.showError(error.message);
            this.showAlert(`Error: ${error.message}`, 'error');
        } finally {
            this.isProcessing = false;
            this.hideLoadingState();
        }
    }

    generateSessionId() {
        return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    showLoadingState() {
        const button = document.getElementById('startBtn');
        const loading = document.getElementById('loadingState');
        
        button.disabled = true;
        button.innerHTML = '<div class="btn-spinner"></div> Processing...';
        loading.classList.remove('hidden');
        
        this.updateLoadingSteps('initialization');
    }

    hideLoadingState() {
        const button = document.getElementById('startBtn');
        const loading = document.getElementById('loadingState');
        
        button.disabled = false;
        button.innerHTML = '<i class="icon-search"></i> Start Search & Visit';
        loading.classList.add('hidden');
    }

    updateLoadingSteps(activeStep) {
        const steps = {
            initialization: 0,
            search_execution: 1,
            page_loading: 2,
            behavior_simulation: 3
        };

        const stepElements = document.querySelectorAll('.loading-step');
        stepElements.forEach((step, index) => {
            step.classList.remove('active');
            if (index <= steps[activeStep]) {
                step.classList.add('active');
            }
        });

        // Update progress bar
        const progress = ((steps[activeStep] + 1) / Object.keys(steps).length) * 100;
        document.getElementById('progressFill').style.width = `${progress}%`;
    }

    showSuccessResults(resultData, responseTime) {
        const resultsContainer = document.getElementById('resultsContainer');
        const resultsContent = document.getElementById('resultsContent');
        
        resultsContent.innerHTML = this.generateResultsHTML(resultData, responseTime);
        resultsContainer.classList.add('show', 'fade-in');
        
        // Animate metrics
        this.animateMetrics(resultData.metrics);
    }

    generateResultsHTML(resultData, responseTime) {
        const isSuccess = resultData.success;
        const steps = resultData.steps || [];
        
        return `
            <div class="result-card ${isSuccess ? 'success' : 'error'}">
                <div class="result-header">
                    <div class="result-icon">
                        ${isSuccess ? '✓' : '✗'}
                    </div>
                    <div>
                        <h3>${isSuccess ? 'Search Completed Successfully' : 'Search Failed'}</h3>
                        <p class="text-secondary">Session: ${resultData.session_id}</p>
                    </div>
                </div>

                ${isSuccess ? this.generateMetricsHTML(resultData.metrics, responseTime) : ''}

                <div class="steps-timeline">
                    ${steps.map(step => this.generateStepHTML(step)).join('')}
                </div>

                ${resultData.error ? `
                    <div class="alert alert-error mt-4">
                        <strong>Error:</strong> ${resultData.error}
                    </div>
                ` : ''}
            </div>
        `;
    }

    generateMetricsHTML(metrics, responseTime) {
        return `
            <div class="result-metrics">
                <div class="metric">
                    <span class="metric-value" id="metricDuration">${metrics.total_duration || 0}s</span>
                    <span class="metric-label">Total Duration</span>
                </div>
                <div class="metric">
                    <span class="metric-value" id="metricResponse">${(responseTime / 1000).toFixed(2)}s</span>
                    <span class="metric-label">Response Time</span>
                </div>
                <div class="metric">
                    <span class="metric-value" id="metricSteps">${metrics.steps_completed || 0}</span>
                    <span class="metric-label">Steps Completed</span>
                </div>
                <div class="metric">
                    <span class="metric-value" id="metricScrolls">${metrics.scroll_actions || 0}</span>
                    <span class="metric-label">Scroll Actions</span>
                </div>
            </div>
        `;
    }

    generateStepHTML(step) {
        const isCompleted = step.status === 'completed';
        const isFailed = step.status === 'failed';
        
        return `
            <div class="step-item ${isCompleted ? 'completed' : isFailed ? 'failed' : ''}">
                <div class="step-content">
                    <div class="step-title">
                        ${this.formatStepName(step.step)}
                    </div>
                    <div class="step-details">
                        ${this.formatStepDetails(step)}
                    </div>
                    ${step.error ? `<div class="text-error mt-1">${step.error}</div>` : ''}
                </div>
            </div>
        `;
    }

    formatStepName(step) {
        const names = {
            initialization: 'Browser Initialization',
            search_execution: 'Google Search',
            page_loading: 'Page Loading',
            behavior_simulation: 'Behavior Simulation',
            error_handling: 'Error Handling'
        };
        return names[step] || step.replace(/_/g, ' ').toUpperCase();
    }

    formatStepDetails(step) {
        const details = [];
        
        if (step.search_position) {
            details.push(`Position: ${step.search_position}`);
        }
        
        if (step.target_url) {
            details.push(`URL: ${this.truncateUrl(step.target_url)}`);
        }
        
        if (step.duration) {
            details.push(`Duration: ${step.duration}s`);
        }
        
        if (step.scroll_actions) {
            details.push(`Scrolls: ${step.scroll_actions}`);
        }
        
        if (step.timestamp) {
            details.push(`Time: ${new Date(step.timestamp).toLocaleTimeString()}`);
        }
        
        return details.join(' • ');
    }

    truncateUrl(url, maxLength = 50) {
        return url.length > maxLength ? url.substring(0, maxLength) + '...' : url;
    }

    animateMetrics(metrics) {
        const elements = {
            metricDuration: metrics.total_duration || 0,
            metricSteps: metrics.steps_completed || 0,
            metricScrolls: metrics.scroll_actions || 0
        };

        Object.entries(elements).forEach(([id, targetValue]) => {
            this.animateCounter(id, 0, targetValue, 2000);
        });
    }

    animateCounter(elementId, start, end, duration) {
        const element = document.getElementById(elementId);
        if (!element) return;

        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            const value = Math.floor(progress * (end - start) + start);
            
            element.textContent = value + (elementId === 'metricDuration' ? 's' : '');
            
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        
        window.requestAnimationFrame(step);
    }

    showError(errorMessage) {
        const resultsContainer = document.getElementById('resultsContainer');
        const resultsContent = document.getElementById('resultsContent');
        
        resultsContent.innerHTML = `
            <div class="result-card error">
                <div class="result-header">
                    <div class="result-icon">✗</div>
                    <div>
                        <h3>Search Failed</h3>
                        <p class="text-secondary">Please check your inputs and try again</p>
                    </div>
                </div>
                <div class="alert alert-error">
                    <strong>Error:</strong> ${errorMessage}
                </div>
                <div class="mt-4">
                    <h4>Troubleshooting Tips:</h4>
                    <ul style="margin-left: 1.5rem; color: var(--text-secondary);">
                        <li>Check if the website exists in Google search results</li>
                        <li>Verify the website domain is correct</li>
                        <li>Try a different search query</li>
                        <li>Ensure the website is not blocking automated requests</li>
                    </ul>
                </div>
            </div>
        `;
        
        resultsContainer.classList.add('show', 'fade-in');
    }

    showAlert(message, type) {
        const alert = document.getElementById('alertContainer');
        alert.innerHTML = `
            <div class="alert alert-${type} show">
                ${message}
            </div>
        `;
        
        setTimeout(() => {
            alert.innerHTML = '';
        }, 5000);
    }

    hideAlerts() {
        document.getElementById('alertContainer').innerHTML = '';
    }

    hideResults() {
        document.getElementById('resultsContainer').classList.remove('show');
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.searchBotApp = new SearchBotApp();
});

// Service Worker for offline functionality (optional)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(registration => {
                console.log('SW registered: ', registration);
            })
            .catch(registrationError => {
                console.log('SW registration failed: ', registrationError);
            });
    });
}