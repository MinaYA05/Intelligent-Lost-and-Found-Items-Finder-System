// Get URL parameters
function getUrlParameter(name) {
    name = name.replace(/[\[]/, '\\[').replace(/[\]]/, '\\]');
    var regex = new RegExp('[\\?&]' + name + '=([^&#]*)');
    var results = regex.exec(location.search);
    return results === null ? '' : decodeURIComponent(results[1].replace(/\+/g, ' '));
}

// Display search results
function displayResults(items) {
    const resultsContainer = document.getElementById('searchResults');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const noResults = document.getElementById('noResults');
    
    loadingSpinner.style.display = 'none';
    
    if (items.length === 0) {
        noResults.style.display = 'block';
        return;
    }
    
    let html = '';
    items.forEach(item => {
        const imageUrl = getItemImage(item);
        
        html += `
            <div class="result-card">
                <img src="${imageUrl}" alt="${item.item_name}" class="result-image" onerror="this.src='https://via.placeholder.com/400x200?text=No+Image'">
                <div class="result-content">
                    <div class="result-title">${item.item_name}</div>
                    <div class="result-description">${item.description}</div>
                    <div class="result-meta">
                        <span class="result-location">
                            <i class="fas fa-map-marker-alt"></i> ${getItemLocation(item)}
                        </span>
                        <span class="result-date">
                            <i class="fas fa-calendar"></i> ${formatDate(getItemDate(item))}
                        </span>
                        <span class="result-category">${item.category}</span>
                        <span class="result-category">${item.item_type === 'lost' ? 'Lost' : 'Found'}</span>
                    </div>
                    <div class="mt-3">
                        <button class="btn btn-primary btn-sm" onclick="viewItemDetails(${item.id})">
                            <i class="fas fa-eye"></i> View Details
                        </button>
                        <button class="btn btn-success btn-sm" onclick="contactAboutItem(${item.id})">
                            <i class="fas fa-phone"></i> Contact
                        </button>
                    </div>
                </div>
            </div>
        `;
    });
    
    resultsContainer.innerHTML = html;
}

// Format date
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString(undefined, options);
}

function getItemLocation(item) {
    return item.location_found || item.location_lost || 'Unknown';
}

function getItemDate(item) {
    return item.date_found || item.date_lost || '';
}

function getItemImage(item) {
    if (!item.image_path) {
        return 'https://via.placeholder.com/400x200?text=No+Image';
    }
    if (item.image_path.startsWith('http')) {
        return item.image_path;
    }
    return `founditems/${item.image_path}`;
}

// View item details
function viewItemDetails(itemId) {
    showToast(`Item Details: To view full details and claim this item, please contact our lost and found office. Item ID: ${itemId}. You will need to provide proof of ownership.`, 'info');
}

// Contact about item
function contactAboutItem(itemId) {
    showToast(`Contact Information: To claim this item, please visit our lost and found office with: 1. Valid ID proof, 2. Description of the item, 3. Item ID: ${itemId}. Our staff will help you verify and claim your item.`, 'info');
}

// Simple search function (basic text matching)
async function performSimpleSearch(query) {
    try {
        const [foundResponse, lostResponse] = await Promise.all([
            fetch('http://127.0.0.1:5000/api/found-items'),
            fetch('http://127.0.0.1:5000/api/lost-items')
        ]);
        const foundResult = await foundResponse.json();
        const lostResult = await lostResponse.json();
        
        if (foundResult.success || lostResult.success) {
            const foundItems = (foundResult.items || []).map(item => ({ ...item, item_type: 'found' }));
            const lostItems = (lostResult.items || []).map(item => ({ ...item, item_type: 'lost' }));
            const items = [...foundItems, ...lostItems];
            // Simple text matching
            const queryLower = query.toLowerCase();
            const matchedItems = items.filter(item => {
                const locationValue = item.location_found || item.location_lost || '';
                const searchText = `${item.item_name} ${item.description} ${locationValue} ${item.category}`.toLowerCase();
                return searchText.includes(queryLower);
            });
            
            displayResults(matchedItems);
        } else {
            showError('Failed to load items');
        }
    } catch (error) {
        console.error('Search error:', error);
        showError('Search failed. Please try again.');
    }
}

// Show error message
function showError(message) {
    const resultsContainer = document.getElementById('searchResults');
    const loadingSpinner = document.getElementById('loadingSpinner');
    
    loadingSpinner.style.display = 'none';
    resultsContainer.innerHTML = `
        <div class="alert alert-danger text-center">
            <i class="fas fa-exclamation-triangle"></i> ${message}
        </div>
    `;
}

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    // Check authentication status on page load
    checkAuthStatus();
    
    // Get search query from URL
    const query = getUrlParameter('q');
    const itemsData = getUrlParameter('items');
    const noResults = getUrlParameter('noresults');
    
    if (query) {
        document.getElementById('searchQuery').textContent = `Search results for: "${query}"`;
        
        if (noResults === 'true') {
            // Show no results immediately
            document.getElementById('loadingSpinner').style.display = 'none';
            document.getElementById('noResults').style.display = 'block';
        } else if (itemsData) {
            // Display pre-fetched items from homepage search
            try {
                const items = JSON.parse(decodeURIComponent(itemsData));
                displayResults(items);
            } catch (error) {
                console.error('Error parsing items data:', error);
                // Fallback to simple search
                performSimpleSearch(query);
            }
        } else {
            // Fallback to simple search
            performSimpleSearch(query);
        }
    } else {
        document.getElementById('searchQuery').textContent = 'No search query provided';
        document.getElementById('loadingSpinner').style.display = 'none';
        document.getElementById('noResults').style.display = 'block';
    }
});

// Check authentication status (copied from script.js)
async function checkAuthStatus() {
    try {
        const response = await fetch('http://127.0.0.1:5000/api/check-auth', {
            credentials: 'include'  // Include cookies for session
        });
        const result = await response.json();
        
        if (result.authenticated) {
            updateAuthUI(true, result.user);
        } else {
            updateAuthUI(false);
        }
    } catch (error) {
        console.error('Auth check error:', error);
        updateAuthUI(false);
    }
}

// Update UI based on authentication status (copied from script.js)
function updateAuthUI(isAuthenticated, user = null) {
    console.log('Updating UI:', { isAuthenticated, user });
    
    const authButtons = document.querySelector('.d-flex');
    if (!authButtons) {
        console.error('Auth buttons container not found');
        return;
    }
    
    if (isAuthenticated && user) {
        authButtons.innerHTML = `
            <span class="navbar-text me-3">Welcome, ${user.name}</span>
            <button class="btn btn-outline-dark shadow-none" onclick="logout()">Logout</button>
        `;
        console.log('UI updated to logged in state');
    } else {
        authButtons.innerHTML = `
            <button class="btn btn-outline-dark shadow-none me-lg-3 me-2 mr-2" data-toggle="modal" data-target="#loginModal" type="button">
                Login
            </button>
            <button class="btn btn-outline-dark shadow-none me-lg-3" data-toggle="modal" data-target="#registerModal" type="button">
                Register
            </button>
        `;
        console.log('UI updated to logged out state');
    }
}

// Logout function (copied from script.js)
async function logout() {
    try {
        const response = await fetch('http://127.0.0.1:5000/api/logout', {
            method: 'POST',
            credentials: 'include'
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Logged out successfully');
            updateAuthUI(false);
        } else {
            alert('Logout failed');
        }
    } catch (error) {
        console.error('Logout error:', error);
        alert('Logout failed: Server error');
    }
}
