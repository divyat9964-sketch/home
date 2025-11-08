from flask import Blueprint, request, jsonify, session
from config.database import db

admin_bp = Blueprint('admin', __name__, url_prefix="/api/admin")

def admin_required(f):
    """Decorator to check if user is admin"""
    def wrapper(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

@admin_bp.route('/register-user', methods=['POST'])
@admin_required
def register_user():
    """Admin can register new owners and guests"""
    data = request.json or {}
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'guest')
    phone = data.get('phone', '')

    if not name or not email or not password:
        return jsonify({'error': 'Name, email, and password are required'}), 400

    if role not in ['owner', 'guest']:
        return jsonify({'error': 'Role must be owner or guest'}), 400

    # Check if email already exists
    rows = db.execute_query("SELECT user_id FROM `User` WHERE email = %s", (email,))
    if rows and len(rows) > 0:
        return jsonify({'error': 'Email already registered'}), 400

    # Insert user with plain password (no hashing)
    insert_res = db.execute_query(
        "INSERT INTO `User` (name, role, email, phone, password) VALUES (%s,%s,%s,%s,%s)",
        (name, role, email, phone, password)
    )
    
    if insert_res is None:
        return jsonify({'error': 'User registration failed'}), 500

    return jsonify({
        'message': 'User registered successfully',
        'user_id': insert_res
    }), 201

@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_all_users():
    """Get all users"""
    rows = db.execute_query("SELECT user_id, name, role, email, phone FROM `User` ORDER BY user_id")
    return jsonify({'users': rows or []}), 200

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """Delete a user"""
    result = db.execute_query("DELETE FROM `User` WHERE user_id = %s", (user_id,))
    if result:
        return jsonify({'message': 'User deleted successfully'}), 200
    return jsonify({'error': 'Failed to delete user'}), 500

@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    """Update user details"""
    data = request.json or {}
    name = data.get('name')
    email = data.get('email')
    phone = data.get('phone')
    password = data.get('password')
    role = data.get('role')

    updates = []
    params = []
    
    if name:
        updates.append("name = %s")
        params.append(name)
    if email:
        updates.append("email = %s")
        params.append(email)
    if phone:
        updates.append("phone = %s")
        params.append(phone)
    if password:
        updates.append("password = %s")
        params.append(password)
    if role and role in ['owner', 'guest', 'admin']:
        updates.append("role = %s")
        params.append(role)
    
    if not updates:
        return jsonify({'error': 'No fields to update'}), 400
    
    params.append(user_id)
    query = f"UPDATE `User` SET {', '.join(updates)} WHERE user_id = %s"
    
    result = db.execute_query(query, tuple(params))
    if result is not None:
        return jsonify({'message': 'User updated successfully'}), 200
    return jsonify({'error': 'Failed to update user'}), 500
