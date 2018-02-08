from flaskext.xmlrpc import XMLRPCHandler, Fault
from app import app
from database import db
from user import User
from country import Country
from customer import Customer, CustomerTag, CustomerTagCustomerRel
from order import Order, OrderProduct
from invoice import Invoice
from commercial import Commercial
from product import Product, ProductCategory
from rma import RmaStatus, RmaStage, Rma, RmaProduct
from auth import auth
from sync_log import SyncLog
from flask import session
from utils import parse_many2one_vals
import xmlrpclib
import datetime
import logging
from implemented_models import MODELS_CLASS
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
    user = User.get(User.id == user_id)
    if not user or not user.check_password(password):
        raise Fault("invalid_user",
                    "Invalid username/password, please try again.")
    return True


@handler.register
def create(user_id, password, model, vals):
    _check_user(user_id, password)
    odoo_id = vals["odoo_id"]
    if model not in MODELS_CLASS.keys():
        raise Fault("unknown_model", "Reference model does not exist!")
    mod_class = MODELS_CLASS[model]
    parse_many2one_vals(mod_class, vals)
    mod_class.create(**vals)
    return True


@handler.register
def write(user_id, password, model, odoo_id, vals):
    _check_user(user_id, password)
    if model not in MODELS_CLASS.keys():
        raise Fault("unknown_model", "Reference model does not exist!")
    mod_class = MODELS_CLASS[model]
    try:
        reg = mod_class.get(mod_class.odoo_id == odoo_id)
    except mod_class.DoesNotExist:
        raise Fault("unknown_registry", "%s not found!" % model)
    parse_many2one_vals(mod_class, vals)
    for field_name in vals.keys():
        value = vals[field_name]
        if isinstance(value, basestring):
            value = value.replace('"','\\"')
            value = '"%s"' % value
        exec('reg.%s = %s' % (field_name, value))
    reg.save(is_update=True)
    return True


@handler.register
def unlink(user_id, password, model, odoo_id):
    _check_user(user_id, password)
    if model not in MODELS_CLASS.keys():
        raise Fault("unknown_model", "Reference model does not exist!")
    mod_class = MODELS_CLASS[model]
    try:
        rec = mod_class.get(mod_class.odoo_id == odoo_id)
    except mod_class.DoesNotExist:
        pass
    else:
        if model == "customer":
            for invoice in Invoice.select().where(Invoice.partner_id == rec.id):
                invoice.delete_instance()
            for rma in Rma.select().where(Rma.partner_id == rec.id):
                for rma_product in RmaProduct.select().where(
                        RmaProduct.id_rma == rma.id):
                    rma_product.delete_instance()
                rma.delete_instance()
        elif model == 'product':
            for rma_product in RmaProduct.select().where(
                    RmaProduct.product_id == rec.id):
                rma_product.delete_instance()
        elif model == 'rma':
            for rma_product in RmaProduct.select().where(
                    RmaProduct.id_rma == rec.id):
                rma_product.delete_instance()
        elif model == 'rmastatus':
            for rma_product in RmaProduct.select().where(
                    RmaProduct.status_id == rec.id):
                rma_product.delete_instance()
        elif model == 'rmastage':
            for rma in Rma.select().where(
                    Rma.stage_id == rec.id):
                rma.delete_instance()
        elif model == 'customertagcustomerrel':
            for customertagcustomerrel in CustomerTagCustomerRel.select().where(
                    CustomerTagCustomerRel.odoo_id == rec.odoo_id):
                customertagcustomerrel.delete_instance()
        elif model == 'order':
            for order in Order.select().where(
                Order.partner_id == rec.id):
                order.delete_instance()
        rec.delete_instance()
    return True