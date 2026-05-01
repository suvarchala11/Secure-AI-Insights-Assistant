"""
FastAPI Application Entry Point

Startup sequence:
  1. Load all CSVs into DataStore
  2. Build FAISS vector index from docs
  3. Register routers
  4. Serve
"""
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.data_loader import store, get_vector_store
from backend.routers.chat import router as chat_router

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)


# ── Lifespan (startup / shutdown) ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("═══ Insights Assistant starting up ═══")
    try:
        store.load()
        get_vector_store()   # build + cache FAISS index
        log.info("═══ All data sources ready ═══")
    except Exception as e:
        log.error(f"Startup failed: {e}")
        raise
    yield
    log.info("═══ Insights Assistant shutting down ═══")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Secure AI Insights Assistant",
    description="Multi-source analytics assistant with tool-based LLM access",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow frontend (any origin in dev — lock this down in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "model": "ollama/llama3.2:3b",
        "data_sources": ["movies.csv", "viewers.csv", "watch_activity.csv",
                         "reviews.csv", "marketing_spend.csv",
                         "regional_performance.csv", "docs/*.txt"],
    }
