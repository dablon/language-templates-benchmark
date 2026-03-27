/**
 * Rust Web Service Template - Client JavaScript
 * 
 * Handles API interactions and dynamic content.
 */

(function() {
    'use strict';

    // API Configuration
    const API_BASE = '/api';

    // API Endpoints
    const endpoints = {
        health: `${API_BASE}/health`,
        hello: `${API_BASE}/hello`,
        echo: `${API_BASE}/echo`
    };

    /**
     * Fetch JSON from API
     * @param {string} url - API endpoint
     * @returns {Promise<Object>} JSON response
     */
    async function fetchJSON(url) {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    }

    /**
     * POST to API and get response
     * @param {string} url - API endpoint
     * @param {string|Object} data - Data to send
     * @returns {Promise<string>} Response body
     */
    async function postData(url, data) {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: typeof data === 'string' ? data : JSON.stringify(data)
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.text();
    }

    /**
     * Initialize the application
     */
    async function init() {
        console.log('Rust Web Service Template initialized');

        // Log API endpoints available
        console.log('Available endpoints:', endpoints);

        // Example: Check health on page load
        try {
            const health = await fetchJSON(endpoints.health);
            console.log('Service health:', health);
        } catch (error) {
            console.error('Health check failed:', error.message);
        }
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Export for testing
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = { fetchJSON, postData };
    }
})();
