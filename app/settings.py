from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    data_dir: Path = Path("tests/data")
    link_info_filename: str = "link_info.parquet.gz"
    speed_data_filename: str = "duval_jan1_2024.parquet.gz"

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def link_info_file(self) -> Path:
        return self.data_dir / self.link_info_filename

    @property
    def speed_data_file(self) -> Path:
        return self.data_dir / self.speed_data_filename


settings = Settings()
