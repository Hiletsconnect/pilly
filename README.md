# 💊 Sistema de Gestión de Medicación con ESP32

Sistema completo de gestión de medicación inteligente con dispositivos ESP32, anillo LED de 24 LEDs (6 casilleros × 3 LEDs), dashboard web para administración y cliente, con comunicación MQTT.

## 🎯 Características

### Backend (FastAPI + PostgreSQL)
- ✅ API REST completa con autenticación JWT
- ✅ Gestión de múltiples dispositivos ESP32
- ✅ Sistema de horarios de medicación
- ✅ Comunicación MQTT bidireccional
- ✅ Control remoto de dispositivos (OTA, reboot, WiFi, LEDs)
- ✅ Roles de usuario (Admin y Cliente)

### Frontend (React + Vite + TailwindCSS)
- ✅ Dashboard moderno y responsivo
- ✅ Gestión de dispositivos en tiempo real
- ✅ Configuración de horarios de medicación
- ✅ Control de anillo LED (24 LEDs, 6 casilleros)
- ✅ Interfaz diferenciada para Admin y Cliente
- ✅ Diseño hermoso con gradientes y animaciones

### ESP32 (Arduino/PlatformIO)
- ✅ Conexión WiFi y MQTT
- ✅ Control de 24 LEDs NeoPixel (6 casilleros × 3 LEDs)
- ✅ Actualización OTA (Over-The-Air)
- ✅ Reporte de estado (IP, MAC, WiFi, firmware)
- ✅ Cambio de red WiFi remoto
- ✅ Almacenamiento persistente de configuración

## 📁 Estructura del Proyecto

```
medication-system/
├── backend/                 # FastAPI Backend
│   ├── app/
│   │   ├── core/           # Configuración, seguridad, DB
│   │   ├── models/         # Modelos SQLAlchemy
│   │   ├── routes/         # Endpoints de la API
│   │   ├── schemas/        # Schemas Pydantic
│   │   └── services/       # Lógica de negocio y MQTT
│   ├── main.py
│   └── requirements.txt
│
├── frontend/               # React Frontend
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/       # API calls
│   │   ├── store/          # Zustand state
│   │   └── utils/
│   └── package.json
│
└── esp32/                  # ESP32 Firmware
    ├── src/
    │   └── main.cpp
    └── platformio.ini
```

## 🚀 Instalación y Configuración

### 1. Backend Setup

```bash
cd backend

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales de PostgreSQL y MQTT

# Ejecutar servidor
python main.py
```

**Archivo .env:**
```env
DATABASE_URL=postgresql://user:password@localhost:5432/medication_db
SECRET_KEY=tu-clave-secreta-muy-segura
MQTT_BROKER=localhost
MQTT_PORT=1883
```

### 2. Frontend Setup

```bash
cd frontend

# Instalar dependencias
npm install

# Configurar API URL (opcional)
echo "VITE_API_URL=http://localhost:8000" > .env

# Ejecutar en desarrollo
npm run dev

# Build para producción
npm run build
```

### 3. ESP32 Setup

```bash
cd esp32

# Editar src/main.cpp y configurar:
# - DEVICE_ID (único para cada ESP32)
# - WiFi credentials
# - MQTT broker

# Con PlatformIO CLI
pio run --target upload

# O usar PlatformIO IDE en VSCode
```

**Configuración del ESP32:**
```cpp
const char* DEVICE_ID = "ESP32_001";
char wifi_ssid[32] = "TU_WIFI_SSID";
char wifi_password[64] = "TU_WIFI_PASSWORD";
char mqtt_server[64] = "TU_MQTT_BROKER_IP";
```

## 🔌 Diagrama de Conexión ESP32

```
ESP32 Pin 5 ──► DIN (NeoPixel Strip)
ESP32 GND   ──► GND
ESP32 5V    ──► VCC (o fuente externa 5V)
```

**NeoPixel Configuration:**
- 24 LEDs total
- 6 compartimentos (0-5)
- 3 LEDs por compartimento
- Pin: GPIO 5

## 📡 Topicos MQTT

### Suscripciones del ESP32:
```
medication/devices/{DEVICE_ID}/command
```

