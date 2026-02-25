import os
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import json
import re

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


def ensure_column(db, table, column, coltype_sql):
    """Add column if it does not exist (SQLite)."""
    cols = [row['name'] for row in db.execute(f"PRAGMA table_info({table})").fetchall()]
    if column not in cols:
        db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype_sql}")

def generate_api_key():
    return secrets.token_urlsafe(32)

def get_device_by_mac(db, mac_address):
    return db.execute('SELECT * FROM devices WHERE mac_address = ?', (mac_address,)).fetchone()

def verify_device_request(db, mac_address, api_key):
    device = get_device_by_mac(db, mac_address)
    if not device:
        return None, (jsonify({'error': 'Unknown device'}), 404)
    if not device.get('api_key') or device['api_key'] != api_key:
        return None, (jsonify({'error': 'Invalid api key'}), 401)
    admin_state = (device.get('admin_state') or 'active').lower()
    if admin_state == 'blocked':
        return None, (jsonify({'error': 'Device blocked'}), 403)
    return device, None

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
        

        # ---- Schema migrations (safe to run multiple times) ----
        ensure_column(db, 'devices', 'api_key', "TEXT")
        ensure_column(db, 'devices', 'admin_state', "TEXT DEFAULT 'active'")
        ensure_column(db, 'devices', 'ota_enabled', "INTEGER DEFAULT 0")
        ensure_column(db, 'devices', 'ota_target_version', "TEXT")
        ensure_column(db, 'firmwares', 'is_stable', "INTEGER DEFAULT 0")

        db.execute('''
            CREATE TABLE IF NOT EXISTS device_commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id INTEGER NOT NULL,
                command TEXT NOT NULL,
                payload TEXT,
                status TEXT DEFAULT 'pending',
                requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sent_at TIMESTAMP,
                ack_at TIMESTAMP,
                FOREIGN KEY (device_id) REFERENCES devices (id)
            )
        ''')

        # Ensure existing devices have API keys
        devices_without_key = db.execute("SELECT id FROM devices WHERE api_key IS NULL OR api_key = ''").fetchall()
        for row in devices_without_key:
            db.execute("UPDATE devices SET api_key = ? WHERE id = ?", (generate_api_key(), row['id']))
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
               firmware_version, last_seen, status, uptime, free_heap,
               api_key, admin_state, ota_enabled, ota_target_version
        FROM devices 
        ORDER BY last_seen DESC
    ''').fetchall()
    db.close()
    
    return jsonify([dict(device) for device in devices])

@app.route('/api/devices', methods=['POST'])
@login_required
def create_device():
    """Create (provision) a new pastillero from the admin panel.
    The ESP32 will NOT need to call /api/esp32/register; it can start sending heartbeat using (mac_address + api_key).
    """
    data = request.json or {}
    mac = (data.get('mac_address') or '').strip().lower()
    if not mac:
        return jsonify({'error': 'mac_address required'}), 400

    # basic MAC sanity (allow ":" or "-")
    mac_clean = mac.replace('-', ':')
    if not re.match(r'^([0-9a-f]{2}:){5}[0-9a-f]{2}$', mac_clean):
        return jsonify({'error': 'Invalid MAC format. Use AA:BB:CC:DD:EE:FF'}), 400

    name = (data.get('device_name') or '').strip()
    firmware_version = (data.get('firmware_version') or '').strip()
    admin_state = (data.get('admin_state') or 'active').strip().lower()
    if admin_state not in ('active', 'suspended', 'blocked'):
        admin_state = 'active'

    ota_enabled = 1 if str(data.get('ota_enabled', 0)).lower() in ('1', 'true', 'yes', 'on') else 0
    ota_target_version = (data.get('ota_target_version') or '').strip() or None

    api_key = generate_api_key()

    db = get_db()
    exists = db.execute('SELECT id FROM devices WHERE mac_address = ?', (mac_clean,)).fetchone()
    if exists:
        db.close()
        return jsonify({'error': 'Device already exists'}), 409

    db.execute('''
        INSERT INTO devices (
            mac_address, device_name, firmware_version,
            status, api_key, admin_state, ota_enabled, ota_target_version,
            created_at
        ) VALUES (?, ?, ?, 'offline', ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (mac_clean, name, firmware_version, api_key, admin_state, ota_enabled, ota_target_version))

    device_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]

    db.execute('''
        INSERT INTO alarms (device_id, alarm_type, message, severity)
        VALUES (?, 'device_provisioned', 'Pastillero provisionado desde el panel', 'info')
    ''', (device_id,))

    db.commit()
    db.close()

    return jsonify({'success': True, 'device_id': device_id, 'api_key': api_key})


