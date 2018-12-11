##############################################################################
#
#    Author: Santi Argüeso
#    Copyright 2014 Pexego Sistemas Informáticos S.L.
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

from datetime import datetime, timedelta
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import odoo.addons.decimal_precision as dp


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    deposit = fields.Boolean('Deposit')
    deposit_date = fields.Date('Date Dep.')

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        super(SaleOrderLine, self)._compute_amount()
        for line in self:
            if line.deposit:
                line.update({
                    'price_tax': 0.0,
                    'price_total': 0.0,
                    'price_subtotal': 0.0,
                })

    @api.onchange('deposit')
    def onchange_deposit(self):
        if self.deposit:
            current_date = datetime.utcnow()
            delta = timedelta(days=15)
            result = current_date + delta
            self.deposit_date = result.strftime(DEFAULT_SERVER_DATE_FORMAT)
        else:
            self.deposit_date = False

    @api.multi
    def invoice_line_create(self):
        lines = self.env['sale.order.line']
        for line in self:
            if not line.deposit or self.env.context.get('invoice_deposit', False):
                lines += line
        return super(SaleOrderLine, lines).invoice_line_create()


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    deposit_ids = fields.One2many('stock.deposit', 'sale_id', 'Deposits')
    deposit_count = fields.Integer('deposit count', compute='_get_deposit_len',
                                   store=True)

    @api.one
    @api.depends('deposit_ids')
    def _get_deposit_len(self):
        self.deposit_count = len(self.deposit_ids)

    @api.model
    def _amount_line_tax(self, line):
        if line.deposit:
            return 0.0
        else:
            return super(SaleOrder, self)._amount_line_tax(line)

    @api.model
    def _prepare_order_line_procurement(self, order, line, group_id=False):
        vals = super(SaleOrder, self)._prepare_order_line_procurement(
            order, line, group_id=group_id)
        if line.deposit:
            deposit_id = self.env.ref('stock_deposit.stock_location_deposit')
            vals['location_id'] = deposit_id.id
        return vals
