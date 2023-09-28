from odoo import fields, models


class ReservesLog(models.TransientModel):
    _name = "product.pricelist.item.log"
    _transient_max_hours = 744  # one month
    _transient_max_count = False
    _inherit = ['mail.thread']

    user_id = fields.Many2one("res.users", "User")
    product_id = fields.Many2one("product.product", "Product")
    pricelist_id  = fields.Many2one("product.pricelist")
    old_fixed_price = fields.Float("Old Fixed Price")
    new_fixed_price = fields.Float("New Fixed Price")
    date = fields.Datetime("Date")
