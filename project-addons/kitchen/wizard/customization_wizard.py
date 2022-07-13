from odoo import models, fields, api, exceptions, _


class KitchenCustomizationWizard(models.TransientModel):
    _name = 'kitchen.customization.wizard'

    user = fields.Char(required=1)

    date_planned = fields.Datetime(string='Date Planned', required=1)

    def mark_received_action(self):
        customization_id = self.env.context.get('active_ids')
        customization = self.env['kitchen.customization'].browse(customization_id)
        customization.write({'state': 'in_progress', 'date_planned': self.date_planned, 'user': self.user})
        picking = customization.customization_line[0].move_ids.filtered(lambda m: m.state != 'cancel')[0].picking_id
        if picking:
            notes = picking.internal_notes or ""
            picking_mssg = self.env['ir.config_parameter'].sudo().get_param('kitchen.picking.message')
            notes += "%s \n" % picking_mssg
            picking.write({'internal_notes': notes, 'not_sync': False})
