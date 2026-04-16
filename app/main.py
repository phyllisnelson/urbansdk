from fastapi import FastAPI

from app.api import aggregates, patterns

app = FastAPI(
    title="UrbanSDK Traffic API",
    description=(
        "Geospatial traffic microservice for ingesting and querying road segment speed data.\n\n"
        "## Endpoints\n\n"
        "- **GET /aggregates/** — Average speed per road segment for a given day and time period\n"
        "- **GET /aggregates/{link_id}** — Speed and metadata for a single road segment\n"
        "- **POST /aggregates/spatial_filter/** — Road segments intersecting a bounding box\n"
        "- **GET /patterns/slow_links/** — Links consistently below a speed threshold\n\n"
        "## Time Periods\n\n"
        "| ID | Name | Hours |\n"
        "|----|------|-------|\n"
        "| 1 | Overnight | 00:00–03:59 |\n"
        "| 2 | Early Morning | 04:00–06:59 |\n"
        "| 3 | AM Peak | 07:00–09:59 |\n"
        "| 4 | Midday | 10:00–12:59 |\n"
        "| 5 | Early Afternoon | 13:00–15:59 |\n"
        "| 6 | PM Peak | 16:00–18:59 |\n"
        "| 7 | Evening | 19:00–23:59 |\n"
    ),
    version="0.1.0",
)

app.include_router(aggregates.router)
app.include_router(patterns.router)


@app.get("/health")
def health():
    return {"status": "ok"}
