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

    can_mount_id = fields.Many2one('product.product.mount', 'Mount')
    mrp_production_ids = fields.One2many('mrp.production', 'sale_line_id',
                                         'Productions')
    customization_types = fields.Many2many(
        'mrp.customize.type', 'sale_line_customizations_rel',
        'sale_order_line_id', 'customization_id', 'Customizations')
    requires_mount = fields.Boolean('Requires mount')

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
    def _prepare_custom_line(self, moves=True):
        prod_obj = self.env['product.product']
        for line in self.order_line:
            new_line = False
            if line.customization_types and not line.product_id.custom:
                if not line.product_id.default_code:
                    raise exceptions.Warning(
                        _('Error'),
                        _('One of the products not have default code'))
                product_code = line.product_id.default_code
                mount = self.env['mrp.customize.type']
                for custom in line.customization_types:
                    if custom.aux_product:
                        mount += custom
                customizations = line.customization_types
                if mount:
                    if not line.can_mount_id.product_id.default_code:
                        raise exceptions.Warning(
                            _('Error'),
                            _('One of the products not have default code'))
                    customizations = customizations - mount
                    product_code += u'#' + line.can_mount_id.product_id.\
                        default_code
                if not self.partner_id.ref:
                    raise exceptions.Warning(
                        _('Partner reference'),
                        _('The partner %s not have reference') %
                        self.partner_id.name)
                if customizations:
                    product_code += u'|' + str(self.partner_id.ref)
                for custom in customizations:
                    product_code += u'|' + str(custom.code)
                product = prod_obj.sudo().\
                    get_product_customized(product_code, line.can_mount_id)

                new_vals = self.env['sale.order.line'].\
                    product_id_change(line.order_id.pricelist_id.id,
                                      product.id, qty=line.product_uom_qty,
                                      uom=product.uom_id.id, qty_uos=0,
                                      uos=False, name=product.default_code,
                                      partner_id=line.order_id.partner_id.id,
                                      lang=line.order_id.partner_id.lang,
                                      update_tax=True,
                                      date_order=line.order_id.date_order,
                                      packaging=False,
                                      fiscal_position=
                                      line.order_id.fiscal_position.id,
                                      flag=False)

                final_line_dict = new_vals['value']

                final_line_dict.update({
                    'product_id': product.id,
                    'order_id': self.id,
                    'customization_types': [(6, 0, [x.id for x in
                                             line.customization_types])],
                    'purchase_price': product.standard_price,
                    'delay': max([product.sale_delay, line.delay]),
                    'product_uom_qty': line.product_uom_qty,
                    'product_uom': product.uom_id.id,
                    'reservation_ids':
                    [(6, 0, [x.id for x in line.reservation_ids])]
                })
                final_line = self.env['sale.order.line'].create(
                    final_line_dict)
                new_line = True
            elif line.customization_types and line.product_id.custom:
                final_line = line
                product = line.product_id
            else:
                final_line = False

            if final_line and product.virtual_available <= \
                    final_line.product_uom_qty and moves:
                bom_id = product.bom_ids[0]
                productions = []
                needed = final_line.product_uom_qty
                if product.virtual_available > 0:
                    needed -= product.virtual_available
                needed = int(needed)
                if final_line.mrp_production_ids:
                    needed -= len(final_line.mrp_production_ids)
                if needed > 0:
                    for i in range(needed):
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
                if productions:
                    if new_line:
                        final_line.mrp_production_ids = [(6, 0, productions)]
                    else:
                        productions.extend([x.id for x in
                                            final_line.mrp_production_ids])
                        final_line.mrp_production_ids = [(6, 0, productions)]
            if new_line:
                line.unlink()

    @api.one
    def order_reserve(self):
        #self._prepare_custom_line()
        super(SaleOrder, self).order_reserve()

    @api.one
    def action_button_confirm(self):
        self._prepare_custom_line()
        #self.order_reserve()
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
