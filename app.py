from flask import Flask, render_template
from todotxt import Todo
from textwrap import dedent

app = Flask(__name__)

@app.route('/') # methods=['GET', 'POST']
def index():
    task = Todo.from_lines(open('todo.txt', encoding='utf8').read())
    return render_template('index.html', task=task)
