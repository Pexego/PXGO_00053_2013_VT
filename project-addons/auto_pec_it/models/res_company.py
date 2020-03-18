from odoo import models, fields


class ResCompany(models.Model):

    _inherit = 'res.company'

    auto_pec_template = fields.Many2one(string="PEC template",
                                        comodel_name='ir.actions.actions',
                                        help='This report will be automatically included in the created XML')
    pec_delay_time = fields.Float(string="PEC Delay time")
