# ESP32 Management System

A professional web-based management system for ESP32 devices with Apple/Unifi-inspired design. Built with Flask, HTML/CSS, and JavaScript.

![Dashboard Preview](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Flask](https://img.shields.io/badge/Flask-3.0.0-lightgrey)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 🚀 Features

### Device Management
- ✅ **Automatic Device Registration** - ESP32 devices auto-register when they connect
- 📊 **Real-time Monitoring** - Track device status, uptime, memory usage, network info
- 🔄 **Remote Restart** - Restart devices remotely (implementation ready)
- 📍 **Network Information** - MAC address, IP, SSID tracking

### OTA Updates
- 🔄 **Over-The-Air Updates** - Update ESP32 firmware remotely
- 📦 **Release Management** - Upload and manage firmware versions
- 🎯 **Automatic Updates** - Devices check and install updates automatically
- 📝 **Version Control** - Track firmware versions and descriptions

### Monitoring & Alarms
- 🔔 **Alarm System** - Track events and alerts from devices
- 📈 **Historical Data** - View alarm history and device activity
- 🎨 **Severity Levels** - Info, Warning, and Error classifications
- 📊 **Statistics** - View alarm trends and statistics

### User Interface
- 🎨 **Apple/Unifi Design** - Clean, professional interface
- 📱 **Responsive** - Works on desktop, tablet, and mobile
- 🔐 **Secure Login** - Simple authentication system
- ⚡ **Auto-refresh** - Real-time data updates

## 📋 Requirements

- Python 3.8 or higher
- SQLite (included with Python)
- Modern web browser
- ESP32 devices (for testing)

## 🛠️ Installation

### Option 1: Deploy to Railway (Recommended)

1. **Fork or clone this repository**
   ```bash
   git clone https://github.com/yourusername/esp32-management-system.git
   cd esp32-management-system
   ```

2. **Deploy to Railway**
   - Create account at [Railway.app](https://railway.app)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select this repository
   - Railway will automatically detect and deploy the app
   - Your app will be live at `https://your-app.railway.app`

3. **Set Environment Variables (Optional)**
   - `SECRET_KEY` - Flask secret key (auto-generated if not set)
   - `PORT` - Port number (Railway sets this automatically)

### Option 2: Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/esp32-management-system.git
   cd esp32-management-system
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the dashboard**
   - Open browser to `http://localhost:5000`
   - Default login: `admin` / `admin123`

## 🔧 ESP32 Integration

### 1. Install Arduino Libraries

Using Arduino IDE Library Manager or PlatformIO, install:
- `ArduinoJson` (v6.21.3 or higher)

### 2. Configure ESP32 Code

Open `esp32_examples/esp32_client.ino` and update:

```cpp
const char* WIFI_SSID = "Your_WiFi_SSID";
const char* WIFI_PASSWORD = "Your_WiFi_Password";
const char* SERVER_URL = "https://your-app.railway.app";  // Your Railway URL
const char* DEVICE_NAME = "ESP32-Device-01";
const char* FIRMWARE_VERSION = "1.0.0";
```

### 3. Upload to ESP32

**Using Arduino IDE:**
1. Open `esp32_client.ino`
2. Select board: ESP32 Dev Module
3. Select port
4. Click Upload

**Using PlatformIO:**
```bash
cd esp32_examples
pio run -t upload
```

### 4. Monitor Serial Output

```bash
# Arduino IDE: Tools → Serial Monitor (115200 baud)
# PlatformIO:
pio device monitor
```

## 📡 API Documentation

### Device Registration
```http
POST /api/esp32/register
Content-Type: application/json

{
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "device_name": "ESP32-Device-01",
  "ip_address": "192.168.1.100",
  "ssid": "MyWiFi",
  "firmware_version": "1.0.0",
  "uptime": 3600,
  "free_heap": 250000
}
```

### Heartbeat
```http
POST /api/esp32/heartbeat
Content-Type: application/json

{
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "uptime": 3600,
  "free_heap": 250000
}
```

### Check for Updates
```http
POST /api/esp32/check_update
Content-Type: application/json

{
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "current_version": "1.0.0"
}
```

Response (if update available):
```json
{
  "update_available": true,
  "version": "1.1.0",
  "url": "https://your-server.com/api/esp32/firmware/1.1.0",
  "size": 524288
}
```

### Send Alarm
```http
POST /api/esp32/alarm
Content-Type: application/json

{
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "alarm_type": "temperature_high",
  "message": "Temperature exceeded threshold",
  "severity": "warning"
}
```

### Download Firmware
```http
GET /api/esp32/firmware/{version}
```

## 🔐 Security

### Change Default Password

1. Log in with default credentials (`admin` / `admin123`)
2. Access the database:
   ```bash
   sqlite3 esp32_management.db
   ```
3. Update password (example using Python):
   ```python
   from werkzeug.security import generate_password_hash
   password_hash = generate_password_hash('your_new_password')
   # Then update in database
   ```

### Production Considerations

- Change `SECRET_KEY` in production
- Use HTTPS (Railway provides this automatically)
- Implement rate limiting for API endpoints
- Consider adding API key authentication for ESP32 devices
- Regular database backups

## 📁 Project Structure

```
esp32-management-system/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── Procfile                    # Railway deployment config
├── README.md                   # This file
├── .gitignore                 # Git ignore rules
│
├── static/
│   ├── css/
│   │   └── style.css          # Apple/Unifi-inspired styles
│   └── js/
│       └── app.js             # Frontend JavaScript
│
├── templates/
│   ├── base.html              # Base template
│   ├── login.html             # Login page
│   ├── dashboard.html         # Dashboard
│   ├── devices.html           # Device management
│   ├── releases.html          # Firmware releases
│   └── alarms.html            # Alarm history
│
├── uploads/
│   └── firmwares/             # Uploaded firmware files
│
└── esp32_examples/
    ├── esp32_client.ino       # ESP32 Arduino code
    └── platformio.ini         # PlatformIO config
```

## 🎨 Design Philosophy

The UI follows Apple and Unifi design principles:

- **Clean and Minimal** - Focus on content, minimal chrome
- **White Space** - Generous padding and margins
- **Subtle Shadows** - Depth without distraction
- **System Font** - SF Pro / Inter / System UI
- **Blue Accents** - Primary actions in blue (#007AFF)
- **Card-based Layout** - Information organized in cards
- **Consistent Spacing** - 8px grid system

## 🔄 Auto-refresh

The dashboard automatically refreshes data every 30 seconds:
- Dashboard stats
- Device list
- Alarm notifications

This can be customized in `static/js/app.js`:
```javascript
function startAutoRefresh(interval = 30000) {  // Change interval here
```

## 📊 Database Schema

### Users
- id, username, password, created_at

### Devices
- id, mac_address, device_name, ip_address, ssid
- firmware_version, last_seen, status, uptime, free_heap

### Firmwares
- id, version, filename, description, file_size, uploaded_at

### Alarms
- id, device_id, alarm_type, message, severity, created_at

### Logs
- id, device_id, log_type, message, created_at

## 🐛 Troubleshooting

### ESP32 Not Connecting
1. Check WiFi credentials
2. Verify server URL (include http:// or https://)
3. Check serial monitor for errors
4. Ensure firewall allows connections

### Devices Show as Offline
- Devices appear offline if no heartbeat for >60 seconds
- Check ESP32 heartbeat interval
- Verify network connectivity

### OTA Update Fails
- Ensure firmware file is valid .bin
- Check ESP32 has enough free space
- Verify network stability during update
- Check serial output for specific error

### Upload Limit Exceeded
- Default max upload size is 16MB
- Change in `app.py`: `app.config['MAX_CONTENT_LENGTH']`

## 🚀 Future Enhancements

Potential features to add:
- [ ] WebSocket for real-time updates
- [ ] Device grouping and tagging
- [ ] Scheduled firmware deployments
- [ ] Email/SMS notifications
- [ ] API key authentication
- [ ] Multi-user roles and permissions
- [ ] Device command queue
- [ ] Grafana integration
- [ ] MQTT support
- [ ] Device configuration management

## 📝 License

MIT License - feel free to use this project for personal or commercial purposes.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing issues for solutions

## 🙏 Acknowledgments

- Design inspired by Apple and Unifi
- Built with Flask and modern web technologies
- ESP32 OTA implementation based on Arduino examples

---

**Made with ❤️ for the ESP32 community**


## API key por pastillero (nuevo)

Al registrar un pastillero (`POST /api/esp32/register`) el servidor devuelve `api_key`. Guardala en el ESP32 y enviála en cada request como header:

- `X-API-Key: <api_key>`

Endpoints que la requieren:
- `POST /api/esp32/heartbeat`
- `POST /api/esp32/check_update`
- `POST /api/esp32/alarm`
- `GET /api/esp32/command/<mac_address>` (opcional)

Además, desde el dashboard podés bloquear/suspender, habilitar OTA por dispositivo, setear versión objetivo y mandar reinicio remoto.
