import os
import queue
import threading
import hashlib
import random

import youtube_dl
import playsound

AUDIO_DIR = os.path.join(os.path.dirname(__file__), "audio")
if not os.path.exists(AUDIO_DIR):
    os.makedirs(AUDIO_DIR)

song_queue = queue.Queue()

played = set(os.listdir(AUDIO_DIR))

currently_playing = None


def playsong(song, retry=4):
    try:
        playsound.playsound(song)
    except playsound.PlaysoundException:
        if retry > 0:
            playsong(song, retry=retry - 1)


def play_worker():
    global currently_playing
    while True:
        try:
            # if there aren't 5 songs in the previously played queue, wait
            songfile, url = song_queue.get(len(played) < 5)
            played.add(songfile)
            currently_playing = url
            playsong(songfile)
            song_queue.task_done()
            currently_playing = None
        except queue.Empty:
            playsong(random.choice(tuple(played)))


t = threading.Thread(target=play_worker, daemon=True)
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


def queue_song(url):
    output_file = AUDIO_DIR + "/" + hashlib.md5(url.encode()).hexdigest() + ".mp3"
    info = output_file, url

    if currently_playing == url or info in song_queue.queue:
        raise Exception("song already in queue, wait until it plays")

    with make_ydl(output_file) as ydl:
        ydl.download([url])
    song_queue.put((output_file, url))
