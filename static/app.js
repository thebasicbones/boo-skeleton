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

// ===================================
// Resource Display Functions
// ===================================

/**
 * Show loading indicator
 */
function showLoading() {
    const loadingIndicator = document.getElementById('loadingIndicator');
    const resourceList = document.getElementById('resourceList');
    const emptyState = document.getElementById('emptyState');
    
    if (loadingIndicator) {
        loadingIndicator.style.display = 'flex';
    }
    if (resourceList) {
        resourceList.style.display = 'none';
    }
    if (emptyState) {
        emptyState.style.display = 'none';
    }
}

/**
 * Hide loading indicator
 */
function hideLoading() {
    const loadingIndicator = document.getElementById('loadingIndicator');
    if (loadingIndicator) {
        loadingIndicator.style.display = 'none';
    }
}

/**
 * Calculate dependency depth for a resource (for visualization)
 * @param {Object} resource - Resource object
 * @param {Array} allResources - All resources
 * @param {Set} visited - Set of visited resource IDs (for cycle detection)
 * @returns {number} Depth level
 */
function calculateDependencyDepth(resource, allResources, visited = new Set()) {
    // Prevent infinite recursion in case of cycles
    if (visited.has(resource.id)) {
        return 0;
    }
    
    if (!resource.dependencies || resource.dependencies.length === 0) {
        return 0;
    }
    
    visited.add(resource.id);
    
    let maxDepth = 0;
    for (const depId of resource.dependencies) {
        const depResource = allResources.find(r => r.id === depId);
        if (depResource) {
            const depth = calculateDependencyDepth(depResource, allResources, new Set(visited));
            maxDepth = Math.max(maxDepth, depth + 1);
        }
    }
    
    return maxDepth;
}

/**
 * Get resource name by ID
 * @param {string} id - Resource ID
 * @param {Array} allResources - All resources
 * @returns {string} Resource name or ID if not found
 */
function getResourceName(id, allResources) {
    const resource = allResources.find(r => r.id === id);
    return resource ? resource.name : id;
}

/**
 * Create a resource card element
 * @param {Object} resource - Resource object
 * @param {Array} allResources - All resources (for dependency name lookup)
 * @returns {HTMLElement} Resource card element
 */
