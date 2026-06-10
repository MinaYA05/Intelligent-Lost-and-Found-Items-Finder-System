let currentUser = null;
// how-it-works section
document.addEventListener("DOMContentLoaded", function () {

    const wrapper = document.getElementById("how-it-works-wrapper");
    const prevBtn = document.getElementById("prev-how-it-works");
    const nextBtn = document.getElementById("next-how-it-works");

    const scrollAmount = 250; // distance to scroll

    nextBtn.addEventListener("click", function () {
        wrapper.scrollBy({
            top: scrollAmount,
            behavior: "smooth"
        });
    });

    prevBtn.addEventListener("click", function () {
        wrapper.scrollBy({
            top: -scrollAmount,
            behavior: "smooth"
        });
    });

});
//Latest-Update section
document.addEventListener("DOMContentLoaded", function () {

    const updatesWrapper = document.getElementById("updates-wrapper");
    const prevBtn = document.getElementById("prev-updates");
    const nextBtn = document.getElementById("next-updates");

    const scrollAmount = 300; // distance for each click

    nextBtn.addEventListener("click", function () {
        updatesWrapper.scrollBy({
            left: scrollAmount,
            behavior: "smooth"
        });
    });

    prevBtn.addEventListener("click", function () {
        updatesWrapper.scrollBy({
            left: -scrollAmount,
            behavior: "smooth"
        });
    });

});

// Toast notification helper
function showToast(message, type = 'info') {
    let backgroundColor;
    switch(type) {
        case 'success':
            backgroundColor = "linear-gradient(to right, #00b09b, #96c93d)";
            break;
        case 'error':
            backgroundColor = "linear-gradient(to right, #ff5f6d, #ffc371)";
            break;
        case 'warning':
            backgroundColor = "linear-gradient(to right, #f2994a, #f2c94c)";
            break;
        case 'info':
        default:
            backgroundColor = "linear-gradient(to right, #56ccf2, #2f80ed)";
    }

    Toastify({
        text: message,
        duration: 3000,
        close: true,
        gravity: "top", // `top` or `bottom`
        position: "right", // `left`, `center` or `right`
        backgroundColor: backgroundColor,
        stopOnFocus: true, // Prevents dismissing of toast on hover
    }).showToast();
}

document.addEventListener('DOMContentLoaded', () => {
    // Check authentication status immediately when page loads
    checkAuthStatus();
    
    // Navigation links functionality
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', (event) => {
            // Allow normal navigation for now
            console.log(`Navigating to: ${event.target.textContent}`);
        });
    });

    // Check if we're on home page and add search functionality
    const homeSearchForm = document.getElementById('homeSearchForm');
    if (homeSearchForm) {
        homeSearchForm.addEventListener('submit', performHomeSearch);
    }

    // Login form handling
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(loginForm);
            const loginData = {
                email_mob: formData.get('email_mob'),
                pass: formData.get('pass')
            };

            try {
                const response = await fetch('http://127.0.0.1:5000/api/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(loginData),
                    credentials: 'include'
                });

                const result = await response.json();

                if (result.success) {
                    showToast('Login successful! Welcome ' + result.user.name, 'success');
                    // Store auth token in localStorage for persistence
                    if (result.token) {
                        localStorage.setItem('authToken', result.token);
                        console.log('Auth token stored in localStorage:', result.token);
                    }
                    // Close modal using jQuery (Bootstrap 4 method)
                    $('#loginModal').modal('hide');
                    loginForm.reset();
                    
                    // Check if user is admin and redirect
                    if (result.user.is_admin) {
                        window.location.href = 'admin.html';
                        return;
                    }

                    // Update UI to show logged in state immediately
                    updateAuthUI(true, result.user);
                } else {
                    showToast('Login failed: ' + result.message, 'error');
                }
            } catch (error) {
                console.error('Login error:', error);
                console.error('Error details:', error.message);
                console.error('Error stack:', error.stack);
                showToast('Login failed: Server error. Please try again.', 'error');
            }
        });
    }

    // Registration form handling
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(registerForm);
            
            try {
                const response = await fetch('http://127.0.0.1:5000/api/register', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();

                if (result.success) {
                    showToast('Registration successful! Please login.', 'success');
                    // Close modal and open login modal using jQuery
                    $('#registerModal').modal('hide');
                    registerForm.reset();
                    
                    // Open login modal
                    $('#loginModal').modal('show');
                } else {
                    showToast('Registration failed: ' + result.message, 'error');
                }
            } catch (error) {
                console.error('Registration error:', error);
                showToast('Registration failed: Server error. Please try again.', 'error');
            }
        });
    }

    // Found items form handling
    const foundItemForm = document.getElementById('foundItemForm');
    if (foundItemForm) {
        foundItemForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            // First test connectivity
            try {
                console.log("Testing server connectivity...");
                const headers = {};
                const authToken = localStorage.getItem('authToken');
                if (authToken) {
                    headers['Authorization'] = `Bearer ${authToken}`;
                }
                
                const testResponse = await fetch('http://127.0.0.1:5000/api/test', {
                    method: 'POST',
                    headers: headers,
                    credentials: 'include'
                });
                const testResult = await testResponse.json();
                console.log("Test result:", testResult);
            } catch (error) {
                console.error("Test failed:", error);
                showToast('Server connectivity test failed. Please check server.', 'error');
                return;
            }
            
            const formData = new FormData(foundItemForm);
            console.log("Form data entries:");
            for (let [key, value] of formData.entries()) {
                console.log(key, value);
            }
            
            try {
                const headers = {};
                const authToken = localStorage.getItem('authToken');
                if (authToken) {
                    headers['Authorization'] = `Bearer ${authToken}`;
                }
                
                const response = await fetch('http://127.0.0.1:5000/api/found-items', {
                    method: 'POST',
                    headers: headers,
                    body: formData,
                    credentials: 'include'  // Include cookies for session
                });

                const result = await response.json();

                if (result.success) {
                    showToast('Found item reported successfully!', 'success');
                    foundItemForm.reset();
                } else {
                    showToast('Failed to report found item: ' + result.message, 'error');
                }
            } catch (error) {
                console.error('Found item report error:', error);
                console.error('Error details:', error.message);
                console.error('Error stack:', error.stack);
                showToast('Failed to report found item: Server error. Please try again.', 'error');
            }
        });
    }

    const lostItemForm = document.getElementById('lostItemForm');
    if (lostItemForm) {
        lostItemForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const payload = {
                item_name: document.getElementById('lostItemName')?.value?.trim(),
                description: document.getElementById('lostItemDesc')?.value?.trim(),
                location_lost: document.getElementById('lostItemLocation')?.value?.trim(),
                date_lost: document.getElementById('lostItemDate')?.value,
                category: document.getElementById('lostItemCategory')?.value
            };

            try {
                const headers = {
                    'Content-Type': 'application/json'
                };
                const authToken = localStorage.getItem('authToken');
                if (authToken) {
                    headers['Authorization'] = `Bearer ${authToken}`;
                }

                const response = await fetch('http://127.0.0.1:5000/api/lost-items', {
                    method: 'POST',
                    headers: headers,
                    body: JSON.stringify(payload),
                    credentials: 'include'
                });

                const result = await response.json();

                if (result.success) {
                    showToast('Lost item reported successfully!', 'success');
                    lostItemForm.reset();
                } else {
                    showToast('Failed to report lost item: ' + result.message, 'error');
                }
            } catch (error) {
                console.error('Lost item report error:', error);
                showToast('Failed to report lost item: Server error. Please try again.', 'error');
            }
        });
    }
});

