# 🚀 Deploy Rápido en Railway - Resumen

## ⏱️ 10 Minutos para estar en producción

### 📝 Checklist Pre-Deploy

- [ ] Cuenta en Railway.app
- [ ] Cuenta en GitHub
- [ ] Proyecto subido a GitHub
- [ ] SECRET_KEY generado

---

## 🔥 Pasos Rápidos

### 1️⃣ Generar SECRET_KEY (30 segundos)

```bash
cd backend
python generate_secret_key.py
# Copia el SECRET_KEY generado
```

### 2️⃣ Subir a GitHub (2 minutos)

```bash
cd medication-system
git init
git add .
git commit -m "Initial commit"

# Crear repo en GitHub.com, luego:
git remote add origin https://github.com/TU_USUARIO/medication-system.git
git branch -M main
git push -u origin main
```

### 3️⃣ Deploy Backend en Railway (3 minutos)

1. **railway.app** → Login → **New Project**
2. **Deploy from GitHub repo** → Selecciona tu repo
3. **Settings** → **Root Directory** → `backend`
4. **+ New** → **Database** → **PostgreSQL** (se crea automáticamente)
5. **Variables** → Agregar:

```env
SECRET_KEY=tu-secret-key-generado-aqui
MQTT_BROKER=broker.hivemq.com
MQTT_PORT=1883
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
MQTT_BASE_TOPIC=medication/devices
```

6. **Deploy** → ¡Listo! Copia la URL del backend

### 4️⃣ Deploy Frontend en Vercel (2 minutos)

1. **vercel.com** → **Add New Project**
2. Importa tu repo de GitHub
3. **Settings**:
   - Framework: **Vite**
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `dist`
4. **Environment Variables**:

```env
VITE_API_URL=https://TU-BACKEND-URL.up.railway.app
```

5. **Deploy** → ¡Listo!

### 5️⃣ Crear Usuario Admin (1 minuto)

```bash
# Reemplaza con tu URL real
curl -X POST https://tu-backend.railway.app/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@ejemplo.com",
    "username": "admin",
    "password": "admin123",
    "full_name": "Administrador"
  }'
```

### 6️⃣ Hacer Admin al Usuario (1 minuto)

En Railway:
1. Click en **PostgreSQL**
2. **Data** tab
3. Ejecuta:

```sql
UPDATE users SET is_admin = true WHERE username = 'admin';
```

### 7️⃣ Configurar ESP32 (1 minuto)

Edita `esp32/src/main.cpp`:

```cpp
const char* DEVICE_ID = "ESP32_001";
char wifi_ssid[32] = "TU_WIFI";
char wifi_password[64] = "TU_PASSWORD";
char mqtt_server[64] = "broker.hivemq.com";
```

Flash:
```bash
cd esp32
pio run --target upload
```

---

## ✅ URLs Finales

- 🔧 **Backend API**: `https://tu-backend.railway.app`
- 📄 **API Docs**: `https://tu-backend.railway.app/docs`
- 🌐 **Frontend**: `https://tu-frontend.vercel.app`
- 🗄️ **Database**: Automático en Railway

---

## 🐛 Problemas Comunes

**Backend no inicia:**
```bash
# Verifica logs en Railway
railway logs

# Verifica variables
railway variables
```

**Frontend no conecta al backend:**
- Verifica CORS en `backend/main.py`
- Verifica `VITE_API_URL` en Vercel

**ESP32 no conecta:**
- Verifica WiFi credentials
- Usa MQTT Explorer para probar broker
- Revisa Serial Monitor (115200 baud)

---

## 💡 Tips

1. **CORS**: Actualiza `allow_origins` en `main.py` con tu dominio de Vercel
2. **Logs**: Railway → Service → Logs
3. **Redeploy**: Solo haz `git push` y Railway redespliega automático
4. **Gratis**: Railway $5/mes gratis, Vercel totalmente gratis

---

## 📱 Probarlo

1. Ve a tu frontend en Vercel
2. Login: `admin` / `admin123`
3. Agrega un dispositivo con el `DEVICE_ID` del ESP32
4. Crea horarios de medicación
5. Controla los LEDs remotamente

---

## 🎉 ¡Listo en 10 minutos!

Tu sistema de medicación está en producción, accesible desde cualquier lugar del mundo.

Para documentación completa, lee: `RAILWAY_DEPLOYMENT.md`
