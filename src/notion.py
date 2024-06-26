import httpx
from datetime import datetime
import pytz

from sqlalchemy.ext.asyncio import AsyncSession
from .settings import get_settings
from .db import insert_data, get_last_call_time, Location

settings = get_settings()


def process_notion_data(data):
    results = data["results"]
    if not results:
        return []
    return [
        {
            "name": (
                properties["properties"]["Name"]["title"][0]["plain_text"]
                if properties["properties"]["Name"]["title"]
                else ""
            ),
            "latitude": properties["properties"]["Latitude"]["number"],
            "longitude": properties["properties"]["Longitude"]["number"],
            "status": (
                properties["properties"]["Status"]["select"]["name"]
                if properties["properties"]["Status"]["select"]
                else ""
            ),
            "location_type": (
                properties["properties"]["Location Type"]["select"]["name"]
                if properties["properties"]["Location Type"]["select"]
                else ""
            ),
            "area": properties["properties"]["Area"]["number"],
        }
        for properties in results
    ]


def process_time(time: datetime) -> datetime:
    if time.tzinfo is None:
        return time.replace(tzinfo=pytz.UTC)
    return time


async def fetch_data(session: AsyncSession) -> list[Location]:
    last_time_insert = await get_last_call_time(session)
    last_time_insert = last_time_insert or datetime(2000, 1, 1, tzinfo=pytz.UTC)
    last_time_insert = process_time(last_time_insert)

    data = await fetch_notion_data()

    if not data.get("results"):
        return []

    last_edited_time = data["results"][0]["last_edited_time"]
    last_edited_time = datetime.fromisoformat(last_edited_time)
    last_edited_time = process_time(last_edited_time)

    if last_edited_time > last_time_insert:
        data = process_notion_data(data)
    else:
        data = []
    db_data = await insert_data(data, session)
    return db_data


async def fetch_notion_data() -> dict:
    headers = {
        "Authorization": f"Bearer {settings.NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }
    url = f"https://api.notion.com/v1/databases/{settings.NOTION_DATABASE_ID}/query"
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers)
        data = response.json()
        if response.status_code != 200:
            print(response.json())
            return {}
        return data