### Publicaciones del ESP32:
```
medication/devices/{DEVICE_ID}/status
medication/devices/{DEVICE_ID}/response
```

### Comandos disponibles:
```json
// Reiniciar dispositivo
{
  "command": "reboot",
  "payload": {}
}

// Actualización OTA
{
  "command": "ota_update",
  "payload": {
    "url": "http://ejemplo.com/firmware.bin",
    "version": "1.1.0"
  }
}

// Cambiar WiFi
{
  "command": "wifi_change",
  "payload": {
    "ssid": "Nueva_Red",
    "password": "nueva_password"
  }
}

// Control de LED
{
  "command": "led_control",
  "payload": {
    "compartment": 0,
    "color": "#FF0000",
    "brightness": 100
  }
}

// Solicitar estado
{
  "command": "get_status",
  "payload": {}
}
```

## 🎨 Funcionalidades del Dashboard

### Usuario Cliente:
- ✅ Ver sus dispositivos y estado (online/offline)
- ✅ Crear/editar/eliminar horarios de medicación
- ✅ Configurar colores de LED por casillero
- ✅ Ver próximos recordatorios
- ✅ Control remoto de dispositivos (reboot, LEDs)

### Usuario Admin:
- ✅ Todo lo del cliente +
- ✅ Ver todos los dispositivos de todos los usuarios
- ✅ Actualización OTA de firmware
- ✅ Gestión avanzada de dispositivos

## 🔐 API Endpoints

### Autenticación
```
POST /auth/register    - Registrar usuario
POST /auth/login       - Login
GET  /auth/me          - Info del usuario actual
```

### Dispositivos
```
GET    /devices              - Listar dispositivos
POST   /devices              - Crear dispositivo
GET    /devices/{id}         - Info de dispositivo
PUT    /devices/{id}         - Actualizar dispositivo
DELETE /devices/{id}         - Eliminar dispositivo
POST   /devices/{id}/reboot  - Reiniciar
POST   /devices/{id}/ota-update - Actualizar firmware
POST   /devices/{id}/wifi    - Cambiar WiFi
POST   /devices/{id}/led     - Control de LED
POST   /devices/{id}/status  - Solicitar estado
```

### Horarios
```
GET    /schedules          - Listar horarios
POST   /schedules          - Crear horario
GET    /schedules/{id}     - Info de horario
PUT    /schedules/{id}     - Actualizar horario
DELETE /schedules/{id}     - Eliminar horario
```

## 🚂 Deployment en Railway

### Backend:
```bash
# Railway detecta automáticamente Python
# Asegúrate de tener:
# - requirements.txt
# - Procfile (opcional): web: python main.py

# Variables de entorno en Railway:
DATABASE_URL=<postgresql_url_from_railway>
SECRET_KEY=<generate_strong_key>
MQTT_BROKER=<your_mqtt_broker>
```

### Frontend:
```bash
# Build command: npm run build
# Start command: npm run preview
# O usar Vercel/Netlify para mejor performance
```

## 🛠️ Tecnologías Utilizadas

**Backend:**
- FastAPI
- SQLAlchemy + PostgreSQL
- Paho MQTT
- JWT Authentication
- Alembic (migrations)

**Frontend:**
- React 18
- Vite
- TailwindCSS
- Zustand (state)
- Axios
- React Router
- Lucide Icons
- React Hot Toast

**Hardware:**
- ESP32
- NeoPixel/WS2812B LED Strip (24 LEDs)
- PlatformIO

## 📝 Notas Importantes

1. **Seguridad:** Cambiar el `SECRET_KEY` en producción
2. **MQTT:** Asegurar el broker MQTT con usuario/password
3. **LED Power:** Para 24 LEDs, considerar fuente externa de 5V 2A
4. **OTA:** El ESP32 necesita acceso HTTP al archivo .bin
5. **Database:** Crear la base de datos PostgreSQL antes de ejecutar

## 🤝 Soporte

Para ayuda con:
- Backend: Revisar logs en `uvicorn`
- Frontend: Consola del navegador
- ESP32: Monitor serial (115200 baud)
- MQTT: Usar MQTT Explorer para debug

## 📄 Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.

---

**¡Sistema listo para usar! 🎉**

Cualquier duda, revisar la documentación en cada carpeta o los comentarios en el código.
