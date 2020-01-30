from odoo import models, api


class CrmLead(models.Model):

    _inherit = 'crm.lead'

    @api.multi
    def action_set_lost(self):
        stage_id=self.env.ref('crm.stage_lead7')
        return self.write({'probability': 0, 'stage_id':stage_id.id})