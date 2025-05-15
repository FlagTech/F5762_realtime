from audio_util import audio_to_pcm16_base64
from audio_util import AudioPlayerAsync
from openai import AsyncOpenAI
import asyncio
import base64

audio_player: AudioPlayerAsync = AudioPlayerAsync()

f = open("ask.mp3", "rb")
audio = f.read()
f.close()

audio = audio_to_pcm16_base64(audio)

async def main():
    client = AsyncOpenAI()

    async with client.beta.realtime.connect(
        model="gpt-4o-realtime-preview",
    ) as connection:
        await connection.session.update(
            session={
                'instructions': '使用繁體中文',
                'voice': 'echo'
            }
        )
        
        await connection.conversation.item.create(
            item={
                "type": "message",
                "role": "user",
                "content": [{
                    "type": "input_audio", "audio": audio
                }],
            }
        )
        await connection.response.create()

        async for event in connection:
            print(event.type)
            if event.type == "response.audio.delta":
                bytes_data = base64.b64decode(event.delta)
                audio_player.add_data(bytes_data)
            elif event.type == 'response.audio_transcript.done':
                print(event.transcript)
            elif event.type == 'response.text.done':
                print(event.text)
            elif event.type == 'response.done':
                while True:
                    await asyncio.sleep(1)
                    if audio_player.idle():
                        return

asyncio.run(main())