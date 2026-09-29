"""
Vercel Serverless Entrypoint for Adsviwer / Mundo Revalida Competitor Intelligence
Author: Lagana Flow
"""
import sys
from pathlib import Path
from fastapi import Request

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard.app import app


@app.middleware("http")
async def vercel_path_rewrite_middleware(request: Request, call_next):
    # Retrieve original path forwarded via query parameter _path
    orig_path = request.query_params.get("_path")
    if orig_path:
        clean_path = "/" + orig_path.lstrip("/").split("?")[0]
        request.scope["path"] = clean_path
        request.scope["raw_path"] = clean_path.encode("latin1")
    return await call_next(request)


@app.get("/api/index")
def api_index_direct():
    from src.dashboard.app import get_dashboard
    return get_dashboard()
