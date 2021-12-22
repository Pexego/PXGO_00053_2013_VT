from odoo import models, api, _


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def write(self, vals):
        res = super().write(vals)
        if vals.get('lots_text', False):
            if self.picking_id.picking_type_id.code == 'outgoing':
                products = self.env['sim.type'].search([]).mapped('product_id')
                if self.product_id in products:
                    sims = vals.get('lots_text', '').upper().split(', ')
                    sim_packages = self.env['sim.package'].search([('code', 'in', sims)])
                    if sim_packages and len(sim_packages) == len(sims):
                        for pkg in sim_packages:
                            pkg.write({'partner_id': self.partner_id.commercial_partner_id.id,
                                       'move_id': self.id,
                                       'state': 'sold'})
                            if 'VISIOTECH' not in self.partner_id.commercial_partner_id.name \
                                    and 'VIP' not in pkg.code:  # TODO: manejar con los tipos
                                pkg.with_delay(priority=10).notify_sale_web('sold')
                    else:
                        # Notify warehouse something missing
                        mail_pool = self.env['mail.mail']
                        context = self._context.copy()
                        context.pop('default_state', False)
                        context['message_warn'] = \
                            _('Some of these SIM cards %s of the picking %s have not been found in the system.') % \
                            (vals.get('lots_text', ''), self.picking_id.name)

                        template_id = self.env.ref('sim_manager.email_template_sim_error')

                        if template_id:
                            mail_id = template_id.with_context(context).send_mail(self.id)
                            if mail_id:
                                mail_id_check = mail_pool.browse(mail_id)
                                mail_id_check.with_context(context).send()
        return res

    @api.multi
    def _action_done(self):
        res = super()._action_done()
        for move in self:
            if move.picking_id.picking_type_id.code == 'incoming' and move.lots_text:
                for pkg_code in move.lots_text.upper().split(', '):
                    sim_packages = self.env['sim.package'].search([('code', '=', pkg_code)])
                    if sim_packages:
                        for pkg in sim_packages:
                            pkg.write({'partner_id': None,
                                       'move_id': None,
                                       'state': 'available'})
                            if 'VISIOTECH' not in move.partner_id.commercial_partner_id.name \
                                    and 'VIP' not in pkg.code:  # TODO: manejar con los tipos
                                pkg.with_delay(priority=10).notify_sale_web('return')
        return res

