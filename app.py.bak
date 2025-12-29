import os
from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, redirect, url_for,abort, session, flash,jsonify
from functools import wraps
import config
app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'todo.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable = False)
    due_date = db.Column(db.Date, nullable = True)
    is_completed = db.Column(db.Boolean, default = False)
    def __repr__(self):
        return f'<Task{self.id}:{self.title}>'
def login_required(f):
    @wraps(f)
    def decorated_function(*arges, **kwargs):
        if 'logged_in' not in session:
            flash('请先登录','danger')
            return redirect(url_for('login'))
        return f(*arges, **kwargs)
    return decorated_function
@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        password_attempt = request.form.get('password')
        if password_attempt == config.MASTER_PASSWORD:
            session['logged_in'] = True
            flash('登录成功' ,'success')
            return redirect(url_for('index'))
        else:
            flash('密码错误','danger')

            return redirect(url_for('login'))
    return render_template('login.html')
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('你已成功登出','info')

    return redirect(url_for('login'))
@app.route('/',methods=['GET'])
@login_required
def index():

    tasks = Task.query.filter_by(is_completed = False).order_by(Task.due_date)

    return render_template('index.html',tasks = tasks)

@app.route('/add',methods=['POST'])
def add_task():

    title = request.form.get('title')
    due_date_str = request.form.get('due_date')

    due_date = None
    if due_date_str:
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
    new_task = Task(
        title = title,
        due_date = due_date,
        is_completed = False
)
    db.session.add(new_task)
    db.session.commit()
    return redirect(url_for('index'))
@app.route('/complete/<int:task_id>')
@login_required
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)

    task.is_completed = True

    db.session.commit()
    return redirect(url_for('index'))
@app.route('/delete/<int:task_id>')
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)

    db.session.delete(task)

    db.session.commit()

    return redirect(url_for('index'))

@app.route('/api/v2/tasks', methods = ['GET'])
@login_required
def get_tasks():
    try:
        tasks = Task.query.filter_by(is_completed=False).order_by(Task.due_date)
        tasks_serializable = []
        for task in tasks:
            tasks_serializable.append({
                'id':task.id,
                'title': task.title,
                'due_date': task.due_date.isoformat() if task.due_date else None,
                'is_completed': task.is_completed
            })

        return jsonify(tasks=tasks_serializable)
    except Exception as e:
        return jsonify(error = str(e)), 500
@app.route('/api/v2/tasks',methods = ['POST'])
@login_required
def add_task_api():
    try:
        data = request.get_json()
        if not data or 'title' not in data:
            return jsonify(error="Missing title"), 400

        due_date_str = data.get('due_date')
        due_date = None
        if due_date_str:
            due_date = datetime.strptime(due_date_str,'%Y-%m-%d').date()
        new_task = Task(
            title = data.get('title'),
            due_date = due_date,
            is_completed = False
        )
        db.session.add(new_task)
        db.session.commit()
        task_serializable = {
            'id': new_task.id,
            'title': new_task.title,
            'due_date': new_task.due_date.isoformat() if new_task.due_date else None
        }
        return jsonify(task = task_serializable), 201
    except Exception as e:
        db.session.rollback()
        return jsonify(error = str(e)), 500
@app.route('/api/v2/tasks/<int:task_id>', methods = ['DELETE'])
@login_required
def delete_task_api(task_id):
    try:
        task = Task.query.get_or_404(task_id)
        db.session.delete(task)
        db.session.commit()

        return jsonify(message="Task deleted successfully"), 200

    except Exception as e:
        db.session.rollback()
        return jsonify(error=str(e)),500

@app.route('/api/v2/tasks/<int:task_id>', methods = ['PATCH'])
@login_required
def update_task_api(task_id):
    try:
        data = request.get_json()
        task = Task.query.get_or_404(task_id)
        if 'title' in data:
            task.title = data.get('title')
        if 'is_completed' in data:
            task.is_completed = data.get('is_completed')
        if 'due_date' in data:
            due_date_str = data.get('due_date')
            if due_date_str:
                task.due_date = datetime.strptime(due_date_str,'%Y-%m-%d').date()
            else:
                task.due_date = None
        db.session.commit()
        task_serializable = {
            'id':task.id,
            'title':task.title,
            'due_date': task.due_date.isoformat() if task.due_date else None,
            'is_completed': task.is_completed
        }
        return jsonify(task = task_serializable), 200
    except Exception as e:
        db.session.rollback()
        return jsonify(error=str(e)),500

@app.route('/v2')
@login_required
def index_v2():

    return render_template('index_v2.html')
if __name__ == '__main__':

    app.run(debug=True)



