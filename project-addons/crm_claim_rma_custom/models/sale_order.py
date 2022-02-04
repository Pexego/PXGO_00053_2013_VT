from odoo import models, fields, _, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _compute_rma_count(self):
        for order in self:
            stage_sale_attach_id = self.env['crm.claim.stage'].search([('name', '=', 'Adjuntar con pedido')]).id
            pending_rmas = self.env['crm.claim'].search_count(
                [('partner_id', '=', order.partner_id.id), ('stage_id', '=', stage_sale_attach_id)])
            order.rma_pending_count = pending_rmas

    rma_pending_count = fields.Integer(compute='_compute_rma_count', default=0)

    def action_view_pending_rma(self):
        stage_sale_attach_id = self.env['crm.claim.stage'].search([('name', '=', 'Adjuntar con pedido')]).id
        pending_rmas = self.env['crm.claim'].search(
            [('partner_id', '=', self.partner_id.id), ('stage_id', '=', stage_sale_attach_id)])

        action = self.env.ref('crm_claim_rma_custom.action_show_pending_claims').read()[0]

        if len(pending_rmas) > 0:
            action['domain'] = [('id', 'in', pending_rmas.mapped('id'))]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action


class SaleOrderClaimWizardLine(models.TransientModel):
    _name = 'sale.order.claim.wizard.line'

    choose = fields.Boolean('Add')
    claim_id = fields.Many2one('crm.claim', 'Claim')
    claim_id_ro = fields.Many2one('crm.claim', 'Claim', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Partner', readonly=True)
    partner_shipping_id = fields.Many2one('res.partner', 'Shipping', readonly=True)
    wizard_id = fields.Many2one('sale.order.claim.wizard')


class SaleOrderClaimWizard(models.TransientModel):
    _name = 'sale.order.claim.wizard'

    @api.model
    def _get_pending_claims(self):
        wiz_lines = []
        order = self.env['sale.order'].browse(self.env.context.get('active_ids'))
        stage_sale_attach_id = self.env['crm.claim.stage'].search([('name', '=', 'Adjuntar con pedido')]).id
        pending_rmas = self.env['crm.claim'].search(
            [('partner_id', '=', order.partner_id.id), ('stage_id', '=', stage_sale_attach_id)])

        for rma in pending_rmas:
            new_line = {'choose': False,
                        'claim_id': rma.id,
                        'claim_id_ro': rma.id,
                        'partner_id': rma.partner_id,
                        'partner_shipping_id': rma.delivery_address_id}
            wiz_lines.append(new_line)
        return wiz_lines

    line_ids = fields.One2many('sale.order.claim.wizard.line', 'wizard_id', default=_get_pending_claims)

    def add_to_sale_order(self):
        order = self.env['sale.order'].browse(self.env.context.get('active_ids'))
        state = self.env.ref('crm_claim_rma_custom.stage_claim_pending_rev')
        for rma in self.line_ids.filtered(lambda l: l.choose):
            notes = order.internal_notes or ''
            order.internal_notes = notes + _(' Add %s  Ub.: %s') % (rma.claim_id.number, rma.claim_id.location)
            rma.claim_id.stage_id = state.id






