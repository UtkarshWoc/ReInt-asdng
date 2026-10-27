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

    # Snapshot location: robust resolution across local, Docker, and Vercel serverless
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent

    @property
    def DATA_SNAPSHOT_PATH(self) -> Path:
        raw = os.getenv("DATA_SNAPSHOT_PATH", "data/jan_2026_snapshot.json")
        candidate = Path(raw)
        if candidate.is_absolute() and candidate.exists():
            return candidate
        # 1. Relative to backend directory (standard)
        if (self.BASE_DIR / raw).exists():
            return self.BASE_DIR / raw
        # 2. Relative to workspace root
        if (self.BASE_DIR.parent / raw).exists():
            return self.BASE_DIR.parent / raw
        # 3. If raw included 'data/...' but from root
        if (self.BASE_DIR / "data" / "jan_2026_snapshot.json").exists():
            return self.BASE_DIR / "data" / "jan_2026_snapshot.json"
        return self.BASE_DIR / raw


settings = Settings()
