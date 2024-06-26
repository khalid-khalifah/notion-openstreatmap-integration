from .notion import fetch_data
from .db import Location, create_all, get_session, get_cached_result

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")
# create tables when start 
@app.on_event("startup")
async def startup_event():
    await create_all()

@app.get('/api/locations', response_model=list[Location])
async def get_locations(session: AsyncSession = Depends(get_session)):
    cached_result = await get_cached_result(session)
    if cached_result:
        return cached_result
    data = await fetch_data(session)
    return data

@app.get('/')
async def index(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
