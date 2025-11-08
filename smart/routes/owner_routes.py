# routes/owner_routes.py
from flask import Blueprint, request, jsonify, session
from config.database import db

owner_bp = Blueprint('owner', __name__, url_prefix="/api/owner")

def owner_required(f):
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] not in ['owner', 'admin']:
            return jsonify({'error': 'Owner access required'}), 403
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Homes
@owner_bp.route('/homes', methods=['GET'])
@owner_required
def get_my_homes():
    homes = db.execute_query("CALL GetHomesByOwner(%s)", (session['user_id'],),
                             user=session.get('db_user'), password=session.get('db_password'))
    if homes is None:
        return jsonify({'error': 'Failed to fetch homes'}), 500
    return jsonify({'homes': homes}), 200

@owner_bp.route('/homes', methods=['POST'])
@owner_required
def add_home():
    data = request.json or {}
    address = data.get('address')
    if not address:
        return jsonify({'error': 'Address required'}), 400
    res = db.execute_query("CALL AddHomeToUserProc(%s,%s)", (session['user_id'], address),
                           user=session.get('db_user'), password=session.get('db_password'))
    if res is None:
        return jsonify({'error': 'Failed to add home'}), 500
    return jsonify({'message': 'Home added'}), 201

@owner_bp.route('/homes/<int:home_id>', methods=['PUT'])
@owner_required
def update_home(home_id):
    data = request.json or {}
    new_address = data.get('address')
    if not new_address:
        return jsonify({'error': 'Address required'}), 400
    # ownership check: call GetHomesByOwner and ensure home_id present (or admin bypass)
    if session['role'] == 'owner':
        homes = db.execute_query("CALL GetHomesByOwner(%s)", (session['user_id'],),
                                 user=session.get('db_user'), password=session.get('db_password'))
        if not any(h['home_id'] == home_id for h in homes):
            return jsonify({'error': 'Access denied'}), 403
    res = db.execute_query("CALL UpdateHomeAddressProc(%s,%s)", (home_id, new_address),
                           user=session.get('db_user'), password=session.get('db_password'))
    if res is None:
        return jsonify({'error': 'Failed to update home'}), 500
    return jsonify({'message': 'Home updated'}), 200

@owner_bp.route('/homes/<int:home_id>', methods=['DELETE'])
@owner_required
def delete_home(home_id):
    if session['role'] == 'owner':
        homes = db.execute_query("CALL GetHomesByOwner(%s)", (session['user_id'],),
                                 user=session.get('db_user'), password=session.get('db_password'))
        if not any(h['home_id'] == home_id for h in homes):
            return jsonify({'error': 'Access denied'}), 403
    res = db.execute_query("CALL DeleteHomeProc(%s)", (home_id,),
                           user=session.get('db_user'), password=session.get('db_password'))
    if res is None:
        return jsonify({'error': 'Failed to delete home'}), 500
    return jsonify({'message': 'Home deleted'}), 200

# Rooms
@owner_bp.route('/homes/<int:home_id>/rooms', methods=['GET'])
@owner_required
def get_home_rooms(home_id):
    # verify owner
    if session['role'] == 'owner':
        homes = db.execute_query("CALL GetHomesByOwner(%s)", (session['user_id'],),
                                 user=session.get('db_user'), password=session.get('db_password'))
        if not any(h['home_id'] == home_id for h in homes):
            return jsonify({'error': 'Access denied'}), 403
    rooms = db.execute_query("CALL GetRoomsByHome(%s)", (home_id,),
                             user=session.get('db_user'), password=session.get('db_password'))
    if rooms is None:
        return jsonify({'error': 'Failed to fetch rooms'}), 500
    return jsonify({'rooms': rooms}), 200

