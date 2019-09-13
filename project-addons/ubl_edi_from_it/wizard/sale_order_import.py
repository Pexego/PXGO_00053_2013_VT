# Copyright 2019 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, api


class SaleOrderImport(models.TransientModel):
    _inherit = 'sale.order.import'

    @api.model
    def _prepare_create_order_line(
            self, product, uom, order, import_line, price_source):
        vals = super()._prepare_create_order_line(product, uom, order,
                                                  import_line, price_source)
        vals['route_id'] = \
            self.env.ref('ubl_edi_from_it.route_from_deposit').id
        return vals

    @api.model
    def _prepare_order(self, parsed_order, price_source):
        so_vals = super()._prepare_order(parsed_order, price_source)
        so_vals['not_sync'] = True
        return so_vals