// My Reports Functionality
function openMyReports() {
    $('#myReportsModal').modal('show');
    loadMyFoundItems();
    loadMyLostItems();
}

async function loadMyFoundItems() {
    const container = document.getElementById('myFoundReportsContainer');
    container.innerHTML = '<div class="text-center"><div class="spinner-border text-primary" role="status"><span class="sr-only">Loading...</span></div></div>';
    
    try {
        const authToken = localStorage.getItem('authToken');
        if (!authToken) {
            container.innerHTML = '<div class="alert alert-warning">Please login to view your reports.</div>';
            return;
        }
        
        const response = await fetch('http://127.0.0.1:5000/api/my-found-items', {
            headers: { 'Authorization': `Bearer ${authToken}` },
            credentials: 'include'
        });
        
        const result = await response.json();
        
        if (result.success && result.items.length > 0) {
            let html = '<div class="row">';
            result.items.forEach(item => {
                const claimsCount = item.claims ? item.claims.length : 0;
                const claimsBadge = claimsCount > 0 ? `<span class="badge badge-danger">${claimsCount} New Claim(s)</span>` : '<span class="badge badge-secondary">No Claims</span>';
                
                let claimsHtml = '';
                if (claimsCount > 0) {
                    claimsHtml = '<div class="mt-3 border-top pt-2"><h6>Claims:</h6><ul class="list-group list-group-flush">';
                    item.claims.forEach(claim => {
                        claimsHtml += `
                            <li class="list-group-item bg-light text-dark p-2 mb-1 rounded">
                                <strong>${claim.claimant_name}</strong> (${claim.claimant_email})<br>
                                <small>${claim.description}</small>
                            </li>`;
                    });
                    claimsHtml += '</ul></div>';
                }

                html += `
                    <div class="col-md-6 mb-4">
                        <div class="card h-100 shadow-sm">
                            <div class="row no-gutters">
                                <div class="col-md-4">
                                    <img src="${getItemImage(item)}" class="card-img h-100" style="object-fit: cover;" onerror="this.src='https://via.placeholder.com/150'">
                                </div>
                                <div class="col-md-8">
                                    <div class="card-body">
                                        <h5 class="card-title">${item.item_name} ${claimsBadge}</h5>
                                        <p class="card-text text-muted small"><i class="fas fa-map-marker-alt"></i> ${getItemLocation(item)} | <i class="fas fa-calendar"></i> ${formatDate(getItemDate(item))}</p>
                                        <p class="card-text">${item.description}</p>
                                        ${claimsHtml}
                                        <div class="mt-3 text-right">
                                            <button class="btn btn-danger btn-sm" onclick="deleteFoundItem(${item.id})">
                                                <i class="fas fa-trash-alt"></i> Delete / Resolve
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            });
            html += '</div>';
            container.innerHTML = html;
        } else {
            container.innerHTML = '<div class="alert alert-info text-center">You haven\'t reported any found items yet.</div>';
        }
    } catch (error) {
        console.error('Error loading found reports:', error);
        container.innerHTML = '<div class="alert alert-danger">Failed to load reports. Please try again later.</div>';
    }
}

async function loadMyLostItems() {
    const container = document.getElementById('myLostReportsContainer');
    container.innerHTML = '<div class="text-center"><div class="spinner-border text-primary" role="status"><span class="sr-only">Loading...</span></div></div>';
    
    try {
        const authToken = localStorage.getItem('authToken');
        if (!authToken) {
            container.innerHTML = '<div class="alert alert-warning">Please login to view your reports.</div>';
            return;
        }
        
        const response = await fetch('http://127.0.0.1:5000/api/my-lost-items', {
            headers: { 'Authorization': `Bearer ${authToken}` },
            credentials: 'include'
        });
        
        const result = await response.json();
        
        if (result.success && result.items.length > 0) {
            let html = '<div class="row">';
            result.items.forEach(item => {
                const requestsCount = item.found_requests ? item.found_requests.length : 0;
                const requestsBadge = requestsCount > 0 ? `<span class="badge badge-success">${requestsCount} Item Found!</span>` : '<span class="badge badge-secondary">Searching...</span>';
                
                let requestsHtml = '';
                if (requestsCount > 0) {
                    requestsHtml = '<div class="mt-3 border-top pt-2"><h6>Found Requests:</h6><ul class="list-group list-group-flush">';
                    item.found_requests.forEach(req => {
                        requestsHtml += `
                            <li class="list-group-item bg-light text-dark p-2 mb-1 rounded">
                                <strong>${req.finder_name}</strong> (${req.finder_email})<br>
                                <small>${req.description}</small>
                            </li>`;
                    });
                    requestsHtml += '</ul></div>';
                }

                html += `
                    <div class="col-md-6 mb-4">
                        <div class="card h-100 shadow-sm">
                            <div class="card-body">
                                <h5 class="card-title">${item.item_name} ${requestsBadge}</h5>
                                <p class="card-text text-muted small"><i class="fas fa-map-marker-alt"></i> ${item.location_lost} | <i class="fas fa-calendar"></i> ${formatDate(item.date_lost)}</p>
                                <p class="card-text">${item.description}</p>
                                ${requestsHtml}
                                <div class="mt-3 text-right">
                                    <button class="btn btn-danger btn-sm" onclick="deleteLostItem(${item.id})">
                                        <i class="fas fa-trash-alt"></i> Delete / Found
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            });
            html += '</div>';
            container.innerHTML = html;
        } else {
            container.innerHTML = '<div class="alert alert-info text-center">You haven\'t reported any lost items yet.</div>';
        }
    } catch (error) {
        console.error('Error loading lost reports:', error);
        container.innerHTML = '<div class="alert alert-danger">Failed to load reports. Please try again later.</div>';
    }
}

async function deleteFoundItem(itemId) {
    if (!confirm('Are you sure you want to delete this report? This action cannot be undone. Use this if the item has been returned or claimed.')) {
        return;
    }
    
    try {
        const authToken = localStorage.getItem('authToken');
        const response = await fetch(`http://127.0.0.1:5000/api/found-items/${itemId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${authToken}` },
            credentials: 'include'
        });
        
        const result = await response.json();
        if (result.success) {
            showToast('Item removed successfully.', 'success');
            loadMyFoundItems(); // Refresh list
            loadRecentItems(); // Refresh home page list
        } else {
            showToast('Failed to delete item: ' + result.message, 'error');
        }
    } catch (error) {
        console.error('Delete error:', error);
        showToast('Server error while deleting item.', 'error');
    }
}

