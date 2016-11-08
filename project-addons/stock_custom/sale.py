# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api, fields


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    is_all_reserved = fields.Boolean(compute='_compute_is_all_reserved',
                                     search='_search_is_all_reserved')

    @api.multi
    def action_ship_create(self):
        res = super(SaleOrder, self).action_ship_create()
        for sale in self:
            sale.picking_ids.write({'commercial': sale.user_id.id})
        return res

    @api.multi
    def _search_is_all_reserved(self, operator, operand):
        self.env.cr.execute(
            """
SELECT B.order_id
FROM
(SELECT distinct order_id
 FROM sale_order_line
    INNER JOIN stock_reservation ON stock_reservation.sale_line_id = sale_order_line.id
    INNER JOIN stock_move ON stock_move.id = stock_reservation.move_id
 WHERE stock_move.state != 'assigned') A
RIGHT JOIN
(SELECT distinct order_id
 FROM sale_order_line
    INNER JOIN stock_reservation ON stock_reservation.sale_line_id = sale_order_line.id
    INNER JOIN stock_move ON stock_move.id = stock_reservation.move_id
 WHERE stock_move.state = 'assigned') B
on A.order_id = B.order_id
WHERE A.order_id IS NULL
            """)
        orders = self.env.cr.fetchall()
        order_ids = [x[0] for x in orders]
        if operator == '=' and operand == True:
            return [('id', 'in', order_ids)]
        elif operator == '!=' and operand == True:
            return [('id', 'not in', order_ids)]

    @api.multi
    def _compute_is_all_reserved(self):
        for order in self:
            if all([x.state == 'assigned'
                    for x in order.mapped('order_line.reservation_ids')]):
                order.is_all_reserved = True
            else:
                order.is_all_reserved = False

    def action_quotation_send_reserve(self, cr, uid, ids, context=None):
        '''
        This function opens a window to compose an email, with the edi sale template message loaded by default
        '''
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        ir_model_data = self.pool.get('ir.model.data')
        try:
            template_id = ir_model_data.get_object_reference(cr, uid, 'sale', 'email_template_edi_sale')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict()
        ctx.update({
            'default_model': 'sale.order',
            'default_res_id': ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }
