from sqlalchemy import Engine, create_engine, text

from app.settings import Settings, get_settings


def create_db_engine(settings: Settings | None = None) -> Engine:
    resolved = settings or get_settings()
    connect_args = (
        {"check_same_thread": False}
        if resolved.database_url.startswith("sqlite")
        else {}
    )
    return create_engine(resolved.database_url, connect_args=connect_args, future=True)


def check_database(engine: Engine | None = None) -> None:
    resolved_engine = engine or create_db_engine()
    with resolved_engine.connect() as connection:
        connection.execute(text("select 1"))
