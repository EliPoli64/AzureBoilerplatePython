from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
import os

_SQL_CONN = os.getenv("SqlConnectionString")
if not _SQL_CONN:
    raise ValueError("SqlConnectionString environment variable is not set.")
ASYNC_URL = f"mssql+pyodbc:///?odbc_connect={_SQL_CONN.replace(' ', '+')}"

engine = create_async_engine(ASYNC_URL, echo=False, future=True)

SessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    expire_on_commit=False,
)

Base = declarative_base()

async def get_session():
    async with SessionLocal() as session:
        yield session