async function deleteLostItem(itemId) {
    if (!confirm('Are you sure you want to delete this lost item report? This action cannot be undone. Use this if you have found your item.')) {
        return;
    }
    
    try {
        const authToken = localStorage.getItem('authToken');
        const response = await fetch(`http://127.0.0.1:5000/api/lost-items/${itemId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${authToken}` },
            credentials: 'include'
        });
        
        const result = await response.json();
        if (result.success) {
            showToast('Item removed successfully.', 'success');
            loadMyLostItems(); // Refresh list
        } else {
            showToast('Failed to delete item: ' + result.message, 'error');
        }
    } catch (error) {
        console.error('Delete error:', error);
        showToast('Server error while deleting item.', 'error');
    }
}

// Claim specific item functionality
function openClaimModal(itemId) {
    if (!currentUser) {
        showToast('Please login to claim an item.', 'info');
        $('#loginModal').modal('show');
        return;
    }
    
    document.getElementById('claimItemId').value = itemId;
    document.getElementById('claimantNameSpecific').value = currentUser.name || '';
    document.getElementById('claimantEmailSpecific').value = currentUser.email || '';
    $('#claimItemModal').modal('show');
}

// Found Request Functionality (when someone finds a lost item)
function openFoundRequestModal(itemId) {
    if (!currentUser) {
        showToast('Please login to report finding this item.', 'info');
        $('#loginModal').modal('show');
        return;
    }
    
    document.getElementById('foundRequestItemId').value = itemId;
    document.getElementById('finderName').value = currentUser.name || '';
    document.getElementById('finderEmail').value = currentUser.email || '';
    $('#foundRequestModal').modal('show');
}

// Handle found request submission
const foundRequestForm = document.getElementById('foundRequestForm');
if (foundRequestForm) {
    foundRequestForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const itemId = document.getElementById('foundRequestItemId').value;
        const name = document.getElementById('finderName').value;
        const email = document.getElementById('finderEmail').value;
        const description = document.getElementById('finderDescription').value;
        
        try {
            const authToken = localStorage.getItem('authToken');
            const headers = { 
                'Content-Type': 'application/json' 
            };
            if (authToken) {
                headers['Authorization'] = `Bearer ${authToken}`;
            }

            const response = await fetch(`http://127.0.0.1:5000/api/lost-items/${itemId}/found-request`, {
                method: 'POST',
                headers: headers,
                credentials: 'include',
                body: JSON.stringify({
                    finder_name: name,
                    finder_email: email,
                    description: description
                })
            });
            
            const result = await response.json();
            if (result.success) {
                showToast(result.message, 'success');
                $('#foundRequestModal').modal('hide');
                foundRequestForm.reset();
            } else {
                showToast('Failed to submit found request: ' + result.message, 'error');
            }
        } catch (error) {
            console.error('Found request error:', error);
            showToast('Server error while submitting found request.', 'error');
        }
    });
}

// Handle specific claim submission
const specificClaimForm = document.getElementById('specificClaimForm');
if (specificClaimForm) {
    specificClaimForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const itemId = document.getElementById('claimItemId').value;
        const name = document.getElementById('claimantNameSpecific').value;
        const email = document.getElementById('claimantEmailSpecific').value;
        const description = document.getElementById('claimDescriptionSpecific').value;
        
        try {
            const authToken = localStorage.getItem('authToken');
            const headers = { 
                'Content-Type': 'application/json' 
            };
            if (authToken) {
                headers['Authorization'] = `Bearer ${authToken}`;
            }

            const response = await fetch(`http://127.0.0.1:5000/api/found-items/${itemId}/claim-request`, {
                method: 'POST',
                headers: headers,
                credentials: 'include',
                body: JSON.stringify({
                    claimant_name: name,
                    claimant_email: email,
                    description: description
                })
            });
            
            const result = await response.json();
            if (result.success) {
                showToast(result.message, 'success');
                $('#claimItemModal').modal('hide');
                specificClaimForm.reset();
            } else {
                showToast('Failed to submit claim: ' + result.message, 'error');
            }
        } catch (error) {
            console.error('Claim error:', error);
            showToast('Server error while submitting claim.', 'error');
        }
    });
}

// Update UI based on authentication status
function updateAuthUI(isAuthenticated, user = null) {
    console.log('=== UPDATING UI ===');
    console.log('Is authenticated:', isAuthenticated);
    console.log('User data:', user);
    console.log('Current URL:', window.location.href);
    
    // Update global user
    currentUser = isAuthenticated ? user : null;
    
    // Try multiple selectors to find the auth buttons container
    const authButtons = document.querySelector('.navbar .d-flex') || 
                        document.querySelector('.d-flex') || 
                        document.querySelector('nav .d-flex');
    
    console.log('Auth buttons container found:', authButtons);
    
    if (!authButtons) {
        console.error('❌ Auth buttons container not found');
        return;
    }
    
    if (isAuthenticated && user) {
        console.log('✅ Setting logged in UI for user:', user.name);
        
        // Only show My Reports on home page
        const isHomePage = window.location.pathname.endsWith('index.html') || window.location.pathname === '/' || window.location.pathname.endsWith('/');
        const myReportsBtn = isHomePage ? `
            <button class="btn btn-outline-dark shadow-none mr-3" onclick="openMyReports()">
                <i class="fas fa-list"></i> My Reports
            </button>` : '';

        // Profile picture handling
        let profileHtml = '';
        if (user.profile_pic) {
            profileHtml = `<img src="${user.profile_pic}" alt="Profile" class="rounded-circle mr-2 border" style="width: 35px; height: 35px; object-fit: cover;">`;
        } else {
             profileHtml = `<i class="bi bi-person-circle mr-2" style="font-size: 1.5rem;"></i>`;
        }

        authButtons.innerHTML = `
            ${myReportsBtn}
            <div class="d-flex align-items-center mr-3">
                ${profileHtml}
                <span class="navbar-text font-weight-bold text-dark">Welcome, ${user.name.split(' ')[0]}</span>
            </div>
            <button class="btn btn-outline-dark shadow-none" onclick="logout()">Logout</button>
        `;
        console.log('✅ UI updated to logged in state');
    } else {
        console.log('❌ Setting logged out UI');
        authButtons.innerHTML = `
            <button class="btn btn-outline-dark shadow-none mr-lg-3 mr-2" data-toggle="modal" data-target="#loginModal" type="button">
                Login
            </button>
            <button class="btn btn-outline-dark shadow-none mr-lg-3" data-toggle="modal" data-target="#registerModal" type="button">
                Register
            </button>
        `;
        console.log('✅ UI updated to logged out state');
    }
}

// Test cookies function
async function testCookies() {
    try {
        console.log('=== TESTING COOKIES ===');
        const headers = {};
        const authToken = localStorage.getItem('authToken');
        if (authToken) {
            headers['Authorization'] = `Bearer ${authToken}`;
        }
        
        const response = await fetch('http://127.0.0.1:5000/api/test-cookies', {
            headers: headers,
            credentials: 'include'
        });
        const result = await response.json();
        console.log('Cookie test result:', result);
        console.log('Cookies received by server:', result.cookies_received);
        console.log('Session data on server:', result.session_data);
    } catch (error) {
        console.error('Cookie test error:', error);
    }
}

