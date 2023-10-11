from odoo import models, fields

class AmazonCompany(models.Model):
    _name = 'amazon.company'

    name = fields.Char(translate=True, required=True)
    partner_id = fields.Many2one("res.partner", required=True)
    vat = fields.Char(required=True)
    sii_enabled = fields.Boolean()
    journal_id = fields.Many2one('account.journal', string="Journal", help="Journal of full invoices", required=True)