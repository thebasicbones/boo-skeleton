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
 * Now uses DAG grouping with selected sort order
 */
async function loadResources() {
    try {
        showLoading();
        
        const sortSelect = document.getElementById('dagSortOrder');
        const sortOrder = sortSelect ? sortSelect.value : 'topological';
        
        // Fetch all resources
        const resources = await fetchResources();
        
        // Render grouped by DAG with selected sort order
        renderResourcesByDAG(resources, sortOrder);
        
    } catch (error) {
        console.error('Error loading resources:', error);
        showError('Failed to load resources');
        renderResourcesByDAG([]);
    } finally {
        hideLoading();
    }
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
        
        // If no query, just load all resources with DAG grouping
        if (!query || !query.trim()) {
            await loadResources();
            return;
        }
        
        // Fetch all resources first (for dependency name lookup)
        const allResources = await fetchResources();
        console.log(`Fetched ${allResources.length} resources for name lookup`);
        
        // Call the search API with the query
        const results = await searchResources(query);
        console.log(`Search returned ${results.length} results for query: "${query}"`);
        
        // Display search results with DAG grouping
        const sortSelect = document.getElementById('dagSortOrder');
        const sortOrder = sortSelect ? sortSelect.value : 'topological';
        renderResourcesByDAG(results, sortOrder);
        
    } catch (error) {
        console.error('Error performing search:', error);
        
        // Parse error and display
        const parsedError = parseApiError(error);
        showError(parsedError.message);
        
        // Show empty state on error
        renderResourcesByDAG([]);
    } finally {
        hideLoading();
    }
}

/**
 * Render search results with topological order indicators
 * @param {Array} resources - Array of resource objects in topological order
 * @param {string} query - The search query used
 * @param {Array} allResources - All resources (for dependency name lookup)
 * @deprecated Use renderResourcesByDAG instead
 */
