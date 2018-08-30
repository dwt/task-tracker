from flask import Flask, render_template
from todotxt import Todo
from textwrap import dedent

app = Flask(__name__)

@app.route('/') # methods=['GET', 'POST']
def index():
    task = Todo.from_lines(dedent("""
    Danish Developments
        first task id:1
            second task with a longer description that would surely be shortened id:2
            third task id:3
                with children id:4
            seventh task status:done id:5 @mh
            eight task status:doing id:6 @rb @juergen_klein
        fourth task id:7
            fifth task id:8
                sixth task id:9
            ninth task status:doing id:10 @fh
        lets have a really long task so the overflowing is nicely demonstrated for the top layer id:11
    """))
    return render_template('index.html', task=task)
