from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    captio_token = fields.Char()
    captio_token_expire = fields.Datetime('Captio Token Expiration date', copy=False)
    captio_last_date = fields.Datetime()
