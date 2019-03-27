import os

class Config(object):
    DEBUG = True
    TESTING = False
    SECRET_KEY = 'A0Zr18h/3yX R~XHH!jmN]LWX/,?RT'
    DATABASE = {
                'engine': 'playhouse.pool.PooledPostgresqlExtDatabase',
                'name': 'middleware',
                'user': 'comunitea',
                'port': '5432',
                'host': 'localhost',
                'max_connections': None,
                'autocommit': True,
                'autorollback': True,
                'stale_timeout': 600}

    NOTIFY_URL = ""
    NOTIFY_USER = os.environ.get('NOTIFY_USER')
    NOTIFY_PASSWORD = os.environ.get('NOTIFY_PASSWORD')
