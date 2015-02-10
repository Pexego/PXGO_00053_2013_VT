# -*- coding: utf-8 -*-
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
from openerp import models, fields, api
from openerp.osv import fields as fields_old
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
import openerp.addons.decimal_precision as dp


class sale_order_line(models.Model):
    _inherit = 'sale.order.line'

    def _amount_line(self, cr, uid, ids, field_name, arg, context=None):
        # se mantiene en la api antigua por no sobreescribir todo el calculo
        if context is None:
            context = {}
        values = super(sale_order_line, self)._amount_line(cr, uid,  ids,
                                                           field_name, arg,
                                                           context=context)
        for line in self.browse(cr, uid, ids, context=context):
            if line.deposit:
                values[line.id] = 0.0
        return values

    _columns = {
        'price_subtotal': fields_old.function(
            _amount_line, string='Subtotal',
            digits_compute=dp.get_precision('Account')),
    }
    deposit = fields.Boolean('Deposit')
    deposit_date = fields.Date('Date Dep.')

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
        return super(sale_order_line, lines).invoice_line_create()


class sale_order(models.Model):
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
            return super(sale_order, self)._amount_line_tax(line)

    @api.model
    def _prepare_order_line_procurement(self, order, line, group_id=False):
        vals = super(sale_order, self)._prepare_order_line_procurement(
            order, line, group_id=group_id)
        if line.deposit:
            deposit_id = self.env.ref('stock_deposit.stock_location_deposit')
            vals['location_id'] = deposit_id.id
        return vals
