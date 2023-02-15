##############################################################################
#
#    Author: Jesus Garcia Manzanas
#    Copyright 2018 Visiotech
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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

from odoo import models, fields
from odoo.addons import decimal_precision as dp


class PickingRatedWizard(models.TransientModel):
    _name = 'picking.rated.wizard'

    sale_order_id = fields.Many2one('sale.order', string='Sale order', required=True)

    total_weight = fields.Char('Total Weight (Kgs)', readonly=True, digits=dp.get_precision('Stock Weight'))
    message_products_weight = fields.Char('', readonly=True)
    product_names_without_weight = fields.Char('', readonly=True)
    total_volume = fields.Char('Total Volume (Cbm)', readonly=True, digits=dp.get_precision('Stock Weight'))
    message_products_volume = fields.Char('', readonly=True)
    product_names_without_volume = fields.Char('', readonly=True)
    message_error = fields.Text('', readonly=True)

    data = fields.One2many('picking.rated.wizard.tree', 'wizard_id', string='Shipping Data', readonly=True)

    def create(self, vals):
        order = vals['sale_order_id']
        message_products_weight = ''
        message_products_volume = ''
        products_without_weight = order.get_product_list_without_weight()
        products_without_volume = order.get_product_list_without_volume()
        number_product_without_weight = len(products_without_weight)
        number_product_without_volume = len(products_without_volume)
        product_names_without_weight = ", ".join(products_without_weight.mapped('default_code'))
        product_names_without_volume = ", ".join(products_without_volume.mapped('default_code'))

        if number_product_without_weight != 0:
            message_products_weight = (
                "%s of the product(s) of the order don't have set the weights,"
                " please take the shipping cost as an approximation"
            ) % number_product_without_weight
        if number_product_without_volume != 0:
            message_products_volume = (
                "%s of the product(s) of the order don't have set the volumes,"
                " please take the shipping cost as an approximation"
            ) % number_product_without_volume
        return super().create({
            'sale_order_id': order.id,
            'total_weight': order.get_sale_order_weight(),
            'message_products_weight': message_products_weight,
            'product_names_without_weight': product_names_without_weight,
            'total_volume': order.get_sale_order_volume(),
            'message_products_volume': message_products_volume,
            'product_names_without_volume': product_names_without_volume
        })


class PickingRatedWizardTree(models.TransientModel):
    _name = 'picking.rated.wizard.tree'
    _order = 'sequence asc, amount asc'

    wizard_id = fields.Many2one('picking.rated.wizard')
    order_id = fields.Many2one('sale.order', 'Order', related='wizard_id.sale_order_id')
    sequence = fields.Integer('Sequence', default=1)
    currency = fields.Char('Currency')
    amount = fields.Float('Amount')
    service = fields.Char('Service')
    transit_time = fields.Char('Arrival')
