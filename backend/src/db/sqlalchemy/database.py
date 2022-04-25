from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from src.config.settings import get_settings


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db_url():
    settings = get_settings()
    return f"postgresql://{settings.db_user}:{settings.db_pw}@{settings.db_url}:{settings.db_port}/{settings.db_database}"


engine = create_engine(
    get_db_url()
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