function createResourceCard(resource, allResources) {
    const card = document.createElement('div');
    card.className = 'resource-card';
    card.setAttribute('data-resource-id', resource.id);
    
    // Calculate and set dependency depth for visual indication
    const depth = calculateDependencyDepth(resource, allResources);
    card.setAttribute('data-depth', Math.min(depth, 3)); // Cap at 3 for styling
    
    // Card header with title and actions
    const header = document.createElement('div');
    header.className = 'resource-card-header';
    
    const title = document.createElement('h3');
    title.className = 'resource-card-title';
    title.textContent = resource.name;
    
    const actions = document.createElement('div');
    actions.className = 'resource-card-actions';
    
    const editBtn = document.createElement('button');
    editBtn.className = 'edit-btn';
    editBtn.textContent = 'Edit';
    editBtn.setAttribute('aria-label', `Edit ${resource.name}`);
    editBtn.onclick = () => handleEditResource(resource.id);
    
    const deleteBtn = document.createElement('button');
    deleteBtn.className = 'delete-btn';
    deleteBtn.textContent = 'Delete';
    deleteBtn.setAttribute('aria-label', `Delete ${resource.name}`);
    deleteBtn.onclick = () => handleDeleteResource(resource.id);
    
    actions.appendChild(editBtn);
    actions.appendChild(deleteBtn);
    
    header.appendChild(title);
    header.appendChild(actions);
    
    // Description
    const description = document.createElement('p');
    description.className = 'resource-card-description';
    description.textContent = resource.description || 'No description provided';
    
    // Meta information (ID)
    const meta = document.createElement('div');
    meta.className = 'resource-card-meta';
    
    const idElement = document.createElement('div');
    idElement.className = 'resource-card-id';
    idElement.textContent = `ID: ${resource.id}`;
    idElement.setAttribute('title', resource.id);
    
    meta.appendChild(idElement);
    
    // Dependencies section
    const dependenciesSection = document.createElement('div');
    dependenciesSection.className = 'resource-dependencies';
    
    const dependenciesLabel = document.createElement('div');
    dependenciesLabel.className = 'dependencies-label';
    dependenciesLabel.textContent = 'Dependencies';
    
    dependenciesSection.appendChild(dependenciesLabel);
    
    if (resource.dependencies && resource.dependencies.length > 0) {
        const dependencyList = document.createElement('div');
        dependencyList.className = 'dependency-list';
        
        resource.dependencies.forEach(depId => {
            const badge = document.createElement('span');
            badge.className = 'dependency-badge';
            const depName = getResourceName(depId, allResources);
            console.log(`Looking up dependency ${depId}: found name "${depName}"`);
            badge.textContent = depName;
            badge.setAttribute('title', `Depends on: ${depId}`);
            badge.setAttribute('data-dependency-id', depId);
            
            // Make badge clickable to scroll to dependency
            badge.style.cursor = 'pointer';
            badge.onclick = () => {
                const depCard = document.querySelector(`[data-resource-id="${depId}"]`);
                if (depCard) {
                    depCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    depCard.style.animation = 'none';
                    setTimeout(() => {
                        depCard.style.animation = 'highlight 1s ease-in-out';
                    }, 10);
                }
            };
            
            dependencyList.appendChild(badge);
        });
        
        dependenciesSection.appendChild(dependencyList);
    } else {
        const noDeps = document.createElement('div');
        noDeps.className = 'no-dependencies';
        noDeps.textContent = 'No dependencies';
        dependenciesSection.appendChild(noDeps);
    }
    
    // Assemble card
    card.appendChild(header);
    card.appendChild(description);
    card.appendChild(meta);
    card.appendChild(dependenciesSection);
    
    return card;
}

/**
 * Render resources to the DOM
 * @param {Array} resources - Array of resource objects
 */
function renderResources(resources) {
    const resourceList = document.getElementById('resourceList');
    const emptyState = document.getElementById('emptyState');
    
    if (!resourceList || !emptyState) {
        console.error('Required DOM elements not found');
        return;
    }
    
    // Clear existing content
    resourceList.innerHTML = '';
    
    // Show empty state if no resources
    if (!resources || resources.length === 0) {
        resourceList.style.display = 'none';
        emptyState.style.display = 'block';
        return;
    }
    
    // Hide empty state and show resource list
    emptyState.style.display = 'none';
    resourceList.style.display = 'grid';
    
    // Create and append resource cards
    resources.forEach(resource => {
        const card = createResourceCard(resource, resources);
        resourceList.appendChild(card);
    });
}

/**
 * Load and display all resources
 * Now uses search with empty query to get topologically sorted results
 */
async function loadResources() {
    const searchInput = document.getElementById('searchInput');
    const query = searchInput ? searchInput.value : '';
    await performSearch(query);
}

/**
 * Handle edit resource button click
 * Opens the modal and populates it with current resource data
 * @param {string} id - Resource ID
 */
async function handleEditResource(id) {
    try {
        // Fetch the resource data
        const resource = await fetchResource(id);
        
        // Open modal in edit mode
        await openEditModal(resource);
        
    } catch (error) {
        console.error('Error loading resource for edit:', error);
        const parsedError = parseApiError(error);
        showError(parsedError.message);
    }
}

/**
 * Handle delete resource button click
 * Opens the delete confirmation modal
 * @param {string} id - Resource ID
 */
async function handleDeleteResource(id) {
    try {
        // Fetch the resource to get its name for the confirmation message
        const resource = await fetchResource(id);
        
        // Open delete confirmation modal
        openDeleteModal(resource);
        
    } catch (error) {
        console.error('Error loading resource for delete:', error);
        const parsedError = parseApiError(error);
        showError(parsedError.message);
    }
}

