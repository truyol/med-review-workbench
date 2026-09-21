from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Imported for Alembic metadata discovery.
from app import models  # noqa: E402,F401
