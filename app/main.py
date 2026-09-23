import logging
import time
from uuid import uuid4
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from .config import settings
from .database import SessionLocal
from .routes import auth, campaigns, dashboard, events, users, organizations

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('deeptrace')
app = FastAPI(title='Deep Trace Security Platform', version='1.0.0', description='Tenant-isolated security operations API. Login, then use the bearer token in Authorize.')
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=['GET', 'POST', 'PATCH', 'DELETE'], allow_headers=['Authorization', 'Content-Type'])


@app.middleware('http')
async def request_context(request: Request, call_next):
    request_id = str(uuid4())
    start = time.monotonic()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception('Unhandled failure request_id=%s method=%s path=%s', request_id, request.method, request.url.path)
        response = JSONResponse(status_code=500, content={'detail': 'Unexpected server error', 'request_id': request_id})
    response.headers.update({'X-Request-ID': request_id, 'X-Content-Type-Options': 'nosniff', 'X-Frame-Options': 'DENY', 'Cache-Control': 'no-store'})
    logger.info('request_id=%s method=%s path=%s status=%s duration_ms=%.1f', request_id, request.method, request.url.path, response.status_code, (time.monotonic() - start) * 1000)
    return response


@app.exception_handler(IntegrityError)
async def conflict_handler(request: Request, exc: IntegrityError):
    return JSONResponse(status_code=409, content={'detail': 'This record already exists or violates a relationship constraint'})


@app.get('/api/health', tags=['Health'])
def health():
    with SessionLocal() as db:
        db.execute(text('SELECT 1'))
    return {'status': 'ok'}


for router in [auth.router, campaigns.router, events.router, users.router, dashboard.router, organizations.router]:
    app.include_router(router)
