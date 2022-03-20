from flask import Flask
from flask import request, url_for, redirect
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'gJ9c96Tz6sI5wzeb420x1zIdu7ZCx5BYmLZfBDHn'


@app.route('/sample_file_upload', methods=['POST', 'GET'])
def sample_file_upload():
    if request.method == 'GET':
        return f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
     <link rel="stylesheet"
     href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.0-beta1/dist/css/bootstrap.min.css"
     integrity="sha384-giJF6kkoqNQ00vy+HMDP7azOuL0xtbfIcaT9wjKHr8RbDVddVHyTfAAsrekwKmP1"
     crossorigin="anonymous">
    <link rel="stylesheet" type="text/css" href="{url_for('static', filename='css/style.css')}" />
    <title>Пример загрузки файла</title>
  </head>
  <body>
    <h1>Загрузить файл</h1>
    <form method="post" enctype="multipart/form-data">
       <div class="form-group">
            <label for="photo">Выберите файл</label>
            <input type="file" class="form-control-file" id="photo" name="file">
            <img src="{url_for('static', filename='imgs/temp')}"
                    width="300" height="300">
        </div>
        <button type="submit" class="btn btn-primary">Отправить</button>
    </form>
  </body>
</html>'''
    elif request.method == 'POST':
        file = request.files['file']
        if file:
            path_to_file = os.path.dirname(__file__)
            full_path = os.path.join(path_to_file, "static", "imgs")
            file.save(os.path.join(full_path, "temp"))
            return redirect("/sample_file_upload")


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')
