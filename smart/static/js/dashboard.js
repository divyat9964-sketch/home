// Global user variable
let currentUser = null;

// Check session and load appropriate dashboard
window.addEventListener('load', async () => {
    try {
        const response = await fetch('/api/auth/check-session');
        const data = await response.json();
        
        if (!data.logged_in) {
            window.location.href = '/';
            return;
        }
        
        currentUser = data.user;
        
        // Update UI with user info
        document.getElementById('userName').textContent = currentUser.name;
        document.getElementById('userRole').textContent = currentUser.role.charAt(0).toUpperCase() + currentUser.role.slice(1);
        
        // Load appropriate dashboard based on role
        if (currentUser.role === 'admin') {
            loadAdminDashboard();
        } else if (currentUser.role === 'owner') {
            loadOwnerDashboard();
        } else if (currentUser.role === 'guest') {
            loadGuestDashboard();
        }
    } catch (error) {
        console.error('Session check error:', error);
        window.location.href = '/';
    }
});

// Logout function
async function logout() {
    try {
        await fetch('/api/auth/logout', { method: 'POST' });
        window.location.href = '/';
    } catch (error) {
        console.error('Logout error:', error);
        alert('Logout failed. Please try again.');
    }
}

// ==================== ADMIN DASHBOARD ====================
function loadAdminDashboard() {
    const content = document.getElementById('dashboardContent');
    content.innerHTML = `
        <div class="admin-dashboard">
            <h2>Admin Dashboard</h2>
            
            <!-- User Management Section -->
            <div class="dashboard-section">
                <h3>User Management</h3>
                <button onclick="showRegisterUserModal()" class="btn btn-primary">Register New User</button>
                <div id="usersList" class="data-list"></div>
            </div>
            
            <!-- System Overview -->
            <div class="dashboard-section">
                <h3>System Overview</h3>
                <div id="systemStats" class="stats-grid"></div>
            </div>
        </div>
        
        <!-- Register User Modal -->
        <div id="registerModal" class="modal" style="display: none;">
            <div class="modal-content">
                <span class="close" onclick="closeRegisterModal()">&times;</span>
                <h3>Register New User</h3>
                <form id="adminRegisterForm">
                    <div class="form-group">
                        <label for="reg-name">Name</label>
                        <input type="text" id="reg-name" required />
                    </div>
                    <div class="form-group">
                        <label for="reg-email">Email</label>
                        <input type="email" id="reg-email" required />
                    </div>
                    <div class="form-group">
                        <label for="reg-password">Password</label>
                        <input type="password" id="reg-password" required />
                    </div>
                    <div class="form-group">
                        <label for="reg-phone">Phone</label>
                        <input type="tel" id="reg-phone" />
                    </div>
                    <div class="form-group">
                        <label for="reg-role">Role</label>
                        <select id="reg-role">
                            <option value="owner">Owner</option>
                            <option value="guest">Guest</option>
                        </select>
                    </div>
                    <button type="submit" class="btn btn-primary">Register User</button>
                    <div id="reg-error" class="error-message"></div>
                    <div id="reg-success" class="success-message"></div>
                </form>
            </div>
        </div>
    `;
    
    loadAllUsers();
    loadSystemStats();
    setupAdminRegisterForm();
}

function showRegisterUserModal() {
    document.getElementById('registerModal').style.display = 'block';
}

function closeRegisterModal() {
    document.getElementById('registerModal').style.display = 'none';
    document.getElementById('adminRegisterForm').reset();
    document.getElementById('reg-error').textContent = '';
    document.getElementById('reg-success').textContent = '';
}

function setupAdminRegisterForm() {
    document.getElementById('adminRegisterForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const name = document.getElementById('reg-name').value;
        const email = document.getElementById('reg-email').value;
        const password = document.getElementById('reg-password').value;
        const phone = document.getElementById('reg-phone').value;
        const role = document.getElementById('reg-role').value;
        
        const errorDiv = document.getElementById('reg-error');
        const successDiv = document.getElementById('reg-success');
        
        errorDiv.textContent = '';
        successDiv.textContent = '';
        
        try {
            const response = await fetch('/api/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, email, password, phone, role })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                successDiv.textContent = 'User registered successfully!';
                document.getElementById('adminRegisterForm').reset();
                setTimeout(() => {
                    closeRegisterModal();
                    loadAllUsers();
                }, 1500);
            } else {
                errorDiv.textContent = data.error || 'Registration failed';
            }
        } catch (error) {
            errorDiv.textContent = 'Network error. Please try again.';
            console.error('Registration error:', error);
        }
    });
}

async function loadAllUsers() {
    try {
        const response = await fetch('/api/admin/users');
        const data = await response.json();
        
        const usersList = document.getElementById('usersList');
        if (data && data.length > 0) {
            usersList.innerHTML = `
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Email</th>
                            <th>Role</th>
                            <th>Phone</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.map(user => `
                            <tr>
                                <td>${user.name}</td>
                                <td>${user.email}</td>
                                <td>${user.role}</td>
                                <td>${user.phone || 'N/A'}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        } else {
            usersList.innerHTML = '<p>No users found</p>';
        }
    } catch (error) {
        console.error('Error loading users:', error);
    }
}

async function loadSystemStats() {
    const statsDiv = document.getElementById('systemStats');
    statsDiv.innerHTML = '<p>Loading system statistics...</p>';
    // Add your admin stats API calls here
}

