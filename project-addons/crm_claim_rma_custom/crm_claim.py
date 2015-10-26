

from openerp import models, fields


class CrmClaimRma(models.Model):

    _inherit = "crm.claim"

    agent_id = fields.Many2one('sale.agent', 'Agent')
    name = fields.Selection([('return', 'Return'),
                             ('rma', 'RMA')], 'Claim Subject',
                            required=True, default='rma')

    def onchange_partner_id(self, cr, uid, ids, partner_id, email=False,
                            context=None):
        res = super(CrmClaimRma, self).onchange_partner_id(cr, uid, ids,
                                                           partner_id,
                                                           email=email,
                                                           context=context)
        if partner_id:
            partner = self.pool["res.partner"].browse(cr, uid, partner_id)
            if partner.commission:
                res['value']['agent_id'] = partner.commission[0].\
                    agent_id.id

        return res