@app.route('/api/devices/<int:device_id>')
@login_required
def device_detail(device_id):
    db = get_db()
    device = db.execute('SELECT * FROM devices WHERE id = ?', (device_id,)).fetchone()
    db.close()
    
    if device:
        return jsonify(dict(device))
    return jsonify({'error': 'Device not found'}), 404


@app.route('/api/devices/<int:device_id>/set_state', methods=['POST'])
@login_required
def set_device_state(device_id):
    data = request.json or {}
    state = (data.get('state') or '').strip().lower()
    if state not in ['active', 'suspended', 'blocked']:
        return jsonify({'error': 'Invalid state'}), 400

    db = get_db()
    device = db.execute('SELECT id FROM devices WHERE id = ?', (device_id,)).fetchone()
    if not device:
        db.close()
        return jsonify({'error': 'Device not found'}), 404

    status = 'offline' if state == 'active' else state
    db.execute('UPDATE devices SET admin_state = ?, status = ? WHERE id = ?', (state, status, device_id))
    db.commit()
    db.close()
    return jsonify({'success': True, 'state': state})

@app.route('/api/devices/<int:device_id>/rotate_key', methods=['POST'])
@login_required
def rotate_device_key(device_id):
    db = get_db()
    device = db.execute('SELECT id FROM devices WHERE id = ?', (device_id,)).fetchone()
    if not device:
        db.close()
        return jsonify({'error': 'Device not found'}), 404

    new_key = generate_api_key()
    db.execute('UPDATE devices SET api_key = ? WHERE id = ?', (new_key, device_id))
    db.commit()
    db.close()
    return jsonify({'success': True, 'api_key': new_key})

@app.route('/api/devices/<int:device_id>/ota', methods=['POST'])
@login_required
def set_device_ota(device_id):
    data = request.json or {}
    ota_enabled = data.get('ota_enabled', None)
    ota_target_version = data.get('ota_target_version', None)

    db = get_db()
    device = db.execute('SELECT id FROM devices WHERE id = ?', (device_id,)).fetchone()
    if not device:
        db.close()
        return jsonify({'error': 'Device not found'}), 404

    if ota_enabled is not None:
        db.execute('UPDATE devices SET ota_enabled = ? WHERE id = ?', (1 if int(ota_enabled) else 0, device_id))
    if ota_target_version is not None:
        ver = ota_target_version.strip()
        if ver == '':
            db.execute('UPDATE devices SET ota_target_version = NULL WHERE id = ?', (device_id,))
        else:
            db.execute('UPDATE devices SET ota_target_version = ? WHERE id = ?', (ver, device_id))

    db.commit()
    db.close()
    return jsonify({'success': True})

