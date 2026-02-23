# Pastillero — Servidor Backend

Backend completo para pastillero inteligente con ESP32.
Stack: **FastAPI + SQLite + Telegram**

## Estructura

```
pastillero/
├── main.py              # App principal, lifespan, rutas raíz
├── config.py            # Settings desde .env
├── database.py          # SQLite, init, tablas
├── requirements.txt
├── .env.example         # → copiá a .env y completá
├── firmware/            # Archivos .bin subidos (se crea solo)
├── templates/
│   └── dashboard.html   # Panel web
├── routers/
│   ├── devices.py       # Heartbeat, estado, reboot remoto
│   ├── ota.py           # Subir firmware, check updates, descargar
│   ├── events.py        # Historial de tomas y eventos
│   └── admin.py         # Auth básica de admin
└── services/
    └── telegram.py      # Notificaciones Telegram
```

## Instalación rápida (VPS Ubuntu)

```bash
# 1. Clonar / subir archivos
git clone ... && cd pastillero

# 2. Crear entorno virtual
python3 -m venv venv && source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
nano .env   # completá API_SECRET_KEY, Telegram, etc.

# 5. Correr
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Correr como servicio (systemd)

```ini
# /etc/systemd/system/pastillero.service
[Unit]
Description=Pastillero Backend
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/pastillero
ExecStart=/home/ubuntu/pastillero/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
EnvironmentFile=/home/ubuntu/pastillero/.env

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable pastillero
sudo systemctl start pastillero
```

## Nginx + HTTPS (recomendado)

```nginx
server {
    server_name api.tupastillero.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo certbot --nginx -d api.tupastillero.com
```

---

## API para el ESP32

### Heartbeat (cada 30-60 segundos)
```
POST /api/devices/heartbeat
X-API-Key: tu-clave
Content-Type: application/json

{
  "device_id": "AA:BB:CC:DD:EE:FF",
  "firmware_version": "1.0.0",
  "ip_address": "192.168.1.50",
  "status": "online",
  "name": "Pastillero Cocina"
}
```

Respuesta normal:
```json
{ "ok": true, "server_time": "2025-01-01T12:00:00Z" }
```

Respuesta con reboot pendiente:
```json
{ "ok": true, "server_time": "...", "command": "reboot" }
```

### Verificar OTA
```
GET /api/ota/check/1.0.0
X-API-Key: tu-clave
```

### Registrar evento
```
POST /api/events/
X-API-Key: tu-clave
Content-Type: application/json

{
  "device_id": "AA:BB:CC:DD:EE:FF",
  "type": "dose_taken",
  "payload": { "alarm_label": "Medicamento mañana" }
}
```

Tipos de evento: `alarm_triggered`, `alarm_ack`, `dose_taken`, `reboot`, `ota_start`, `ota_done`, `ota_fail`

---

## Panel Web

Accedé a `http://tu-servidor` para ver el dashboard con:
- Estado en tiempo real de todos los dispositivos
- IP, versión de firmware, último contacto
- Reboot remoto con un click
- Subida y gestión de firmwares OTA
- Historial de eventos / tomas
