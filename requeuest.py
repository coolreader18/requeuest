from flask import Flask, request, redirect, render_template, url_for

import song_queue

app = Flask(__name__)


@app.route("/")
def main():
    return render_template(
        "index.html",
        ok=request.args.get("ok"),
        err=request.args.get("err"),
        playing=song_queue.currently_playing,
        queue=tuple(map(lambda x: x[1], song_queue.song_queue.queue)),
    )


@app.route("/queue-song", methods=["POST"])
def queue_song():
    url = request.form["url"]
    try:
        song_queue.queue_song(url)
    except Exception as e:
        params = {"ok": 1, "err": e.args[0]}
    else:
        params = {"ok": 0}
    return redirect(url_for(".main", **params))


if __name__ == "__main__":
    app.run()
