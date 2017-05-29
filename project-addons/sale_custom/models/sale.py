# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api, _
from openerp.exceptions import except_orm


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    @api.multi
    def write(self, vals):
        for line in self:
            if vals.get('product_id', False):
                product = self.env['product.product'].browse(vals['product_id'])
                vals['name'] = product.name_get()[0][1]
                if product.description_sale:
                    vals['name'] += '\n' + product.description_sale
        return super(SaleOrderLine, self).write(vals)

    @api.multi
    def product_id_change(self, pricelist, product, qty=0,
                          uom=False, qty_uos=0, uos=False, name='', partner_id=False,
                          lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False,
                          flag=False):
        if qty <= 0:
            raise except_orm(_('Error'), _('Product quantity cannot be negative or zero'))

        return super(SaleOrderLine, self).product_id_change(
            pricelist, product, qty=qty, uom=uom, qty_uos=qty_uos, uos=uos,
            name=name, partner_id=partner_id, lang=lang, update_tax=update_tax,
            date_order=date_order, packaging=packaging,
            fiscal_position=fiscal_position, flag=flag)

