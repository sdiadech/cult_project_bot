from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.declarative import declarative_base

# Base class for models
Base = declarative_base()

import asyncpg
from config.constants import DATABASE_URL


class DatabaseMiddleware(BaseMiddleware):
    """
    Middleware to inject the database pool into handler contexts.
    """

    def __init__(self, pool):
        self.pool = pool

    async def __call__(self, handler, event: TelegramObject, data: dict):
        # Add the pool to the handler data
        data["pool"] = self.pool
        return await handler(event, data)


async def init_db_pool() -> asyncpg.Pool:
    """
    Initialize the asyncpg connection pool.
    """
    # Assuming DATABASE_URL is in the format: "postgresql://user:password@localhost/dbname"
    url = DATABASE_URL.replace("postgresql+asyncpg", "postgresql")
    pool = await asyncpg.create_pool(url, min_size=1, max_size=10, command_timeout=60)
    return pool


async def close_db_pool() -> None:
    """
    Close the asyncpg connection pool.
    """
    global pool
    if pool:
        await pool.close()


async def insert_payment(pool, payment_data):
    """
    Insert payment data into the database using the asyncpg connection pool.

    Args:
        pool: The asyncpg connection pool.
        payment_data: A dictionary with keys: telegram_id, user_name, course_name, amount, status.
    """
    query = """
    INSERT INTO payments (telegram_id, user_name, course_name, amount, status)
    VALUES ($1, $2, $3, $4, $5)
    """
    # Use positional unpacking for the values
    async with pool.acquire() as conn:
        await conn.execute(
            query,
            payment_data["telegram_id"],
            payment_data["user_name"],
            payment_data["course_name"],
            payment_data["amount"],
            payment_data["status"],
        )
