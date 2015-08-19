# -*- coding: utf-8 -*-
"""
Database management and base model
using Peewee <https://github.com/coleifer/peewee> as ORM.
Actually we just use Flask-Peewee <https://github.com/coleifer/flask-peewee>.
"""

from app import app
from flask_peewee.db import Database

#
# Database backend (Flask-Peewee).
#
# Note: It gets the database backend and name from the app configuration.
#
database = Database(app)
db = database.database

#
# Base model and models management.
#

class BaseModel(database.Model):
    """Base model for the selected database backend."""
    pass