// ==================== OWNER DASHBOARD ====================
function loadOwnerDashboard() {
    const content = document.getElementById('dashboardContent');
    content.innerHTML = `
        <div class="owner-dashboard">
            <h2>Owner Dashboard</h2>
            
            <div class="dashboard-section">
                <h3>My Homes</h3>
                <div id="homesList" class="data-list"></div>
            </div>
            
            <div class="dashboard-section">
                <h3>Energy Usage</h3>
                <div id="energyUsage" class="data-list"></div>
            </div>
            
            <div class="dashboard-section">
                <h3>Alerts</h3>
                <div id="alertsList" class="data-list"></div>
            </div>
        </div>
    `;
    
    loadOwnerHomes();
    loadOwnerEnergy();
    loadOwnerAlerts();
}

async function loadOwnerHomes() {
    try {
        const response = await fetch('/api/owner/homes');
        const data = await response.json();
        
        const homesList = document.getElementById('homesList');
        if (data && data.length > 0) {
            homesList.innerHTML = `
                <div class="homes-grid">
                    ${data.map(home => `
                        <div class="home-card">
                            <h4>${home.address}</h4>
                            <p>Type: ${home.home_type}</p>
                            <p>Square Feet: ${home.square_feet}</p>
                        </div>
                    `).join('')}
                </div>
            `;
        } else {
            homesList.innerHTML = '<p>No homes found</p>';
        }
    } catch (error) {
        console.error('Error loading homes:', error);
        document.getElementById('homesList').innerHTML = '<p class="error">Error loading homes</p>';
    }
}

async function loadOwnerEnergy() {
    try {
        const response = await fetch('/api/owner/energy-usage');
        const data = await response.json();
        
        const energyDiv = document.getElementById('energyUsage');
        if (data && data.length > 0) {
            energyDiv.innerHTML = `
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Energy (kWh)</th>
                            <th>Cost</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.map(item => `
                            <tr>
                                <td>${new Date(item.date).toLocaleDateString()}</td>
                                <td>${item.energy_kwh}</td>
                                <td>$${item.cost}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        } else {
            energyDiv.innerHTML = '<p>No energy data available</p>';
        }
    } catch (error) {
        console.error('Error loading energy usage:', error);
        document.getElementById('energyUsage').innerHTML = '<p class="error">Error loading energy data</p>';
    }
}

async function loadOwnerAlerts() {
    try {
        const response = await fetch('/api/owner/alerts');
        const data = await response.json();
        
        const alertsDiv = document.getElementById('alertsList');
        if (data && data.length > 0) {
            alertsDiv.innerHTML = `
                <div class="alerts-list">
                    ${data.map(alert => `
                        <div class="alert-card ${alert.severity}">
                            <h4>${alert.alert_type}</h4>
                            <p>${alert.message}</p>
                            <small>${new Date(alert.timestamp).toLocaleString()}</small>
                        </div>
                    `).join('')}
                </div>
            `;
        } else {
            alertsDiv.innerHTML = '<p>No alerts</p>';
        }
    } catch (error) {
        console.error('Error loading alerts:', error);
        document.getElementById('alertsList').innerHTML = '<p class="error">Error loading alerts</p>';
    }
}

// ==================== GUEST DASHBOARD ====================
function loadGuestDashboard() {
    const content = document.getElementById('dashboardContent');
    content.innerHTML = `
        <div class="guest-dashboard">
            <h2>Guest Dashboard</h2>
            
            <div class="dashboard-section">
                <h3>Sensor Data</h3>
                <div id="sensorsData" class="data-list"></div>
            </div>
            
            <div class="dashboard-section">
                <h3>Active Alerts</h3>
                <div id="guestAlerts" class="data-list"></div>
            </div>
        </div>
    `;
    
    loadGuestSensors();
    loadGuestAlerts();
}

async function loadGuestSensors() {
    try {
        const response = await fetch('/api/guest/sensors');
        const data = await response.json();
        
        const sensorsDiv = document.getElementById('sensorsData');
        if (data && data.length > 0) {
            sensorsDiv.innerHTML = `
                <div class="sensors-grid">
                    ${data.map(sensor => `
                        <div class="sensor-card">
                            <h4>${sensor.sensor_type}</h4>
                            <p>Location: ${sensor.location}</p>
                            <p>Value: ${sensor.value}</p>
                        </div>
                    `).join('')}
                </div>
            `;
        } else {
            sensorsDiv.innerHTML = '<p>No sensor data available</p>';
        }
    } catch (error) {
        console.error('Error loading sensors:', error);
        document.getElementById('sensorsData').innerHTML = '<p class="error">Error loading sensor data</p>';
    }
}

async function loadGuestAlerts() {
    try {
        const response = await fetch('/api/guest/alerts');
        const data = await response.json();
        
        const alertsDiv = document.getElementById('guestAlerts');
        if (data && data.length > 0) {
            alertsDiv.innerHTML = `
                <div class="alerts-list">
                    ${data.map(alert => `
                        <div class="alert-card ${alert.severity}">
                            <h4>${alert.alert_type}</h4>
                            <p>${alert.message}</p>
                        </div>
                    `).join('')}
                </div>
            `;
        } else {
            alertsDiv.innerHTML = '<p>No active alerts</p>';
        }
    } catch (error) {
        console.error('Error loading alerts:', error);
        document.getElementById('guestAlerts').innerHTML = '<p class="error">Error loading alerts</p>';
    }
}