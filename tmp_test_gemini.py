import asyncio, os, sys
sys.path.append('C:/gemini-wa-bot')
from services.gemini import gemini_service
async def main():
    resp = await gemini_service.generate_response_with_history('halo', [])
    print('Response:', resp)
asyncio.run(main())