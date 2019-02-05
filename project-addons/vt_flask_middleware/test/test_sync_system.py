"""
    Se prueban los mensajes de sincronizacion que manda el middleware al
    cliente, imprime el mensaje y devuelve un estado 200
"""
from functools import wraps
from flask import Flask, request, Response
from datetime import datetime


app = Flask(__name__)


def check_auth(username, password):
    return username == 'admin' and password == 'admin'


def authenticate():
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


@app.route('/api', methods=['POST'])
def index():
    content = request.get_json(force=True, silent=True)
    resp = Response(status=200)
    return resp


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
