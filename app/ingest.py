"""
Data ingestion script.

Usage:
    python -m app.ingest           # ingest data from tests/data/ (or DATA_DIR env var)
    python -m app.ingest --migrate # create tables only, no data load
"""

import argparse
import io
import json
import logging

import pandas as pd
from shapely import wkt

from app.database import SessionLocal, migrate
from app.settings import settings

log = logging.getLogger(__name__)


def _copy_speed_records(df: pd.DataFrame, db) -> None:
    """Bulk-load speed records using PostgreSQL COPY (much faster than INSERT)."""
    buf = io.StringIO()
    df.to_csv(buf, index=False, header=False)
    buf.seek(0)

    sa_conn = db.connection()
    cursor = sa_conn.connection.dbapi_connection.cursor()
    cursor.copy_expert(
        "COPY speed_records (link_id, timestamp, day_of_week, speed) FROM STDIN WITH (FORMAT CSV)",
        buf,
    )
    cursor.close()


class Ingester:
    @property
    def link_info_file(self):
        return settings.link_info_file

    @property
    def speed_data_file(self):
        return settings.speed_data_file

    def load_links(self, df: pd.DataFrame, db) -> None:
        df.columns = [c.strip().lower() for c in df.columns]

        geom_col = next((c for c in df.columns if "geom" in c or "geo" in c or c == "wkt"), None)
        id_col = next((c for c in df.columns if "link_id" in c or c == "id"), None)
        name_col = next((c for c in df.columns if "name" in c or "road" in c), None)

        if geom_col is None or id_col is None:
            raise RuntimeError(
                f"Cannot identify id/geometry columns in link file. Columns: {list(df.columns)}"
            )

        out = pd.DataFrame({"link_id": df[id_col].astype(str)})
        out["road_name"] = df[name_col].where(df[name_col].notna(), None) if name_col else None
        # Normalise geometry to GeoJSON string; PostgreSQL will parse it

        def _to_geojson(g):
            if isinstance(g, str) and g.startswith("{"):
                return g
            if isinstance(g, str):
                return json.dumps(wkt.loads(g).__geo_interface__)
            return json.dumps(g.__geo_interface__)

        out["geo_json"] = df[geom_col].apply(_to_geojson)

        buf = io.StringIO()
        out.to_csv(buf, index=False, header=False)
        buf.seek(0)

        sa_conn = db.connection()
        cursor = sa_conn.connection.dbapi_connection.cursor()
        cursor.execute(
            "CREATE TEMP TABLE _links_stage"
            " (link_id text, road_name text, geo_json text) ON COMMIT DROP"
        )
        cursor.copy_expert(
            "COPY _links_stage (link_id, road_name, geo_json) FROM STDIN WITH (FORMAT CSV)",
            buf,
        )
        cursor.execute(
            """
            INSERT INTO links (link_id, road_name, geometry)
            SELECT link_id, road_name, ST_SetSRID(ST_GeomFromGeoJSON(geo_json), 4326)
            FROM _links_stage
            ON CONFLICT (link_id) DO UPDATE
                SET road_name = EXCLUDED.road_name,
                    geometry  = EXCLUDED.geometry
        """
        )
        cursor.close()
        db.commit()
        log.info("Inserted/updated %d links.", len(out))

    def load_speed_records(self, df: pd.DataFrame, db) -> None:
        df.columns = [c.strip().lower() for c in df.columns]

        id_col = next((c for c in df.columns if "link_id" in c or c == "id"), None)
        ts_col = next((c for c in df.columns if "time" in c or "ts" in c or "date" in c), None)
        speed_col = next((c for c in df.columns if "speed" in c), None)

        if None in (id_col, ts_col, speed_col):
            raise RuntimeError(f"Cannot identify required columns. Columns: {list(df.columns)}")

        df = df[[id_col, ts_col, speed_col]].copy()
        df.columns = ["link_id", "timestamp", "speed"]
        df["link_id"] = df["link_id"].astype(str)
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        df["day_of_week"] = df["timestamp"].dt.isocalendar().day.astype(int)
        df = df[["link_id", "timestamp", "day_of_week", "speed"]]

        _copy_speed_records(df, db)
        db.commit()
        log.info("Inserted %d speed records.", len(df))

    def run(self) -> None:
        db = SessionLocal()
        try:
            log.info("Loading link info from %s …", self.link_info_file)
            self.load_links(pd.read_parquet(self.link_info_file), db)

            log.info("Loading speed data from %s …", self.speed_data_file)
            self.load_speed_records(pd.read_parquet(self.speed_data_file), db)
        finally:
            db.close()


if __name__ == "__main__":  # pragma: no cover
    parser = argparse.ArgumentParser()
    parser.add_argument("--migrate", action="store_true", help="Create tables only")
    args = parser.parse_args()

    migrate()
    if not args.migrate:
        Ingester().run()
