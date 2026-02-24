# 🚂 Guía de Deployment en Railway

## 📋 Requisitos Previos

1. Cuenta en [Railway.app](https://railway.app) (gratis)
2. Cuenta en GitHub
3. Broker MQTT público (o usar CloudMQTT/HiveMQ)

---

## 🔧 Paso 1: Preparar el Proyecto

### Crear archivos necesarios para Railway:

#### 1.1 Backend - Crear `railway.json`

Crea este archivo en la carpeta `backend/`:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

#### 1.2 Backend - Crear `Procfile`

Crea este archivo en la carpeta `backend/`:

```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

#### 1.3 Backend - Crear `nixpacks.toml`

Crea este archivo en la carpeta `backend/`:

```toml
[phases.setup]
nixPkgs = ["python310", "postgresql"]

[phases.install]
cmds = ["pip install -r requirements.txt"]

[start]
cmd = "uvicorn main:app --host 0.0.0.0 --port $PORT"
```

---

## 🚀 Paso 2: Subir a GitHub

```bash
# Si no tienes git inicializado
cd medication-system
git init
git add .
git commit -m "Initial commit - Medication System"

# Crear repo en GitHub y conectar
git remote add origin https://github.com/TU_USUARIO/medication-system.git
git branch -M main
git push -u origin main
```

---

## 🎯 Paso 3: Deploy del Backend en Railway

### 3.1 Crear Proyecto en Railway

1. Ve a [railway.app](https://railway.app)
2. Click en **"New Project"**
3. Selecciona **"Deploy from GitHub repo"**
4. Conecta tu cuenta de GitHub (si no lo hiciste)
5. Selecciona el repositorio `medication-system`

### 3.2 Configurar el Backend Service

1. Railway detectará automáticamente Python
2. Click en el servicio creado
3. Ve a **Settings** → **Root Directory**
4. Establece: `backend`
5. Click **Save**

### 3.3 Agregar PostgreSQL

1. Click en **"+ New"** en tu proyecto
2. Selecciona **"Database"** → **"Add PostgreSQL"**
3. Railway creará automáticamente la base de datos
4. La variable `DATABASE_URL` se agregará automáticamente

### 3.4 Configurar Variables de Entorno

En tu servicio backend, ve a **Variables** y agrega:

```env
# Railway ya provee DATABASE_URL automáticamente

# JWT Secret (IMPORTANTE: generar uno único)
SECRET_KEY=tu-clave-super-segura-aqui-cambiar-123456789

# JWT Config
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# MQTT Broker (opción 1: usar uno público)
MQTT_BROKER=broker.hivemq.com
MQTT_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=
MQTT_BASE_TOPIC=medication/devices

# Server
HOST=0.0.0.0
PORT=$PORT

# Python
PYTHON_VERSION=3.11
```

**⚠️ IMPORTANTE: Para generar SECRET_KEY seguro:**

```bash
# En tu terminal local:
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3.5 Deploy

1. Click en **"Deploy"**
2. Espera a que termine el build (2-5 minutos)
3. Una vez completado, verás la URL pública
4. Ejemplo: `https://medication-backend-production.up.railway.app`

---

## 🌐 Paso 4: Deploy del Frontend en Railway (Opción 1)

### 4.1 Crear Segundo Servicio

1. En tu proyecto Railway, click **"+ New"**
2. Selecciona **"GitHub Repo"** (el mismo repositorio)
3. Railway creará otro servicio

### 4.2 Configurar Frontend Service

1. Click en el nuevo servicio
2. Ve a **Settings** → **Root Directory**
3. Establece: `frontend`
4. Click **Save**

### 4.3 Crear archivo de configuración para Railway

Crea `frontend/railway.json`:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "npm run preview -- --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE"
  }
}
```

### 4.4 Modificar `package.json`

Asegúrate que tenga:

```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  }
}
```

### 4.5 Configurar Variables de Entorno

En el servicio frontend, agrega:

```env
VITE_API_URL=https://TU-BACKEND-URL.up.railway.app
```

Reemplaza `TU-BACKEND-URL` con la URL real de tu backend.

### 4.6 Deploy

Railway hará el build automáticamente.

---

## 🚀 Paso 4 Alternativo: Frontend en Vercel (RECOMENDADO)

Es más fácil y rápido usar Vercel para el frontend:

### 1. Ve a [vercel.com](https://vercel.com)
### 2. Click en **"Add New Project"**
### 3. Importa tu repo de GitHub
### 4. Configura:
   - **Framework Preset:** Vite
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`

### 5. Variables de Entorno en Vercel:
```env
VITE_API_URL=https://TU-BACKEND-URL.up.railway.app
```

### 6. Click **Deploy**

---

## 🔌 Paso 5: Configurar MQTT Broker

### Opción 1: Broker Público (Desarrollo)

