import speech_recognition as sr
import asyncio
import json
import websockets
import base64


def takecommand():  
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.pause_threshold = 1
        audio = r.listen(source)
        frames = audio.get_wav_data()
        return frames, audio.sample_width
    

async def send_bytes():
    url = 'ws://localhost:8000/ws/64d22632419a232875f6d4e4/recording'
    token = "eyJzZXNzaW9uX2lkIjogInNlc3Npb246OWM0ZTVhZTdkZjJmYTY5NjFhZmJhYjJjMTUxM2EyYmVmMTg0N2E0NzgyMDM5ZjM5YTk3NWJlYzhkZDg0NjUzOCJ9.ZNJZIQ.Acs0CtAvuY4cg9JumCvcnVBZ7T8"
    headers={
        "cookie": f"session={token}"
        }
    async with websockets.connect(url, extra_headers=headers) as ws:
        while True:
            frames, sample_width = takecommand()
            encoded_frames = base64.b64encode(frames).decode("utf-8")
            await ws.send(json.dumps({
                "frames": encoded_frames, 
                "sample_width": sample_width
            }))
            
asyncio.get_event_loop().run_until_complete(send_bytes())