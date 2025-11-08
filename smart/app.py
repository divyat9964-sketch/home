from flask import Flask, render_template, session, redirect, url_for
from flask_cors import CORS
import os
import sys

# Print Python path for debugging
print("Python version:", sys.version)
print("Current directory:", os.getcwd())
print("Python path:", sys.path)

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'
CORS(app)

# Import routes with error handling
try:
    from routes.auth_routes import auth_bp
    print("✓ Successfully imported auth_routes")
except Exception as e:
    print(f"✗ Error importing auth_routes: {e}")
    sys.exit(1)

try:
    from routes.admin_routes import admin_bp
    print("✓ Successfully imported admin_routes")
except Exception as e:
    print(f"✗ Error importing admin_routes: {e}")
    sys.exit(1)

try:
    from routes.owner_routes import owner_bp
    print("✓ Successfully imported owner_routes")
except Exception as e:
    print(f"✗ Error importing owner_routes: {e}")
    sys.exit(1)

try:
    from routes.guest_routes import guest_bp
    print("✓ Successfully imported guest_routes")
except Exception as e:
    print(f"✗ Error importing guest_routes: {e}")
    sys.exit(1)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(owner_bp, url_prefix='/api/owner')
app.register_blueprint(guest_bp, url_prefix='/api/guest')

print("✓ All blueprints registered successfully")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template('dashboard.html')

if __name__ == '__main__':
    print("\n" + "="*50)
    print("Starting Flask application...")
    print("Access the application at: http://localhost:5000")
    print("="*50 + "\n")
    app.run(debug=True, port=5000)