@app.route('/api/devices/<int:device_id>/command', methods=['POST'])
@login_required
def queue_device_command(device_id):
    data = request.json or {}
    command = (data.get('command') or '').strip().lower()
    if command not in ['restart']:
        return jsonify({'error': 'Unsupported command'}), 400

    payload = data.get('payload')
    payload_json = json.dumps(payload) if payload is not None else None

    db = get_db()
    device = db.execute('SELECT id FROM devices WHERE id = ?', (device_id,)).fetchone()
    if not device:
        db.close()
        return jsonify({'error': 'Device not found'}), 404

    db.execute('''
        INSERT INTO device_commands (device_id, command, payload, status)
        VALUES (?, ?, ?, 'pending')
    ''', (device_id, command, payload_json))

    db.execute('''
        INSERT INTO logs (device_id, log_type, message)
        VALUES (?, 'command', ?)
    ''', (device_id, f'Queued command: {command}'))

    db.commit()
    db.close()
    return jsonify({'success': True})

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
    # If blocked, deny registration/updates
    if device and (device.get('admin_state') == 'blocked'):
        db.close()
        return jsonify({'error': 'Device blocked'}), 403

    
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
        if not device.get('api_key'):
            db.execute('UPDATE devices SET api_key = ? WHERE id = ?', (generate_api_key(), device_id))
    else:
        # Create new device
        db.execute('''
            INSERT INTO devices (mac_address, ip_address, ssid, firmware_version, 
                               device_name, last_seen, status, uptime, free_heap, api_key, admin_state, ota_enabled)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 'online', ?, ?, ?, 'active', 0)
        ''', (data['mac_address'], data['ip_address'], data.get('ssid', ''),
              data['firmware_version'], data.get('device_name', ''),
              data.get('uptime', 0), data.get('free_heap', 0), generate_api_key()))
        device_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        
        # Log new device
        db.execute('''
            INSERT INTO alarms (device_id, alarm_type, message, severity)
            VALUES (?, 'device_registered', 'New device registered', 'info')
        ''', (device_id,))
    
    db.commit()
    db.close()
    
    device_row = get_db().execute('SELECT api_key FROM devices WHERE id = ?', (device_id,)).fetchone()
    return jsonify({'success': True, 'device_id': device_id, 'api_key': device_row['api_key'] if device_row else None})

@app.route('/api/esp32/heartbeat', methods=['POST'])
def esp32_heartbeat():
    data = request.json or {}
    mac = data.get('mac_address')
    if not mac:
        return jsonify({'error': 'MAC address required'}), 400

    api_key = request.headers.get('X-API-Key') or data.get('api_key')
    if not api_key:
        return jsonify({'error': 'API key required'}), 401

    db = get_db()
    device, err = verify_device_request(db, mac, api_key)
    if err:
        db.close()
        return err

    admin_state = (device.get('admin_state') or 'active').lower()
    status = 'online' if admin_state == 'active' else 'suspended'

    db.execute('''
        UPDATE devices
        SET last_seen = CURRENT_TIMESTAMP,
            status = ?,
            uptime = ?,
            free_heap = ?,
            ip_address = COALESCE(?, ip_address),
            ssid = COALESCE(?, ssid),
            firmware_version = COALESCE(?, firmware_version)
        WHERE mac_address = ?
    ''', (status, data.get('uptime', 0), data.get('free_heap', 0),
          data.get('ip_address'), data.get('ssid'), data.get('firmware_version'), mac))

    cmd_row = db.execute('''
        SELECT id, command, payload FROM device_commands
        WHERE device_id = ? AND status = 'pending'
        ORDER BY requested_at ASC
        LIMIT 1
    ''', (device['id'],)).fetchone()

    command = None
    if cmd_row and admin_state == 'active':
        db.execute("UPDATE device_commands SET status='sent', sent_at=CURRENT_TIMESTAMP WHERE id=?", (cmd_row['id'],))
        payload = None
        if cmd_row['payload']:
            try:
                payload = json.loads(cmd_row['payload'])
            except Exception:
                payload = {'raw': cmd_row['payload']}
        command = {'command': cmd_row['command'], 'payload': payload}

    db.commit()
    db.close()
    return jsonify({'success': True, 'command': command})


