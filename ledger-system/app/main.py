from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.database.connection import db_manager
from app.api.routes import accounts, transfers, events

# Configure logging
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up ledger service")
    await db_manager.connect()
    yield
    # Shutdown
    logger.info("Shutting down ledger service")
    await db_manager.disconnect()

app = FastAPI(
    title="Event-Sourced Ledger System",
    description="A double-entry, event-sourced ledger system with REST APIs",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(accounts.router, prefix="/ledger")
app.include_router(transfers.router, prefix="/ledger")
app.include_router(events.router, prefix="/ledger")

@app.get("/")
async def root():
    return {"message": "Event-Sourced Ledger System", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ledger-system"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )