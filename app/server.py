"""FastAPI server for the Partiful invite generator."""

from __future__ import annotations

from fastapi import FastAPI

from .extract import extract, ExtractionRequest, ExtractionResponse

app = FastAPI(title="Partiful Invite Generator", version="1.0.0")


@app.post("/extract", response_model=ExtractionResponse)
async def extract_event(request: ExtractionRequest) -> ExtractionResponse:
    """Extract structured event data from natural language."""
    return extract(request)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
