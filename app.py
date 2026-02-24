import os
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import json

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['UPLOAD_FOLDER'] = 'uploads/firmwares'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['DATABASE'] = 'esp32_management.db'

ALLOWED_EXTENSIONS = {'bin'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    db = sqlite3.connect(app.config['DATABASE'])
    db.row_factory = sqlite3.Row
    return db

def init_db():
    with app.app_context():
        db = get_db()
        
        # Users table
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Devices table
        db.execute('''
            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mac_address TEXT UNIQUE NOT NULL,
                device_name TEXT,
                ip_address TEXT,
                ssid TEXT,
                firmware_version TEXT,
                last_seen TIMESTAMP,
                status TEXT DEFAULT 'offline',
                uptime INTEGER DEFAULT 0,
                free_heap INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Firmwares table
        db.execute('''
            CREATE TABLE IF NOT EXISTS firmwares (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT UNIQUE NOT NULL,
                filename TEXT NOT NULL,
                description TEXT,
                file_size INTEGER,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Alarms table
        db.execute('''
            CREATE TABLE IF NOT EXISTS alarms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id INTEGER,
                alarm_type TEXT NOT NULL,
                message TEXT,
                severity TEXT DEFAULT 'info',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (device_id) REFERENCES devices (id)
            )
        ''')
        
        # Logs table
        db.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id INTEGER,
                log_type TEXT NOT NULL,
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (device_id) REFERENCES devices (id)
            )
        ''')
        
        # Check if default user exists
        cursor = db.execute('SELECT * FROM users WHERE username = ?', ('admin',))
        if not cursor.fetchone():
            # Create default admin user (password: admin123)
            hashed_password = generate_password_hash('admin123')
            db.execute('INSERT INTO users (username, password) VALUES (?, ?)', 
                      ('admin', hashed_password))
        
        db.commit()
        db.close()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Web Routes
@app.route('/')
@login_required
def index():
    return render_template('dashboard.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        db.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/devices')
@login_required
def devices():
    return render_template('devices.html')

@app.route('/releases')
@login_required
def releases():
    return render_template('releases.html')

@app.route('/alarms')
@login_required
def alarms():
    return render_template('alarms.html')

# API Routes for Web Dashboard
@app.route('/api/dashboard/stats')
@login_required
def dashboard_stats():
    db = get_db()
    
    total_devices = db.execute('SELECT COUNT(*) as count FROM devices').fetchone()['count']
    online_devices = db.execute('SELECT COUNT(*) as count FROM devices WHERE status = "online"').fetchone()['count']
    total_releases = db.execute('SELECT COUNT(*) as count FROM firmwares').fetchone()['count']
    recent_alarms = db.execute('SELECT COUNT(*) as count FROM alarms WHERE created_at > datetime("now", "-24 hours")').fetchone()['count']
    
    db.close()
    
    return jsonify({
        'total_devices': total_devices,
        'online_devices': online_devices,
        'offline_devices': total_devices - online_devices,
        'total_releases': total_releases,
        'recent_alarms': recent_alarms
    })

@app.route('/api/devices/list')
@login_required
def devices_list():
    db = get_db()
    devices = db.execute('''
        SELECT id, mac_address, device_name, ip_address, ssid, 
               firmware_version, last_seen, status, uptime, free_heap
        FROM devices 
        ORDER BY last_seen DESC
    ''').fetchall()
    db.close()
    
    return jsonify([dict(device) for device in devices])

@app.route('/api/devices/<int:device_id>')
@login_required
def device_detail(device_id):
    db = get_db()
    device = db.execute('SELECT * FROM devices WHERE id = ?', (device_id,)).fetchone()
    db.close()
    
    if device:
        return jsonify(dict(device))
    return jsonify({'error': 'Device not found'}), 404

@app.route('/api/releases/list')
@login_required
def releases_list():
    db = get_db()
    firmwares = db.execute('''
        SELECT id, version, filename, description, file_size, uploaded_at
        FROM firmwares 
        ORDER BY uploaded_at DESC
    ''').fetchall()
    db.close()
    
    return jsonify([dict(firmware) for firmware in firmwares])

@app.route('/api/releases/upload', methods=['POST'])
@login_required
def upload_release():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    version = request.form.get('version')
    description = request.form.get('description', '')
    
    if not version:
        return jsonify({'error': 'Version is required'}), 400
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{version}.bin")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        file_size = os.path.getsize(filepath)
        
        db = get_db()
        try:
            db.execute('''
                INSERT INTO firmwares (version, filename, description, file_size)
                VALUES (?, ?, ?, ?)
            ''', (version, filename, description, file_size))
            db.commit()
            firmware_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
            db.close()
            
            return jsonify({
                'success': True,
                'id': firmware_id,
                'version': version,
                'filename': filename
            })
        except sqlite3.IntegrityError:
            db.close()
            os.remove(filepath)
            return jsonify({'error': 'Version already exists'}), 400
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/api/releases/<int:release_id>', methods=['DELETE'])
@login_required
def delete_release(release_id):
    db = get_db()
    firmware = db.execute('SELECT * FROM firmwares WHERE id = ?', (release_id,)).fetchone()
    
    if firmware:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], firmware['filename'])
        if os.path.exists(filepath):
            os.remove(filepath)
        
        db.execute('DELETE FROM firmwares WHERE id = ?', (release_id,))
        db.commit()
        db.close()
        
        return jsonify({'success': True})
    
    db.close()
    return jsonify({'error': 'Release not found'}), 404

@app.route('/api/alarms/list')
@login_required
def alarms_list():
    limit = request.args.get('limit', 100, type=int)
    
    db = get_db()
    alarms = db.execute('''
        SELECT a.id, a.alarm_type, a.message, a.severity, a.created_at,
               d.device_name, d.mac_address
        FROM alarms a
        LEFT JOIN devices d ON a.device_id = d.id
        ORDER BY a.created_at DESC
        LIMIT ?
    ''', (limit,)).fetchall()
    db.close()
    
    return jsonify([dict(alarm) for alarm in alarms])

# API Routes for ESP32 Devices
@app.route('/api/esp32/register', methods=['POST'])
def esp32_register():
    data = request.json
    
    required_fields = ['mac_address', 'ip_address', 'firmware_version']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    db = get_db()
    
    # Check if device exists
    device = db.execute('SELECT * FROM devices WHERE mac_address = ?', 
                       (data['mac_address'],)).fetchone()
    
    if device:
        # Update existing device
        db.execute('''
            UPDATE devices 
            SET ip_address = ?, ssid = ?, firmware_version = ?, 
                device_name = ?, last_seen = CURRENT_TIMESTAMP, status = 'online',
                uptime = ?, free_heap = ?
            WHERE mac_address = ?
        ''', (data['ip_address'], data.get('ssid', ''), data['firmware_version'],
              data.get('device_name', ''), data.get('uptime', 0), 
              data.get('free_heap', 0), data['mac_address']))
        device_id = device['id']
    else:
        # Create new device
        db.execute('''
            INSERT INTO devices (mac_address, ip_address, ssid, firmware_version, 
                               device_name, last_seen, status, uptime, free_heap)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 'online', ?, ?)
        ''', (data['mac_address'], data['ip_address'], data.get('ssid', ''),
              data['firmware_version'], data.get('device_name', ''),
              data.get('uptime', 0), data.get('free_heap', 0)))
        device_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        
        # Log new device
        db.execute('''
            INSERT INTO alarms (device_id, alarm_type, message, severity)
            VALUES (?, 'device_registered', 'New device registered', 'info')
        ''', (device_id,))
    
    db.commit()
    db.close()
    
    return jsonify({'success': True, 'device_id': device_id})

@app.route('/api/esp32/heartbeat', methods=['POST'])
def esp32_heartbeat():
    data = request.json
    
    if 'mac_address' not in data:
        return jsonify({'error': 'MAC address required'}), 400
    
    db = get_db()
    db.execute('''
        UPDATE devices 
        SET last_seen = CURRENT_TIMESTAMP, status = 'online',
            uptime = ?, free_heap = ?
        WHERE mac_address = ?
    ''', (data.get('uptime', 0), data.get('free_heap', 0), data['mac_address']))
    db.commit()
    db.close()
    
    return jsonify({'success': True})

@app.route('/api/esp32/check_update', methods=['POST'])
def esp32_check_update():
    data = request.json
    
    if 'mac_address' not in data or 'current_version' not in data:
        return jsonify({'error': 'MAC address and current version required'}), 400
    
    db = get_db()
    
    # Get latest firmware
    latest_firmware = db.execute('''
        SELECT * FROM firmwares 
        ORDER BY uploaded_at DESC 
        LIMIT 1
    ''').fetchone()
    
    db.close()
    
    if not latest_firmware:
        return jsonify({'update_available': False})
    
    if latest_firmware['version'] != data['current_version']:
        return jsonify({
            'update_available': True,
            'version': latest_firmware['version'],
            'url': url_for('download_firmware', version=latest_firmware['version'], _external=True),
            'size': latest_firmware['file_size']
        })
    
    return jsonify({'update_available': False})

@app.route('/api/esp32/firmware/<version>')
def download_firmware(version):
    db = get_db()
    firmware = db.execute('SELECT * FROM firmwares WHERE version = ?', (version,)).fetchone()
    db.close()
    
    if firmware:
        return send_from_directory(app.config['UPLOAD_FOLDER'], firmware['filename'])
    
    return jsonify({'error': 'Firmware not found'}), 404

@app.route('/api/esp32/alarm', methods=['POST'])
def esp32_alarm():
    data = request.json
    
    required_fields = ['mac_address', 'alarm_type', 'message']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    db = get_db()
    
    # Get device ID
    device = db.execute('SELECT id FROM devices WHERE mac_address = ?', 
                       (data['mac_address'],)).fetchone()
    
    if device:
        db.execute('''
            INSERT INTO alarms (device_id, alarm_type, message, severity)
            VALUES (?, ?, ?, ?)
        ''', (device['id'], data['alarm_type'], data['message'], 
              data.get('severity', 'info')))
        db.commit()
    
    db.close()
    
    return jsonify({'success': True})

@app.route('/api/esp32/command/<mac_address>', methods=['GET'])
def esp32_get_command(mac_address):
    """ESP32 polls this endpoint to check for pending commands"""
    # This is a simple implementation - in production you might use Redis or WebSockets
    # For now, we'll return a command if one was recently requested
    
    # Check if there's a pending restart command (stored in session or temp file)
    # This is a simplified version - you'd want to implement proper command queue
    
    return jsonify({'command': None})

if __name__ == '__main__':
    # Create upload folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize database
    init_db()
    
    # Run the app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
