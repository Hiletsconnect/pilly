# 🚀 Guía de Inicio Rápido

## Opción 1: Desarrollo Local (Recomendado)

### 1. Instalar PostgreSQL
```bash
# macOS
brew install postgresql@15
brew services start postgresql@15

# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql

# Windows: Descargar desde https://www.postgresql.org/download/
```

### 2. Instalar Mosquitto (MQTT Broker)
```bash
# macOS
brew install mosquitto
brew services start mosquitto

# Ubuntu/Debian
sudo apt install mosquitto mosquitto-clients
sudo systemctl start mosquitto

# Windows: Descargar desde https://mosquitto.org/download/
```

### 3. Configurar Base de Datos
```bash
# Crear base de datos
psql postgres
CREATE DATABASE medication_db;
CREATE USER medication_user WITH PASSWORD 'medication_pass';
GRANT ALL PRIVILEGES ON DATABASE medication_db TO medication_user;
\q
```

### 4. Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configurar .env
cp .env.example .env
# Editar .env con tus credenciales

# Ejecutar
python main.py
```

El backend estará en: http://localhost:8000
Documentación API: http://localhost:8000/docs

### 5. Frontend
```bash
cd frontend
npm install
npm run dev
```

El frontend estará en: http://localhost:3000

### 6. ESP32
```bash
cd esp32

# Editar src/main.cpp:
# - Cambiar DEVICE_ID a un ID único
# - Configurar WiFi SSID y password
# - Configurar IP del broker MQTT

# Flashear con PlatformIO
pio run --target upload
pio device monitor
```

## Opción 2: Con Docker

```bash
# Crear archivo mosquitto.conf
mkdir -p mosquitto/config
echo "listener 1883" > mosquitto/config/mosquitto.conf
echo "allow_anonymous true" >> mosquitto/config/mosquitto.conf

# Levantar servicios
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener
docker-compose down
```

## Opción 3: Deploy en Railway

### Backend:
1. Crear cuenta en Railway.app
2. New Project → Deploy from GitHub
3. Seleccionar el repo y carpeta `backend`
4. Agregar PostgreSQL addon
5. Configurar variables de entorno:
   - SECRET_KEY (generar una nueva)
   - MQTT_BROKER (tu broker público)
6. Deploy automático

### Frontend:
1. Usar Vercel o Netlify para mejor performance
2. Conectar GitHub repo, carpeta `frontend`
3. Configurar variable: VITE_API_URL=<tu_backend_url>
4. Deploy

## 📱 Primer Uso

### 1. Crear Usuario Admin
```bash
# Usando la API directamente
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@ejemplo.com",
    "username": "admin",
    "password": "admin123",
    "full_name": "Administrador"
  }'

# Luego en la base de datos, hacer al usuario admin:
psql medication_db
UPDATE users SET is_admin = true WHERE username = 'admin';
\q
```

### 2. Login en el Dashboard
- Ir a http://localhost:3000/login
- Usuario: admin
- Password: admin123

### 3. Agregar Dispositivo ESP32
- En el dashboard ir a "Dispositivos"
- Click en "Agregar Dispositivo"
- Ingresar:
  - Device ID: ESP32_001 (mismo que en el código)
  - Nombre: Mi Dispositivo
  - Descripción: Primer dispositivo

### 4. Crear Horario de Medicación
- Ir a "Horarios"
- Click en "Nuevo Horario"
- Completar:
  - Medicamento: Aspirina
  - Dosis: 500mg
  - Compartimento: 0 (primero)
  - Hora: 08:00
  - Días: Lunes a Viernes
  - Color LED: #FF0000 (rojo)

### 5. Probar Control del ESP32
- En "Dispositivos", click en tu dispositivo
- Probar:
  - "Reiniciar" para reboot
  - "Control LED" para probar colores
  - Ver estado online/offline

## 🔍 Troubleshooting

### Backend no inicia:
- Verificar que PostgreSQL está corriendo
- Verificar credenciales en .env
- Revisar logs: `python main.py`

### Frontend no conecta:
- Verificar que backend está en http://localhost:8000
- Revisar consola del navegador (F12)
- Verificar CORS en backend

### ESP32 no conecta MQTT:
- Verificar IP del broker
- Probar con MQTT Explorer
- Revisar serial monitor (115200 baud)
- Verificar WiFi credentials

### LEDs no encienden:
- Verificar conexión física (GPIO 5)
- Probar con código simple primero
- Verificar fuente de alimentación (5V suficiente)

## 📚 Recursos

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [React Docs](https://react.dev/)
- [PlatformIO Docs](https://docs.platformio.org/)
- [Adafruit NeoPixel Guide](https://learn.adafruit.com/adafruit-neopixel-uberguide)
- [MQTT.org](https://mqtt.org/)

## 🎯 Próximos Pasos

1. Personalizar colores del dashboard
2. Agregar notificaciones push
3. Integrar con Google Calendar
4. Crear app móvil (React Native)
5. Agregar reconocimiento por voz

¡Disfruta tu sistema! 💊✨
