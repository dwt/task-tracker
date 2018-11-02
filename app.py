from textwrap import dedent

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO

from todotxt import Todo

app = Flask(__name__)
socketio = SocketIO(app)

@app.route('/', methods=['GET'])
def index():
    task = Todo.from_lines(open('todo.txt', encoding='utf8').read())
    return render_template('index.html', task=task)

@app.route('/api/v1/todos', methods=['GET', 'POST'])
def todos():
    task = Todo.from_lines(open('todo.txt', encoding='utf8').read())
    if 'POST' == request.method:
        task.json = request.json
        with open('todo.txt', encoding='utf8', mode='w') as f:
            f.write(str(task))
    return jsonify(dict(json=task.json, txt=str(task)))

@socketio.on('update_todo')
def update_todo(json):
    print('received json: ' + str(json))

if __name__ == '__main__':
    socketio.run(app)
