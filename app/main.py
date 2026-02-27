from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import secrets
from database import engine
from models import Base
from database import SessionLocal
from models import URL
from sqlalchemy import text
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response


# יצירת האפליקציה
app = FastAPI(title="URL Shortener", version="0.2.0")
Base.metadata.create_all(bind=engine)

# הגדרת תיקיית templates
templates = Jinja2Templates(directory="templates")

# אחסון זמני בזיכרון (שלב ראשון בלבד)
url_store: dict[str, str] = {}


# -------------------------
# 1️⃣ Home Page (UI)
# -------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    """
    מחזיר את דף הבית עם הטופס.
    """
    return templates.TemplateResponse("index.html", {"request": request})


# -------------------------
# 2️⃣ Shorten via UI Form
# -------------------------
@app.post("/shorten-ui", response_class=HTMLResponse)
def shorten_ui(request: Request, url: str = Form(...)):
    db = SessionLocal()

    code = secrets.token_urlsafe(5)

    existing = db.query(URL).filter(URL.code == code).first()
    while existing:
        code = secrets.token_urlsafe(5)
        existing = db.query(URL).filter(URL.code == code).first()

    new_url = URL(code=code, original_url=url)
    db.add(new_url)
    db.commit()

    base_url = str(request.base_url).rstrip("/")
    short_url = f"{base_url}/{code}"

    db.close()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "short_url": short_url
        }
    )

# -------------------------
# 3️⃣ Health Check
# -------------------------
@app.get("/ready")
def readiness():
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        db.close()
        return {"status": "ok"}
    except Exception:
        db.close()
        raise HTTPException(status_code=500, detail="Database not available")

@app.get("/live")
def liveness():
    return {"status": "alive"}

# -------------------------
# 5️⃣ Metrics Endpoint
# -------------------------
@app.get("/metrics")
def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# -------------------------
# 4️⃣ Redirect Route (חייב להיות אחרון!)
# -------------------------
@app.get("/{code}")
def redirect(code: str):
    db = SessionLocal()

    url_entry = db.query(URL).filter(URL.code == code).first()

    db.close()

    if not url_entry:
        raise HTTPException(status_code=404, detail="Code not found")

    return RedirectResponse(url=url_entry.original_url, status_code=307)

