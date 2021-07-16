from odoo import models, fields, api, exceptions, _


class CrmClaimInvoiceDiscount(models.TransientModel):
    _name = 'invoice.discount.wiz'
    
    origin_reference = fields.Reference(
        lambda self: [
            (m.model, m.name) for m in self.env['ir.model'].search([])],
        string='Object')
    continue_method = fields.Char()
    message = fields.Char(string='Message', readonly=True)


    @api.multi
    def action_show(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Crm Claim Invoice Discount'),
            'res_model': self._name,
            'res_id': self.id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
        }

    @api.multi
    def button_continue(self):
        self.ensure_one()
        return getattr(self.origin_reference.with_context(), self.continue_method)()