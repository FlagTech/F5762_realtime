import asyncio
from urllib import response
import openai

async def main():
    client = openai.AsyncOpenAI()

    # 連線建立 session
    async with client.beta.realtime.connect(
        model="gpt-4o-realtime-preview"
    ) as connection:
        
        # 更新 session設定僅回覆文字，不生成語音
        await connection.session.update(
            session={
                'modalities': ['text'],
                'instructions': '使用繁體中文'
            })
        # 建立一個新的對話項目
        await connection.conversation.item.create(
            item={
                "type": "message",
                "role": "user",
                "content": [{
                    "type": "input_text", 
                    "text": "你好"
                }],
            }
        )
        # 要求生成回覆
        await connection.response.create()
        # 處理伺服端送來的事件
        async for event in connection:
            print(event.type)
            if event.type == 'response.text.delta':
                print(event.delta)
            elif event.type == 'response.text.done':
                print(event.text)
            elif event.type == "response.done":
                # 取得熟悉的回應物件
                response = event.response
                print(response.output[0].content[0].text)
                return

if __name__ == "__main__":
    asyncio.run(main())