Usa brokers públicos gratuitos:
- `broker.hivemq.com:1883`
- `test.mosquitto.org:1883`

**⚠️ No recomendado para producción (sin seguridad)**

### Opción 2: CloudMQTT / HiveMQ Cloud (Recomendado)

1. Crea cuenta en [HiveMQ Cloud](https://www.hivemq.com/cloud/)
2. Crea un cluster gratuito
3. Obtén las credenciales:
   - Host
   - Port
   - Username
   - Password

4. Actualiza las variables en Railway:
```env
MQTT_BROKER=tu-cluster.hivemq.cloud
MQTT_PORT=8883
MQTT_USERNAME=tu-usuario
MQTT_PASSWORD=tu-password
```

### Opción 3: Mosquitto en Railway

1. Busca un template de Mosquitto en Railway
2. O usa Docker:
   - Crea un nuevo servicio
   - Usa imagen: `eclipse-mosquitto:2`
   - Configura puerto 1883

---

## 🔧 Paso 6: Configurar CORS en Backend

Asegúrate que tu `backend/main.py` tenga el CORS correcto:

```python
# En main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://tu-frontend.vercel.app",  # Tu dominio de Vercel
        "http://localhost:3000",            # Para desarrollo local
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Después de cambiar, haz commit y push:

```bash
git add backend/main.py
git commit -m "Update CORS for production"
git push
```

Railway redesplegará automáticamente.

---

## 📱 Paso 7: Configurar ESP32

En tu código ESP32 (`esp32/src/main.cpp`), actualiza:

```cpp
// MQTT Broker
char mqtt_server[64] = "tu-broker-hivemq.cloud";  // Tu broker MQTT
int mqtt_port = 8883;  // O 1883 si no usas SSL
char mqtt_user[32] = "tu-usuario";
char mqtt_password[64] = "tu-password";
```

Flashea el ESP32:

```bash
cd esp32
pio run --target upload
```

---

## ✅ Paso 8: Verificación Final

### 8.1 Backend
Visita: `https://tu-backend.up.railway.app/docs`

Deberías ver la documentación Swagger de la API.

### 8.2 Frontend
Visita tu URL de Vercel o Railway.

Deberías ver la página de login.

### 8.3 Crear Usuario Admin

Desde tu terminal local:

```bash
# Reemplaza URL con tu backend real
curl -X POST https://tu-backend.up.railway.app/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@ejemplo.com",
    "username": "admin",
    "password": "admin123",
    "full_name": "Administrador"
  }'
```

### 8.4 Hacer Admin al Usuario

Conecta a tu base de datos desde Railway:

1. Ve a PostgreSQL en Railway
2. Click en **"Data"** o usa el **Query** tab
3. Ejecuta:

```sql
UPDATE users SET is_admin = true WHERE username = 'admin';
```

O usa Railway CLI:

```bash
railway login
railway link
railway connect postgres
```

---

## 🎉 ¡Listo!

Tu sistema ya está en producción:

- ✅ Backend: `https://tu-backend.up.railway.app`
- ✅ Frontend: `https://tu-frontend.vercel.app`
- ✅ Base de datos PostgreSQL en Railway
- ✅ MQTT Broker configurado
- ✅ ESP32 conectado

---

## 🐛 Troubleshooting

### Error: "Database connection failed"

```bash
# Verifica las variables de entorno
railway variables

# Reinicia el servicio
railway restart
```

### Error: "CORS policy error"

Actualiza `allow_origins` en `backend/main.py` con tu URL real de frontend.

### Error: "ESP32 no conecta"

1. Verifica credenciales MQTT
2. Prueba con MQTT Explorer en tu PC primero
3. Revisa serial monitor del ESP32

### Error: "502 Bad Gateway"

El backend puede estar iniciando. Espera 1-2 minutos.

---

## 💰 Costos

**Railway:**
- $5/mes de crédito gratis
- Backend + PostgreSQL = ~$3-4/mes
- Si excedes, pasas a plan de pago

**Vercel:**
- Frontend: Completamente gratis
- Banda ancha ilimitada

**HiveMQ Cloud:**
- Plan gratuito disponible
- Suficiente para desarrollo y uso personal

---

## 📚 Recursos

- [Railway Docs](https://docs.railway.app/)
- [Vercel Docs](https://vercel.com/docs)
- [HiveMQ Cloud](https://www.hivemq.com/cloud/)

---

## 🔐 Seguridad en Producción

1. ✅ Cambiar `SECRET_KEY` (nunca usar el de ejemplo)
2. ✅ Usar MQTT con autenticación
3. ✅ Habilitar HTTPS (Railway lo hace automático)
4. ✅ No exponer credenciales en el código
5. ✅ Usar variables de entorno para todo

---

¡Tu sistema de medicación ya está en la nube! 🚀💊
