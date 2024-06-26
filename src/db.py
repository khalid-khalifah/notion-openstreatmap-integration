from sqlmodel import Field, SQLModel
from sqlalchemy import select, delete, create_engine, Column, JSON
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
import uuid
from datetime import datetime, timedelta
from .settings import get_settings

settings = get_settings()


class Location(SQLModel, table=True):
    id: str = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    latitude: float
    longitude: float
    status: str = Field(nullable=True)
    location_type: str = Field(nullable=True)
    area: float = Field(nullable=True)


class LastCallTime(SQLModel, table=True):
    id: str = Field(default_factory=uuid.uuid4, primary_key=True)
    last_call_time: datetime = Field(default_factory=datetime.now)


class CashedResult(SQLModel, table=True):
    id: str = Field(default_factory=uuid.uuid4, primary_key=True)
    data: list[dict] = Field(sa_column=Column(JSON))
    date: datetime = Field(default_factory=datetime.now)


engine = create_async_engine(f"sqlite+aiosqlite:///db.sqlite3")
session_generator = async_sessionmaker(engine, class_=AsyncSession)


async def get_session():
    async with session_generator() as session:
        yield session


async def create_all():
    engine = create_engine(f"sqlite:///db.sqlite3")
    SQLModel.metadata.create_all(engine)


async def get_cached_result(session: AsyncSession) -> list[Location]:
    result = await session.execute(select(CashedResult).order_by(CashedResult.date.desc()).limit(1))  # type: ignore
    data = result.scalars().first()
    now = datetime.now()
    if data and now - data.date < timedelta(minutes=settings.CACHE_TIME):
        return [Location(**item) for item in data.data]
    return []


async def write_to_cache(data: list[Location] | None, session: AsyncSession):
    if data:
        session.add(
            CashedResult(data=[location.model_dump(mode="json") for location in data])
        )
        await session.commit()


async def insert_data(data: list | None, session: AsyncSession) -> list[Location]:
    if data:
        await session.execute(delete(Location))

        for record in data:
            await session.merge(Location(**record))
        await session.merge(LastCallTime(last_call_time=datetime.now()))
        await session.commit()
    result = await session.execute(select(Location).where(Location.status.in_(settings.STATUS_TO_INCLUDE)))  # type: ignore
    result = result.scalars().all()
    result = list(result)
    await write_to_cache(result, session)
    return result


async def get_last_call_time(session: AsyncSession) -> datetime | None:
    result = await session.execute(select(LastCallTime).order_by(LastCallTime.last_call_time.desc()).limit(1))  # type: ignore
    data = result.scalars().first()
    return data.last_call_time if data else None
