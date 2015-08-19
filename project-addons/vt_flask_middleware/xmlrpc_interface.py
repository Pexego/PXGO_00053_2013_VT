from flaskext.xmlrpc import XMLRPCHandler, Fault
from app import app
from database import db
from user import User
from customer import Customer
from product import Product
from auth import auth
from flask import session

handler = XMLRPCHandler('xmlrpc')
handler.connect(app, '/xmlrpc')

@handler.register
def login(username, password):
    if not username or not password:
        raise Fault("unknown_data", "Username and password are required!")
    user = auth.authenticate(username, password)
    if not user:
        raise Fault("invalid_user",
                    "Invalid username/password, please try again.")
    else:
        auth.login_user(user)
    return session["user_pk"]

def _check_user(user_id, password):
    user = User.get(User.id==user_id)
    if not user or not user.check_password(password):
        raise Fault("invalid_user",
                    "Invalid username/password, please try again.")
    return True

@handler.register
def create(user_id, password, model, vals):
    _check_user(user_id, password)
    odoo_id = vals["odoo_id"]
    if model not in ["customer", "product"]:
        raise Fault("unknown_model", "Reference model does not exist!")
    if model == "customer":
        try:
            customer = Customer.get(Customer.odoo_id == odoo_id)
        except Customer.DoesNotExist:
            q = Customer.insert(**vals)
        else:
            q = Customer.update(**vals).where(Customer.odoo_id == odoo_id)
    else:
        try:
            product = Product.get(Product.odoo_id == odoo_id)
        except Product.DoesNotExist:
            q = Product.insert(**vals)
        else:
            q = Product.update(**vals).where(Product.odoo_id == odoo_id)
    q.execute()
    return True

@handler.register
def write(user_id, password, model, odoo_id, vals):
    _check_user(user_id, password)
    if model not in ["customer", "product"]:
        raise Fault("unknown_model", "Reference model does not exist!")
    if model == "customer":
        try:
            customer = Customer.get(Customer.odoo_id == odoo_id)
        except Customer.DoesNotExist:
            raise Fault("unknown_registry", "Customer not found!")
        q = Customer.update(**vals).where(Customer.odoo_id == odoo_id)
    else:
        try:
            product = Product.get(Product.odoo_id == odoo_id)
        except Product.DoesNotExist:
            raise Fault("unknown_registry", "Product not found!")
        q = Product.update(**vals).where(Product.odoo_id == odoo_id)
    q.execute()
    return True

@handler.register
def unlink(user_id, password, model, odoo_id):
    _check_user(user_id, password)
    if model not in ["customer", "product"]:
        raise Fault("unknown_model", "Reference model does not exist!")
    q = False
    if model == "customer":
        try:
            customer = Customer.get(Customer.odoo_id == odoo_id)
        except Customer.DoesNotExist:
            pass
        else:
            q = Customer.delete().where(Customer.odoo_id == odoo_id)
    else:
        try:
            product = Product.get(Product.odoo_id == odoo_id)
        except Product.DoesNotExist:
            pass
        else:
            q = Product.delete().where(Product.odoo_id == odoo_id)
    if q:
        q.execute()
    return True
