# -*- coding: utf-8 -*-
"""
Main web page controller.
Handles database connections, login, errors and basic routes.
Can be invoqued as a script to run a local server for testing/development.
"""

from flask import *

from app import app
from database import db
from user import User
from auth import auth
from admin import admin
import xmlrpc_interface

################################################################################
# Pre/post-processing filters
################################################################################

@app.before_request
def before_request():
    """
    Executed before processing every request.

    It performs common initialization actions needed for every request,
    like opening database connections, creating temporary files
    or loading the current user basic information.
    Note: The database connection is 'automagically' open by Flask-Peewee.
    """
    #
    # Config the database.
    #
    g.db = db
    g.db.set_autocommit(False)

    # Load the current user info:
    g.user = auth.get_logged_in_user()


@app.teardown_request
def teardown_request(exception):
    """
    Executed after processing every request, even if it failed.

    It performs common house-keeping actions needed after every request,
    like closing database connections or removing temporary files.
    Note: The database connection is 'automagically' closed by Flask-Peewee.
    """
    # Commit or rollback:
    if hasattr(g, 'db'):
        if exception:
            g.db.rollback()
        else:
            g.db.commit()


################################################################################
# Main script body
################################################################################

if __name__ == "__main__":
    # This code is only executed if the cowlab.py file is directly called from
    # python and not imported from another python file / console.
    app.run(debug=True)
