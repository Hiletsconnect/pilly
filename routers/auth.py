from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.status import HTTP_303_SEE_OTHER
from passlib.context import CryptContext

from database import get_db
from config import settings

router = APIRouter()
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

def _render_login(error: str = "", username: str = "") -> str:
    # HTML simple pero cheto (sin dependencias externas)
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Pilly — Login</title>
  <style>
    :root {{
      --bg:#0a0e12; --card:#111820; --border:#1e2d3d;
      --text:#e2eaf4; --muted:#5a7a99; --accent:#00d4aa; --danger:#ff2d55;
    }}
    *{{box-sizing:border-box}}
    body{{margin:0;min-height:100vh;display:grid;place-items:center;background:radial-gradient(circle at top, #1d253b 0, #020617 45%, #000 100%);font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu;color:var(--text);}}
    .card{{width:min(420px,92vw);background:rgba(17,24,32,.9);border:1px solid var(--border);border-radius:18px;padding:22px;box-shadow:0 10px 30px rgba(0,0,0,.45)}}
    h1{{margin:0 0 6px 0;font-size:22px;letter-spacing:.2px}}
    p{{margin:0 0 16px 0;color:var(--muted);font-size:13px;line-height:1.35}}
    label{{display:block;font-size:12px;color:var(--muted);margin:12px 0 6px}}
    input{{width:100%;padding:12px 12px;border-radius:12px;border:1px solid var(--border);background:#0b1118;color:var(--text);outline:none}}
    input:focus{{border-color:rgba(0,212,170,.7);box-shadow:0 0 0 4px rgba(0,212,170,.12)}}
    button{{margin-top:14px;width:100%;padding:12px;border-radius:12px;border:none;background:linear-gradient(90deg,var(--accent),#0091ff);color:#041014;font-weight:800;cursor:pointer}}
    .err{{margin-top:12px;padding:10px 12px;border-radius:12px;border:1px solid rgba(255,45,85,.35);background:rgba(255,45,85,.12);color:#ffd7df;font-size:13px}}
    .footer{{margin-top:12px;color:var(--muted);font-size:12px;text-align:center}}
    .pill{{display:inline-flex;align-items:center;gap:8px}}
    .dot{{width:10px;height:10px;border-radius:50%;background:var(--accent);box-shadow:0 0 14px rgba(0,212,170,.6)}}
  </style>
</head>
<body>
  <div class="card">
    <div class="pill"><span class="dot"></span><h1>Pilly — Panel</h1></div>
    <p>Entrá con tu usuario admin para ver dispositivos, eventos y firmwares.</p>

    <form method="post" action="/login">
      <label>Usuario</label>
      <input name="username" value="{username}" autocomplete="username" required />
      <label>Contraseña</label>
      <input name="password" type="password" autocomplete="current-password" required />
      <button type="submit">Entrar</button>
      {f'<div class="err">{error}</div>' if error else ''}
    </form>

    <div class="footer">Tip: el admin inicial se crea desde <code>ADMIN_USER</code>/<code>ADMIN_PASS</code> si la tabla está vacía.</div>
  </div>
</body>
</html>"""

def require_login(request: Request):
    user = request.session.get("user")
    if not user:
        # Para APIs devolvemos 401; para páginas HTML redirigimos (lo manejan las rutas)
        return None
    return user

def require_login_api(request: Request):
    user = request.session.get("user")
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="No autenticado")
    return user

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    # si ya está logueado, al dashboard
    if request.session.get("user"):
        return RedirectResponse(url="/", status_code=HTTP_303_SEE_OTHER)
    return HTMLResponse(_render_login())

@router.post("/login", response_class=HTMLResponse)
async def login_action(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db=Depends(get_db),
):
    username = username.strip()
    if not username or not password:
        return HTMLResponse(_render_login("Faltan datos", username))

    cur = db.cursor()
    cur.execute("SELECT id, username, password_hash, role FROM users WHERE username=%s", (username,))
    row = cur.fetchone()

    ok = False
    if row and pwd.verify(password, row["password_hash"]):
        ok = True

    if not ok:
        return HTMLResponse(_render_login("Usuario o contraseña incorrectos", username))

    request.session["user"] = {"id": row["id"], "username": row["username"], "role": row["role"]}
    return RedirectResponse(url="/", status_code=HTTP_303_SEE_OTHER)

@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=HTTP_303_SEE_OTHER)

def bootstrap_admin(db):
    """Crea el admin inicial si la tabla users está vacía."""
    cur = db.cursor()
    cur.execute("SELECT COUNT(*) as c FROM users")
    c = cur.fetchone()["c"]
    if c and int(c) > 0:
        return False

    u = settings.ADMIN_USER
    p = settings.ADMIN_PASS
    ph = pwd.hash(p)

    cur.execute("INSERT INTO users (username, password_hash, role) VALUES (%s,%s,'admin')", (u, ph))
    db.commit()
    return True
