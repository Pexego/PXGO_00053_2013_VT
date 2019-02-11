from odoo import api, models


class CreditControlPolicy(models.Model):

    _inherit = "credit.control.policy"

    @api.multi
    def _move_lines_domain(self, controlling_date):
        """ Build the default domain for searching move lines """
        res = super()._move_lines_domain(controlling_date)
        res.append(('blocked', '!=', True))
        return res
