import os
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.pipeline import run_agent
from agent.store import list_applications

app = FastAPI(title="JobPilot Agent")

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class RunRequest(BaseModel):
    job_text: str
    profile_text: str


@app.get("/")
def index():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/api/run")
async def run(req: RunRequest):
    result = await run_agent(req.job_text, req.profile_text)
    return result


@app.get("/api/applications")
def applications():
    return list_applications()


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
