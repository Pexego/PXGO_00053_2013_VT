# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, api


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.multi
    def button_mark_done(self):
        res = super().button_mark_done()
        under_min = self.env['product.stock.unsafety']
        for production in self:
            domain = [
                ('state', '=', 'in_action'),
                ('production_id', '=', production.id)
            ]
            under_min_objs = under_min.search(domain)
            if under_min_objs:
                under_min_objs.write({'state': 'finalized'})
        return res

    @api.multi
    def unlink(self):
        under_min_obj = self.env['product.stock.unsafety']
        for production in self:
            under_mins = under_min_obj.search([('production_id', '=',
                                                production.id)])
            if under_mins:
                under_mins.write({"state": "in_progress",
                                  "production_id": False})
        return super().unlink()
