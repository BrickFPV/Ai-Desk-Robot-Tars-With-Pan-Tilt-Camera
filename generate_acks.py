import asyncio
import os
from groq import AsyncGroq

GROQ_API_KEY = "PLACE YOUR GROQ API KEY HERE"
GROQ_TTS_MODEL = "canopylabs/orpheus-v1-english"
GROQ_TTS_VOICE = "troy"

ACK_DIR = os.path.join(os.path.dirname(__file__), "acks")
ACK_PHRASES = ["HUH?", "YES?", "YOU CALLED?", "GO ON", "THATS ME"]

client = AsyncGroq(api_key=GROQ_API_KEY)

async def generate_acks():
    os.makedirs(ACK_DIR, exist_ok=True)
    for phrase in ACK_PHRASES:
        filename = phrase.lower().replace("?", "").replace(" ", "_") + ".wav"
        filepath = os.path.join(ACK_DIR, filename)
        response = await client.audio.speech.create(
            model=GROQ_TTS_MODEL,
            voice=GROQ_TTS_VOICE,
            input=phrase,
            response_format="wav"
        )
        audio_bytes = await response.read()
        with open(filepath, "wb") as f:
            f.write(audio_bytes)
    print("Offline acknowledgments generated in 'acks/' directory.")

if __name__ == "__main__":
    asyncio.run(generate_acks())
