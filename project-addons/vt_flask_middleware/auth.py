# -*- coding: utf-8 -*-
"""
User authentification.
"""

from flask_peewee.auth import Auth
from app import app
from database import database
from user import User

#
# Authentification object.
# Note: we are providing our own user model, as we want to customize some fields
#       but we could just relay on an user model 'automagically' generated
#       by Auth, see Auth.get_user_model().
#
auth = Auth(app, database, user_model=User, prefix='')
