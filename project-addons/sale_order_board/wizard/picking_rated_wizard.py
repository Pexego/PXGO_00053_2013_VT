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

    total_weight = fields.Char('Total Weight (Kgs)', readonly=True, digits=dp.get_precision('Stock Weight'))
    message_products_weight = fields.Char('', readonly=True)
    product_names_without_weight = fields.Char('', readonly=True)
    total_volume = fields.Char('Total Volume (Cbm)', readonly=True, digits=dp.get_precision('Stock Weight'))
    message_products_volume = fields.Char('', readonly=True)
    product_names_without_volume = fields.Char('', readonly=True)
    message_error = fields.Text('', readonly=True)

    data = fields.One2many('picking.rated.wizard.tree', 'wizard_id', string='Shipping Data', readonly=True)


class PickingRatedWizardTree(models.TransientModel):
    _name = 'picking.rated.wizard.tree'
    _order = 'sequence asc, amount asc'

    wizard_id = fields.Many2one('picking.rated.wizard')
    sequence = fields.Integer('Sequence', default=1)
    currency = fields.Char('Currency')
    amount = fields.Float('Amount')
    service = fields.Char('Service')
    transit_time = fields.Char('Arrival')
    shipping_weight = fields.Float(string="Shipping weight", readonly=True, default=0)
