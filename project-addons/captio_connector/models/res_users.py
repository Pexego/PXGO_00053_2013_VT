from odoo import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    captio_id = fields.Integer()

    cash_account_id = fields.Many2one('account.account', string='Cash Account')
    card_account_id = fields.Many2one('account.account', string='Card Account')
