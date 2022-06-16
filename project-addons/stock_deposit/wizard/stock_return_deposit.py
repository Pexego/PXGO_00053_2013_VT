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
from odoo.exceptions import ValidationError, UserError

class StockReturnDeposit(models.TransientModel):
    _name = 'stock.return.deposit'

    @api.multi
    def _get_active_deposits(self):
        wiz_lines = []
        deposit_obj = self.env['stock.deposit']
        deposit_ids = self.env.context.get('active_ids', [])
        deposits = deposit_obj.search([('id', 'in', deposit_ids)])
        for deposit in deposits:
            wiz_lines.append({'deposit_id': deposit.id,
                              'partner_id': deposit.partner_id.id,
                              'sale_id': deposit.sale_id.id,
                              'picking_id': deposit.picking_id.id,
                              'date': deposit.delivery_date,
                              'product_id': deposit.product_id.id,
                              'qty_to_return': deposit.product_uom_qty})
        return wiz_lines

    deposit_change_qty = fields.One2many('stock.return.deposit.change.qty', 'wizard_id',
                                         string='Deposits', default=_get_active_deposits)
    options = fields.Selection(
        selection=[('client_warehouse', 'Return to client warehouse'),
                   ('own_warehouse', 'Return to our warehouse'), ],
        default='own_warehouse' ,required=True)

    @api.multi
    def create_return(self):
        deposit_ids = []
        # Change deposit quantity -> create a new deposit with the remaining qty
        if self.options=='own_warehouse' and any([x.state != 'draft' for x in self.deposit_change_qty.mapped('deposit_id')]):
            raise UserError(_("You cannot return a deposit that is in a non-draft status to our warehouse"))
        for line in self.deposit_change_qty:
            qty_deposit = line.deposit_id.product_uom_qty
            if line.qty_to_return > qty_deposit or line.qty_to_return == 0:
                raise ValidationError(_('The quantity to sale cannot be zero or greater than the original.'))
            elif line.qty_to_return < qty_deposit:
                new_deposit = line.deposit_id.copy()
                new_deposit.write({'product_uom_qty': qty_deposit - line.qty_to_return})
                line.deposit_id.write({'product_uom_qty': line.qty_to_return})
            deposit_ids.append(line.deposit_id.id)
        deposits = self.env['stock.deposit'].browse(deposit_ids)
        if self.options == 'client_warehouse':
            deposits.with_context({'client_warehouse':True}).return_deposit()
        else:
            deposits.return_deposit()



class StockReturnDepositChangeQty(models.TransientModel):
    _name = 'stock.return.deposit.change.qty'

    wizard_id = fields.Many2one('stock.return.deposit')
    deposit_id = fields.Many2one('stock.deposit', "Deposit", readonly=True)
    partner_id = fields.Many2one('res.partner', "Partner", readonly=True)
    sale_id = fields.Many2one('sale.order', "Order", readonly=True)
    picking_id = fields.Many2one('stock.picking', "Picking", readonly=True)
    date = fields.Datetime(string='Date', readonly=True)
    product_id = fields.Many2one('product.product', "Product", readonly=True)
    qty_to_return = fields.Float("Qty to return")