from odoo import _, api, fields, models


class ProductIncidencesAdviseWiz(models.TransientModel):
    _name = 'product.incidences.advise.wiz'

    origin_reference = fields.Reference(
        lambda self: [
            (m.model, m.name) for m in self.env['ir.model'].search([])],
        string='Object')
    continue_method = fields.Char()
    incidence_ids = fields.Many2many(comodel_name='product.incidence')
    claim_id = fields.Many2one('crm.claim')

    @api.multi
    def action_show(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Product Incidences Advise'),
            'res_model': self._name,
            'res_id': self.id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
        }

    @api.multi
    def button_continue(self):
        self.ensure_one()
        return getattr(self.origin_reference.with_context(
            bypass_product_incidences_advise=True, active_id=self.claim_id.id), self.continue_method)()

