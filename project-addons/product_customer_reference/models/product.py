from odoo import models, fields, api, _


class ProductCustomerReference(models.Model):
    _name = 'product.customer.reference'

    product_id = fields.Many2one('product.product', "Product", required=True)
    partner_id = fields.Many2one('res.partner', required=True)
    customer_reference = fields.Char("Customer Reference", required=True)

    _sql_constraints = [
        ('product_partner_uniq', 'unique (product_id, partner_id)',
         _('There cannot be more than one different reference per product and customer'))]