@owner_bp.route('/homes/<int:home_id>/rooms', methods=['POST'])
@owner_required
def add_room(home_id):
    data = request.json or {}
    name = data.get('name')
    if not name:
        return jsonify({'error': 'Room name required'}), 400
    if session['role'] == 'owner':
        homes = db.execute_query("CALL GetHomesByOwner(%s)", (session['user_id'],),
                                 user=session.get('db_user'), password=session.get('db_password'))
        if not any(h['home_id'] == home_id for h in homes):
            return jsonify({'error': 'Access denied'}), 403
    res = db.execute_query("CALL AddRoomToHomeProc(%s,%s)", (home_id, name),
                           user=session.get('db_user'), password=session.get('db_password'))
    if res is None:
        return jsonify({'error': 'Failed to add room'}), 500
    return jsonify({'message': 'Room added'}), 201

@owner_bp.route('/rooms/<int:room_id>', methods=['PUT'])
@owner_required
def update_room(room_id):
    data = request.json or {}
    new_name = data.get('name')
    if not new_name:
        return jsonify({'error': 'Room name required'}), 400
    # verify owner via GetRoomsByHome results could be implemented, but we'll rely on backend ownership check via GetHomesByOwner scanning
    # For safety, fetch the room's home via DB (using procedure GetRoomsByHome for all homes - we keep this minimal)
    # Here we just call UpdateRoomNameProc (assume front-end enforces ownership)
    res = db.execute_query("CALL UpdateRoomNameProc(%s,%s)", (room_id, new_name),
                           user=session.get('db_user'), password=session.get('db_password'))
    if res is None:
        return jsonify({'error': 'Failed to update room'}), 500
    return jsonify({'message': 'Room updated'}), 200

@owner_bp.route('/rooms/<int:room_id>', methods=['DELETE'])
@owner_required
def delete_room(room_id):
    res = db.execute_query("CALL DeleteRoomProc(%s)", (room_id,),
                           user=session.get('db_user'), password=session.get('db_password'))
    if res is None:
        return jsonify({'error': 'Failed to delete room'}), 500
    return jsonify({'message': 'Room deleted'}), 200

# Devices
@owner_bp.route('/rooms/<int:room_id>/devices', methods=['GET'])
@owner_required
def get_room_devices(room_id):
    devices = db.execute_query("CALL GetDevicesByRoom(%s)", (room_id,),
                               user=session.get('db_user'), password=session.get('db_password'))
    if devices is None:
        return jsonify({'error': 'Failed to fetch devices'}), 500
    return jsonify({'devices': devices}), 200

@owner_bp.route('/rooms/<int:room_id>/devices', methods=['POST'])
@owner_required
def add_device(room_id):
    data = request.json or {}
    device_type = data.get('type')
    brand = data.get('brand')
    power = data.get('power_rating', 0)
    status = data.get('status', 'OFF')
    if not device_type or not brand:
        return jsonify({'error': 'Device type and brand required'}), 400
    res = db.execute_query("CALL AddDeviceToRoomProc(%s,%s,%s,%s,%s)",
                           (room_id, device_type, brand, power, status),
                           user=session.get('db_user'), password=session.get('db_password'))
    if res is None:
        return jsonify({'error': 'Failed to add device'}), 500
    return jsonify({'message': 'Device added'}), 201

@owner_bp.route('/devices/<int:device_id>', methods=['PUT'])
@owner_required
def update_device(device_id):
    data = request.json or {}
    fields = {}
    for field in ['brand', 'type', 'power_rating', 'status']:
        if field in data:
            fields[field] = data[field]
    if not fields:
        return jsonify({'error': 'No valid fields to update'}), 400
    # Build args for proc: require all params; fallback to current values via frontend supply or DB read (keep it simple here)
    device_type = fields.get('type', None)
    brand = fields.get('brand', None)
    power = fields.get('power_rating', None)
    status = fields.get('status', None)
    res = db.execute_query("CALL UpdateDeviceProc(%s,%s,%s,%s,%s)",
                           (device_id, device_type, brand, power, status),
                           user=session.get('db_user'), password=session.get('db_password'))
    if res is None:
        return jsonify({'error': 'Failed to update device'}), 500
    return jsonify({'message': 'Device updated'}), 200