/**
 * Show error message
 * @param {string} message - Error message
 * @param {Object} fieldErrors - Optional field-specific errors for inline display
 */
function showError(message, fieldErrors = null) {
    const messageContainer = document.getElementById('messageContainer');
    if (messageContainer) {
        messageContainer.textContent = message;
        messageContainer.className = 'message-container error show';
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            messageContainer.classList.remove('show');
        }, 5000);
    }
    
    // Display inline field errors if provided
    if (fieldErrors) {
        displayFieldErrors(fieldErrors);
    }
}

/**
 * Display field-specific validation errors inline on forms
 * @param {Object} fieldErrors - Object mapping field names to error messages
 */
function displayFieldErrors(fieldErrors) {
    // Clear any existing field errors first
    clearFormErrors();
    
    // Map of field names to their error element IDs
    const fieldErrorMap = {
        'name': 'nameError',
        'description': 'descriptionError',
        'dependencies': 'dependenciesError'
    };
    
    // Display each field error
    for (const [field, errorMessage] of Object.entries(fieldErrors)) {
        const errorElementId = fieldErrorMap[field];
        if (errorElementId) {
            const errorElement = document.getElementById(errorElementId);
            const inputElement = document.getElementById(`resource${field.charAt(0).toUpperCase() + field.slice(1)}`);
            
            if (errorElement) {
                errorElement.textContent = errorMessage;
            }
            
            if (inputElement) {
                inputElement.classList.add('error');
            }
        }
    }
}

/**
 * Parse API error response and extract field-specific errors
 * @param {Error} error - Error object from API call
 * @returns {Object} Object with message and optional fieldErrors
 */
function parseApiError(error) {
    const result = {
        message: error.message || 'An error occurred',
        fieldErrors: null
    };
    
    // Try to extract field-specific errors from common API error formats
    const errorMessage = error.message || '';
    
    // Check for circular dependency errors
    if (errorMessage.toLowerCase().includes('circular')) {
        result.fieldErrors = {
            dependencies: 'Circular dependency detected'
        };
    }
    
    // Check for validation errors mentioning specific fields
    if (errorMessage.toLowerCase().includes('name')) {
        result.fieldErrors = result.fieldErrors || {};
        result.fieldErrors.name = errorMessage;
    }
    
    if (errorMessage.toLowerCase().includes('description')) {
        result.fieldErrors = result.fieldErrors || {};
        result.fieldErrors.description = errorMessage;
    }
    
    if (errorMessage.toLowerCase().includes('dependencies') || errorMessage.toLowerCase().includes('dependency')) {
        result.fieldErrors = result.fieldErrors || {};
        result.fieldErrors.dependencies = errorMessage;
    }
    
    return result;
}

/**
 * Show success message
 * @param {string} message - Success message
 */
function showSuccess(message) {
    const messageContainer = document.getElementById('messageContainer');
    if (messageContainer) {
        messageContainer.textContent = message;
        messageContainer.className = 'message-container success show';
        
        // Auto-dismiss after 3 seconds
        setTimeout(() => {
            messageContainer.classList.remove('show');
        }, 3000);
    }
}

/**
 * Show warning message
 * @param {string} message - Warning message
 */
function showWarning(message) {
    const messageContainer = document.getElementById('messageContainer');
    if (messageContainer) {
        messageContainer.textContent = message;
        messageContainer.className = 'message-container warning show';
        
        // Auto-dismiss after 4 seconds
        setTimeout(() => {
            messageContainer.classList.remove('show');
        }, 4000);
    }
}

// ===================================
// Modal Management Functions
// ===================================

/**
 * Open the resource modal for creating a new resource
 */
