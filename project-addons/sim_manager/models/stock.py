from odoo import models, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.model
    def write(self, vals):
        res = super().write(vals)
        if 'lots_text' in vals:
            if self.picking_id.picking_type_id.code == 'outgoing':
                sim_packages = self.env['sim.package'].search([('code', 'in', vals.get('lots_text', '').split(', '))])
                if sim_packages and not sim_packages.partner_id:
                    for pkg in sim_packages:
                        pkg.write({'partner_id': self.partner_id.commercial_partner_id.id,
                                   'move_id': self.id,
                                   'state': 'sold'})
                        sim_packages.with_delay(priority=10).notify_sale_web('sold')
            elif self.picking_id.picking_type_id.code == 'incoming':
                for pkg_code in vals.get('lots_text', '').split(', '):
                    sim_packages = self.env['sim.package'].search([('code', '=', pkg_code)])
                    if sim_packages:
                        sim_packages.write({'partner_id': None,
                                            'move_id': None,
                                            'state': 'available'})
                        sim_packages.with_delay(priority=10).notify_sale_web('return')
        return res


