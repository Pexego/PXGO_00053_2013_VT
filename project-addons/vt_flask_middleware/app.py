"""
Main application object and shared configuration.
Contains singleton objects that need to be imported by several modules.
"""

from flask import *

#
# Create and configure the application object.
#
app = Flask(__name__)
app.config.from_object('config.Config')
