# Copyright 2019 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, exceptions, _


class BaseIOFolder(models.Model):

    _inherit = "base.io.folder"

    def action_batch_import(self, file_name, file_content):
        if 'UBL-Quotation' in file_name:
            partner = self.env['res.partner'].\
                search([('automatice_purchases', '=', True)], limit=1)
            pick_type = self.env.\
                ref('automatize_edi_it.picking_type_receive_top_deposit')
            if not partner:
                raise exceptions.\
                    UserError(_("Any partner set as automatice purchases"))
            purchase = self.env['purchase.order'].\
                create({'partner_id': partner.id,
                        'currency_id': partner.property_purchase_currency_id
                        and partner.property_purchase_currency_id.id or
                        self.env.user.company_id.currency_id.id,
                        'date_planned': fields.Datetime.now(),
                        'picking_type_id': pick_type.id})
            self.env['purchase.order.import'].\
                create({'quote_file': file_content,
                        'quote_filename': file_name,
                        'update_option': 'all',
                        'purchase_id': purchase.id}).update_rfq_button()

        else:
            super().action_batch_import(file_name, file_content)
