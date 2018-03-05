# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api, _
from openerp.exceptions import except_orm


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    @api.multi
    def write(self, vals):
        data = {}
        for line in self:
            if vals.get('product_uom_qty', False) and line.product_id.pack_line_ids:
                for subline in line.product_id.pack_line_ids:
                    subproduct = subline.product_id
                    quantity = subline.quantity * vals['product_uom_qty']
                    subproduct_id = self.env['sale.order.line'].search([('product_id', '=', subproduct.id),
                                                                        ('order_id', '=', line.order_id.id),
                                                                        ('pack_parent_line_id', '=', line.id)])
                    if subproduct_id:
                        data = {'product_uom_qty': quantity}
                        subproduct_id.write(data)
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


class SaleOrder(models.Model):

    _inherit = "sale.order"

    @api.multi
    def onchange_partner_id(self, partner_id, context=None):
        val = super(SaleOrder, self).onchange_partner_id(partner_id, context=None)
        new_partner = self.env['res.partner'].browse(partner_id)
        for child in new_partner.child_ids:
            if child.default_shipping_address:
                val['value']['partner_shipping_id'] = child.id
                break

        return val

    @api.multi
    def open_historical_orders(self):
        self.ensure_one()
        partner_id = self.partner_id.commercial_partner_id.id
        order_view_id = self.env.ref('sale.act_res_partner_2_sale_order').id
        last_order = self.env['sale.order'].search([('id', '!=', self.id),
                                                    ('partner_id', 'child_of', [partner_id]),
                                                    ('state', 'not in', ['cancel', 'draft', 'sent'])],
                                                   limit=1, order='date_order DESC').id
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        record_url = base_url + '/web/?#id=' + str(last_order) + '&view_type=form&model=sale.order&action=' + \
                                str(order_view_id) + '&active_id=' + str(partner_id)
        return {
            'name': 'Historical Partner Orders',
            'type': 'ir.actions.act_url',
            'view_type': 'form',
            'url': record_url,
            'target': 'new'
        }


