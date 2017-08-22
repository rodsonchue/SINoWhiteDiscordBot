import asyncio
import aiohttp
import async_timeout
import json

class JishoResult:
    def __init__(self):
        self.japanese = list()
        self.definitions = list()

async def fetch(session, url):
    with async_timeout.timeout(10):
        async with session.get(url) as response:
            return await response.text()

async def j2e(query):
    result = list()
    async with aiohttp.ClientSession() as session:
        response = await fetch(session, 'http://jisho.org/api/v1/search/words?keyword='+query)
        payload = json.loads(response)['data']
        for match in payload:
            jsresult = JishoResult()

            japanese = match['japanese']
            for japanese_match in japanese:
                jsresult.japanese.append(japanese_match)
                print (japanese_match)
                
            senses = match['senses']
            for sense in senses:
                jsresult.definitions.append(sense['english_definitions'])

            result.append(jsresult)
            
    return result
