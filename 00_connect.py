import asyncio
import openai

async def main():
    client = openai.AsyncOpenAI()
    # 連線建立 session
    async with client.beta.realtime.connect(
        model='gpt-4o-realtime-preview'
    ) as connection:
        async for event in connection:
            print(event.type)
            return

if __name__ == "__main__":
    asyncio.run(main())