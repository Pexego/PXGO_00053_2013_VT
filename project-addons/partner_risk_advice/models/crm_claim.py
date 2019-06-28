# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models, _


class CrmClaim(models.Model):
    _inherit = 'crm.claim'

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        warning = {}
        title = False
        message = False
        if self.partner_id.rma_warn and \
                self.partner_id.rma_warn != 'no-message':
            title = _("Warning for %s") % self.partner_id.name
            message = self.partner_id.rma_warn_msg
            warning = {
                'title': title,
                'message': message,
            }
            if self.partner_id.rma_warn == 'block':
                return {'value': {'partner_id': False}, 'warning': warning}
        result = super().onchange_partner_id()

        if result and result.get('warning', False):
            warning['title'] = title and title + ' & ' + \
                result['warning']['title'] or result['warning']['title']
            warning['message'] = message and message + ' ' + \
                result['warning']['message'] or result['warning']['message']

        if warning:
            if not result:
                result = {}
            result['warning'] = warning
        return result
