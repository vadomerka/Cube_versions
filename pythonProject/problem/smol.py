from flask import Flask, url_for

app = Flask(__name__)


@app.route('/')
def index():
    return url_for("static", filename="еуые.mp3")


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')
