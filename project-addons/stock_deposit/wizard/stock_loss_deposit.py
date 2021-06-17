##############################################################################
#
#    Copyright (C) 2015 Pexego All Rights Reserved
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
from odoo import models, fields, api, exceptions, _


class StockLossDeposit(models.TransientModel):
    _name = 'stock.loss.deposit'

    wizard_id = fields.Many2one('stock.sale.deposit')
    deposit_id = fields.Many2one('stock.deposit', "Deposit", readonly=True)
    partner_id = fields.Many2one('res.partner', "Partner", readonly=True)
    sale_id = fields.Many2one('sale.order', "Order", readonly=True)
    picking_id = fields.Many2one('stock.picking', "Picking", readonly=True)
    date = fields.Datetime(string='Date', readonly=True)
    product_id = fields.Many2one('product.product', "Product", readonly=True)
    qty_to_loss = fields.Float("Qty to loss")

    @api.multi
    def _get_active_deposits(self):
        wiz_lines = []
        deposit_obj = self.env['stock.deposit']
        deposit_ids = self.env.context.get('active_ids', [])
        deposits = deposit_obj.search([('id', 'in', deposit_ids),
                                       ('state', '=', 'draft')])
        for deposit in deposits:
            wiz_lines.append({'deposit_id': deposit.id,
                              'partner_id': deposit.partner_id.id,
                              'sale_id': deposit.sale_id.id,
                              'picking_id': deposit.picking_id.id,
                              'date': deposit.delivery_date,
                              'product_id': deposit.product_id.id,
                              'qty_to_loss': deposit.product_uom_qty})
        return wiz_lines

    deposit_change_qty = fields.One2many('stock.loss.deposit', 'wizard_id',
                                         string='Deposits', default=_get_active_deposits)

    @api.multi
    def create_loss(self):
        import ipdb
        ipdb.set_trace()
        return None
