class Config(object):
    DEBUG = True
    TESTING = False
    SECRET_KEY = 'A0Zr18h/3yX R~XHH!jmN]LWX/,?RT'
    DATABASE_URI = 'sqlite://:memory:'
    DATABASE = {'engine': 'peewee.SqliteDatabase',
                'name': 'middleware.db',
                'check_same_thread': False}