function openCreateModal() {
    const modal = document.getElementById('resourceModal');
    const modalTitle = document.getElementById('modalTitle');
    const submitButtonText = document.getElementById('submitButtonText');
    const form = document.getElementById('resourceForm');
    
    if (!modal || !modalTitle || !submitButtonText || !form) {
        console.error('Modal elements not found');
        return;
    }
    
    // Set modal to create mode
    modalTitle.textContent = 'Create Resource';
    submitButtonText.textContent = 'Create';
    form.setAttribute('data-mode', 'create');
    form.removeAttribute('data-resource-id');
    
    // Clear form
    clearForm();
    
    // Populate dependencies dropdown with all existing resources
    populateDependenciesDropdown();
    
    // Show modal
    modal.style.display = 'flex';
    
    // Focus on name input
    const nameInput = document.getElementById('resourceName');
    if (nameInput) {
        setTimeout(() => nameInput.focus(), 100);
    }
}

/**
 * Open the resource modal for editing an existing resource
 * @param {Object} resource - Resource object to edit
 */
async function openEditModal(resource) {
    const modal = document.getElementById('resourceModal');
    const modalTitle = document.getElementById('modalTitle');
    const submitButtonText = document.getElementById('submitButtonText');
    const form = document.getElementById('resourceForm');
    
    if (!modal || !modalTitle || !submitButtonText || !form) {
        console.error('Modal elements not found');
        return;
    }
    
    // Set modal to edit mode
    modalTitle.textContent = 'Edit Resource';
    submitButtonText.textContent = 'Update';
    form.setAttribute('data-mode', 'edit');
    form.setAttribute('data-resource-id', resource.id);
    
    // Clear form first
    clearForm();
    clearFormErrors();
    
    // Populate dependencies dropdown (excluding the current resource)
    await populateDependenciesDropdown(resource.id);
    
    // Populate form with resource data
    const nameInput = document.getElementById('resourceName');
    const descriptionInput = document.getElementById('resourceDescription');
    const dependenciesSelect = document.getElementById('resourceDependencies');
    
    if (nameInput) {
        nameInput.value = resource.name || '';
    }
    
    if (descriptionInput) {
        descriptionInput.value = resource.description || '';
    }
    
    // Select the current dependencies
    if (dependenciesSelect && resource.dependencies) {
        Array.from(dependenciesSelect.options).forEach(option => {
            option.selected = resource.dependencies.includes(option.value);
        });
    }
    
    // Show modal
    modal.style.display = 'flex';
    
    // Focus on name input
    if (nameInput) {
        setTimeout(() => nameInput.focus(), 100);
    }
}

/**
 * Close the resource modal
 */
function closeModal() {
    const modal = document.getElementById('resourceModal');
    if (modal) {
        modal.style.display = 'none';
    }
    clearForm();
    clearFormErrors();
}

/**
 * Clear the resource form
 */
function clearForm() {
    const form = document.getElementById('resourceForm');
    if (form) {
        form.reset();
    }
}

/**
 * Clear form validation errors
 */
function clearFormErrors() {
    const errorElements = document.querySelectorAll('.form-error');
    errorElements.forEach(el => {
        el.textContent = '';
    });
    
    const inputElements = document.querySelectorAll('.form-input');
    inputElements.forEach(el => {
        el.classList.remove('error');
    });
}

/**
 * Populate the dependencies dropdown with available resources
 */
async function populateDependenciesDropdown(excludeId = null) {
    const select = document.getElementById('resourceDependencies');
    if (!select) {
        return;
    }
    
    try {
        const resources = await fetchResources();
        
        // Clear existing options
        select.innerHTML = '';
        
        // Add options for each resource (excluding the current one if editing)
        resources
            .filter(resource => resource.id !== excludeId)
            .forEach(resource => {
                const option = document.createElement('option');
                option.value = resource.id;
                option.textContent = resource.name;
                select.appendChild(option);
            });
    } catch (error) {
        console.error('Error populating dependencies:', error);
    }
}

/**
 * Validate the resource form
 * @returns {Object} Validation result {isValid: boolean, errors: Object}
 */
