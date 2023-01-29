# This file defines an interface for talking with the airtable API
import aiohttp
import os
import datetime
from config import cfg


class Airtable():
    def __init__(self) -> None:
        self.apikey: str = os.environ.get("AIRTABLE")
        self.session: aiohttp.ClientSession = None
        self.explore: dict = None
        self.lastfetch = None

    async def refresh_records(self) -> None:
        headers = {"Authorization": f"Bearer {self.apikey}"}

        if not self.session:
            self.session = aiohttp.ClientSession()

        params = {"view": "Approved Sheets"}  # Get only the approved sheets
        async with self.session.get(cfg["Settings"]["airtable-url"],
                                    headers=headers, params=params) as resp:
            self.explore = await resp.json()
            self.lastfetch = datetime.datetime.utcnow()

    @property
    async def sheets(self) -> dict:
        '''
        Fetches sheets, possibly using cached
        '''
        if not self.lastfetch or \
                datetime.datetime.utcnow() - self.lastfetch > \
                datetime.timedelta(seconds=300):
            await self.refresh_records()
            print("Airtable records refreshed due to staleness (300).")
        return self.explore["records"]

    async def find_sheet(self, name: str) -> dict:
        '''
        Finds named sheet
        '''
        for record in await self.sheets:
            if record["fields"]["Sheet Name"].lower() == name.lower():
                return record
        return None
