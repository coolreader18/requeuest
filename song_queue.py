import os
import queue
import threading
import hashlib
import random

import youtube_dl
import simpleaudio as sa

AUDIO_DIR = os.path.join(os.path.dirname(__file__), "audio")
if not os.path.exists(AUDIO_DIR):
    os.makedirs(AUDIO_DIR)

song_queue = queue.Queue()

played = set()

currently_playing = None

skip_event = threading.Event()


def playsong(song, retry=4):
    wav = sa.WaveObject.from_wave_file(song)
    play = wav.play()
    while play.is_playing():
        if skip_event.wait(timeout=0.5):
            skip_event.clear()
            play.stop()
            break


def play_worker():
    global currently_playing
    while True:
        try:
            # if there aren't 5 songs in the previously played queue, wait
            info = song_queue.get(len(played) < 5)
            played.add(info)
        except queue.Empty:
            info = random.choice(tuple(played))
        songfile, url = info
        currently_playing = url
        playsong(songfile)
        song_queue.task_done()
        currently_playing = None


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
                    "preferredcodec": "wav",
                    "preferredquality": "5",
                }
            ],
            "no_color": True,
        }
    )


def queue_song(url):
    with make_ydl("") as ydl:
        info_dict = ydl.extract_info(url, process=False,)
        url = info_dict.get("url", info_dict.get("webpage_url", url))
        output_file = AUDIO_DIR + "/" + hashlib.md5(url.encode()).hexdigest()
        info = output_file + ".wav", url
        ydl.params["outtmpl"] = output_file + ".pre"
        if currently_playing == url or info in song_queue.queue:
            raise Exception("song already in queue, wait until it plays")
        ydl.process_ie_result(info_dict)

    song_queue.put(info)
