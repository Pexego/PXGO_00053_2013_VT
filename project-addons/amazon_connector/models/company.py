from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    refresh_token = fields.Char()
    lwa_app_id = fields.Char()
    lwa_client_secret = fields.Char()
    aws_secret_key = fields.Char()
    aws_access_key = fields.Char()
    role_arn = fields.Char()
    marketplace_ids = fields.Many2many('amazon.marketplace')
