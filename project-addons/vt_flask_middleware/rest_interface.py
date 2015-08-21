from flask_peewee.rest import RestAPI, RestResource, UserAuthentication

from app import app
from customer import Customer
from product import Product
from auth import auth

user_auth = UserAuthentication(auth, protected_methods=['GET', 'POST', 'PUT', 'DELETE'])
api = RestAPI(app, default_auth=user_auth)

class ApiResource(RestResource):
    def check_post(self, obj=None):
        return False

    def check_put(self, obj):
        return False

    def check_delete(self, obj):
        return False

api.register(Customer, ApiResource)
api.register(Product, ApiResource)

api.setup()
