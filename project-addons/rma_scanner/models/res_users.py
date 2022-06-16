from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    default_printer = fields.Many2one('printing.printer', 'Printer')
