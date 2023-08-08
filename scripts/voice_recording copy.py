import speech_recognition as sr
import requests
import websockets


def takecommand():  
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.pause_threshold = 1
        audio = r.listen(source)
        frames = audio.get_wav_data()
        if frames == b'':
            return None, None
        return frames, audio.sample_width
    

def send_bytes(frames: bytes, sample_width: int):
    requests.post(
        f'http://localhost:8000/64d22632419a232875f6d4e4/recording?sample_width={sample_width}', 
        data=frames,
        headers={
            'Content-Type': 'application/octet-stream',
            "cookie": "session=eyJzZXNzaW9uX2lkIjogInNlc3Npb246NTg1YzBjYTc1MjIxNzlmMzNmMzI3ZDYxYjY4OWQyNThmYTM3MWNkMDBiYjNkZmY4MDMxZDFjYzAzNjEzNGUzNSJ9.ZNI2tw.05MNxpv8Rf1XU2UEKc7v7fT2Kwo"
            }
    )


print("Listening...")
while True:
    frames, sample_width = takecommand()
    if frames is None:
        continue
    send_bytes(frames, sample_width)