// Check authentication status
async function checkAuthStatus() {
    try {
        console.log('=== CHECKING AUTHENTICATION STATUS ===');
        console.log('Current URL:', window.location.href);
        
        // Check if we have a stored auth token
        const authToken = localStorage.getItem('authToken');
        console.log('Stored auth token:', authToken);
        
        const headers = {};
        if (authToken) {
            headers['Authorization'] = `Bearer ${authToken}`;
        }
        
        const response = await fetch('http://127.0.0.1:5000/api/check-auth', {
            method: 'GET',
            headers: headers,
            credentials: 'include'  // Include cookies for session
        });
        
        console.log('Auth check response status:', response.status);
        const result = await response.json();
        console.log('Auth check result:', result);
        
        if (result.authenticated) {
            console.log('✅ User is authenticated, updating UI');
            updateAuthUI(true, result.user);
        } else {
            console.log('❌ User is not authenticated, updating UI');
            updateAuthUI(false);
        }
    } catch (error) {
        console.error('❌ Auth check error:', error);
        console.error('Error details:', error.message);
        updateAuthUI(false);
    }
}

// Logout function
let adminHistoryData = {};

async function loadHistory() {
    const tbody = document.getElementById('history-table-body');
    tbody.innerHTML = '<tr><td colspan="7" class="text-center">Loading...</td></tr>';

    try {
        const authToken = localStorage.getItem('authToken');
        const response = await fetch('http://127.0.0.1:5000/api/admin/history', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        if (response.status === 401 || response.status === 403) {
            logout();
            return;
        }

        const data = await response.json();
        
        if (data.success) {
            tbody.innerHTML = '';
            adminHistoryData = {};
            
            if (!data.history || data.history.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" class="text-center">No history found</td></tr>';
                return;
            }

            data.history.forEach(item => {
                adminHistoryData[item.id] = item.details;
                
                const tr = document.createElement('tr');
                
                // Format action type badge
                let actionBadge = '';
                if (item.action_type === 'DELETE') {
                    actionBadge = '<span class="badge badge-danger">DELETE</span>';
                } else if (item.action_type === 'APPROVE') {
                    actionBadge = '<span class="badge badge-success">APPROVE</span>';
                } else {
                    actionBadge = `<span class="badge badge-secondary">${item.action_type}</span>`;
                }

                tr.innerHTML = `
                    <td>${item.id}</td>
                    <td>${item.admin_name || 'Unknown'}</td>
                    <td>${actionBadge}</td>
                    <td>${item.item_type}</td>
                    <td>${item.item_id || 'N/A'}</td>
                    <td>${item.created_at}</td>
                    <td>
                        <button class="btn btn-info btn-sm" onclick="viewHistoryDetails(${item.id})">
                            <i class="fas fa-eye"></i> View
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        } else {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center text-danger">Error: ${data.message}</td></tr>`;
        }
    } catch (error) {
        console.error('Error loading history:', error);
        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-danger">Failed to load history</td></tr>';
    }
}

function viewHistoryDetails(id) {
    const details = adminHistoryData[id];
    let formattedHtml = '';
    
    try {
        const jsonObj = JSON.parse(details);
        formattedHtml = '<pre style="text-align: left; max-height: 300px; overflow: auto; background: #f8f9fa; padding: 10px; border-radius: 5px;">' + 
            JSON.stringify(jsonObj, null, 2) + 
            '</pre>';
    } catch (e) {
        formattedHtml = `<p>${details}</p>`;
    }
        
    Swal.fire({
        title: 'Action Details',
        html: formattedHtml,
        width: '600px',
        confirmButtonText: 'Close'
    });
}

async function logout() {
    try {
        // Clear stored auth token
        localStorage.removeItem('authToken');
        console.log('Auth token cleared from localStorage');
        
        const headers = {};
        const authToken = localStorage.getItem('authToken');
        if (authToken) {
            headers['Authorization'] = `Bearer ${authToken}`;
        }
        
        const response = await fetch('http://127.0.0.1:5000/api/logout', {
            method: 'POST',
            headers: headers,
            credentials: 'include'  // Include cookies for session
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast('Logged out successfully', 'success');
            updateAuthUI(false);
        } else {
            showToast('Logout failed', 'error');
        }
    } catch (error) {
        showToast('Logout failed: Server error', 'error');
    }
}

// Toggle recent items visibility
function toggleRecentItems() {
    const recentSection = document.getElementById('recentItemsSection');
    const searchSection = document.getElementById('search');
    
    if (recentSection.style.display === 'none') {
        recentSection.style.display = 'block';
        searchSection.style.display = 'none';
        loadRecentItems();
    } else {
        recentSection.style.display = 'none';
        searchSection.style.display = 'block';
    }
}

// Load recently reported items (both found and lost)
async function loadRecentItems() {
    try {
        const headers = {};
        const authToken = localStorage.getItem('authToken');
        if (authToken) {
            headers['Authorization'] = `Bearer ${authToken}`;
        }
        
        const [foundResponse, lostResponse] = await Promise.all([
            fetch('http://127.0.0.1:5000/api/found-items', {
                headers: headers,
                credentials: 'include'
            }),
            fetch('http://127.0.0.1:5000/api/lost-items', {
                headers: headers,
                credentials: 'include'
            })
        ]);
        
        const foundResult = await foundResponse.json();
        const lostResult = await lostResponse.json();
        
        const container = document.getElementById('recentItemsContainer');
        
        let allItems = [];
        if (foundResult.success) {
            allItems = allItems.concat(foundResult.items.map(i => ({...i, item_type: 'found'})));
        }
        if (lostResult.success) {
            allItems = allItems.concat(lostResult.items.map(i => ({...i, item_type: 'lost'})));
        }
        
        // Sort by date descending (newest first)
        allItems.sort((a, b) => {
            const dateA = new Date(getItemDate(a));
            const dateB = new Date(getItemDate(b));
            return dateB - dateA;
        });
        
        if (allItems.length > 0) {
            displayRecentItems(allItems);
        } else {
            container.innerHTML = `
                <div class="no-items">
                    <i class="fas fa-box-open fa-3x mb-3"></i>
                    <h4>No items reported yet</h4>
                    <p>Be the first to report a lost or found item!</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading recent items:', error);
        const container = document.getElementById('recentItemsContainer');
        container.innerHTML = `
            <div class="no-items">
                <i class="fas fa-exclamation-triangle fa-3x mb-3"></i>
                <h4>Error loading items</h4>
                <p>Please try again later.</p>
            </div>
        `;
    }
}

// Display recent items
function displayRecentItems(items) {
    const container = document.getElementById('recentItemsContainer');
    
    const itemsHtml = items.map(item => {
        const isFound = item.item_type === 'found';
        const badgeClass = isFound ? 'badge-success' : 'badge-danger';
        const badgeText = isFound ? 'Found' : 'Lost';
        const actionButton = isFound 
            ? `<button class="btn btn-warning btn-sm" onclick="openClaimModal(${item.id})">
                 <i class="fas fa-hand-holding"></i> Claim This Item
               </button>`
            : `<button class="btn btn-info btn-sm" onclick="openFoundRequestModal(${item.id})">
                 <i class="fas fa-search-location"></i> I Found This
               </button>`;

        return `
        <div class="col-md-4 mb-4">
            <div class="card h-100 shadow-sm">
                <img src="${getItemImage(item)}" class="card-img-top item-image" alt="${item.item_name}"
                     onerror="this.src='https://via.placeholder.com/400x200?text=No+Image'">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <h5 class="card-title mb-0">${item.item_name}</h5>
                        <span class="badge ${badgeClass}">${badgeText}</span>
                    </div>
                    <p class="card-text description-truncate">${item.description}</p>
                    <div class="item-meta mb-2">
                        <small class="text-muted">
                            <i class="fas fa-map-marker-alt"></i> ${getItemLocation(item)}
                        </small>
                        <br>
                        <small class="text-muted">
                            <i class="fas fa-calendar"></i> ${formatDate(getItemDate(item))}
                        </small>
                    </div>
                    <span class="badge badge-primary">${item.category}</span>
                    <div class="mt-3 text-right">
                         ${actionButton}
                    </div>
                </div>
            </div>
        </div>
    `}).join('');
    
    container.innerHTML = `<div class="row">${itemsHtml}</div>`;
}

// Format date helper function
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
    });
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

function getItemTypeBadge(item) {
    if (item.item_type === 'lost') {
        return '<span class="badge badge-danger ml-2">Lost</span>';
    }
    return '<span class="badge badge-success ml-2">Found</span>';
}

// Home page search function
async function performHomeSearch(event) {
    event.preventDefault();
    
    const searchQuery = document.getElementById('searchInput').value.trim();
    
    if (!searchQuery) {
        showToast('Please enter a search query', 'info');
        return;
    }
    
    // Show loading state
    const searchInput = document.getElementById('searchInput');
    const originalPlaceholder = searchInput.placeholder;
    searchInput.placeholder = 'Searching...';
    searchInput.disabled = true;
    
    try {
        const headers = {
            'Content-Type': 'application/json'
        };
        
        const authToken = localStorage.getItem('authToken');
        if (authToken) {
            headers['Authorization'] = `Bearer ${authToken}`;
        }
        
        // Call smart search backend
        const response = await fetch('http://127.0.0.1:5000/api/smart-search', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({
                query: searchQuery,
                category: '',
                location: '',
                date_filter: '',
                min_match_score: 5
            }),
            credentials: 'include'
        });
        
        const result = await response.json();
        
        if (result.success && result.items.length > 0) {
            // Show search results directly on homepage
            showSearchResults(result.items, searchQuery);
        } else {
            const fallbackItems = await performSimpleHomeSearch(searchQuery);
            if (fallbackItems.length > 0) {
                showSearchResults(fallbackItems, searchQuery);
            } else {
                showNoResults(searchQuery);
            }
        }
        
    } catch (error) {
        console.error('Search error:', error);
        const fallbackItems = await performSimpleHomeSearch(searchQuery);
        if (fallbackItems.length > 0) {
            showSearchResults(fallbackItems, searchQuery);
        } else {
            showToast('Search failed. Please try again.', 'error');
        }
    } finally {
        // Restore input state
        searchInput.placeholder = originalPlaceholder;
        searchInput.disabled = false;
    }
}

async function performSimpleHomeSearch(query) {
    try {
        const headers = {};
        const authToken = localStorage.getItem('authToken');
        if (authToken) {
            headers['Authorization'] = `Bearer ${authToken}`;
        }
        
        const [foundResponse, lostResponse] = await Promise.all([
            fetch('http://127.0.0.1:5000/api/found-items', {
                headers: headers,
                credentials: 'include'
            }),
            fetch('http://127.0.0.1:5000/api/lost-items', {
                headers: headers,
                credentials: 'include'
            })
        ]);
        const foundResult = await foundResponse.json();
        const lostResult = await lostResponse.json();
        
        if (foundResult.success || lostResult.success) {
            const foundItems = (foundResult.items || []).map(item => ({ ...item, item_type: 'found' }));
            const lostItems = (lostResult.items || []).map(item => ({ ...item, item_type: 'lost' }));
            const items = [...foundItems, ...lostItems];
            const queryLower = query.toLowerCase();
            return items.filter(item => {
                const locationValue = item.location_found || item.location_lost || '';
                const searchText = `${item.item_name} ${item.description} ${locationValue} ${item.category}`.toLowerCase();
                return searchText.includes(queryLower);
            });
        }
        
        return [];
    } catch (error) {
        console.error('Simple search error:', error);
        return [];
    }
}

// Show search results on homepage
function showSearchResults(items, query) {
    const recentSection = document.getElementById('recentItemsSection');
    const searchSection = document.getElementById('search');
    
    // Hide recent items, show search area
    recentSection.style.display = 'block';
    searchSection.style.display = 'block';
    
    // Update recent items section to show search results
    const container = document.getElementById('recentItemsContainer');
    const header = recentSection.querySelector('.recent-items-header h2');
    
    header.textContent = `Search Results for: "${query}"`;
    
    if (items.length > 0) {
        const itemsHtml = items.map(item => {
            const isFound = item.item_type === 'found';
            const actionButton = isFound 
                ? `<button class="btn btn-warning btn-sm" onclick="openClaimModal(${item.id})">
                     <i class="fas fa-hand-holding"></i> Claim This Item
                   </button>`
                : `<button class="btn btn-info btn-sm" onclick="openFoundRequestModal(${item.id})">
                     <i class="fas fa-search-location"></i> I Found This
                   </button>`;

            return `
            <div class="col-md-4 mb-4">
                <div class="card h-100 shadow-sm">
                    <img src="${getItemImage(item)}" class="card-img-top item-image" alt="${item.item_name}"
                         onerror="this.src='https://via.placeholder.com/400x200?text=No+Image'">
                    <div class="card-body">
                        <h5 class="card-title">${item.item_name}</h5>
                        <p class="card-text description-truncate">${item.description.substring(0, 100)}${item.description.length > 100 ? '...' : ''}</p>
                        <div class="item-meta mb-2">
                            <span class="item-location">
                                <i class="fas fa-map-marker-alt"></i> ${getItemLocation(item)}
                            </span>
                            <br>
                            <span class="item-date">
                                <i class="fas fa-calendar"></i> ${formatDate(getItemDate(item))}
                            </span>
                        </div>
                        <div class="mt-2">
                            <span class="badge badge-primary">${item.category}</span>
                            ${getItemTypeBadge(item)}
                            <span class="badge badge-success ml-2">Match: ${item.match_score ? Math.round(item.match_score) : 'N/A'}%</span>
                        </div>
                        <div class="mt-2 text-right">
                             ${actionButton}
                        </div>
                    </div>
                </div>
            </div>
        `}).join('');
        
        container.innerHTML = `<div class="row">${itemsHtml}</div>`;
    } else {
        container.innerHTML = `
            <div class="no-items">
                <i class="fas fa-search fa-3x mb-3"></i>
                <h4>No items found for "${query}"</h4>
                <p>Try different keywords or browse recently reported items.</p>
                <button class="btn btn-primary mt-3" onclick="clearSearchResults()">
                    <i class="fas fa-arrow-left"></i> Back to Recent Items
                </button>
            </div>
        `;
    }
}

// Show no results message
function showNoResults(query) {
    const recentSection = document.getElementById('recentItemsSection');
    const searchSection = document.getElementById('search');
    
    recentSection.style.display = 'block';
    searchSection.style.display = 'block';
    
    const container = document.getElementById('recentItemsContainer');
    const header = recentSection.querySelector('.recent-items-header h2');
    
    header.textContent = `Search Results for: "${query}"`;
    
    container.innerHTML = `
        <div class="no-items">
            <i class="fas fa-search fa-3x mb-3"></i>
            <h4>No items found for "${query}"</h4>
            <p>Try different keywords or browse recently reported items.</p>
            <button class="btn btn-primary mt-3" onclick="clearSearchResults()">
                <i class="fas fa-arrow-left"></i> Back to Recent Items
            </button>
        </div>
    `;
}

// Clear search results and show recent items
function clearSearchResults() {
    const recentSection = document.getElementById('recentItemsSection');
    const searchSection = document.getElementById('search');
    const searchInput = document.getElementById('searchInput');
    
    // Clear search input
    searchInput.value = '';
    
    // Show recent items section
    recentSection.style.display = 'block';
    searchSection.style.display = 'block';
    
    // Reset header
    const header = recentSection.querySelector('.recent-items-header h2');
    header.textContent = 'Recently Reported Items';
    
    // Load recent items
    loadRecentItems();
}

// AI Category Suggestion
async function suggestCategory(descriptionId, categoryId) {
    const description = document.getElementById(descriptionId).value;
    const categorySelect = document.getElementById(categoryId);
    
    if (!description || description.trim().length < 5) {
        showToast('Please enter a more detailed description first.', 'warning');
        return;
    }
    
    // Show loading state
    const loadingOption = new Option('Analyzing...', '');
    categorySelect.add(loadingOption, 0);
    categorySelect.selectedIndex = 0;
    categorySelect.disabled = true;
    
    try {
        const response = await fetch('http://127.0.0.1:5000/api/predict-category', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ description: description })
        });
        
        const result = await response.json();
        
        // Remove loading option before selecting
        if (categorySelect.options[0].text === 'Analyzing...') {
            categorySelect.remove(0);
        }
        
        if (result.success) {
            // Find and select the predicted category
            let found = false;
            for (let i = 0; i < categorySelect.options.length; i++) {
                if (categorySelect.options[i].value === result.category) {
                    categorySelect.selectedIndex = i;
                    found = true;
                    break;
                }
            }
            
            if (found) {
                showToast(`Category suggested: ${result.category} (${Math.round(result.confidence * 100)}% confidence)`, 'success');
            } else {
                showToast(`Suggested category "${result.category}" not found in list.`, 'info');
            }
        } else {
            showToast('Could not suggest a category. Please select manually.', 'error');
        }
    } catch (error) {
        console.error('Category suggestion error:', error);
        // Remove loading option if it exists
        if (categorySelect.options[0].text === 'Analyzing...') {
            categorySelect.remove(0);
        }
        showToast('Error getting suggestion. Please select manually.', 'error');
    } finally {
        categorySelect.disabled = false;
    }
}

// Admin and Forms Functionality
document.addEventListener('DOMContentLoaded', () => {
    // Contact Form Handling
    const contactForm = document.getElementById('contactForm');
    if (contactForm) {
        contactForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const submitBtn = contactForm.querySelector('button[type="submit"]');
            const originalBtnText = submitBtn.innerHTML;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';

            const formData = {
                userName: document.getElementById('userName').value,
                userEmail: document.getElementById('userEmail').value,
                userMessage: document.getElementById('userMessage').value
            };

            try {
                const response = await fetch('http://127.0.0.1:5000/api/contact', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData)
                });

                const result = await response.json();
                
                if (result.success) {
                    showToast('Message sent successfully!', 'success');
                    contactForm.reset();
                } else {
                    showToast('Failed to send message: ' + result.message, 'error');
                }
            } catch (error) {
                console.error('Contact form error:', error);
                showToast('Server error. Please try again later.', 'error');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnText;
            }
        });
    }

    // Feedback Form Handling
    const feedbackForm = document.getElementById('feedback-form');
    if (feedbackForm) {
        feedbackForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const submitBtn = feedbackForm.querySelector('button[type="submit"]');
            const originalBtnText = submitBtn.innerHTML;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting...';

            const formData = {
                name: document.getElementById('name').value,
                email: document.getElementById('email').value,
                phone: document.getElementById('phone').value,
                comments: document.getElementById('comments').value
            };

            try {
                const response = await fetch('http://127.0.0.1:5000/api/feedback', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData)
                });

                const result = await response.json();
                
                if (result.success) {
                    showToast('Feedback submitted successfully!', 'success');
                    feedbackForm.reset();
                } else {
                    showToast('Failed to submit feedback: ' + result.message, 'error');
                }
            } catch (error) {
                console.error('Feedback form error:', error);
                showToast('Server error. Please try again later.', 'error');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnText;
            }
        });
    }
});

// Admin Dashboard Functions
async function checkAdminAccess() {
    const authToken = localStorage.getItem('authToken');
    if (!authToken) {
        window.location.href = 'index.html';
        return;
    }

    // Decode token to check admin status (client-side check only, server validates requests)
    try {
        const payload = JSON.parse(atob(authToken.split('.')[1]));
        if (!payload.is_admin) {
            window.location.href = 'index.html';
            return;
        }
    } catch (e) {
        window.location.href = 'index.html';
        return;
    }

    // Initial load
    loadAdminStats();
}

async function deleteItem(type, id) {
    // Beautiful alert using SweetAlert2
    const result = await Swal.fire({
        title: 'Are you sure?',
        text: "You won't be able to revert this!",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#e74a3b', // Bootstrap danger color
        cancelButtonColor: '#858796', // Bootstrap secondary color
        confirmButtonText: 'Yes, delete it!',
        cancelButtonText: 'Cancel',
        reverseButtons: true, // Cancel on left, Confirm on right
        focusCancel: true // Focus on cancel button by default for safety
    });

    if (!result.isConfirmed) {
        return;
    }

    const endpointMap = {
        'feedback': `feedbacks/${id}`,
        'message': `contact-messages/${id}`,
        'lost-item': `lost-items/${id}`,
        'found-item': `found-items/${id}`,
        'claim': `claims/${id}`,
        'found-request': `found-requests/${id}`,
        'claim-request': `claim-requests/${id}`
    };

    const endpoint = endpointMap[type];
    if (!endpoint) return;

    try {
        const authToken = localStorage.getItem('authToken');
        const response = await fetch(`http://127.0.0.1:5000/api/admin/${endpoint}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        const data = await response.json();
        
        if (data.success) {
            Swal.fire(
                'Deleted!',
                'The item has been deleted.',
                'success'
            );
            
            // Reload current section
            const currentSection = document.querySelector('.sidebar-link.active');
            if (currentSection) {
                const onclick = currentSection.getAttribute('onclick');
                if (onclick) {
                    // Extract section ID from onclick="...showSection('id', this)"
                    const match = onclick.match(/showSection\('([^']+)'/);
                    if (match && match[1]) {
                        const sectionId = match[1];
                        if (sectionId === 'feedbacks') loadFeedbacks();
                        else if (sectionId === 'messages') loadMessages();
                        else if (sectionId === 'lost-items') loadLostItems();
                        else if (sectionId === 'found-items') loadFoundItems();
                        else if (sectionId === 'claims') loadClaims();
                        loadAdminStats(); // Refresh stats too
                    }
                }
            }
        } else {
            Swal.fire(
                'Error!',
                'Failed to delete item: ' + data.message,
                'error'
            );
        }
    } catch (error) {
        console.error('Delete error:', error);
        Swal.fire(
            'Error!',
            'An error occurred while deleting the item.',
            'error'
        );
    }
}

async function verifyClaim(id) {
    const result = await Swal.fire({
        title: 'Verify Claim?',
        text: "This will mark the claim as verified.",
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#1cc88a',
        cancelButtonColor: '#858796',
        confirmButtonText: 'Yes, verify it!'
    });

    if (result.isConfirmed) {
        try {
            const authToken = localStorage.getItem('authToken');
            const response = await fetch(`http://127.0.0.1:5000/api/admin/claims/${id}/verify`, {
                method: 'PUT',
                headers: { 'Authorization': `Bearer ${authToken}` }
            });

            const data = await response.json();
            
            if (data.success) {
                Swal.fire('Verified!', 'The claim has been verified.', 'success');
                loadClaims();
                loadAdminStats();
            } else {
                Swal.fire('Error!', data.message, 'error');
            }
        } catch (error) {
            console.error('Verify error:', error);
            Swal.fire('Error!', 'An error occurred.', 'error');
        }
    }
}

async function rejectClaim(id) {
    const result = await Swal.fire({
        title: 'Reject Claim?',
        text: "This will mark the claim as rejected.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#e74a3b',
        cancelButtonColor: '#858796',
        confirmButtonText: 'Yes, reject it!'
    });

    if (result.isConfirmed) {
        try {
            const authToken = localStorage.getItem('authToken');
            const response = await fetch(`http://127.0.0.1:5000/api/admin/claims/${id}/reject`, {
                method: 'PUT',
                headers: { 'Authorization': `Bearer ${authToken}` }
            });

            const data = await response.json();
            
            if (data.success) {
                Swal.fire('Rejected!', 'The claim has been rejected.', 'success');
                loadClaims();
                loadAdminStats();
            } else {
                Swal.fire('Error!', data.message, 'error');
            }
        } catch (error) {
            console.error('Reject error:', error);
            Swal.fire('Error!', 'An error occurred.', 'error');
        }
    }
}

async function loadAdminStats() {
    try {
        const authToken = localStorage.getItem('authToken');
        
        // Fetch feedbacks count
        const feedResponse = await fetch('http://127.0.0.1:5000/api/admin/feedbacks', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (feedResponse.status === 401 || feedResponse.status === 403) {
            console.warn('Unauthorized access to admin stats. Redirecting to login.');
            logout();
            return;
        }

        const feedResult = await feedResponse.json();
        if (feedResult.success) {
            document.getElementById('total-feedbacks').textContent = feedResult.feedbacks.length;
        } else {
            console.error('Failed to load feedback stats:', feedResult.message);
        }

        // Fetch messages count
        const msgResponse = await fetch('http://127.0.0.1:5000/api/admin/contact-messages', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (msgResponse.status === 401 || msgResponse.status === 403) {
            logout(); // Should have been caught above, but just in case
            return;
        }

        const msgResult = await msgResponse.json();
        if (msgResult.success) {
            document.getElementById('total-messages').textContent = (msgResult.messages || []).length;
        } else {
             console.error('Failed to load message stats:', msgResult.message);
        }

        // Fetch lost items count
        const lostResponse = await fetch('http://127.0.0.1:5000/api/admin/lost-items', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const lostResult = await lostResponse.json();
        if (lostResult.success) {
            document.getElementById('total-lost').textContent = (lostResult.items || []).length;
        }

        // Fetch found items count
        const foundResponse = await fetch('http://127.0.0.1:5000/api/admin/found-items', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const foundResult = await foundResponse.json();
        if (foundResult.success) {
            document.getElementById('total-found').textContent = (foundResult.items || []).length;
        }

        // Fetch claims count
        const claimsResponse = await fetch('http://127.0.0.1:5000/api/admin/claims', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const claimsResult = await claimsResponse.json();
        if (claimsResult.success) {
            const totalClaims = (claimsResult.claims || []).length + (claimsResult.found_requests || []).length + (claimsResult.claim_requests || []).length;
            document.getElementById('total-claims').textContent = totalClaims;
        }

    } catch (error) {
        console.error('Error loading stats:', error);
        // Don't show toast on initial load error to avoid spamming if one fails
    }
}

async function loadFeedbacks() {
    const tbody = document.getElementById('feedbacks-table-body');
    tbody.innerHTML = '<tr><td colspan="6" class="text-center">Loading...</td></tr>';

    try {
        const authToken = localStorage.getItem('authToken');
        const response = await fetch('http://127.0.0.1:5000/api/admin/feedbacks', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        if (response.status === 401 || response.status === 403) {
            logout();
            return;
        }

        const result = await response.json();

        if (result.success) {
            if (result.feedbacks.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" class="text-center">No feedbacks found</td></tr>';
                return;
            }

            tbody.innerHTML = result.feedbacks.map(f => `
                <tr>
                    <td>${f.id}</td>
                    <td>${f.name || '-'}</td>
                    <td>${f.email || '-'}</td>
                    <td>${f.phone || '-'}</td>
                    <td>${f.comments}</td>
                    <td>${new Date(f.created_at).toLocaleDateString()}</td>
                    <td>
                        <button class="btn btn-danger btn-sm" onclick="deleteItem('feedback', ${f.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `).join('');
        } else {
             tbody.innerHTML = `<tr><td colspan="6" class="text-center text-danger">Error: ${result.message}</td></tr>`;
        }
    } catch (error) {
        console.error('Error loading feedbacks:', error);
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-danger">Error loading data. Please try again later.</td></tr>';
    }
}

async function loadMessages() {
    const tbody = document.getElementById('messages-table-body');
    tbody.innerHTML = '<tr><td colspan="5" class="text-center">Loading...</td></tr>';

    try {
        const authToken = localStorage.getItem('authToken');
        const response = await fetch('http://127.0.0.1:5000/api/admin/contact-messages', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.status === 401 || response.status === 403) {
            logout();
            return;
        }

        const result = await response.json();

        if (result.success) {
            if (result.messages.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="text-center">No messages found</td></tr>';
                return;
            }

            tbody.innerHTML = result.messages.map(m => `
                <tr>
                    <td>${m.id}</td>
                    <td>${m.user_name}</td>
                    <td>${m.user_email}</td>
                    <td>${m.message}</td>
                    <td>${new Date(m.created_at).toLocaleDateString()}</td>
                    <td>
                        <button class="btn btn-danger btn-sm" onclick="deleteItem('message', ${m.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `).join('');
        } else {
             tbody.innerHTML = `<tr><td colspan="5" class="text-center text-danger">Error: ${result.message}</td></tr>`;
        }
    } catch (error) {
        console.error('Error loading messages:', error);
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-danger">Error loading data. Please try again later.</td></tr>';
    }
}

async function logout() {
    try {
        // Call backend to clear cookies/session
        await fetch('http://127.0.0.1:5000/api/logout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include'
        });
    } catch (error) {
        console.error('Logout error:', error);
    } finally {
        // Always clear local storage and redirect
        localStorage.removeItem('authToken');
        window.location.href = 'index.html';
    }
}

async function loadLostItems() {
    const tbody = document.getElementById('lost-items-table-body');
    tbody.innerHTML = '<tr><td colspan="6" class="text-center">Loading...</td></tr>';

    try {
        const authToken = localStorage.getItem('authToken');
        const response = await fetch('http://127.0.0.1:5000/api/admin/lost-items', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        if (response.status === 401 || response.status === 403) {
            logout();
            return;
        }

        const result = await response.json();

        if (result.success) {
            if (result.items.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" class="text-center">No lost items found</td></tr>';
                return;
            }

            tbody.innerHTML = result.items.map(item => `
                <tr>
                    <td>${item.id}</td>
                    <td>${item.item_name}</td>
                    <td>
                        <div>${item.reported_by_name || 'Unknown'}</div>
                        <small class="text-muted">${item.reported_by_email || ''}</small>
                    </td>
                    <td><span class="badge badge-warning">${item.category}</span></td>
                    <td>${item.location_lost}</td>
                    <td>${item.date_lost}</td>
                    <td>${item.description.substring(0, 50)}${item.description.length > 50 ? '...' : ''}</td>
                    <td>
                        <button class="btn btn-danger btn-sm" onclick="deleteItem('lost-item', ${item.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `).join('');
        } else {
             tbody.innerHTML = `<tr><td colspan="6" class="text-center text-danger">Error: ${result.message}</td></tr>`;
        }
    } catch (error) {
        console.error('Error loading lost items:', error);
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-danger">Error loading data. Please try again later.</td></tr>';
    }
}

async function loadFoundItems() {
    const tbody = document.getElementById('found-items-table-body');
    tbody.innerHTML = '<tr><td colspan="7" class="text-center">Loading...</td></tr>';

    try {
        const authToken = localStorage.getItem('authToken');
        const response = await fetch('http://127.0.0.1:5000/api/admin/found-items', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        if (response.status === 401 || response.status === 403) {
            logout();
            return;
        }

        const result = await response.json();

        if (result.success) {
            if (result.items.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" class="text-center">No found items found</td></tr>';
                return;
            }

            tbody.innerHTML = result.items.map(item => `
                <tr>
                    <td>${item.id}</td>
                    <td>${item.item_name}</td>
                    <td>
                        <div>${item.reported_by_name || 'Unknown'}</div>
                        <small class="text-muted">${item.reported_by_email || ''}</small>
                    </td>
                    <td><span class="badge badge-info">${item.category}</span></td>
                    <td>${item.location_found}</td>
                    <td>${item.date_found}</td>
                    <td><span class="badge badge-${item.status === 'available' ? 'success' : 'secondary'}">${item.status}</span></td>
                    <td>
                        ${item.image_path ? `<img src="/founditems/${item.image_path}" alt="Item" style="height: 40px; border-radius: 4px;">` : '<span class="text-muted">No Img</span>'}
                    </td>
                    <td>
                        <button class="btn btn-danger btn-sm" onclick="deleteItem('found-item', ${item.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `).join('');
        } else {
             tbody.innerHTML = `<tr><td colspan="7" class="text-center text-danger">Error: ${result.message}</td></tr>`;
        }
    } catch (error) {
        console.error('Error loading found items:', error);
        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-danger">Error loading data. Please try again later.</td></tr>';
    }
}

async function loadClaims() {
    const tbody = document.getElementById('claims-table-body');
    tbody.innerHTML = '<tr><td colspan="6" class="text-center">Loading...</td></tr>';

    try {
        const authToken = localStorage.getItem('authToken');
        const response = await fetch('http://127.0.0.1:5000/api/admin/claims', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        if (response.status === 401 || response.status === 403) {
            logout();
            return;
        }

        const result = await response.json();

        if (result.success) {
            const claims = result.claims || [];
            const foundRequests = result.found_requests || [];
            const claimRequests = result.claim_requests || [];
            
            if (claims.length === 0 && foundRequests.length === 0 && claimRequests.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" class="text-center">No claims or requests found</td></tr>';
                return;
            }

            let html = '';
            
            // Add Claims (Verified/Processed)
            claims.forEach(claim => {
                html += `
                <tr>
                    <td><span class="badge badge-success">Verified Claim</span></td>
                    <td>${claim.item_name}</td>
                    <td>
                        <div>${claim.reported_by_name || 'Unknown'}</div>
                        <small class="text-muted">${claim.reported_by_email || ''}</small>
                    </td>
                    <td>
                        <div>${claim.claimed_by_name || 'Unknown'}</div>
                        <small class="text-muted">${claim.claimed_by_email || ''}</small>
                    </td>
                    <td><span class="badge badge-${claim.verification_status === 'verified' ? 'success' : claim.verification_status === 'rejected' ? 'danger' : 'warning'}">${claim.verification_status}</span></td>
                    <td>${claim.date_claimed || claim.created_at}</td>
                    <td>
                        <div class="btn-group" role="group">
                            ${claim.verification_status !== 'verified' ? 
                                `<button class="btn btn-success btn-sm" onclick="verifyClaim(${claim.id})" title="Verify">
                                    <i class="fas fa-check"></i>
                                </button>` : ''}
                            ${claim.verification_status !== 'rejected' ? 
                                `<button class="btn btn-warning btn-sm" onclick="rejectClaim(${claim.id})" title="Reject">
                                    <i class="fas fa-times"></i>
                                </button>` : ''}
                            <button class="btn btn-danger btn-sm" onclick="deleteItem('claim', ${claim.id})" title="Delete">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
                `;
            });
            
            // Add Found Requests (Someone found a lost item)
            foundRequests.forEach(req => {
                html += `
                <tr>
                    <td><span class="badge badge-primary">Found Report</span></td>
                    <td>${req.item_name}</td>
                    <td>
                        <div>${req.finder_name}</div>
                        <small class="text-muted">${req.finder_email}</small>
                    </td>
                    <td>-</td>
                    <td><span class="badge badge-info">New Report</span></td>
                    <td>${req.created_at}</td>
                    <td>
                        <button class="btn btn-danger btn-sm" onclick="deleteItem('found-request', ${req.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                </tr>
                `;
            });

            // Add Claim Requests (Someone wants to claim a found item)
            claimRequests.forEach(req => {
                html += `
                <tr>
                    <td><span class="badge badge-warning">Claim Request</span></td>
                    <td>${req.item_name}</td>
                    <td>-</td>
                    <td>
                        <div>${req.claimant_name}</div>
                        <small class="text-muted">${req.claimant_email}</small>
                    </td>
                    <td><span class="badge badge-info">Pending Review</span></td>
                    <td>${req.created_at}</td>
                    <td>
                        <button class="btn btn-danger btn-sm" onclick="deleteItem('claim-request', ${req.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                </tr>
                `;
            });

            tbody.innerHTML = html;
        } else {
             tbody.innerHTML = `<tr><td colspan="6" class="text-center text-danger">Error: ${result.message}</td></tr>`;
        }
    } catch (error) {
        console.error('Error loading claims:', error);
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-danger">Error loading data. Please try again later.</td></tr>';
    }
}
