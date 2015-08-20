from flask_peewee.rest import RestAPI, RestResource

from app import app
from customer import Customer
from product import Product

api = RestAPI(app)

api.register(Customer)
api.register(Product)

api.setup()