function validateResourceForm() {
    const nameInput = document.getElementById('resourceName');
    const descriptionInput = document.getElementById('resourceDescription');
    
    const errors = {};
    let isValid = true;
    
    // Clear previous errors
    clearFormErrors();
    
    // Validate name (required, max 100 chars)
    if (!nameInput || !nameInput.value.trim()) {
        errors.name = 'Name is required';
        isValid = false;
        if (nameInput) {
            nameInput.classList.add('error');
        }
    } else if (nameInput.value.length > 100) {
        errors.name = 'Name must be 100 characters or less';
        isValid = false;
        nameInput.classList.add('error');
    }
    
    // Validate description (optional, max 500 chars)
    if (descriptionInput && descriptionInput.value.length > 500) {
        errors.description = 'Description must be 500 characters or less';
        isValid = false;
        descriptionInput.classList.add('error');
    }
    
    // Display errors
    if (errors.name) {
        const nameError = document.getElementById('nameError');
        if (nameError) {
            nameError.textContent = errors.name;
        }
    }
    
    if (errors.description) {
        const descriptionError = document.getElementById('descriptionError');
        if (descriptionError) {
            descriptionError.textContent = errors.description;
        }
    }
    
    return { isValid, errors };
}

/**
 * Get form data as an object
 * @returns {Object} Form data {name, description, dependencies}
 */
function getFormData() {
    const nameInput = document.getElementById('resourceName');
    const descriptionInput = document.getElementById('resourceDescription');
    const dependenciesSelect = document.getElementById('resourceDependencies');
    
    const data = {
        name: nameInput ? nameInput.value.trim() : '',
        description: descriptionInput ? descriptionInput.value.trim() : '',
        dependencies: []
    };
    
    // Get selected dependencies
    if (dependenciesSelect) {
        const selectedOptions = Array.from(dependenciesSelect.selectedOptions);
        data.dependencies = selectedOptions.map(option => option.value);
    }
    
    return data;
}

/**
 * Handle create resource form submission
 * @param {Event} event - Form submit event
 */
async function handleCreateResource(event) {
    event.preventDefault();
    
    // Validate form
    const validation = validateResourceForm();
    if (!validation.isValid) {
        showError('Please fix the form errors before submitting');
        return;
    }
    
    // Get form data
    const formData = getFormData();
    
    // Show loading state on submit button
    const submitButton = document.getElementById('submitButton');
    const submitButtonText = document.getElementById('submitButtonText');
    const originalText = submitButtonText ? submitButtonText.textContent : 'Create';
    
    if (submitButton) {
        submitButton.disabled = true;
    }
    if (submitButtonText) {
        submitButtonText.textContent = 'Creating...';
    }
    
    try {
        // Call API to create resource
        const createdResource = await createResource(formData);
        
        // Close modal
        closeModal();
        
        // Show success message
        showSuccess(`Resource "${createdResource.name}" created successfully`);
        
        // Reload resources to display the new one
        await loadResources();
        
        // Scroll to the new resource
        setTimeout(() => {
            const newCard = document.querySelector(`[data-resource-id="${createdResource.id}"]`);
            if (newCard) {
                newCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
                newCard.style.animation = 'highlight 1s ease-in-out';
            }
        }, 100);
        
    } catch (error) {
        console.error('Error creating resource:', error);
        
        // Parse error and display with field-specific errors if available
        const parsedError = parseApiError(error);
        showError(parsedError.message, parsedError.fieldErrors);
        
    } finally {
        // Restore button state
        if (submitButton) {
            submitButton.disabled = false;
        }
        if (submitButtonText) {
            submitButtonText.textContent = originalText;
        }
    }
}

/**
 * Handle update resource form submission
 * @param {Event} event - Form submit event
 */
