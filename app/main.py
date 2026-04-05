from fastapi import FastAPI

from app.api import aggregates, patterns

app = FastAPI(
    title="UrbanSDK Traffic API",
    description="Geospatial traffic microservice — speed aggregation over PostGIS road segments.",
    version="0.1.0",
)

app.include_router(aggregates.router)
app.include_router(patterns.router)


@app.get("/health")
def health():
    return {"status": "ok"}
