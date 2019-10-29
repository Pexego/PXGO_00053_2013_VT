##############################################################################
#
#    Copyright (C) 2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@pexego.es>$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import fields, models, api


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    original_line_id = fields.Many2one('sale.order.line', "Origin", ondelete='cascade')
    assoc_line_ids = fields.One2many('sale.order.line', 'original_line_id', "Associated lines", ondelete='cascade')

    @api.model
    def create(self, vals):
        product_obj = self.env['product.product']
        fiscal_obj = self.env['account.fiscal.position']
        pricelist_obj = self.env['product.pricelist']

        product_id = vals.get('product_id')

        line = super(SaleOrderLine, self).create(vals)
        if product_id:
            product = product_obj.browse(product_id)
            for associated in product.associated_product_ids:
                qty = line.product_uom._compute_quantity(line.product_uom_qty, line.product_id.uom_id)
                tax_ids = fiscal_obj.map_tax(associated.associated_id.taxes_id)
                pricelist = line.order_id.pricelist_id.id
                price = pricelist_obj.price_get(associated.associated_id.id,
                                                associated.quantity * qty,
                                                line.order_id.partner_id.id)[pricelist]
                price *= (1 - associated.discount / 100)
                args_line = {
                    'order_id': line.order_id.id,
                    'price_unit': price,
                    'product_uom': associated.uom_id.id,
                    'product_uom_qty': associated.quantity * qty,
                    'product_id': associated.associated_id.id,
                    'original_line_id': line.id,
                    'customer_lead': associated.associated_id.sale_delay or 0.0,
                    'tax_id': [(6, 0, tax_ids.ids)],
                    'discount':associated.discount
                    # TODO: migrar junto con módulo commision_report
                    # 'agent': line.agent.id,
                    # 'commission': line.commission.id
                }
                new_line = self.create(args_line)
                new_line.product_id_change()
        return line

    @api.multi
    def write(self, vals):
        pricelist_obj = self.env['product.pricelist']
        fiscal_obj = self.env['account.fiscal.position']
        if vals.get('product_id'):
            res = super(SaleOrderLine, self).write(vals)
            for line in self:
                if line.assoc_line_ids:
                    self.unlink([x.id for x in line.assoc_line_ids])
                for associated in line.product_id.associated_product_ids:
                    qty = line.product_uom._compute_quantity(line.product_uom_qty, line.product_id.uom_id)
                    tax_ids = fiscal_obj.map_tax(associated.associated_id.taxes_id)
                    pricelist = line.order_id.pricelist_id.id
                    price = pricelist_obj.price_get([pricelist],
                                                    associated.associated_id.id,
                                                    associated.quantity * qty,
                                                    line.order_id.partner_id.id,
                                                    {'uom': associated.uom_id.id,
                                                     'date': line.order_id.date_order}
                                                    )[pricelist]
                    price *= (1-associated.discount/100)
                    args_line = {
                     'order_id': line.order_id.id,
                     'price_unit': price,
                     'product_uom': associated.uom_id.id,
                     'product_uom_qty': associated.quantity * qty,
                     'product_id': associated.associated_id.id,
                     'original_line_id': line.id,
                     'customer_lead': associated.associated_id.sale_delay or 0.0,
                     'tax_id': [(6, 0, tax_ids.ids)],
                     # TODO: migrar junto con módulo commision_report
                     # 'agent': line.agent.id,
                     # 'commission': line.commission.id
                    }
                    new_line = self.create(args_line)
                    new_line.product_id_change()
            return res

        if vals.get('product_uom_qty'):
            for line in self:
                if line.assoc_line_ids:
                    diff = vals.get('product_uom_qty', line.product_uom_qty) - line.product_uom_qty
                    for assoc_line in line.assoc_line_ids:
                        quantity = diff * line.product_id.associated_product_ids.quantity
                        assoc_line.write({'product_uom_qty': (assoc_line.product_uom_qty + quantity)})

        return super(SaleOrderLine, self).write(vals)
