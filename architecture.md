# Architecture Diagram

```mermaid
flowchart TD
    subgraph Ingestion
        PQ1[link_info.parquet]
        PQ2[duval_jan1_2024.parquet]
        ING[python -m app.ingest]
        PQ1 --> ING
        PQ2 --> ING
    end

    subgraph Storage["PostgreSQL + PostGIS"]
        LNK[(links\nlink_id · road_name · geometry)]
        SR[(speed_records\nlink_id · timestamp · day_of_week · speed)]
        LNK -- FK --> SR
    end

    ING -- COPY / upsert --> Storage

    subgraph API["FastAPI Microservice (app/)"]
        MAIN[main.py]
        AGG[api/aggregates.py\nGET /aggregates/\nGET /aggregates/{link_id}\nPOST /aggregates/spatial_filter/]
        PAT[api/patterns.py\nGET /patterns/slow_links/]
        SCH[schemas/]
        MAIN --> AGG
        MAIN --> PAT
        AGG --> SCH
        PAT --> SCH
    end

    Storage -- SQLAlchemy ORM --> API

    subgraph Clients
        NB[Jupyter Notebook\nMapboxGL visualization]
        CL[curl / HTTP client]
    end

    API --> Clients
```

## Component Summary

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Ingestion | pandas + psycopg2 COPY | Bulk-load parquet datasets into PostgreSQL |
| Database | PostgreSQL 15 + PostGIS 3.3 | Spatial storage, geometry queries |
| ORM | SQLAlchemy 2.0 | Model definitions and query building |
| API | FastAPI | RESTful endpoints for aggregation and spatial queries |
| Visualization | MapboxGL + Jupyter | Interactive map of road segment speeds |
