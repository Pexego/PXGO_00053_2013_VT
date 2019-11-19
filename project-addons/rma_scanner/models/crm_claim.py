from odoo import api, models, fields, _


class CrmClaim(models.Model):
    _inherit = 'crm.claim'

    @api.multi
    def find_claim_by_number_using_barcode(self, barcode):
        barcode = barcode.replace("-", "/")
        barcode = barcode.replace("'", "-")
        claim = self.search([('number', '=', barcode)], limit=1)

        if claim:
            if claim.stage_id.name != "Pendiente de recibir":
                message = _("The {} is already received").format(claim.number)
                self.env.user.notify_warning(message=message, sticky=True)
            else:
                claim.message_post(body="RMA scanned")
                claim.stage_id = self.env["crm.claim.stage"].search([('name', '=', 'Recibido')])
                claim.date_received = fields.Date.today()
                message = _("{} received").format(claim.number)
                self.env.user.notify_info(title="RMA scanned", message=message)
        else:
            message = _("The RMA {} doesn't exist").format(barcode)
            self.env.user.notify_warning(message=message, sticky=True)

        action = self.env.ref('rma_scanner.crm_claim_rma_scanner')
        result = action.read()[0]

        return result