async function handleUpdateResource(event) {
    event.preventDefault();
    
    // Get resource ID from form
    const form = document.getElementById('resourceForm');
    const resourceId = form ? form.getAttribute('data-resource-id') : null;
    
    if (!resourceId) {
        showError('Resource ID not found');
        return;
    }
    
    // Validate form
    const validation = validateResourceForm();
    if (!validation.isValid) {
        showError('Please fix the form errors before submitting');
        return;
    }
    
    // Get form data
    const formData = getFormData();
    
    // Show loading state on submit button
    const submitButton = document.getElementById('submitButton');
    const submitButtonText = document.getElementById('submitButtonText');
    const originalText = submitButtonText ? submitButtonText.textContent : 'Update';
    
    if (submitButton) {
        submitButton.disabled = true;
    }
    if (submitButtonText) {
        submitButtonText.textContent = 'Updating...';
    }
    
    try {
        // Call API to update resource
        const updatedResource = await updateResource(resourceId, formData);
        
        // Close modal
        closeModal();
        
        // Show success message
        showSuccess(`Resource "${updatedResource.name}" updated successfully`);
        
        // Reload resources to display the updated one
        await loadResources();
        
        // Scroll to the updated resource
        setTimeout(() => {
            const updatedCard = document.querySelector(`[data-resource-id="${updatedResource.id}"]`);
            if (updatedCard) {
                updatedCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
                updatedCard.style.animation = 'highlight 1s ease-in-out';
            }
        }, 100);
        
    } catch (error) {
        console.error('Error updating resource:', error);
        
        // Parse error and display with field-specific errors if available
        const parsedError = parseApiError(error);
        showError(parsedError.message, parsedError.fieldErrors);
        
    } finally {
        // Restore button state
        if (submitButton) {
            submitButton.disabled = false;
        }
        if (submitButtonText) {
            submitButtonText.textContent = originalText;
        }
    }
}

// ===================================
// Delete Modal Management Functions
// ===================================

/**
 * Open the delete confirmation modal
 * @param {Object} resource - Resource object to delete
 */
function openDeleteModal(resource) {
    const modal = document.getElementById('deleteModal');
    const deleteMessage = document.getElementById('deleteMessage');
    const cascadeCheckbox = document.getElementById('cascadeCheckbox');
    const confirmDeleteButton = document.getElementById('confirmDeleteButton');
    
    if (!modal || !deleteMessage || !cascadeCheckbox || !confirmDeleteButton) {
        console.error('Delete modal elements not found');
        return;
    }
    
    // Set the delete message with resource name
    deleteMessage.textContent = `Are you sure you want to delete "${resource.name}"?`;
    
    // Reset cascade checkbox
    cascadeCheckbox.checked = false;
    
    // Store resource ID on the confirm button for later use
    confirmDeleteButton.setAttribute('data-resource-id', resource.id);
    
    // Show modal
    modal.style.display = 'flex';
    
    // Focus on cancel button for safety
    const cancelButton = document.getElementById('cancelDeleteButton');
    if (cancelButton) {
        setTimeout(() => cancelButton.focus(), 100);
    }
}

/**
 * Close the delete confirmation modal
 */
function closeDeleteModal() {
    const modal = document.getElementById('deleteModal');
    if (modal) {
        modal.style.display = 'none';
    }
    
    // Reset cascade checkbox
    const cascadeCheckbox = document.getElementById('cascadeCheckbox');
    if (cascadeCheckbox) {
        cascadeCheckbox.checked = false;
    }
    
    // Clear stored resource ID
    const confirmDeleteButton = document.getElementById('confirmDeleteButton');
    if (confirmDeleteButton) {
        confirmDeleteButton.removeAttribute('data-resource-id');
    }
}

/**
 * Handle delete confirmation
 * Deletes the resource with the cascade option if selected
 */
