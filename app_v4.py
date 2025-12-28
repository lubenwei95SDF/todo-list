import os
import jwt
import datetime
import uuid
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
import config

app = Flask(__name__)

app.config['SECRET_KEY'] = config.SECRET_KEY
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'todo_v4.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    public_id = db.Column(db.String(64), unique = True)
    name = db.Column(db.String(50), unique = True)
    password = db.Column(db.String(80))
    tasks = db.relationship('Task', backref='owner', lazy= True)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(200), nullable = False)
    due_date = db.Column(db.Date, nullable = False)
    is_completed = db.Column(db.Boolean, default = False)

    user_id = db.Column( db.Integer, db.ForeignKey('user.id'), nullable = False)

    def to_json(self):

        return{
            'id': self.id,
            'title': self.title,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'is_completed': self.is_completed
        }

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer'):
                token = auth_header.split(' ')[1]
        if not token:
            return jsonify({'message': 'Token is missing'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms = ["HS256"])
            current_user = User.query.filter_by(public_id = data['public_id']).first()
        except:
            return jsonify({'message': 'Token is invalid'}), 401
        return f(current_user, *args, **kwargs)
    return decorated


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if User.query.filter_by(name = data['name']).first():
        return jsonify({'message': '用户名已存在'}), 400
    hashed_pw = generate_password_hash(data['password'], method='pbkdf2:sha256')
    new_user = User(
        public_id = str(uuid.uuid4()),
        name = data['name'],
        password = hashed_pw,
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': '注册成功'})

@app.route('/login', methods=['POST'])
def login():
    auth = request.get_json()
    if not auth or not auth.get('name') or not auth.get('password'):
        return make_response('Could not verify', 401)
    user = User.query.filter_by(name = auth.get('name')).first()

    if not user:
        return make_response('用户不存在', 401)
    if check_password_hash(user.password, auth.get('password')):
        token = jwt.encode({'public_id': user.public_id,
                            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'], algorithm = 'HS256')
        return jsonify({'token': token})

    return make_response('密码错误', 401)

@app.route('/api/tasks', methods=['GET'])
@token_required
def get_tasks(current_user):
    output = [task.to_json() for task in current_user.tasks]
    return jsonify(({'tasks': output}))

@app.route('/api/tasks', methods=['POST'])
@token_required
def add_task(current_user):
    data = request.get_json()
    due_date = None
    if data.get('due_date'):
        due_date = datetime.datetime.strptime(data['due_date'], '%Y-%m-%d').date()
    new_task = Task(
        title = data['title'],
        due_date = due_date,
        is_completed = False,
        owner = current_user
    )
    db.session.add(new_task)
    db.session.commit()
    return jsonify({'message':'任务创建成功', 'task': new_task.to_json()})

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
@token_required
def delete_task(current_user, task_id):
    task = Task.query.filter_by(id = task_id, owner = current_user).first()
    if not task:
        return jsonify({'message': '任务不存在或无权删除'}), 404
    db.session.delete(task)
    db.session.commit()
    return jsonify({'message': '已删除'})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(debug=True, port = 5000)