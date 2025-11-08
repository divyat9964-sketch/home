-- =====================================================
-- SMART HOME DATABASE (FINAL VERSION)
-- Author: Divya
-- Purpose: Role-based smart home management with alerts, 
--          devices, sensors, energy tracking, and automation.
-- =====================================================

CREATE DATABASE IF NOT EXISTS SmartHomeDB;
USE SmartHomeDB;

-- =====================================================
-- USERS
-- =====================================================
CREATE TABLE IF NOT EXISTS `User` (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL,
    role VARCHAR(20) CHECK (role IN ('owner','guest','admin')),
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(15),
    password VARCHAR(255) DEFAULT NULL;
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- HOMES, ROOMS, DEVICES, SENSORS
-- =====================================================
CREATE TABLE IF NOT EXISTS Home (
    home_id INT PRIMARY KEY AUTO_INCREMENT,
    address VARCHAR(200) NOT NULL,
    owner_id INT,
    FOREIGN KEY (owner_id) REFERENCES `User`(user_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Room (
    room_id INT PRIMARY KEY AUTO_INCREMENT,
    home_id INT NOT NULL,
    name VARCHAR(50),
    FOREIGN KEY (home_id) REFERENCES Home(home_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Device (
    device_id INT PRIMARY KEY AUTO_INCREMENT,
    room_id INT NOT NULL,
    type VARCHAR(30) NOT NULL,
    brand VARCHAR(30),
    power_rating DECIMAL(7,2),
    status VARCHAR(10) CHECK (status IN ('ON','OFF')),
    FOREIGN KEY (room_id) REFERENCES Room(room_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Sensor (
    sensor_id INT PRIMARY KEY AUTO_INCREMENT,
    device_id INT NOT NULL,
    type VARCHAR(30) NOT NULL,
    last_reading DECIMAL(10,2),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES Device(device_id)
        ON DELETE CASCADE
);

-- =====================================================
-- LOGS, ALERTS, ENERGY USAGE
-- =====================================================
CREATE TABLE IF NOT EXISTS EventLog (
    event_id INT PRIMARY KEY AUTO_INCREMENT,
    device_id INT,
    event_type VARCHAR(100),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    value DECIMAL(10,2),
    FOREIGN KEY (device_id) REFERENCES Device(device_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS AutomationRule (
    rule_id INT PRIMARY KEY AUTO_INCREMENT,
    home_id INT NOT NULL,
    created_by INT NOT NULL,
    trigger_condition VARCHAR(200),
    action VARCHAR(200),
    priority INT,
    FOREIGN KEY (home_id) REFERENCES Home(home_id)
        ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES `User`(user_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Alert (
    alert_id INT PRIMARY KEY AUTO_INCREMENT,
    sensor_id INT NOT NULL,
    alert_type VARCHAR(100),
    severity VARCHAR(20) CHECK (severity IN ('Low','Medium','High')),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (sensor_id) REFERENCES Sensor(sensor_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS EnergyUsage (
    usage_id INT PRIMARY KEY AUTO_INCREMENT,
    device_id INT NOT NULL,
    room_id INT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    energy_consumed DECIMAL(10,2),
    cost DECIMAL(10,2),
    FOREIGN KEY (device_id) REFERENCES Device(device_id)
        ON DELETE CASCADE,
    FOREIGN KEY (room_id) REFERENCES Room(room_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS MaintenanceLog (
    maintenance_id INT PRIMARY KEY AUTO_INCREMENT,
    device_id INT NOT NULL,
    description VARCHAR(255),
    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES Device(device_id)
        ON DELETE CASCADE
);

-- =====================================================
-- INDEXES
-- =====================================================
CREATE INDEX idx_room_home_id ON Room(home_id);
CREATE INDEX idx_device_room_id ON Device(room_id);
CREATE INDEX idx_sensor_device_id ON Sensor(device_id);
CREATE INDEX idx_alert_sensor_id ON Alert(sensor_id);
CREATE INDEX idx_home_owner_id ON Home(owner_id);

-- =====================================================
-- TRIGGERS
-- =====================================================
DELIMITER //

CREATE TRIGGER trg_high_temp_alert_insert
AFTER INSERT ON Sensor
FOR EACH ROW
BEGIN
    IF NEW.type = 'temperature' AND NEW.last_reading > 30 THEN
        INSERT INTO Alert(sensor_id, alert_type, severity, timestamp, resolved)
        VALUES (NEW.sensor_id, 'High Temperature', 'High', NOW(), FALSE);
    END IF;
END //

CREATE TRIGGER trg_high_temp_alert_update
AFTER UPDATE ON Sensor
FOR EACH ROW
BEGIN
    IF NEW.type = 'temperature' AND NEW.last_reading > 30 THEN
        INSERT INTO Alert(sensor_id, alert_type, severity, timestamp, resolved)
        VALUES (NEW.sensor_id, 'High Temperature', 'High', NOW(), FALSE);
    END IF;
END //

CREATE TRIGGER trg_update_device_status
AFTER INSERT ON EventLog
FOR EACH ROW
BEGIN
    IF NEW.event_type = 'turned_on' THEN
        UPDATE Device SET status = 'ON' WHERE device_id = NEW.device_id;
    ELSEIF NEW.event_type = 'turned_off' THEN
        UPDATE Device SET status = 'OFF' WHERE device_id = NEW.device_id;
    END IF;
END //

CREATE TRIGGER trg_energy_usage_log
AFTER INSERT ON EventLog
FOR EACH ROW
BEGIN
    IF NEW.event_type = 'usage' THEN
        INSERT INTO EnergyUsage(device_id, room_id, timestamp, energy_consumed, cost)
        SELECT d.device_id, d.room_id, NOW(), NEW.value, NEW.value * 6.0
        FROM Device d WHERE d.device_id = NEW.device_id;
    END IF;
END //

CREATE TRIGGER trg_rule_audit
AFTER INSERT ON AutomationRule
FOR EACH ROW
BEGIN
    INSERT INTO EventLog(device_id, event_type, timestamp, value)
    VALUES (NULL, CONCAT('Rule Created: ', NEW.action), NOW(), NULL);
END //

CREATE TRIGGER trg_device_maintenance
AFTER UPDATE ON Device
FOR EACH ROW
BEGIN
    IF NEW.status <> OLD.status THEN
        INSERT INTO MaintenanceLog(device_id, description)
        VALUES (NEW.device_id, CONCAT('Device status changed to ', NEW.status));
    END IF;
END //
DELIMITER ;

-- =====================================================
-- FUNCTIONS
-- =====================================================
DELIMITER //
CREATE FUNCTION GetDeviceCost(dev_id INT)
RETURNS DECIMAL(10,2)
DETERMINISTIC
BEGIN
    DECLARE total DECIMAL(10,2);
    SELECT SUM(cost) INTO total FROM EnergyUsage WHERE device_id = dev_id;
    RETURN IFNULL(total,0);
END //

CREATE FUNCTION CountHomeAlerts(hid INT)
RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE cnt INT;
    SELECT COUNT(a.alert_id)
    INTO cnt
    FROM Alert a
    JOIN Sensor s ON a.sensor_id = s.sensor_id
    JOIN Device d ON s.device_id = d.device_id
    JOIN Room r ON d.room_id = r.room_id
    WHERE r.home_id = hid;
    RETURN cnt;
END //
DELIMITER ;

-- =====================================================
-- STORED PROCEDURES
-- =====================================================
DELIMITER //

-- --- User Authentication ---
CREATE PROCEDURE GetUserByEmail(IN p_email VARCHAR(100))
BEGIN
    SELECT user_id, name, role, email, phone, password_hash
    FROM `User`
    WHERE email = p_email;
END //

CREATE PROCEDURE RegisterUser(
    IN p_name VARCHAR(50),
    IN p_role VARCHAR(20),
    IN p_email VARCHAR(100),
    IN p_phone VARCHAR(15),
    IN p_password_hash VARCHAR(255)
)
BEGIN
    INSERT INTO `User` (name, role, email, phone, password_hash)
    VALUES (p_name, p_role, p_email, p_phone, p_password_hash);
    SELECT LAST_INSERT_ID() AS user_id;
END //

CREATE PROCEDURE ResetUserPassword(
    IN p_user_id INT,
    IN p_password_hash VARCHAR(255)
)
BEGIN
    UPDATE `User` SET password_hash = p_password_hash WHERE user_id = p_user_id;
END //

-- --- Admin / Overview ---
CREATE PROCEDURE GetSystemOverview()
BEGIN
    SELECT 'users' AS metric, COUNT(*) AS cnt FROM `User`
    UNION ALL
    SELECT 'homes', COUNT(*) FROM Home
    UNION ALL
    SELECT 'rooms', COUNT(*) FROM Room
    UNION ALL
    SELECT 'devices', COUNT(*) FROM Device
    UNION ALL
    SELECT 'alerts_unresolved', COUNT(*) FROM Alert WHERE resolved = FALSE
    UNION ALL
    SELECT 'rules', COUNT(*) FROM AutomationRule;
END //

CREATE PROCEDURE GetAllHomes()
BEGIN
    SELECT h.home_id, h.address, h.owner_id, u.name AS owner_name,
           (SELECT COUNT(*) FROM Room r WHERE r.home_id = h.home_id) AS rooms,
           (SELECT COUNT(*) FROM Device d 
             JOIN Room r2 ON d.room_id = r2.room_id 
             WHERE r2.home_id = h.home_id) AS devices
    FROM Home h
    LEFT JOIN `User` u ON h.owner_id = u.user_id
    ORDER BY h.home_id;
END //

CREATE PROCEDURE GetAlertsRecent()
BEGIN
    SELECT a.alert_id, a.alert_type, a.severity, a.timestamp, a.resolved,
           s.sensor_id, s.type AS sensor_type, h.home_id, h.address
    FROM Alert a
    JOIN Sensor s ON a.sensor_id = s.sensor_id
    JOIN Device d ON s.device_id = d.device_id
    JOIN Room r ON d.room_id = r.room_id
    JOIN Home h ON r.home_id = h.home_id
    ORDER BY a.timestamp DESC
    LIMIT 200;
END //

CREATE PROCEDURE ResolveAlertProc(IN p_alert_id INT)
BEGIN
    UPDATE Alert SET resolved = TRUE WHERE alert_id = p_alert_id;
END //

-- --- Owner-specific Operations ---
CREATE PROCEDURE GetHomesByOwner(IN p_owner_id INT)
BEGIN
    SELECT h.home_id, h.address,
           COUNT(DISTINCT r.room_id) AS total_rooms,
           COUNT(DISTINCT d.device_id) AS total_devices
    FROM Home h
    LEFT JOIN Room r ON h.home_id = r.home_id
    LEFT JOIN Device d ON r.room_id = d.room_id
    WHERE h.owner_id = p_owner_id
    GROUP BY h.home_id;
END //

CREATE PROCEDURE AddHomeToUserProc(IN p_owner_id INT, IN p_address VARCHAR(200))
BEGIN
    INSERT INTO Home (owner_id, address) VALUES (p_owner_id, p_address);
END //

CREATE PROCEDURE AddRoomToHomeProc(IN p_home_id INT, IN p_room_name VARCHAR(50))
BEGIN
    INSERT INTO Room (home_id, name) VALUES (p_home_id, p_room_name);
END //

CREATE PROCEDURE AddDeviceToRoomProc(
    IN p_room_id INT,
    IN p_type VARCHAR(30),
    IN p_brand VARCHAR(30),
    IN p_power DECIMAL(7,2),
    IN p_status VARCHAR(10)
)
BEGIN
    INSERT INTO Device (room_id, type, brand, power_rating, status)
    VALUES (p_room_id, p_type, p_brand, p_power, p_status);
END //

CREATE PROCEDURE AddSensorToDeviceProc(
    IN p_device_id INT,
    IN p_type VARCHAR(30),
    IN p_last_reading DECIMAL(10,2)
)
BEGIN
    INSERT INTO Sensor (device_id, type, last_reading)
    VALUES (p_device_id, p_type, p_last_reading);
END //
DELIMITER ;

-- =====================================================
-- DATABASE USERS & PRIVILEGES
-- =====================================================
DROP USER IF EXISTS 'admin_user'@'localhost';
DROP USER IF EXISTS 'home_owner'@'localhost';
DROP USER IF EXISTS 'guest_viewer'@'localhost';

CREATE USER 'admin_user'@'localhost' IDENTIFIED BY 'Admin@123';
CREATE USER 'home_owner'@'localhost' IDENTIFIED BY 'Owner@123';
CREATE USER 'guest_viewer'@'localhost' IDENTIFIED BY 'Guest@123';

-- Grant EXECUTE permissions to all users for stored procedures

-- For home_owner user
GRANT EXECUTE ON PROCEDURE SmartHomeDB.GetHomesByOwner TO 'home_owner'@'localhost';
GRANT EXECUTE ON PROCEDURE SmartHomeDB.GetUnresolvedAlertsProc TO 'home_owner'@'localhost';
GRANT EXECUTE ON PROCEDURE SmartHomeDB.GetEnergyUsageByOwnerProc TO 'home_owner'@'localhost';
GRANT EXECUTE ON PROCEDURE SmartHomeDB.GetAlertsByOwnerProc TO 'home_owner'@'localhost';

-- For guest_viewer user
GRANT EXECUTE ON PROCEDURE SmartHomeDB.GetUnresolvedAlertsProc TO 'guest_viewer'@'localhost';
GRANT EXECUTE ON PROCEDURE SmartHomeDB.GetHomesByOwner TO 'guest_viewer'@'localhost';

-- For admin_user (if needed)
GRANT EXECUTE ON PROCEDURE SmartHomeDB.* TO 'admin_user'@'localhost';

-- Flush privileges
FLUSH PRIVILEGES;

-- Verify permissions
SHOW GRANTS FOR 'home_owner'@'localhost';
SHOW GRANTS FOR 'guest_viewer'@'localhost';
SHOW GRANTS FOR 'admin_user'@'localhost';
FLUSH PRIVILEGES;

SELECT User, Host FROM mysql.user
WHERE User IN ('admin_user', 'home_owner', 'guest_viewer');






UPDATE `User`
SET password = 'Admin@123'
WHERE email = 'admin@smarthome.com';

-- 3) For convenience, set plaintext passwords for some test users (example)
UPDATE `User` SET password = 'Owner@123' WHERE role = 'owner' LIMIT 1;
UPDATE `User` SET password = 'Guest@123' WHERE role = 'guest' LIMIT 1;

