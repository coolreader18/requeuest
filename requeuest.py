from flask import Flask, request, redirect, render_template, url_for

import hashlib

import song_queue
import youtube_dl

app = Flask(__name__)

@app.route('/')
def main():
    return render_template("index.html", status=request.args.get("status"))

@app.route("/queue-song", methods=["POST"])
def queue_song():
    url = request.form["url"]
    output_file = (
        song_queue.AUDIO_DIR + "/" + hashlib.md5(url.encode()).hexdigest() + ".mp3"
    )
    with song_queue.make_ydl(output_file) as ydl:
        try:
            ydl.download([url])
            ret = 0
        except youtube_dl.utils.YoutubeDLError as e:
            ret = e.args[0]
    song_queue.queue_song(output_file)
    return redirect(url_for(".main", status=ret))
