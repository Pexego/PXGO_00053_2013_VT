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

from openerp import models, fields, api
from odoo import _


class StockReserve(models.Model):

    _inherit = 'stock.reservation'

    mrp_id = fields.Many2one('mrp.production', 'Production')


class StockPicking(models.Model):

    _inherit = "stock.picking"

    @api.one
    def _get_if_productions(self):
        with_prods = False
        for line in self.move_lines:
            if line.sale_line_id and line.sale_line_id.mrp_production_ids:
                with_prods = True
                break
        self.with_productions = with_prods

    with_productions = fields.Boolean("With productions", readonly=True,
                                      compute='_get_if_productions')

    @api.multi
    def write(self, vals):
        res = super(StockPicking, self).write(vals)
        production_obj = self.env['mrp.production']
        for picking in self:
            if picking.origin and 'MO' in picking.origin and vals.get('date_done', False) and picking.state == 'done':
                mrp_product = production_obj.search([('name', '=', picking.origin)])
                location_dest_id = self.env.ref('stock.stock_location_company')
                if mrp_product and mrp_product.picking_out.id == picking.id:
                    # Create in picking
                    pick_in = picking.create({'partner_id': picking.partner_id.id,
                                              'picking_type_id': self.env.ref('stock.picking_type_in').id,
                                              'location_id': mrp_product.move_finished_ids and
                                                             mrp_product.move_finished_ids[0].location_id.id,
                                              'location_dest_id': location_dest_id.id,
                                              'origin': picking.origin})
                    # Update reference in_picking
                    mrp_product.picking_in = pick_in.id
                    cost_moves = sum(picking.move_lines.mapped('price_unit'))
                    production = production_obj.search([('name', '=', picking.origin)])
                    production.move_finished_ids.write({'price_unit': -cost_moves,
                                                        'picking_id': pick_in.id,
                                                        'location_dest_id': location_dest_id.id})
                    production.move_finished_ids.mapped('move_line_ids').write({'picking_id': pick_in.id,
                                                                                'location_dest_id': location_dest_id.id})
                    pick_in.action_assign()
                elif mrp_product.picking_in.id == picking.id:
                    mrp_product.button_mark_done()
                    mail_pool = self.env['mail.mail']
                    values={
                        'subject': _('Manufacturing order {} completed').format(mrp_product.name),
                        'email_from': "odoo_team@visiotechsecurity.com",
                        'email_to': mrp_product.user_id.login,
                        'reply_to': "",
                        'body_html': _('Your {} manufacturing order has been completed').format(mrp_product.name)
                    }
                    msg_id = mail_pool.create(values)

                    if msg_id:
                        mail_pool.send([msg_id])
        return res

    @api.multi
    def _get_purchase_ids(self):
        for picking in self:
            picking.purchase_ids = [(6, 0, picking.move_lines.mapped('purchase_line_id.order_id').ids)]

    purchase_ids = fields.Many2many("purchase.order", compute=_get_purchase_ids)

    @api.multi
    def _get_mrp_productions(self):
        for picking in self:
            picking.production_ids = picking.move_lines.mapped(
                'raw_material_production_id') + picking.move_lines.mapped('production_id')

    production_ids = fields.One2many("mrp.production", compute=_get_mrp_productions)

    def _show_sale(self):
        """
        This method displays the form view of the sale associated with the picking
        :return: action
        """
        action = self.env.ref('sale.action_orders')
        result = action.read()[0]
        result['context'] = {}
        res = self.env.ref('sale.view_order_form', False)
        result['views'] = [(res and res.id or False, 'form')]
        result['res_id'] = self.sale_id.id
        return result

    def _show_purchases(self):
        """
        This method displays the view(tree or form depending on the quantity) of purchases associated with the picking
        :return: action
        """
        action = self.env.ref('purchase.purchase_form_action')
        result = action.read()[0]
        result['context'] = {}
        purchases = self.purchase_ids
        if not purchases or len(purchases) > 1:
            result['domain'] = "[('id', 'in', %s)]" % purchases.ids
        elif len(purchases) == 1:
            res = self.env.ref('purchase.purchase_order_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = purchases.id
        return result

    def _show_productions(self):
        """
        This method displays the view (tree or form depending on the quantity) of productions associated with the picking
        :return: action
        """
        action = self.env.ref('mrp.mrp_production_action')
        result = action.read()[0]
        result['context'] = {}
        if len(self.production_ids) > 1:
            result['domain'] = [('id', 'in', self.production_ids.ids)]
        else:
            result['views'] = [
                (self.env.ref('mrp.mrp_production_form_view').id, 'form')]
            result['res_id'] = self.production_ids.id
        return result

    def action_open_origin(self):
        """ This method shows the source document(s) of the picking
        :return: action
        """
        if self.sale_id:
            return self._show_sale()
        elif self.purchase_ids:
            return self._show_purchases()
        elif self.production_ids:
            return self._show_productions()


