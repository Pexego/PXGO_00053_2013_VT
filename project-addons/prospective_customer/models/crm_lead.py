from odoo import models, api, fields


class CrmLead(models.Model):

    _inherit = 'crm.lead'

    contact_email = fields.Char()

    @api.multi
    def action_set_lost(self):
        stage_id=self.env.ref('crm.stage_lead7')
        return self.write({'probability': 0, 'stage_id':stage_id.id})
    
    def _onchange_partner_id_values(self, partner_id):
        """ returns the new values when partner_id has changed """
        res = super(CrmLead, self)._onchange_partner_id_values(partner_id)
        if partner_id:
            partner = self.env['res.partner'].browse(partner_id)
            res.update({'contact_email':partner.email})
        return res
