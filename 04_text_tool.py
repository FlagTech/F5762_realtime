from tools_utils import google_res
from tools_utils import tools
from tools_utils import call_tools
from openai import AsyncOpenAI
import asyncio

async def main():
    client = AsyncOpenAI()

    async with client.beta.realtime.connect(
        model="gpt-4o-realtime-preview"
    ) as connection:
        
        await connection.session.update(
            session={
                'modalities': ['text'],
                'tools': tools,
                "tool_choice": "auto"
            }
        )

        await connection.conversation.item.create(
            item={
                "type": "message",
                "role": "user",
                "content": [{
                    "type": "input_text", 
                    "text": "十二強棒球賽冠軍是哪一隊？"
                }],
            }
        )
        await connection.response.create()
        
        async for event in connection:
            print(event.type)
            if event.type == 'response.text.done':
                print(event.text)
                return
            elif event.type == "response.done":
                msgs = call_tools(event.response.output)
                if msgs == []: continue
                for msg in msgs:
                    await connection.conversation.item.create(
                        item = msg
                    )
                await connection.response.create()               
            elif event.type == "error":
                print(f'\t{event.error.message}')

asyncio.run(main())