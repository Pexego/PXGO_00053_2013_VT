import os

class Config(object):
    DEBUG = False
    TESTING = False
    SECRET_KEY = 'A0Zr18h/3yX R~XHH!jmN]LWX/,?RT'
    DATABASE = {
                'engine': 'playhouse.pool.PooledPostgresqlExtDatabase',
                'name': 'middleware',
                'user': 'oerp',
                'password': 'oerp',
                'port': '5432',
                'host': 'localhost',
                'max_connections': None,
                'stale_timeout': 600}

    NOTIFY_URL = "http://localhost:8080/api"
    NOTIFY_USER = os.environ.get('NOTIFY_USER')
    NOTIFY_PASSWORD = os.environ.get('NOTIFY_PASSWORD')
