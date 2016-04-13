import os

class Config(object):
    DEBUG = False
    TESTING = False
    SECRET_KEY = 'A0Zr18h/3yX R~XHH!jmN]LWX/,?RT'
    DATABASE_URI = 'sqlite://:memory:'
    DATABASE = {'engine': 'peewee.SqliteDatabase',
                'name': 'middleware.db',
                'threadlocals': True}

    NOTIFY_URL = os.environ.get('NOTIFY_URL') 
    NOTIFY_USER = os.environ.get('NOTIFY_USER')
    NOTIFY_PASSWORD = os.environ.get('NOTIFY_PASSWORD')
