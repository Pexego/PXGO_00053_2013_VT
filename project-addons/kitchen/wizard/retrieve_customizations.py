from odoo import _, api, fields, models
from odoo.exceptions import UserError

class RetrieveCustomizationsWiz(models.TransientModel):
    _name = 'retrieve.customizations.wiz'

    sale_id = fields.Many2one("sale.order", readonly=True, string='Sale')
    origin_reference = fields.Reference(
        lambda self: [
            (m.model, m.name) for m in self.env['ir.model'].search([])],
        string='Object')
    continue_method = fields.Char()
    customizations_ids = fields.Many2many('kitchen.customization')

    @api.multi
    def action_show(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Retrieve Customizations'),
            'res_model': self._name,
            'res_id': self.id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
        }

    @api.multi
    def button_continue(self):
        self.ensure_one()
        if self.customizations_ids:
            if len(self.customizations_ids)==1:
                self.customizations_ids.action_draft()
            else:
                raise UserError(_("You can't retrieve several customizations for the same order"))
        return getattr(self.origin_reference.with_context(
            bypass_retrieve_customization=True), self.continue_method)()
