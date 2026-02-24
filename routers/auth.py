from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from database import get_db
from security import verify_password
from config import settings

router = APIRouter()

def get_current_user(request: Request):
    return request.session.get("user")

def require_login(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="No logueado")
    return user

def require_admin(request: Request):
    user = require_login(request)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Solo admin")
    return user

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return request.app.state.templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...), db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT id, username, password_hash, role FROM users WHERE username=%s LIMIT 1", (username,))
    u = cur.fetchone()
    if not u or not verify_password(password, u["password_hash"]):
        return request.app.state.templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Credenciales inválidas"}
        )

    request.session["user"] = {"id": u["id"], "username": u["username"], "role": u["role"]}
    # Redirect según rol
    target = "/admin" if u["role"] == "admin" else "/app"
    return RedirectResponse(url=target, status_code=303)

@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)

# Para endpoints API que usan sesión (panel)
def require_login_api(request: Request):
    return require_login(request)

def require_admin_api(request: Request):
    return require_admin(request)