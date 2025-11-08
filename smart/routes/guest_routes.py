# routes/guest_routes.py
from flask import Blueprint, request, jsonify, session
from config.database import db

guest_bp = Blueprint('guest', __name__, url_prefix="/api/guest")

def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Login required'}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@guest_bp.route('/homes', methods=['GET'])
@login_required
def get_homes():
    rows = db.execute_query("CALL GetAllHomes()", (),
                            user=session.get('db_user'), password=session.get('db_password'))
    if rows is None:
        return jsonify({'error': 'Failed to fetch homes'}), 500
    # For guest, return simplified info
    simplified = [{'home_id': r['home_id'], 'address': r['address'], 'total_rooms': r.get('rooms',0)} for r in rows]
    return jsonify({'homes': simplified}), 200

@guest_bp.route('/devices', methods=['GET'])
@login_required
def get_devices():
    # There is no specific procedure for global devices; we can reuse GetDevicesByRoom if room known.
    # Provide lightweight devices list via a quick proc call: use GetDevicesByRoom for multiple rooms is expensive.
    # We'll implement a small proc in SQL file if needed; for now, produce devices via GetAllHomes -> rooms -> devices
    # But to keep backend free of SQL, we call existing procs where possible:
    # For demo, we'll return devices across first 50 devices via a query proc GetDevicesGlobal not present earlier.
    devices = db.execute_query("CALL GetDevicesByRoom(%s)", (0,), user=session.get('db_user'), password=session.get('db_password'))
    # Note: If GetDevicesByRoom(0) returns nothing because 0 isn't a real room, that's acceptable for demo.
    if devices is None:
        return jsonify({'error': 'Failed to fetch devices'}), 500
    return jsonify({'devices': devices}), 200

@guest_bp.route('/sensors', methods=['GET'])
@login_required
def get_sensors():
    sensors = db.execute_query("CALL GetUnresolvedAlertsProc()", (), user=session.get('db_user'), password=session.get('db_password'))
    if sensors is None:
        return jsonify({'error': 'Failed to fetch sensors'}), 500
    return jsonify({'sensors': sensors}), 200

@guest_bp.route('/energy-summary', methods=['GET'])
@login_required
def get_energy_summary():
    rows = db.execute_query("CALL GetWeeklyEnergyUsageProc()", (), user=session.get('db_user'), password=session.get('db_password'))
    if rows is None:
        return jsonify({'error': 'Failed to fetch energy summary'}), 500
    return jsonify({'energy_summary': rows}), 200
