import os
import queue
import threading
import collections
import random
import pickle

import youtube_dl
import simpleaudio as sa

SCRIPT_DIR = os.path.dirname(__file__)

INFO_FILE = os.path.join(SCRIPT_DIR, "queue_info")

AUDIO_DIR = os.path.join(SCRIPT_DIR, "audio")
if not os.path.exists(AUDIO_DIR):
    os.makedirs(AUDIO_DIR)

info_fields = ("id", "url", "title", "filename")
SongInfo = collections.namedtuple("SongInfo", info_fields)


class SongInfo(SongInfo):
    @classmethod
    def filter_dict(cls, info_dict):
        info_dict["url"] = info_dict.get("webpage_url")
        d = {k: info_dict.get(k) for k in info_fields}
        return cls(**d)

    def __eq__(self, other):
        item_eq = lambda s: getattr(self, s, object()) == getattr(other, s, object())
        return other and any(map(item_eq, info_fields))

    def __hash__(self):
        return super().__hash__()


song_queue = queue.Queue()

if os.path.exists(INFO_FILE):
    with open(INFO_FILE, "rb") as f:
        playing, q, played = pickle.load(f)
        song_queue.queue = q
else:
    playing = None
    played = set()

statelock = threading.Lock()


def savestate():
    with statelock, open(INFO_FILE, "wb") as f:
        pickle.dump((playing, song_queue.queue, played), f)


skip_event = threading.Event()


def playsong(info, retry=4):
    wav = sa.WaveObject.from_wave_file(info.filename)
    play = wav.play()
    while play.is_playing():
        if skip_event.wait(timeout=0.5):
            skip_event.clear()
            play.stop()
            played.remove(info)
            break


def get_song():
    try:
        # if there aren't 5 songs in the previously played queue, wait
        return song_queue.get(len(played) < 5)
    except queue.Empty:
        return random.choice(tuple(played))


def play_worker():
    global playing
    while True:
        if playing is None:
            playing = get_song()
        played.add(playing)
        savestate()
        playsong(playing)
        playing = None
        savestate()


t = threading.Thread(target=play_worker, daemon=True)
start = t.start

ydl = youtube_dl.YoutubeDL(
    {
        # "quiet": True,
        "outtmpl": AUDIO_DIR + "/%(title)s-%(id)s.%(ext)s",
        "format": "bestaudio/best",
        "download_archive": "archive.txt",
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
    info_dict = ydl.extract_info(url, process=False)
    info_dict = ydl.process_ie_result(info_dict, download=True)
    info_dict["filename"] = (
        os.path.splitext(ydl.prepare_filename(info_dict))[0] + ".wav"
    )
    info_dict = SongInfo.filter_dict(info_dict)
    if info_dict == playing or any(
        map(lambda info: info == info_dict, song_queue.queue)
    ):
        raise Exception("song already in queue, wait until it plays")

    song_queue.put(info_dict)
    savestate()
