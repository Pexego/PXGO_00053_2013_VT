from odoo import models, api, fields


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    contact_email = fields.Char()

    @api.multi
    def action_set_lost(self):
        stage_id = self.env.ref('crm.stage_lead7')
        return self.write({'probability': 0, 'stage_id': stage_id.id})

    def _onchange_partner_id_values(self, partner_id):
        """ returns the new values when partner_id has changed """
        res = super(CrmLead, self)._onchange_partner_id_values(partner_id)
        if partner_id:
            partner = self.env['res.partner'].browse(partner_id)
            res.update({'contact_email': partner.email})
        return res

    @api.multi
    def write(self, vals):
        if vals.get('stage_id', False):
            stages = [self.env.ref('crm.stage_lead4').id, self.env.ref('crm.stage_lead3').id]
            for lead in self:
                stage = vals.get('stage_id')
                message = self.env['ir.config_parameter'].sudo().get_param('message.lead')
                sale_warn = lead.partner_id.sale_warn
                if sale_warn == 'no-message':
                    lead.partner_id.sale_warn = 'warning'
                warning_message = lead.partner_id.sale_warn_msg or ''
                if stage in stages:
                    if message not in warning_message:
                        lead.partner_id.sale_warn_msg = '%s\n %s.' % (warning_message, message)
                elif message in warning_message and not self.env['crm.lead'].search(
                        [('stage_id', 'in', stages), ('id', '!=', lead.id), ('partner_id', '=',
                                                                             lead.partner_id.id if not vals.get(
                                                                                     'partner_id', False) else vals.get(
                                                                                     'partner_id', False))]):
                    lead.partner_id.sale_warn_msg = lead.partner_id.sale_warn_msg.replace('\n %s.' % message, '')
        return super(CrmLead, self).write(vals)
