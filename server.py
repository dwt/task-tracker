from flask import Flask, render_template
from todotxt import Todo
from textwrap import dedent

app = Flask(__name__)

@app.route('/') # methods=['GET', 'POST']
def index():
    return render_template('index.html', todos=Todo.from_lines(dedent("""
    first task
        second task with a longer description that would surely be shortened
        third task
            with children
        seventh task status:done
        eight task status:doing
    fourth task
        fifth task
            sixth task
        ninth task status:doing
    """)))
