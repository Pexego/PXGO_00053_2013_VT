from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_confirm(self):
        if not self.env.context.get('bypass_risk', False) or self.env.context.get('force_check', False):
            for order in self:
                if order.partner_id.prospective:
                    order.partner_id.write({'active': True, 'prospective': False})
        res = super().action_confirm()
        return res

    def _leads_count(self):
        stages = [self.env.ref('crm.stage_lead4').id, self.env.ref('crm.stage_lead3').id]
        for order in self:
            leads_count = self.env['crm.lead'].search_count(
                [('partner_id', '=', order.partner_id.id), ('stage_id', 'in', stages)])
            order.leads_count = leads_count

    leads_count = fields.Integer(compute='_leads_count', default=0)

    def action_view_leads(self):
        stages = [self.env.ref('crm.stage_lead4').id, self.env.ref('crm.stage_lead3').id]
        leads = self.env['crm.lead'].search(
            [('partner_id', '=', self.partner_id.id), ('stage_id', 'in', stages)])

        action = self.env.ref('crm.crm_lead_opportunities_tree_view').read()[0]

        if len(leads) > 0:
            action['domain'] = [('id', 'in', leads.ids)]
            action['context'] = {
                'default_type': 'opportunity',
            }
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action
