import os
from dataclasses import dataclass, fields

from dotenv import load_dotenv


@dataclass
class Config:
    DB_PATH: str = "referee.db"
    PORT: int = 8080
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"


def load_config() -> Config:
    """Load config from .env file and environment variables."""
    load_dotenv()

    kwargs = {}
    for f in fields(Config):
        val = os.environ.get(f.name)
        if val is not None:
            if f.type == "bool":
                kwargs[f.name] = val.lower() in ("true", "1", "yes")
            elif f.type == "int":
                kwargs[f.name] = int(val)
            else:
                kwargs[f.name] = val

    return Config(**kwargs)