function renderSearchResults(resources, query, allResources = null) {
    console.log(`renderSearchResults (deprecated) called - redirecting to renderResourcesByDAG`);
    const sortSelect = document.getElementById('dagSortOrder');
    const sortOrder = sortSelect ? sortSelect.value : 'topological';
    renderResourcesByDAG(resources, sortOrder);
    return;
    
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
    // Set up DAG sort order handler
    handleDAGSortChange();
    
    // Load resources on page load with DAG grouping
    loadResources();
    
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


// ===================================
// DAG Grouping and Sorting Functions
// ===================================

/**
 * Identify disconnected DAGs in the resource graph
 * @param {Array} resources - All resources
 * @returns {Array} Array of DAG groups, each containing resources
 */
function identifyDAGs(resources) {
    if (!resources || resources.length === 0) {
        return [];
    }
    
    const visited = new Set();
    const dags = [];
    
    // Build adjacency list (bidirectional for component detection)
    const graph = {};
    resources.forEach(r => {
        graph[r.id] = new Set();
    });
    
    resources.forEach(resource => {
        const deps = resource.dependencies || [];
        deps.forEach(depId => {
            if (graph[resource.id]) graph[resource.id].add(depId);
            if (graph[depId]) graph[depId].add(resource.id);
        });
    });
    
    // DFS to find connected components
    function dfs(nodeId, component) {
        if (visited.has(nodeId)) return;
        visited.add(nodeId);
        
        const resource = resources.find(r => r.id === nodeId);
        if (resource) {
            component.push(resource);
        }
        
        const neighbors = graph[nodeId] || new Set();
        neighbors.forEach(neighborId => {
            dfs(neighborId, component);
        });
    }
    
    // Find all connected components (DAGs)
    resources.forEach(resource => {
        if (!visited.has(resource.id)) {
            const component = [];
            dfs(resource.id, component);
            if (component.length > 0) {
                dags.push(component);
            }
        }
    });
    
    return dags;
}

/**
 * Find root nodes (nodes with no dependencies) in a DAG
 * @param {Array} dagResources - Resources in a DAG
 * @returns {Array} Root resources
 */
function findRootNodes(dagResources) {
    return dagResources.filter(r => !r.dependencies || r.dependencies.length === 0);
}

/**
 * Sort DAGs based on the selected sort order
 * @param {Array} dags - Array of DAG groups
 * @param {string} sortOrder - Sort order option
 * @returns {Array} Sorted DAGs
 */
function sortDAGs(dags, sortOrder) {
    const sortedDags = [...dags];
    
    switch (sortOrder) {
        case 'created-asc':
            // Sort by earliest created date of root nodes
            sortedDags.sort((a, b) => {
                const rootsA = findRootNodes(a);
                const rootsB = findRootNodes(b);
                const minDateA = Math.min(...rootsA.map(r => new Date(r.created_at).getTime()));
                const minDateB = Math.min(...rootsB.map(r => new Date(r.created_at).getTime()));
                return minDateA - minDateB;
            });
            break;
            
        case 'created-desc':
            // Sort by latest created date of root nodes
            sortedDags.sort((a, b) => {
                const rootsA = findRootNodes(a);
                const rootsB = findRootNodes(b);
                const maxDateA = Math.max(...rootsA.map(r => new Date(r.created_at).getTime()));
                const maxDateB = Math.max(...rootsB.map(r => new Date(r.created_at).getTime()));
                return maxDateB - maxDateA;
            });
            break;
            
        case 'updated-asc':
            // Sort by earliest updated date in the entire DAG
            sortedDags.sort((a, b) => {
                const minDateA = Math.min(...a.map(r => new Date(r.updated_at).getTime()));
                const minDateB = Math.min(...b.map(r => new Date(r.updated_at).getTime()));
                return minDateA - minDateB;
            });
            break;
            
        case 'updated-desc':
            // Sort by latest updated date in the entire DAG
            sortedDags.sort((a, b) => {
                const maxDateA = Math.max(...a.map(r => new Date(r.updated_at).getTime()));
                const maxDateB = Math.max(...b.map(r => new Date(r.updated_at).getTime()));
                return maxDateB - maxDateA;
            });
            break;
            
        case 'name-asc':
            // Sort by root node name (A-Z)
            sortedDags.sort((a, b) => {
                const rootsA = findRootNodes(a);
                const rootsB = findRootNodes(b);
                const nameA = rootsA.length > 0 ? rootsA[0].name.toLowerCase() : '';
                const nameB = rootsB.length > 0 ? rootsB[0].name.toLowerCase() : '';
                return nameA.localeCompare(nameB);
            });
            break;
            
        case 'name-desc':
            // Sort by root node name (Z-A)
            sortedDags.sort((a, b) => {
                const rootsA = findRootNodes(a);
                const rootsB = findRootNodes(b);
                const nameA = rootsA.length > 0 ? rootsA[0].name.toLowerCase() : '';
                const nameB = rootsB.length > 0 ? rootsB[0].name.toLowerCase() : '';
                return nameB.localeCompare(nameA);
            });
            break;
            
        case 'topological':
        default:
            // Keep original topological order
            break;
    }
    
    return sortedDags;
}

/**
 * Render resources grouped by DAG
 * @param {Array} resources - All resources in topological order
 * @param {string} sortOrder - Sort order option
 */
function renderResourcesByDAG(resources, sortOrder = 'topological') {
    console.log(`renderResourcesByDAG called with ${resources?.length || 0} resources, sortOrder: ${sortOrder}`);
    
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
    
    // Hide empty state
    emptyState.style.display = 'none';
    resourceList.style.display = 'block';
    
    // Identify DAGs
    const dags = identifyDAGs(resources);
    console.log(`Identified ${dags.length} DAG(s)`, dags.map(d => d.length));
    
    // Sort DAGs based on selected order
    const sortedDags = sortDAGs(dags, sortOrder);
    
    // Render each DAG as a group
    sortedDags.forEach((dagResources, dagIndex) => {
        // Create DAG group container
        const dagGroup = document.createElement('div');
        dagGroup.className = 'dag-group';
        
        // Create DAG header
        const dagHeader = document.createElement('div');
        dagHeader.className = 'dag-group-header';
        
        const roots = findRootNodes(dagResources);
        const rootNames = roots.map(r => r.name).join(', ');
        
        const dagTitle = document.createElement('h3');
        dagTitle.className = 'dag-group-title';
        dagTitle.textContent = `DAG ${dagIndex + 1}: ${rootNames || 'Unknown'}`;
        
        const dagInfo = document.createElement('div');
        dagInfo.className = 'dag-group-info';
        dagInfo.textContent = `${dagResources.length} resource${dagResources.length !== 1 ? 's' : ''}`;
        
        dagHeader.appendChild(dagTitle);
        dagHeader.appendChild(dagInfo);
        
        dagGroup.appendChild(dagHeader);
        
        // Add view toggle buttons
        addViewToggle(dagGroup, dagIndex);
        
        // Create tree visualization
        const treeViz = createTreeVisualization(dagResources, dagIndex);
        dagGroup.appendChild(treeViz);
        
        // Create resources container for this DAG (card view)
        const dagResourcesContainer = document.createElement('div');
        dagResourcesContainer.className = 'dag-group-resources hidden';
        
        // Sort resources within DAG topologically
        const sortedDagResources = topologicalSortWithinDAG(dagResources);
        
        // Render each resource in the DAG
        sortedDagResources.forEach((resource, index) => {
            const card = createResourceCard(resource, resources);
            
            // Add topological order badge within DAG
            const orderBadge = document.createElement('div');
            orderBadge.className = 'topological-order-badge';
            orderBadge.textContent = `#${index + 1}`;
            orderBadge.setAttribute('title', `Position in DAG: ${index + 1}`);
            
            card.insertBefore(orderBadge, card.firstChild);
            dagResourcesContainer.appendChild(card);
        });
        
        dagGroup.appendChild(dagResourcesContainer);
        resourceList.appendChild(dagGroup);
    });
}

/**
 * Topologically sort resources within a DAG
 * @param {Array} dagResources - Resources in a DAG
 * @returns {Array} Topologically sorted resources
 */
function topologicalSortWithinDAG(dagResources) {
    const sorted = [];
    const visited = new Set();
    const inDag = new Set(dagResources.map(r => r.id));
    
    function visit(resource) {
        if (visited.has(resource.id)) return;
        visited.add(resource.id);
        
        // Visit dependencies first (only those in this DAG)
        const deps = (resource.dependencies || []).filter(depId => inDag.has(depId));
        deps.forEach(depId => {
            const depResource = dagResources.find(r => r.id === depId);
            if (depResource) {
                visit(depResource);
            }
        });
        
        sorted.push(resource);
    }
    
    // Start with root nodes
    const roots = findRootNodes(dagResources);
    roots.forEach(root => visit(root));
    
    // Visit any remaining nodes
    dagResources.forEach(resource => {
        if (!visited.has(resource.id)) {
            visit(resource);
        }
    });
    
    return sorted;
}

/**
 * Handle DAG sort order change
 */
function handleDAGSortChange() {
    const sortSelect = document.getElementById('dagSortOrder');
    if (!sortSelect) return;
    
    sortSelect.addEventListener('change', async () => {
        const sortOrder = sortSelect.value;
        console.log(`Changing DAG sort order to: ${sortOrder}`);
        
        try {
            showLoading();
            
            // Fetch all resources
            const resources = await fetchResources();
            
            // Render with new sort order
            renderResourcesByDAG(resources, sortOrder);
            
        } catch (error) {
            console.error('Error changing sort order:', error);
            showError('Failed to update sort order');
        } finally {
            hideLoading();
        }
    });
}


// ===================================
// Tree/Graph Visualization Functions
// ===================================

/**
 * Create a tree visualization for a DAG
 * @param {Array} dagResources - Resources in the DAG
 * @param {number} dagIndex - Index of the DAG
 * @returns {HTMLElement} Tree visualization element
 */
function createTreeVisualization(dagResources, dagIndex) {
    const container = document.createElement('div');
    container.className = 'dag-visualization';
    container.id = `dag-tree-${dagIndex}`;
    
    // Organize resources by depth level
    const levels = organizeDagByLevels(dagResources);
    const resourceMap = new Map(dagResources.map(r => [r.id, r]));
    
    const treeContainer = document.createElement('div');
    treeContainer.className = 'tree-container';
    
    // Create each level
    levels.forEach((levelResources, levelIndex) => {
        const levelDiv = document.createElement('div');
        levelDiv.className = 'tree-level';
        levelDiv.setAttribute('data-level', levelIndex);
        
        levelResources.forEach(resource => {
            const node = createTreeNode(resource, levelIndex, dagResources);
            levelDiv.appendChild(node);
        });
        
        treeContainer.appendChild(levelDiv);
        
        // Add arrow connector between levels
        if (levelIndex < levels.length - 1) {
            const connector = document.createElement('div');
            connector.className = 'level-connector';
            connector.innerHTML = '<div class="connector-arrow">↓</div>';
            treeContainer.appendChild(connector);
        }
    });
    
    container.appendChild(treeContainer);
    return container;
}

/**
 * Organize DAG resources by depth levels
 * @param {Array} dagResources - Resources in the DAG
 * @returns {Array} Array of arrays, each containing resources at that level
 */
function organizeDagByLevels(dagResources) {
    const levels = [];
    const visited = new Set();
    const resourceMap = new Map(dagResources.map(r => [r.id, r]));
    
    // Calculate depth for each resource
    function getDepth(resource, visiting = new Set()) {
        if (visiting.has(resource.id)) return 0; // Cycle detection
        if (!resource.dependencies || resource.dependencies.length === 0) return 0;
        
        visiting.add(resource.id);
        let maxDepth = 0;
        
        for (const depId of resource.dependencies) {
            const dep = resourceMap.get(depId);
            if (dep) {
                maxDepth = Math.max(maxDepth, getDepth(dep, visiting) + 1);
            }
        }
        
        visiting.delete(resource.id);
        return maxDepth;
    }
    
    // Group resources by depth
    const depthMap = new Map();
    dagResources.forEach(resource => {
        const depth = getDepth(resource);
        if (!depthMap.has(depth)) {
            depthMap.set(depth, []);
        }
        depthMap.get(depth).push(resource);
    });
    
    // Convert to array of levels
    const maxDepth = Math.max(...depthMap.keys());
    for (let i = 0; i <= maxDepth; i++) {
        levels.push(depthMap.get(i) || []);
    }
    
    return levels;
}

/**
 * Create a tree node element
 * @param {Object} resource - Resource object
 * @param {number} level - Depth level
 * @param {Array} allResources - All resources in DAG for dependency lookup
 * @returns {HTMLElement} Tree node element
 */
function createTreeNode(resource, level, allResources) {
    const node = document.createElement('div');
    node.className = `tree-node level-${level}`;
    if (level === 0) {
        node.classList.add('root');
    }
    node.setAttribute('data-resource-id', resource.id);
    
    const title = document.createElement('div');
    title.className = 'tree-node-title';
    title.textContent = resource.name;
    
    const desc = document.createElement('div');
    desc.className = 'tree-node-desc';
    desc.textContent = resource.description || 'No description';
    
    // Append title and description first
    node.appendChild(title);
    node.appendChild(desc);
    
    // Show dependencies as small badges
    if (resource.dependencies && resource.dependencies.length > 0) {
        const depsContainer = document.createElement('div');
        depsContainer.className = 'tree-node-deps';
        
        resource.dependencies.forEach(depId => {
            const depResource = allResources.find(r => r.id === depId);
            if (depResource) {
                const depBadge = document.createElement('span');
                depBadge.className = 'tree-dep-badge';
                depBadge.textContent = `← ${depResource.name}`;
                depBadge.title = `Depends on: ${depResource.name}`;
                depsContainer.appendChild(depBadge);
            }
        });
        
        node.appendChild(depsContainer);
    }
    
    const badge = document.createElement('div');
    badge.className = 'tree-node-badge';
    badge.textContent = level === 0 ? '🌱 ROOT' : `🍃 Level ${level}`;
    
    node.appendChild(badge);
    
    // Click to scroll to card view
    node.onclick = () => {
        const card = document.querySelector(`.resource-card[data-resource-id="${resource.id}"]`);
        if (card) {
            card.scrollIntoView({ behavior: 'smooth', block: 'center' });
            card.style.animation = 'none';
            setTimeout(() => {
                card.style.animation = 'highlight 1s ease-in-out';
            }, 10);
        }
    };
    
    return node;
}

/**
 * Add view toggle buttons to DAG group
 * @param {HTMLElement} dagGroup - DAG group container
 * @param {number} dagIndex - Index of the DAG
 */
function addViewToggle(dagGroup, dagIndex) {
    const toggleContainer = document.createElement('div');
    toggleContainer.className = 'view-toggle';
    
    const treeBtn = document.createElement('button');
    treeBtn.className = 'view-toggle-btn tree-view active';
    treeBtn.textContent = 'Tree View';
    treeBtn.onclick = () => {
        treeBtn.classList.add('active');
        gridBtn.classList.remove('active');
        
        const tree = dagGroup.querySelector(`#dag-tree-${dagIndex}`);
        const grid = dagGroup.querySelector('.dag-group-resources');
        
        if (tree) tree.classList.remove('hidden');
        if (grid) grid.classList.add('hidden');
    };
    
    const gridBtn = document.createElement('button');
    gridBtn.className = 'view-toggle-btn grid-view';
    gridBtn.textContent = 'Card View';
    gridBtn.onclick = () => {
        gridBtn.classList.add('active');
        treeBtn.classList.remove('active');
        
        const tree = dagGroup.querySelector(`#dag-tree-${dagIndex}`);
        const grid = dagGroup.querySelector('.dag-group-resources');
        
        if (tree) tree.classList.add('hidden');
        if (grid) grid.classList.remove('hidden');
    };
    
    toggleContainer.appendChild(treeBtn);
    toggleContainer.appendChild(gridBtn);
    
    // Insert after header
    const header = dagGroup.querySelector('.dag-group-header');
    if (header && header.nextSibling) {
        dagGroup.insertBefore(toggleContainer, header.nextSibling);
    } else {
        dagGroup.appendChild(toggleContainer);
    }
}
