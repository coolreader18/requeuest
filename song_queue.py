import os
import queue
import threading

import youtube_dl
from playsound import playsound

AUDIO_DIR = os.path.join(os.path.dirname(__file__), "audio")
if not os.path.exists(AUDIO_DIR):
    os.makedirs(AUDIO_DIR)

song_queue = queue.Queue()


def play_worker(played=()):
    played = set(played)
    while True:
        try:
            # if there aren't 5 songs in the previously played queue, wait
            song = song_queue.get(len(played) < 5)
            played.add(song)
            playsound(song)
            song_queue.task_done()
        except queue.Empty:
            playsound(random.choice(tuple(played)))


prev_queue = list(os.listdir(AUDIO_DIR))

t = threading.Thread(target=play_worker, args=(prev_queue,))
t.start()


def make_ydl(out):
    return youtube_dl.YoutubeDL(
        {
            "quiet": True,
            "format": "bestaudio/best",
            "download_archive": "archive.txt",
            "outtmpl": out,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": 5,
                    "nopostoverwrites": False,
                }
            ],
            "no_color": True,
        }
    )


queue_song = song_queue.put