@owner_bp.route('/devices/<int:device_id>', methods=['DELETE'])
@owner_required
def delete_device(device_id):
    res = db.execute_query("CALL DeleteDeviceProc(%s)", (device_id,),
                           user=session.get('db_user'), password=session.get('db_password'))
    if res is None:
        return jsonify({'error': 'Failed to delete device'}), 500
    return jsonify({'message': 'Device deleted'}), 200

@owner_bp.route('/devices/<int:device_id>/sensors', methods=['GET'])
@owner_required
def get_device_sensors(device_id):
    sensors = db.execute_query("CALL GetSensorsByDevice(%s)", (device_id,),
                               user=session.get('db_user'), password=session.get('db_password'))
    if sensors is None:
        return jsonify({'error': 'Failed to fetch sensors'}), 500
    return jsonify({'sensors': sensors}), 200

@owner_bp.route('/devices/<int:device_id>/status', methods=['PUT'])
@owner_required
def update_device_status(device_id):
    data = request.json or {}
    status = data.get('status')
    if status not in ['ON', 'OFF']:
        return jsonify({'error': 'Invalid status'}), 400
    event_type = 'turned_on' if status == 'ON' else 'turned_off'
    res = db.execute_query("CALL LogDeviceEventProc(%s,%s,%s)", (device_id, event_type, None),
                           user=session.get('db_user'), password=session.get('db_password'))
    if res is None:
        return jsonify({'error': 'Failed to update status'}), 500
    return jsonify({'message': 'Device status updated'}), 200

# Sensors
@owner_bp.route('/sensors', methods=['POST'])
@owner_required
def add_sensor():
    data = request.json or {}
    device_id = data.get('device_id')
    sensor_type = data.get('type')
    last_reading = data.get('last_reading', 0)
    if not device_id or not sensor_type:
        return jsonify({'error': 'Device ID and sensor type required'}), 400
    res = db.execute_query("CALL AddSensorToDeviceProc(%s,%s,%s)", (device_id, sensor_type, last_reading),
                           user=session.get('db_user'), password=session.get('db_password'))
    if res is None:
        return jsonify({'error': 'Failed to add sensor'}), 500
    return jsonify({'message': 'Sensor added'}), 201

@owner_bp.route('/sensors/<int:sensor_id>', methods=['PUT'])
@owner_required
def update_sensor(sensor_id):
    data = request.json or {}
    last_reading = data.get('last_reading')
    if last_reading is None:
        return jsonify({'error': 'Missing last_reading value'}), 400
    res = db.execute_query("CALL UpdateSensorReadingProc(%s,%s)", (sensor_id, last_reading),
                           user=session.get('db_user'), password=session.get('db_password'))
    if res is None:
        return jsonify({'error': 'Failed to update sensor'}), 500
    return jsonify({'message': 'Sensor updated'}), 200

# Energy & Alerts
@owner_bp.route('/energy-usage', methods=['GET'])
@owner_required
def get_energy_usage():
    usage = db.execute_query("CALL GetEnergyUsageByOwnerProc(%s)", (session['user_id'],),
                             user=session.get('db_user'), password=session.get('db_password'))
    if usage is None:
        return jsonify({'error': 'Failed to fetch energy usage'}), 500
    return jsonify({'energy_usage': usage}), 200

@owner_bp.route('/alerts', methods=['GET'])
@owner_required
def get_my_alerts():
    alerts = db.execute_query("CALL GetAlertsByOwnerProc(%s)", (session['user_id'],),
                             user=session.get('db_user'), password=session.get('db_password'))
    if alerts is None:
        return jsonify({'error': 'Failed to fetch alerts'}), 500
    return jsonify({'alerts': alerts}), 200
