import asyncio
from functools import reduce
from pprint import pprint

from .notion import fetch_data
from .db import Location, create_all, get_session, get_cached_result, write_to_cache
from .settings import get_settings

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates

settings = get_settings()
app = FastAPI()
templates = Jinja2Templates(directory="templates")


# create tables when start
@app.on_event("startup")
async def startup_event():
    await create_all()


@app.get("/api/locations", response_model=list[Location])
async def get_locations(session: AsyncSession = Depends(get_session)):
    async with session:
        if cached_result := await get_cached_result(session):
            return cached_result
        data = await asyncio.gather(*[fetch_data(session, database_id) for database_id in settings.NOTION_DATABASE_ID])
        data = reduce(lambda x, y: x + y, data)
        await write_to_cache(data, session)
        return data


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.jinja", {"request": request, 'settings':settings})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
