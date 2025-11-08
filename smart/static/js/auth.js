// auth.js

// Check if already logged in
window.addEventListener('load', async () => {
    try {
        const response = await fetch('/api/auth/check-session');
        const data = await response.json();
        
        if (data.logged_in) {
            window.location.href = '/dashboard';
        }
    } catch (error) {
        console.error('Session check error:', error);
    }
});

// Login form submission
document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    const errorDiv = document.getElementById('login-error');
    
    errorDiv.textContent = '';
    
    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Redirect to dashboard
            window.location.href = '/dashboard';
        } else {
            errorDiv.textContent = data.error || 'Login failed';
        }
    } catch (error) {
        errorDiv.textContent = 'Network error. Please try again.';
        console.error('Login error:', error);
    }
});