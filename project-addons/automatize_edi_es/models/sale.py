# Copyright 2019 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models
from lxml import etree


class SaleOrder(models.Model):

    _inherit = "sale.order"

    @api.multi
    def _ubl_add_quotation_line(
            self, parent_node, oline, line_number, ns, version='2.1'):
        line_root = etree.SubElement(
            parent_node, ns['cac'] + 'QuotationLine')
        dpo = self.env['decimal.precision']
        qty_precision = dpo.precision_get('Product Unit of Measure')
        price_precision = dpo.precision_get('Product Price')
        self._ubl_add_line_item(
            line_number, oline.name, oline.product_id, 'sale',
            oline.product_uom_qty, oline.product_uom, line_root, ns,
            currency=self.currency_id,
            price_subtotal=oline.price_unit * (1.0 - oline.discount / 100.0) *
            oline.product_uom_qty,
            qty_precision=qty_precision, price_precision=price_precision,
            version=version)
