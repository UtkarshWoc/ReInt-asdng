import os
from pathlib import Path


class Settings:
    PROJECT_NAME: str = "UK Wind Generation Day-Ahead Decision Support"
    API_V1_STR: str = "/api"
    DEFAULT_CUTOFF: str = os.getenv("DEFAULT_CUTOFF", "09:00")
    PORT: int = int(os.getenv("PORT", "8000"))

    # CORS configuration
    CORS_ORIGINS_RAW: str = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000,*",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS_RAW.split(",") if origin.strip()]

    # Snapshot location: default to data/jan_2026_snapshot.json relative to backend root
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_SNAPSHOT_PATH: Path = BASE_DIR / os.getenv("DATA_SNAPSHOT_PATH", "data/jan_2026_snapshot.json")


settings = Settings()
