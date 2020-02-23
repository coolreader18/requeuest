from flask import Flask, request, redirect, render_template, url_for

import song_queue

app = Flask(__name__)


@app.route("/")
def main():
    return render_template(
        "index.html",
        ok=request.args.get("ok"),
        err=request.args.get("err"),
        playing=song_queue.playing,
        queue=tuple(song_queue.song_queue.queue),
    )


def result(**args):
    return redirect(url_for(".main", **args))


@app.route("/queue-song", methods=["POST"])
def queue_song():
    url = request.form["url"]
    if url.startswith("skipsong "):
        with open("skippasswd") as f:
            secret = f.read()
        if url == "skipsong " + secret:
            song_queue.skip_event.set()
            return result(ok=0)
    try:
        song_queue.queue_song(url)
    except Exception as e:
        return result(ok=1, err=e.args[0])
    else:
        return result(ok=0)


song_queue.start()

if __name__ == "__main__":
    app.run()
