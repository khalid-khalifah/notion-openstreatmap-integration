from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import select, delete, create_engine, Column, JSON
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
import uuid
from datetime import datetime, timedelta
from .settings import get_settings


settings = get_settings()


class Status(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str 
    color: str = Field(default='Blue', nullable=True)

class Location(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    database_id: str
    name: str
    latitude: float
    longitude: float
    location_type: str = Field(nullable=True)
    area: float = Field(nullable=True)
    status: dict = Field(sa_column=Column(JSON))

class LastCallTime(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    database_id: str 
    last_call_time: datetime = Field(default_factory=datetime.now)

class CashedResult(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
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

async def pick_status_color(status: dict, session: AsyncSession) -> str:
    colors = ['red', 'yellow', 'green', 'blue', 'violet', 'grey', 'gold', 'orange', 'black']
    unique_colors = await session.execute(select(Status.color).distinct())  # type: ignore
    unique_colors_list = unique_colors.scalars().all()
    if status['color'] in colors:
        if status['color'] not in unique_colors_list and status['color'] in colors:
            return status['color']
    list_of_colors = [color for color in colors if color not in unique_colors_list]
    return list_of_colors[0]


async def get_or_create_status(session: AsyncSession, status:dict) -> Status:
    result = await session.execute(select(Status).where(Status.name == status['name']))  # type: ignore
    result = result.scalars().first()
    if result:
        return result
    color = await pick_status_color(status, session)
    status_obj = Status(name= status['name'], color= color)
    session.add(status_obj)
    await session.commit()
    await session.refresh(status_obj)   
    return status_obj

async def insert_data(data: list | None, session: AsyncSession, database_id: str) -> list[Location]:
    if data:
        await session.execute(delete(Location).where(Location.database_id == database_id))   # type: ignore
        await session.commit() 
        for record in data:
            status = await get_or_create_status(session, record.pop('status'))  
            session.add(Location(database_id=database_id, **record, status= status.model_dump(mode="json")))
        session.add(LastCallTime(database_id=database_id, last_call_time=datetime.now()))
        await session.commit()
    result = await session.execute(select(Location).where(Location.database_id == database_id))  # type: ignore
    result = result.scalars().all()
    final_result = [x.model_dump(mode="json") for x in result]
    return [Location(**x) for x in final_result]


async def get_last_call_time(session: AsyncSession, database_id: str) -> datetime | None:
    result = await session.execute(select(LastCallTime).where(LastCallTime.database_id == database_id).order_by(LastCallTime.last_call_time.desc()).limit(1))  # type: ignore
    data = result.scalars().first()
    return data.last_call_time if data else None