async function handleConfirmDelete() {
    const confirmDeleteButton = document.getElementById('confirmDeleteButton');
    const cascadeCheckbox = document.getElementById('cascadeCheckbox');
    
    if (!confirmDeleteButton) {
        console.error('Confirm delete button not found');
        return;
    }
    
    const resourceId = confirmDeleteButton.getAttribute('data-resource-id');
    if (!resourceId) {
        console.error('Resource ID not found');
        return;
    }
    
    const cascade = cascadeCheckbox ? cascadeCheckbox.checked : false;
    
    // Show loading state on delete button
    const originalText = confirmDeleteButton.textContent;
    confirmDeleteButton.disabled = true;
    confirmDeleteButton.textContent = 'Deleting...';
    
    try {
        // Call API to delete resource
        await deleteResource(resourceId, cascade);
        
        // Close modal
        closeDeleteModal();
        
        // Show success message
        const cascadeMessage = cascade ? ' and its dependents' : '';
        showSuccess(`Resource deleted successfully${cascadeMessage}`);
        
        // Reload resources to update the display
        await loadResources();
        
    } catch (error) {
        console.error('Error deleting resource:', error);
        
        // Parse error and display
        const parsedError = parseApiError(error);
        showError(parsedError.message);
        
    } finally {
        // Restore button state
        confirmDeleteButton.disabled = false;
        confirmDeleteButton.textContent = originalText;
    }
}

// ===================================
// Search Functionality
// ===================================

// Store the debounce timer
let searchDebounceTimer = null;

/**
 * Perform search and display results in topological order
 * @param {string} query - Search query string
 */
async function performSearch(query) {
    try {
        showLoading();
        
        // Fetch all resources first (for dependency name lookup)
        const allResources = await fetchResources();
        console.log(`Fetched ${allResources.length} resources for name lookup`);
        
        // Call the search API with the query
        const results = await searchResources(query);
        console.log(`Search returned ${results.length} results`);
        
        // Display results in topological order, passing all resources for name lookup
        renderSearchResults(results, query, allResources);
        
    } catch (error) {
        console.error('Error performing search:', error);
        
        // Parse error and display
        const parsedError = parseApiError(error);
        showError(parsedError.message);
        
        // Show empty state on error
        renderResources([]);
    } finally {
        hideLoading();
    }
}

/**
 * Render search results with topological order indicators
 * @param {Array} resources - Array of resource objects in topological order
 * @param {string} query - The search query used
 * @param {Array} allResources - All resources (for dependency name lookup)
 */
function renderSearchResults(resources, query, allResources = null) {
    const resourceList = document.getElementById('resourceList');
    const emptyState = document.getElementById('emptyState');
    const resourceSection = document.querySelector('.resource-section h2');
    
    if (!resourceList || !emptyState) {
        console.error('Required DOM elements not found');
        return;
    }
    
    // Use allResources if provided, otherwise use resources for name lookup
    const resourcesForLookup = allResources || resources;
    
    // Update section title to indicate search/sort mode
    if (resourceSection) {
        if (query && query.trim()) {
            resourceSection.textContent = `Search Results for "${query}" (Topological Order)`;
        } else {
            resourceSection.textContent = 'Resources (Topological Order)';
        }
    }
    
    // Clear existing content
    resourceList.innerHTML = '';
    
    // Show empty state if no resources
    if (!resources || resources.length === 0) {
        resourceList.style.display = 'none';
        emptyState.style.display = 'block';
        
        if (query && query.trim()) {
            emptyState.innerHTML = '<p>No resources found matching your search.</p>';
        } else {
            emptyState.innerHTML = '<p>No resources found. Create your first resource to get started!</p>';
        }
        return;
    }
    
    // Hide empty state and show resource list
    emptyState.style.display = 'none';
    resourceList.style.display = 'grid';
    
    // Create and append resource cards with topological order indicators
    resources.forEach((resource, index) => {
        // Use allResources for dependency name lookup
        const card = createResourceCard(resource, resourcesForLookup);
        
        // Add topological order number badge
        const orderBadge = document.createElement('div');
        orderBadge.className = 'topological-order-badge';
        orderBadge.textContent = `#${index + 1}`;
        orderBadge.setAttribute('title', `Topological order position: ${index + 1}`);
        
        // Insert the badge at the beginning of the card
        card.insertBefore(orderBadge, card.firstChild);
        
        resourceList.appendChild(card);
    });
}

/**
 * Handle search input with debouncing
 * @param {Event} event - Input event
 */
