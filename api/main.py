from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .cases import router as cases_router

app = FastAPI(title="Grande Investigations API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cases_router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
