"""server.py - small FastAPI backend."""

from __future__ import annotations

import json
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from auraqa import generator, runner, reporter

app = FastAPI(title="AuraQA")

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"],
    allow_headers=["*"],
)

REPORT_JSON = os.path.join(os.getcwd(), "reports", "report.json")
FRONTEND_DIR = os.path.join(os.getcwd(), "frontend")
STORE_DIR = os.path.join(os.getcwd(), "tests_store")


class RunRequest(BaseModel):
    suite: str
    heal: bool = True
    headed: bool = False


class GenRequest(BaseModel):
    url: str
    flows: int = 3


@app.get("/api/suites")
def suites():
    """List every saved test suite in tests_store/."""
    if not os.path.isdir(STORE_DIR):
        return []
    return [
        {"name": f, "path": os.path.join("tests_store", f)}
        for f in sorted(os.listdir(STORE_DIR)) if f.endswith(".json")
    ]


@app.post("/api/generate")
def generate(req: GenRequest):
    """Visit a URL and let the AI write a new test suite for it."""
    suite = generator.generate_suite(req.url, n_flows=req.flows, save=False)
    safe = "".join(c if c.isalnum() else "_" for c in suite.name).lower()
    path = os.path.join("tests_store", f"{safe or 'suite'}.json")
    generator.save_suite(suite, path)
    return {"name": os.path.basename(path), "path": path,
            "steps": len(suite.steps)}


@app.post("/api/run")
def run(req: RunRequest):
    suite = generator.load_suite(req.suite)
    result = runner.run_suite(suite, heal=req.heal, headless=not req.headed)
    if req.heal and result.healed:
        generator.save_suite(suite, req.suite)
    reporter.build_report(result)
    return result.to_dict()


@app.get("/api/report")
def report():
    if not os.path.exists(REPORT_JSON):
        return JSONResponse(
            {"suite_name": "", "passed": 0, "healed": 0, "failed": 0,
             "results": []}
        )
    with open(REPORT_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)


@app.get("/")
def index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
