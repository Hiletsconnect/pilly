from fastapi import APIRouter, Request, Depends
from routers.auth import require_admin_api

router = APIRouter()

@router.get("/admin")
def admin_dashboard(request: Request, _=Depends(require_admin_api)):
    return request.app.state.templates.TemplateResponse("admin_dashboard.html", {"request": request})