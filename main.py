from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager

from config import settings
from database import init_db

from routers import auth, admin, app_client, devices, events, ota, admin_tools

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_SECRET)

templates = Jinja2Templates(directory="templates")
app.state.templates = templates

app.mount("/static", StaticFiles(directory="static"), name="static")

# Routes
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(app_client.router)
app.include_router(devices.router)
app.include_router(events.router)
app.include_router(ota.router)
app.include_router(admin_tools.router)

@app.get("/")
def root():
    return RedirectResponse("/login", status_code=303)