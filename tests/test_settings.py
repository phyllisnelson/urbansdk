from pathlib import Path

from app.settings import Settings


def test_settings_file_properties():
    s = Settings(
        database_url="postgresql+psycopg2://u:p@localhost:5432/db",
        data_dir=Path("/tmp/data"),
        link_info_filename="links.parquet.gz",
        speed_data_filename="speed.parquet.gz",
    )

    assert s.link_info_file == Path("/tmp/data/links.parquet.gz")
    assert s.speed_data_file == Path("/tmp/data/speed.parquet.gz")
