import os


class Config(object):
    DEBUG = False
    TESTING = False
    SECRET_KEY = 'A0Zr18h/3yX R~XHH!jmN]LWX/,?RT'
    DATABASE = {
                'engine': 'playhouse.pool.PooledPostgresqlExtDatabase',
                'name': os.environ.get('FLASK_DATABASE'),
                'user': os.environ.get('PGUSER'),
                'password': os.environ.get('PGPASSWORD'),
                'port': os.environ.get('PGPORT'),
                'host': os.environ.get('PGHOST'),
                'max_connections': None,
                'autocommit': True,
                'autorollback': True,
                'stale_timeout': 600}

    NOTIFY_URL = os.environ.get('FLASK_URL')
    NOTIFY_HEADER = os.environ.get('FLASK_HEADER') 
    NOTIFY_COUNTRY = os.environ.get('FLASK_COUNTRY')  # ES, IT, ... depending on the odoo instance
