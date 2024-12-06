import sys
import os

import sqlalchemy
from alembic import context
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.constants import DATABASE_URL

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/../"
sys.path.append(BASE_DIR)
from app.db import Base  # Import your async Base

target_metadata = Base.metadata

config = context.config


def run_sync_migrations(config):
    """
    Run migrations in 'online' mode using a synchronous engine.
    """
    url = DATABASE_URL.replace("postgresql+asyncpg", "postgresql")

    engine = create_engine(url, echo=True)  # Use sync engine here
    # Get connection and configure context
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=Base.metadata,
            compare_type=True,
        )

        # Running the migrations
        with context.begin_transaction():
            context.run_migrations()


def run(config):
    """Run migrations in 'online' mode."""
    run_sync_migrations(config)


run(config)
