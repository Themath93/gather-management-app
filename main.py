import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from core.logging_setup import setup_logging
from core.middleware import LoggingMiddleware

from api.v1.router import api_router

setup_logging()

app = FastAPI()
app.add_middleware(LoggingMiddleware)
app.include_router(api_router, prefix="/api/v1")

static_dir = os.path.join(os.path.dirname(__file__), "static")

# static 폴더 mount
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# index.html 라우팅
@app.get("/")
def read_index():
    return FileResponse(os.path.join(static_dir, "index.html"))


@app.get("/admin")
def admin_page():
    return FileResponse(os.path.join("static", "admin.html"))

@app.get("/login")
def login_page():
    return FileResponse("static/login.html")