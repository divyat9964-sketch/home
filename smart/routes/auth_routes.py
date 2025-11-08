# auth_routes.py
from flask import Blueprint, request, jsonify, session
from config.database import db

auth_bp = Blueprint('auth', __name__, url_prefix="/api/auth")

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json or {}
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400

    # Simple query - no password hashing
    rows = db.execute_query(
        "SELECT user_id, name, role, email FROM `User` WHERE email = %s AND password = %s", 
        (email, password)
    )
    
    if not rows or len(rows) == 0:
        return jsonify({'error': 'Invalid credentials'}), 401

    user = rows[0]

    # Set session
    session['user_id'] = user['user_id']
    session['name'] = user['name']
    session['role'] = user['role']
    session['email'] = user['email']

    # Set DB credentials by role
    if user['role'] == 'admin':
        session['db_user'] = 'root'
        session['db_password'] = 'divyat9731'
    elif user['role'] == 'owner':
        session['db_user'] = 'root'
        session['db_password'] = 'divyat9731'
    else:
        session['db_user'] = 'root'
        session['db_password'] = 'divyat9731'

    return jsonify({
        'message': 'Login successful',
        'user': {
            'user_id': user['user_id'],
            'name': user['name'],
            'role': user['role'],
            'email': user['email']
        }
    }), 200

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logout successful'}), 200

@auth_bp.route('/check-session', methods=['GET'])
def check_session():
    if 'user_id' in session:
        return jsonify({
            'logged_in': True,
            'user': {
                'user_id': session['user_id'],
                'name': session['name'],
                'role': session['role'],
                'email': session['email']
            }
        }), 200
    return jsonify({'logged_in': False}), 200