function handleSearchInput(event) {
    const query = event.target.value;
    
    // Clear any existing debounce timer
    if (searchDebounceTimer) {
        clearTimeout(searchDebounceTimer);
    }
    
    // Set a new debounce timer (300ms delay)
    searchDebounceTimer = setTimeout(() => {
        performSearch(query);
    }, 300);
}

/**
 * Handle search button click
 */
function handleSearchButtonClick() {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        const query = searchInput.value;
        
        // Clear any pending debounce timer
        if (searchDebounceTimer) {
            clearTimeout(searchDebounceTimer);
            searchDebounceTimer = null;
        }
        
        // Perform search immediately
        performSearch(query);
    }
}

// ===================================
// Initialization
// ===================================

/**
 * Initialize the application
 */
function init() {
    // Load resources on page load (using search with empty query for topological sort)
    performSearch('');
    
    // Set up event listeners
    setupEventListeners();
}

/**
 * Set up all event listeners
 */
function setupEventListeners() {
    // Search input - debounced search
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', handleSearchInput);
        
        // Also handle Enter key for immediate search
        searchInput.addEventListener('keydown', (event) => {
            if (event.key === 'Enter') {
                event.preventDefault();
                handleSearchButtonClick();
            }
        });
    }
    
    // Search button - immediate search
    const searchButton = document.getElementById('searchButton');
    if (searchButton) {
        searchButton.addEventListener('click', handleSearchButtonClick);
    }
    
    // Create button - open modal
    const createButton = document.getElementById('createButton');
    if (createButton) {
        createButton.addEventListener('click', openCreateModal);
    }
    
    // Resource form submission
    const resourceForm = document.getElementById('resourceForm');
    if (resourceForm) {
        resourceForm.addEventListener('submit', async (event) => {
            const mode = resourceForm.getAttribute('data-mode');
            if (mode === 'create') {
                await handleCreateResource(event);
            } else if (mode === 'edit') {
                await handleUpdateResource(event);
            }
        });
    }
    
    // Modal close buttons
    const modalCloseButton = document.querySelector('#resourceModal .modal-close');
    if (modalCloseButton) {
        modalCloseButton.addEventListener('click', closeModal);
    }
    
    const cancelButton = document.getElementById('cancelButton');
    if (cancelButton) {
        cancelButton.addEventListener('click', closeModal);
    }
    
    // Close modal when clicking outside
    const modal = document.getElementById('resourceModal');
    if (modal) {
        modal.addEventListener('click', (event) => {
            if (event.target === modal) {
                closeModal();
            }
        });
    }
    
    // Delete modal event listeners
    const deleteModal = document.getElementById('deleteModal');
    
    // Close delete modal buttons
    const modalCloseDelete = document.querySelector('#deleteModal .modal-close-delete');
    if (modalCloseDelete) {
        modalCloseDelete.addEventListener('click', closeDeleteModal);
    }
    
    const cancelDeleteButton = document.getElementById('cancelDeleteButton');
    if (cancelDeleteButton) {
        cancelDeleteButton.addEventListener('click', closeDeleteModal);
    }
    
    // Confirm delete button
    const confirmDeleteButton = document.getElementById('confirmDeleteButton');
    if (confirmDeleteButton) {
        confirmDeleteButton.addEventListener('click', handleConfirmDelete);
    }
    
    // Close delete modal when clicking outside
    if (deleteModal) {
        deleteModal.addEventListener('click', (event) => {
            if (event.target === deleteModal) {
                closeDeleteModal();
            }
        });
    }
    
    // Keyboard shortcuts
    document.addEventListener('keydown', (event) => {
        // Escape key closes modals
        if (event.key === 'Escape') {
            const resourceModal = document.getElementById('resourceModal');
            const deleteModal = document.getElementById('deleteModal');
            
            if (resourceModal && resourceModal.style.display === 'flex') {
                closeModal();
            } else if (deleteModal && deleteModal.style.display === 'flex') {
                closeDeleteModal();
            }
        }
    });
}

// Run initialization when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
