from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
import urllib.parse
from contextlib import asynccontextmanager

server = "localhost"
port = 1433
database = "VotoPV01"
driver = "ODBC Driver 17 for SQL Server"

rawConnString = (
    f"DRIVER={{{driver}}};"
    f"SERVER={server},{port};"
    f"DATABASE={database};"
    f"Trusted_Connection=yes;"
    f"TrustServerCertificate=yes;"
)
encodedConnString = urllib.parse.quote_plus(rawConnString)

asyncUrl = f"mssql+aioodbc:///?odbc_connect={encodedConnString}"

engine = create_async_engine(asyncUrl, echo=False, future=True)

SessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    expire_on_commit=False,
)

Base = declarative_base()

@asynccontextmanager
async def get_session():
    async with SessionLocal() as session:
        yield session
