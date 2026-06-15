from fastapi import FastAPI

from app.api.v1.router import router


app = FastAPI(
    title="Data Quality & Report Management API",
    version="1.0.0"
)

app.include_router(router)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}