@app.route('/api/esp32/check_update', methods=['POST'])
def esp32_check_update():
    data = request.json or {}
    mac = data.get('mac_address')
    current = data.get('current_version')
    if not mac or current is None:
        return jsonify({'error': 'MAC address and current version required'}), 400

    api_key = request.headers.get('X-API-Key') or data.get('api_key')
    if not api_key:
        return jsonify({'error': 'API key required'}), 401

    db = get_db()
    device, err = verify_device_request(db, mac, api_key)
    if err:
        db.close()
        return err

    admin_state = (device.get('admin_state') or 'active').lower()
    if admin_state != 'active':
        db.close()
        return jsonify({'update_available': False, 'reason': 'suspended'})

    ota_enabled = int(device.get('ota_enabled') or 0)
    target_version = (device.get('ota_target_version') or '').strip()

    firmware = None
    if target_version:
        firmware = db.execute('SELECT * FROM firmwares WHERE version = ? LIMIT 1', (target_version,)).fetchone()
        if not firmware:
            db.close()
            return jsonify({'update_available': False, 'reason': 'target_not_found'})
    else:
        if not ota_enabled:
            db.close()
            return jsonify({'update_available': False, 'reason': 'ota_disabled'})
        firmware = db.execute('''
            SELECT * FROM firmwares
            WHERE is_stable = 1
            ORDER BY uploaded_at DESC
            LIMIT 1
        ''').fetchone()

    db.close()

    if not firmware:
        return jsonify({'update_available': False})

    if firmware['version'] != current:
        return jsonify({
            'update_available': True,
            'version': firmware['version'],
            'url': url_for('download_firmware', version=firmware['version'], _external=True),
            'size': firmware.get('file_size')
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
    data = request.json or {}
    mac = data.get('mac_address')
    if not mac or 'alarm_type' not in data:
        return jsonify({'error': 'MAC address and alarm_type required'}), 400

    api_key = request.headers.get('X-API-Key') or data.get('api_key')
    if not api_key:
        return jsonify({'error': 'API key required'}), 401

    db = get_db()
    device, err = verify_device_request(db, mac, api_key)
    if err:
        db.close()
        return err

    db.execute('''
        INSERT INTO alarms (device_id, alarm_type, message, severity)
        VALUES (?, ?, ?, ?)
    ''', (device['id'], data['alarm_type'], data.get('message', ''),
          data.get('severity', 'info')))

    db.commit()
    db.close()
    return jsonify({'success': True})


@app.route('/api/esp32/command/<mac_address>', methods=['GET'])
def esp32_get_command(mac_address):
    """ESP32 polls this endpoint to check for pending commands (fallback)."""
    api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
    if not api_key:
        return jsonify({'error': 'API key required'}), 401

    db = get_db()
    device, err = verify_device_request(db, mac_address, api_key)
    if err:
        db.close()
        return err

    admin_state = (device.get('admin_state') or 'active').lower()
    if admin_state != 'active':
        db.close()
        return jsonify({'command': None})

    cmd_row = db.execute('''
        SELECT id, command, payload FROM device_commands
        WHERE device_id = ? AND status = 'pending'
        ORDER BY requested_at ASC
        LIMIT 1
    ''', (device['id'],)).fetchone()

    command = None
    if cmd_row:
        db.execute("UPDATE device_commands SET status='sent', sent_at=CURRENT_TIMESTAMP WHERE id=?", (cmd_row['id'],))
        payload = None
        if cmd_row['payload']:
            try:
                payload = json.loads(cmd_row['payload'])
            except Exception:
                payload = {'raw': cmd_row['payload']}
        command = {'id': cmd_row['id'], 'command': cmd_row['command'], 'payload': payload}
        db.commit()
    db.close()
    return jsonify({'command': command})

@app.route('/api/devices/<int:device_id>', methods=['DELETE'])
def delete_device(device_id):
    conn = get_db()
    cursor = conn.cursor()

    # Primero borramos logs asociados
    cursor.execute("DELETE FROM alarms WHERE device_id = ?", (device_id,))
    cursor.execute("DELETE FROM commands WHERE device_id = ?", (device_id,))
    
    # Después borramos el dispositivo
    cursor.execute("DELETE FROM devices WHERE id = ?", (device_id,))
    conn.commit()
    conn.close()

    return jsonify({"success": True})


if __name__ == '__main__':
    # Create upload folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize database
    init_db()
    
    # Run the app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
