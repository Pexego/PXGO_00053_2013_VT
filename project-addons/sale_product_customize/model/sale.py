# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego All Rights Reserved
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

from openerp import models, fields, exceptions, api, _


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    can_mount = fields.Many2one('product.product', 'Mount')
    mrp_production_ids = fields.One2many('mrp.production', 'sale_line_id',
                                         'Productions')
    customization_types = fields.Many2many(
        'mrp.customize.type', 'sale_line_customizations_rel',
        'sale_order_line_id', 'customization_id', 'Customizations')
    requires_mount = fields.Boolean('Requires mount')

    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
                          uom=False, qty_uos=0, uos=False, name='',
                          partner_id=False, lang=False, update_tax=True,
                          date_order=False, packaging=False,
                          fiscal_position=False, flag=False, context=None):

        res = super(SaleOrderLine, self).product_id_change(
            cr, uid, ids, pricelist, product, qty, uom, qty_uos, uos, name,
            partner_id, lang, update_tax, date_order, packaging,
            fiscal_position, flag, context)
        prod = self.pool.get('product.product').browse(cr, uid, product,
                                                       context)
        res['domain']['can_mount'] = [('id', 'in',
                                       [x.id for x in prod.can_mount_ids])]
        return res

    def product_id_change2(self, cr, uid, ids, pricelist, product, qty=0,
                           uom=False, qty_uos=0, uos=False, name='',
                           partner_id=False, lang=False, update_tax=True,
                           date_order=False, packaging=False,
                           fiscal_position=False,
                           flag=False, warehouse_id=False, sale_agent_ids=False, context=None):
        res = super(SaleOrderLine, self).product_id_change2(
            cr, uid, ids, pricelist, product, qty, uom, qty_uos, uos, name,
            partner_id, lang, update_tax, date_order, packaging,
            fiscal_position, flag, warehouse_id, sale_agent_ids, context)
        prod = self.pool.get('product.product').browse(cr, uid, product,
                                                       context)
        res['domain']['can_mount'] = [('id', 'in',
                                       [x.id for x in prod.can_mount_ids])]
        return res

    @api.multi
    @api.onchange('customization_types')
    def onchange_customization_types(self):
        for line in self:
            requires_mount = False
            for custom in line.customization_types:
                if custom.aux_product:
                    requires_mount = True
            line.requires_mount = requires_mount


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    @api.one
    def order_reserve(self):
        prod_obj = self.env['product.product']
        for line in self.order_line:
            if line.customization_types:
                if not line.product_id.default_code:
                    raise exceptions.except_orm(
                        _('Error'),
                        _('One of the products not have default code'))
                product_code = line.product_id.default_code
                mount = self.env['mrp.customize.type']
                for custom in line.customization_types:
                    if custom.aux_product:
                        mount += custom
                customizations = line.customization_types
                if mount:
                    if not line.can_mount.default_code:
                        raise exceptions.except_orm(
                            _('Error'),
                            _('One of the products not have default code'))
                    customizations = customizations - mount
                    product_code += '#' + line.can_mount.default_code
                if not self.partner_id.ref:
                    raise exceptions.Warning(
                        _('Partner reference'),
                        _('The partner %s not have reference') %
                        self.partner_id.name)
                product_code += '|' + str(self.partner_id.ref)
                for custom in customizations:
                    product_code += '|' + str(custom.code)
                product = prod_obj.get_product_customized(product_code)

                final_line_dict = {
                    'product_id': product.id,
                    'order_id': self.id,
                    'customization_types': [(6, 0, [x.id for x in
                                             line.customization_types])],
                    'price_unit': product.list_price2,
                    'purchase_price': product.standard_price,
                    'delay': max([product.sale_delay, line.delay]),
                    'product_uom_qty': line.product_uom_qty,
                    'product_uom': product.uom_id.id
                }
                final_line = self.env['sale.order.line'].create(
                    final_line_dict)
                if product.qty_available <= 0:
                    bom_id = product.bom_ids[0]
                    productions = []
                    for i in range(int(final_line.product_uom_qty -
                                       product.qty_available)):
                        mrp_dict = {
                            'product_id': product.id,
                            'bom_id': bom_id.id,
                            'product_uom': bom_id.product_uom.id,
                            'product_qty': 1,
                            'type_ids': [(6, 0, [x.id for x in
                                          line.customization_types])]
                        }
                        productions.append(
                            self.env['mrp.production'].create(mrp_dict).id)
                    final_line.mrp_production_ids = [(6, 0, productions)]
                    line.unlink()
        super(SaleOrder, self).order_reserve()

    @api.one
    def action_button_confirm(self):
        super(SaleOrder, self).action_button_confirm()
        for line in self.order_line:
            for production in line.mrp_production_ids:
                production.signal_workflow('button_confirm')

    @api.one
    def action_cancel(self):
        for line in self.order_line:
            for production in line.mrp_production_ids:
                production.signal_workflow('button_cancel')
        return super(SaleOrder, self).action_cancel()
