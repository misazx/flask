from flask import Flask
from flask import request
from flask import session
from flask_session import Session
import os
from flask import render_template
from flask_socketio import SocketIO
from flask import jsonify
import json
import redis

port = 8001
secret_key = os.urandom(24)  # 生成密钥，为session服务。
app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key  # 配置会话密钥
app.config['SESSION_TYPE'] = "redis"  # session类型为redis
app.config['SESSION_PERMANENT'] = True  # 如果设置为True，则关闭浏览器session就失效
# 访问远程redis
# app.config['SESSION_REDIS'] = redis.from_url(os.environ['REDIS_URL'])
# r= redis.Redis(host='127.0.0.1', port='6379')#,db=1, decode_responses=True)
r= redis.from_url(os.environ['REDIS_URL'])
app.config['SESSION_REDIS'] = r
app.config.from_object(__name__)
Session(app)
socket_io = SocketIO(app, logger=True, engineio_logger=True)


r_whoisghost_lobby = 'whoisghost_lobby'

@app.route("/whoisghost/lobby/list/", methods=['post', 'get'])
def game_whoisghost_lobby_list():
    mes= r.lrange(r_whoisghost_lobby,0,-1)
    print(mes)
    return jsonify(mes)

@app.route("/whoisghost/lobby/create/", methods=['post', 'get'])
def game_whoisghost_lobby_create():
    data = request.args['data'] if request.args.get('data') else request.form.get('data')
    print(data)
    mes=data
    r.lpushx(r_whoisghost_lobby,mes)
    return jsonify(mes)


@app.route("/listen", methods=['post', 'get'])
def listen_func():
    """"监听发送来的消息,并使用socketio向所有客户端发送消息"""
    mes = {"message": "unknown error"}
    data = request.args['data'] if request.args.get('data') else request.form.get('data')
    if data is not None:
        socket_io.emit(data=data, event="mes")  # js客户端on绑定的就是这个event的事件
        mes['message'] = "success"
    else:
        pass
    return json.dumps(mes)


@socket_io.on("login")
def quotations_func(mes):
    """客户端连接"""
    print(mes)
    sid = request.sid  # io客户端的sid, socketio用此唯一标识客户端.
    can = True #False
    host = request.host
    host_list = ['127.0.0.1']
    """
    根据页面的访问地址决定是否允许连接, 你可以自己实现自己对访问的控制逻辑.
    最后决定是允许连接还是使用socket_io.server.disconnect(sid)断开链接.
    """
    if host in host_list:
        can = True
    elif host.startswith("192.168") or host.startswith("local"):
        can = True
    else:
        pass

    if can:
        socket_io.emit(event="login", data=json.dumps({"message": "connect success!"}))
    else:
        socket_io.emit(event="login", data=json.dumps({"message": "connect refuse!"}))
        socket_io.server.disconnect(sid)

@app.route("/")
def test_func():
    """测试页面"""
    return render_template("test.html")

@app.route("/index")
def test_func2():
    """测试页面"""
    return render_template("index.html")

if __name__ == '__main__':
    socket_io.run(app=app)