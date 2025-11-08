"""
FastAPI application for serving VerityNgn reports.

This API server provides endpoints to serve HTML, JSON, and Markdown reports,
making all links in HTML reports work correctly.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from verityngn.api.routes import reports, verification

app = FastAPI(
    title="VerityNgn API",
    description="API for video verification and serving reports",
    version="1.0.0",
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])
app.include_router(verification.router, prefix="/api/v1/verification", tags=["verification"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)





