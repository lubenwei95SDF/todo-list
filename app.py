import os
import jwt
import datetime
import uuid
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy

from extensions import redis_client
from flasgger import Swagger
import config
import json
import pika
app = Flask(__name__)

app.config['SECRET_KEY'] = config.SECRET_KEY
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'todo_v4.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

swagger = Swagger(app)
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
            jti = data.get('jti')
            if jti and redis_client.get(jti):
                return jsonify({'message': 'Token has been revoked (Logged out)'}),401
            current_user = User.query.filter_by(public_id = data['public_id']).first()
        except:
            return jsonify({'message': 'Token is invalid'}), 401
        return f(current_user, *args, **kwargs)
    return decorated


@app.route('/test_redis')
def test_redis_connection():
    try:
        redis_client.set('test_key', 'working', ex=60)

        value = redis_client.get('test_key')

        return {
            "status": "success",
            "redis_reply": value
        }, 200
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }, 500

@app.route('/register', methods=['POST'])
def register():
    """
    用户注册接口
    ---
    tags:
      - 认证 (Auth)
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
              example: engineer_li
            password:
              type: string
              example: password123
    responses:
      200:
        description: 注册成功
      400:
        description: 用户名已存在
    """
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

    #-------v7 A-TRack-------------
    try:
        mq_host = os.getenv('RABBITMQ_HOST', 'localhost')
        credentials = pika.PlainCredentials('admin', 'secret')
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host = mq_host, credentials = credentials)
        )
        channel = connection.channel()
        channel.queue_declare(queue='email_queue', durable=True)
        message = {'name': data['name'], 'email_type': 'welcome'}
        channel.basic_publish(
            exchange='',
            routing_key='email_queue',
            body = json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode = 2,
            )
        )
        connection.close()
        print(f"📤 [Producer] 已向队列投递任务: {data['name']}")
    except Exception as e:
        print(f"❌ [Producer] MQ 连接失败: {e}")
    return jsonify({'message': '注册成功'})

@app.route('/login', methods=['POST'])
def login():
    """
        用户登录接口 (获取 Token)
        ---
        tags:
          - 认证 (Auth)
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              properties:
                name:
                  type: string
                  example: engineer_li
                password:
                  type: string
                  example: password123
        responses:
          200:
            description: 登录成功，返回 Token
            schema:
              type: object
              properties:
                token:
                  type: string
    """
    auth = request.get_json()
    if not auth or not auth.get('name') or not auth.get('password'):
        return make_response('Could not verify', 401)
    user = User.query.filter_by(name = auth.get('name')).first()

    if not user:
        return make_response('用户不存在', 401)
    if check_password_hash(user.password, auth.get('password')):
        token = jwt.encode({'public_id': user.public_id,
                            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30),
                            'jti': str(uuid.uuid4())    #给token增加一个uuid
                            }, app.config['SECRET_KEY'], algorithm = 'HS256')
        return jsonify({'token': token})

    return make_response('密码错误', 401)

@app.route('/logout', methods=['POST'])
@token_required
def logout(current_user):
    """
        用户注销 (加入黑名单)
        ---
        tags:
          - 认证 (Auth)
        parameters:
          - name: Authorization
            in: header
            type: string
            required: true
            description: Bearer <你的Token>
        responses:
          200:
            description: 注销成功
    """
    auth_header = request.headers.get('Authorization')
    token = auth_header.split(' ')[1]
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        jti = payload.get('jti')
        exp_timestamp = payload.get('exp')
        now_timestamp = datetime.datetime.utcnow().timestamp()
        ttl = exp_timestamp - now_timestamp
        if ttl > 0:
            redis_client.set(jti, 'blacklisted', ex=int(ttl))

        return jsonify({'message': "Successfully logged out. Token revoked"}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500
@app.route('/api/tasks', methods=['GET'])
@token_required
def get_tasks(current_user):
    """
        获取我的任务列表
        ---
        tags:
          - 任务 (Todo)
        security:
          - APIKeyHeader: []
        parameters:
          - name: Authorization
            in: header
            type: string
            required: true
            description: Bearer <你的Token>
        responses:
          200:
            description: 任务列表
    """
    output = [task.to_json() for task in current_user.tasks]
    return jsonify(({'tasks': output}))

@app.route('/api/tasks', methods=['POST'])
@token_required
def add_task(current_user):
    """
        创建新任务
        ---
        tags:
          - 任务 (Todo)
        parameters:
          - name: Authorization
            in: header
            type: string
            required: true
            description: Bearer <你的Token>
          - in: body
            name: body
            schema:
              type: object
              properties:
                title:
                  type: string
                  example: 学习Swagger
                due_date:
                  type: string
                  example: 2025-12-31
        responses:
          200:
            description: 创建成功
    """
    data = request.get_json()
    due_date = None
    if data.get('due_date'):
        try:
            # 尝试按 YYYY-MM-DD 解析
            due_date = datetime.datetime.strptime(data['due_date'], '%Y-%m-%d').date()
        except ValueError:
            # 如果格式不对，不要崩，而是温柔地告诉前端：你发错了
            return jsonify({'message': '日期格式错误，请使用 YYYY-MM-DD (例如 2025-12-31)'}), 400
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
    """
        删除任务
        ---
        tags:
          - 任务 (Todo)
        parameters:
          - name: Authorization
            in: header
            type: string
            required: true
            description: Bearer <你的Token>

          # 👇 新知识点：in: path 表示这是一个 URL 路径参数
          - name: task_id
            in: path
            type: integer
            required: true
            description: 要删除的任务ID (例如 1)

        responses:
          200:
            description: 删除成功
          404:
            description: 任务不存在或无权删除
    """
    task = Task.query.filter_by(id = task_id, owner = current_user).first()
    if not task:
        return jsonify({'message': '任务不存在或无权删除'}), 404
    db.session.delete(task)
    db.session.commit()
    return jsonify({'message': '已删除'})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(debug=True, port = 8000)