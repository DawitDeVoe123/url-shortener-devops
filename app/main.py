from fastapi import FastAPI, Depends, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter, Histogram
import secrets
import os
import time

from app.database import get_db, engine
from app.models import Base, Link, Click
from app.auth import verify_token

Base.metadata.create_all(bind=engine)

app = FastAPI(title="URL Shortener")
templates = Jinja2Templates(directory="app/templates")

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])
URLS_CREATED = Counter('urls_created_total', 'Total URLs created')
REDIRECTS_TOTAL = Counter('redirects_total', 'Total redirects')

class ShortenRequest(BaseModel):
    url: str
    custom_code: Optional[str] = None

def generate_short_code(length=6):
    return secrets.token_urlsafe(length)[:length]

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": None, "links": []})

# TEST ENDPOINT - No authentication required
@app.post("/api/test/shorten")
async def test_shorten_url(
    request_data: ShortenRequest,
    db: Session = Depends(get_db)
):
    """TEST ONLY: Create a shortened URL without authentication"""
    short_code = request_data.custom_code if request_data.custom_code else generate_short_code()
    
    existing = db.query(Link).filter(Link.short_code == short_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Short code already exists")
    
    link = Link(
        short_code=short_code,
        original_url=request_data.url,
        created_by="test_user"
    )
    
    db.add(link)
    db.commit()
    db.refresh(link)
    
    URLS_CREATED.inc()
    
    return {
        "short_url": f"http://192.168.137.229:8000/{short_code}",
        "short_code": short_code,
        "original_url": request_data.url
    }

@app.post("/api/shorten")
async def shorten_url(
    request_data: ShortenRequest,
    token: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    short_code = request_data.custom_code if request_data.custom_code else generate_short_code()
    
    existing = db.query(Link).filter(Link.short_code == short_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Short code already exists")
    
    link = Link(
        short_code=short_code,
        original_url=request_data.url,
        created_by=token["sub"]
    )
    
    db.add(link)
    db.commit()
    db.refresh(link)
    
    URLS_CREATED.inc()
    
    return {
        "short_url": f"http://192.168.137.229:8000/{short_code}",
        "short_code": short_code,
        "original_url": request_data.url
    }

@app.get("/{short_code}")
async def redirect_to_url(short_code: str, request: Request, db: Session = Depends(get_db)):
    link = db.query(Link).filter(Link.short_code == short_code, Link.is_active == 1).first()
    
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    click = Click(
        link_id=link.id,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    db.add(click)
    link.clicks += 1
    db.commit()
    
    REDIRECTS_TOTAL.inc()
    
    return RedirectResponse(url=link.original_url)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)