from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mcp.server.fastmcp.server import StreamableHTTPASGIApp
from starlette.routing import Route

from .api import api_router
from .core.config import settings
from .core.database import engine, Base
from .mcp.server import McpBearerAuth, paywise_mcp

# Create database tables
Base.metadata.create_all(bind=engine)

# Building the MCP app also creates its session manager, which must run
# for the lifetime of the server.
paywise_mcp.streamable_http_app()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    async with paywise_mcp.session_manager.run():
        yield


app = FastAPI(
    lifespan=lifespan,
    title=settings.app_name,
    version=settings.app_version,
    description="Smart Payment Recommendation API",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://blissful-charisma-production.up.railway.app",
        "https://paywise-production-35a1.up.railway.app",
        "https://paywise.vikramkumar.org",
        "https://paywise-beta.vikramkumar.org",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.app_version}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
    }


# Include API routes
app.include_router(api_router, prefix="/api")

# Claude connector endpoint: https://<backend>/mcp  (Bearer pw_live_... required)
app.router.routes.append(
    Route("/mcp", endpoint=McpBearerAuth(StreamableHTTPASGIApp(paywise_mcp.session_manager)))
)
