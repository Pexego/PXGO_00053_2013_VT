from odoo import models, fields

class AmazonMarketplace(models.Model):
    _name = 'amazon.marketplace'

    name = fields.Char(translate=True)
    code = fields.Char()
    amazon_name = fields.Char()
    account_id = fields.Many2one("account.account")
    color = fields.Integer()
