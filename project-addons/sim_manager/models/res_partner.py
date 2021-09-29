from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    sim_serial_ids = fields.One2many('sim.package', 'partner_id')
