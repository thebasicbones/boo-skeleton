// API Configuration
const API_BASE_URL = '/api';

// API Client Functions

/**
 * Fetch all resources from the API
 * @returns {Promise<Array>} Array of resource objects
 * @throws {Error} Network or API error
 */
async function fetchResources() {
    try {
        const response = await fetch(`${API_BASE_URL}/resources`);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.message || `HTTP ${response.status}: Failed to fetch resources`);
        }
        
        return await response.json();
    } catch (error) {
        if (error instanceof TypeError && error.message.includes('fetch')) {
            throw new Error('Network error: Unable to connect to the server');
        }
        throw error;
    }
}

/**
 * Fetch a single resource by ID
 * @param {string} id - Resource ID
 * @returns {Promise<Object>} Resource object
 * @throws {Error} Network or API error
 */
async function fetchResource(id) {
    try {
        const response = await fetch(`${API_BASE_URL}/resources/${id}`);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.message || `HTTP ${response.status}: Failed to fetch resource`);
        }
        
        return await response.json();
    } catch (error) {
        if (error instanceof TypeError && error.message.includes('fetch')) {
            throw new Error('Network error: Unable to connect to the server');
        }
        throw error;
    }
}

/**
 * Create a new resource
 * @param {Object} data - Resource data {name, description, dependencies}
 * @returns {Promise<Object>} Created resource object
 * @throws {Error} Network or API error
 */
async function createResource(data) {
    try {
        const response = await fetch(`${API_BASE_URL}/resources`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.message || `HTTP ${response.status}: Failed to create resource`);
        }
        
        return await response.json();
    } catch (error) {
        if (error instanceof TypeError && error.message.includes('fetch')) {
            throw new Error('Network error: Unable to connect to the server');
        }
        throw error;
    }
}

/**
 * Update an existing resource
 * @param {string} id - Resource ID
 * @param {Object} data - Updated resource data {name, description, dependencies}
 * @returns {Promise<Object>} Updated resource object
 * @throws {Error} Network or API error
 */
async function updateResource(id, data) {
    try {
        const response = await fetch(`${API_BASE_URL}/resources/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.message || `HTTP ${response.status}: Failed to update resource`);
        }
        
        return await response.json();
    } catch (error) {
        if (error instanceof TypeError && error.message.includes('fetch')) {
            throw new Error('Network error: Unable to connect to the server');
        }
        throw error;
    }
}

/**
 * Delete a resource
 * @param {string} id - Resource ID
 * @param {boolean} cascade - Whether to cascade delete dependent resources
 * @returns {Promise<void>}
 * @throws {Error} Network or API error
 */
async function deleteResource(id, cascade = false) {
    try {
        const url = new URL(`${window.location.origin}${API_BASE_URL}/resources/${id}`);
        if (cascade) {
            url.searchParams.append('cascade', 'true');
        }
        
        const response = await fetch(url.toString(), {
            method: 'DELETE',
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.message || `HTTP ${response.status}: Failed to delete resource`);
        }
        
        // DELETE returns 204 No Content, so no body to parse
        return;
    } catch (error) {
        if (error instanceof TypeError && error.message.includes('fetch')) {
            throw new Error('Network error: Unable to connect to the server');
        }
        throw error;
    }
}

/**
 * Search resources with topological sorting
 * @param {string} query - Search query string
 * @returns {Promise<Array>} Array of resource objects in topological order
 * @throws {Error} Network or API error
 */
async function searchResources(query = '') {
    try {
        const url = new URL(`${window.location.origin}${API_BASE_URL}/search`);
        if (query) {
            url.searchParams.append('q', query);
        }
        
        const response = await fetch(url.toString());
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.message || `HTTP ${response.status}: Failed to search resources`);
        }
        
        return await response.json();
    } catch (error) {
        if (error instanceof TypeError && error.message.includes('fetch')) {
            throw new Error('Network error: Unable to connect to the server');
        }
        throw error;
    }
}
