import os


class Config(object):
    DEBUG = False
    TESTING = False
    SECRET_KEY = 'A0Zr18h/3yX R~XHH!jmN]LWX/,?RT'
    DATABASE = {
                'engine': 'playhouse.pool.PooledPostgresqlDatabase',
                'name': 'middleware',
                'user': 'comunitea',
                'port': '5433',
                'host': '172.20.0.2',
                'password': 'komklave',
                'max_connections': None,
                'autocommit': True,
                'autorollback': True,
                'stale_timeout': 600}

    NOTIFY_URL = ""
    NOTIFY_USER = os.environ.get('NOTIFY_USER')
    NOTIFY_PASSWORD = os.environ.get('NOTIFY_PASSWORD')
    NOTIFY_HEADER = ""
    NOTIFY_COUNTRY = ""  # ES, IT, ... depending on the odoo instance
