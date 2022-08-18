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
from odoo import models, fields, api, exceptions, _
from datetime import datetime
from odoo.exceptions import UserError


class StockDeposit(models.Model):
    _name = 'stock.deposit'
    _description = "Deposits"
    _inherit = ['mail.thread']

    product_id = fields.Many2one(string='Product',
                                 related='move_id.product_id',
                                 store=True, readonly=True)
    product_uom_qty = fields.Float('Product qty',
                                   related='move_id.product_uom_qty',
                                   store=True, readonly=True)
    product_uom = fields.Many2one(related='move_id.product_uom',
                                  string='Uom',
                                  store=True,
                                  readonly=True)
    invoice_id = fields.Many2one('account.invoice', 'Invoice')
    move_id = fields.Many2one('stock.move', 'Deposit Move', required=True,
                              readonly=True, ondelete='cascade', index=1)
    picking_id = fields.Many2one(related='move_id.picking_id',
                                 string='Picking',
                                 store=True,
                                 readonly=True)
    partner_id = fields.Many2one(related='move_id.partner_id',
                                 string='Destination Address',
                                 store=True,
                                 readonly=True)
    sale_id = fields.Many2one(related='move_id.sale_line_id.order_id',
                              string='Sale',
                              store=True,
                              readonly=True)
    delivery_date = fields.Datetime('Date of Transfer')
    return_date = fields.Date('Return date')
    company_id = fields.Many2one(related='move_id.company_id',
                                 string='Date of Transfer',
                                 store=True,
                                 readonly=True)
    state = fields.Selection([('draft', 'Draft'), ('sale', 'Sale'),
                              ('returned', 'Returned'),
                              ('invoiced', 'Invoiced'),
                              ('loss', 'Loss'),
                              ('rma', 'RMA'),
                              ('damaged', 'Damaged')], 'State',
                             readonly=True, required=True)
    sale_move_id = fields.Many2one('stock.move', 'Sale Move', required=False,
                                   readonly=True, ondelete='cascade', index=1)
    sale_picking_id = fields.Many2one(related='sale_move_id.picking_id',
                                      string='Sale picking',
                                      readonly=True)
    return_picking_id = fields.Many2one('stock.picking', 'Return Picking',
                                        required=False, readonly=True,
                                        ondelete='cascade', index=1)
    loss_move_id = fields.Many2one('stock.move', 'Loss Move', required=False,
                                   readonly=True, ondelete='cascade', index=1)
    loss_picking_id = fields.Many2one(related='loss_move_id.picking_id',
                                      string='Loss picking',
                                      readonly=True)
    user_id = fields.Many2one('res.users', 'Comercial', required=False,
                              readonly=False, ondelete='cascade', index=1)

    def _compute_damaged_move_ids(self):
        for deposit in self:
            if deposit.damaged_picking_id:
                deposit.damaged_move_ids = [(6, 0, deposit.damaged_picking_id.move_lines.filtered(
                    lambda m, d=deposit: m.product_id == d.product_id).ids)]

    damaged_move_ids = fields.Many2many(
        comodel_name='stock.move',
        string='Move to damaged location', compute="_compute_damaged_move_ids")
    damaged_picking_id = fields.Many2one('stock.picking', string='Damaged Picking',
                                         readonly=True)

    claim_move_id = fields.Many2one('stock.move', 'Move to RMA location', required=False,
                                    readonly=True, ondelete='cascade', index=1)
    claim_picking_id = fields.Many2one(related='claim_move_id.picking_id',
                                       string='RMA Picking',
                                       readonly=True)
    # cost_subtotal = fields.Float('Cost', related='move_id.cost_subtotal',
    #                              store=True, readonly=True) TODO:Migrar.

    claim_id = fields.Many2one('crm.claim')

    @api.multi
    def set_damaged(self, picking_id):
        for d in self:
            d.state = 'damaged'
            d.damaged_picking_id = picking_id.id

    @api.multi
    def set_rma(self, move_id):
        for d in self:
            d.state = 'rma'
            d.claim_move_id = move_id

    @api.multi
    def sale(self):
        move_obj = self.env['stock.move']
        picking_type_id = self.env.ref('stock.picking_type_out')
        for deposit in self:
            picking = self.env['stock.picking'].create(
                {'picking_type_id': picking_type_id.id,
                 'partner_id': deposit.partner_id.id,
                 'origin': deposit.sale_id.name,
                 'date_done': datetime.now(),
                 'commercial': deposit.user_id.id,
                 'group_id': deposit.move_id.group_id.id,
                 'location_id': deposit.move_id.location_dest_id.id,
                 'location_dest_id': picking_type_id.default_location_dest_id.id})
            values = {
                'product_id': deposit.product_id.id,
                'product_uom_qty': deposit.product_uom_qty,
                'product_uom': deposit.product_uom.id,
                'partner_id': deposit.partner_id.id,
                'name': 'Sale Deposit: ' + deposit.move_id.name,
                'location_id': deposit.move_id.location_dest_id.id,
                'location_dest_id': deposit.partner_id.property_stock_customer.id,
                'picking_id': picking.id,
                'commercial': deposit.user_id.id,
                'group_id': deposit.move_id.group_id.id
            }
            move = move_obj.create(values)
            move._action_confirm()
            picking.action_assign()
            picking.action_done()
            deposit.move_id.sale_line_id.write(
                {'qty_invoiced': deposit.move_id.sale_line_id.qty_invoiced - deposit.product_uom_qty,
                 'invoice_status': 'to invoice'})
            deposit.write({'state': 'sale', 'sale_move_id': move.id})

    def return_deposit(self, picking_claim_id=False):
        sorted_deposits = sorted(self, key=lambda d: d.sale_id)
        move_obj = self.env['stock.move']
        picking_type_id = self.env.ref('stock.picking_type_in')
        for deposit in sorted_deposits:
            if picking_claim_id:
                deposit.write({'state': 'returned', 'return_picking_id': picking_claim_id.id})
                continue

            location_dest_id = picking_type_id.default_location_dest_id.id
            location_id = deposit.move_id.location_dest_id.id
            if self.env.context.get("client_warehouse"):
                if deposit.state == 'draft':
                    raise UserError(_("You cannot return a draft deposit to client warehouse"))
                location_dest_id = deposit.sale_move_id.location_id.id
                location_id = deposit.sale_move_id.location_dest_id.id
            picking = self.env['stock.picking'].create({
                'picking_type_id': picking_type_id.id,
                'location_id': location_id,
                'location_dest_id': location_dest_id}
            )
            if not picking['partner_id']:
                partner_id = deposit.partner_id.id
                commercial = deposit.user_id.id
                group_id = deposit.sale_id.procurement_group_id.id
                picking.write({'partner_id': partner_id, 'commercial': commercial,
                               'group_id': group_id, 'origin': deposit.sale_id.name})

            elif picking['group_id'] != deposit.sale_id.procurement_group_id:
                picking = self.env['stock.picking'].create({
                    'picking_type_id': picking_type_id.id,
                    'partner_id': deposit.partner_id.id,
                    'location_id': location_id,
                    'location_dest_id': location_dest_id,
                })
                partner_id = deposit.partner_id.id
                commercial = deposit.user_id.id
                group_id = deposit.sale_id.procurement_group_id.id
                picking.write({'partner_id': partner_id, 'commercial': commercial,
                               'group_id': group_id, 'origin': deposit.sale_id.name})

            values = {
                'product_id': deposit.product_id.id,
                'product_uom_qty': deposit.product_uom_qty,
                'product_uom': deposit.product_uom.id,
                'partner_id': deposit.partner_id.id,
                'name': 'Sale Deposit: ' + deposit.move_id.name,
                'location_id': location_id,
                'location_dest_id': location_dest_id,
                'picking_id': picking.id,
                'commercial': deposit.user_id.id,
                'group_id': group_id
            }
            move = move_obj.create(values)
            move._action_confirm()
            deposit.write({'state': 'returned', 'return_picking_id': picking.id})
            picking.action_assign()
            if self.env.context.get("client_warehouse"):
                deposit.move_id.sale_line_id.write(
                    {'qty_invoiced': deposit.move_id.sale_line_id.qty_invoiced - deposit.product_uom_qty,
                 'invoice_status': 'to invoice'})
                picking.action_done()

    @api.model
    def send_advise_email(self):
        deposits = self.search([('return_date', '=', fields.Date.today())])
        # ~ mail_pool = self.env['mail.mail']
        # ~ mail_ids = self.env['mail.mail']
        template = self.env.ref('stock_deposit.stock_deposit_advise_partner', False)
        for deposit in deposits:
            ctx = dict(self._context)
            ctx.update({
                'default_model': 'stock.deposit',
                'default_res_id': deposit.id,
                'default_use_template': bool(template.id),
                'default_template_id': template.id,
                'default_composition_mode': 'comment',
                'mark_so_as_sent': True
            })
            composer_id = self.env['mail.compose.message'].with_context(
                ctx).create({})
            composer_id.with_context(ctx).send_mail()
            # ~ mail_id = template.send_mail(deposit.id)
            # ~ mail_ids += mail_pool.browse(mail_id)
        # ~ if mail_ids:
        # ~ mail_ids.send()
        return True

    @api.multi
    def deposit_loss(self, move_claim_id=False):
        move_obj = self.env['stock.move']
        picking_type_id = self.env.ref('stock.picking_type_out')
        deposit_loss_loc = self.env.ref('stock_deposit.stock_location_deposit_loss')
        for deposit in self:
            if move_claim_id:
                loss_move = move_claim_id
            else:
                group_id = deposit.sale_id.procurement_group_id
                picking = self.env['stock.picking'].create(
                    {'picking_type_id': picking_type_id.id,
                     'partner_id': deposit.partner_id.id,
                     'origin': deposit.sale_id.name,
                     'date_done': fields.Datetime.now(),
                     'invoice_state': 'none',
                     'commercial': deposit.user_id.id,
                     'location_id': deposit.move_id.location_dest_id.id,
                     'location_dest_id': deposit_loss_loc.id,
                     'group_id': group_id.id,
                     'not_sync': True})
                values = {
                    'product_id': deposit.product_id.id,
                    'product_uom_qty': deposit.product_uom_qty,
                    'product_uom': deposit.product_uom.id,
                    'partner_id': deposit.partner_id.id,
                    'name': u'Loss Deposit: ' + deposit.move_id.name,
                    'location_id': deposit.move_id.location_dest_id.id,
                    'location_dest_id': deposit_loss_loc.id,
                    'invoice_state': 'none',
                    'picking_id': picking.id,
                    'commercial': deposit.user_id.id,
                    'group_id': group_id.id
                }
                loss_move = move_obj.create(values)
                loss_move._action_confirm()
                picking.action_assign()
                picking.action_done()
            deposit.write({'state': 'loss', 'loss_move_id': loss_move.id})

    @api.multi
    def create_invoice(self, journal_id=None):
        deposit_obj = self.env['stock.deposit']
        deposits = self.filtered(lambda d: d.state == 'sale')
        invoice_ids = []
        if not deposits:
            raise exceptions.Warning(_('No deposit selected'))
        sales = list(set([x.sale_id for x in deposits]))
        for sale in sales:
            sale_deposit = deposit_obj.search(
                [('id', 'in', deposits.ids), ('sale_id', '=', sale.id)])

            sale_lines = sale_deposit.mapped('move_id.sale_line_id')
            my_context = dict(self.env.context)
            my_context['invoice_deposit'] = True
            inv_vals = sale._prepare_invoice()
            if self.env.context.get('force_partner_id', False):
                partner_id = self.env.context.get('force_partner_id')
                inv_vals['partner_id'] = partner_id.id
                inv_vals['partner_shipping_id'] = partner_id.id
                inv_vals['payment_term_id'] = \
                    partner_id.property_payment_term_id.id
            else:
                partner_id = sale.partner_id
            inv_vals[
                'journal_id'] = journal_id.id if journal_id else partner_id.commercial_partner_id.invoice_type_id.journal_id.id
            if not inv_vals.get("payment_term_id", False):
                inv_vals['payment_term_id'] = \
                    partner_id.property_payment_term_id.id
            if not inv_vals.get("payment_mode_id", False):
                inv_vals['payment_mode_id'] = \
                    partner_id.customer_payment_mode_id.id
            if not inv_vals.get("partner_bank_id", False):
                inv_vals['partner_bank_id'] = partner_id.bank_ids \
                                              and partner_id.bank_ids[0].id or False
            invoice = self.env['account.invoice'].create(inv_vals)
            for line in sale_lines:
                deposit = deposits.filtered(lambda d: d.move_id.sale_line_id.id == line.id)
                invoice_line = line.with_context(my_context).invoice_line_create(invoice.id,
                                                                                 sum(deposit.mapped('product_uom_qty')))
                invoice_line.move_line_ids = [(6, 0, deposit.mapped('sale_move_id.id'))]
                line.qty_invoiced = line.product_qty
            invoice_ids.append(invoice.id)
            sale_deposit.write({'invoice_id': invoice.id})
        deposits.write({'state': 'invoiced'})
        return invoice_ids

    @api.multi
    def revert_sale(self):
        move_obj = self.env['stock.move']
        picking_type_id = self.env.ref('stock.picking_type_in')
        for deposit in self:
            picking = self.env['stock.picking'].create(
                {'picking_type_id': picking_type_id.id,
                 'partner_id': deposit.partner_id.id,
                 'origin': deposit.sale_picking_id.name,
                 'date_done': datetime.now(),
                 'commercial': deposit.user_id.id,
                 'group_id': deposit.sale_move_id.group_id.id,
                 'location_id': deposit.sale_move_id.location_dest_id.id,
                 'location_dest_id': deposit.sale_move_id.location_id.id})
            values = {
                'product_id': deposit.product_id.id,
                'product_uom_qty': deposit.product_uom_qty,
                'product_uom': deposit.product_uom.id,
                'partner_id': deposit.partner_id.id,
                'name': 'Return Sale Deposit: ' + deposit.sale_move_id.name,
                'location_id': deposit.sale_move_id.location_dest_id.id,
                'location_dest_id': deposit.sale_move_id.location_id.id,
                'picking_id': picking.id,
                'commercial': deposit.user_id.id,
                'group_id': deposit.sale_move_id.group_id.id
            }
            move = move_obj.create(values)
            move._action_confirm()
            picking.action_assign()
            picking.action_done()
            new_qty_invoiced = deposit.move_id.sale_line_id.qty_invoiced + deposit.product_uom_qty
            if new_qty_invoiced == deposit.move_id.sale_line_id.product_qty:
                invoice_status = 'invoiced'
            else:
                invoice_status = 'to invoice'
            deposit.move_id.sale_line_id.write({'qty_invoiced': new_qty_invoiced, 'invoice_status': invoice_status})
            deposit.write({'state': 'draft', 'sale_move_id': False})

    @api.multi
    def revert_invoice(self):
        for deposit in self:
            if deposit.invoice_id:
                if deposit.invoice_id.state not in ['draft', 'cancel']:
                    raise UserError(
                        _("This deposit has invoices in non-draft status, please check it before reverting it"))
                deposit.invoice_id.action_invoice_cancel()
                deposit.invoice_id = False
                deposit.revert_sale()

    @api.multi
    def name_get(self):
        res = []
        for record in self:
            res.append((record.id, record.picking_id.name))
        return res

    @api.multi
    def create_claim(self):
        for deposit in self:
            customer_type = self.env.ref('crm_claim_type.crm_claim_type_customer').id

            if deposit.claim_id:
                raise UserError(_("There is already an RMA created for this deposit"))
            wh_ids = self.env['stock.warehouse'].search([('company_id', '=',
                                                          self.env.user.company_id.id)])
            commercial_partner_id = deposit.partner_id.commercial_partner_id
            claim_vals = {
                'user_id': self.env.user.id,
                'claim_type': customer_type,
                'partner_id': commercial_partner_id.id,
                'partner_phone': commercial_partner_id.phone,
                'email_from': commercial_partner_id.email,
                'warehouse_id': wh_ids and wh_ids[0].id,
                'comercial': deposit.user_id.id,
                'country': commercial_partner_id.country_id.id,
            }
            claim_id = self.env['crm.claim'].create(claim_vals)
            line_vals = {
                'product_id': deposit.product_id.id,
                'deposit_id': deposit.id,
                'claim_origine': 'broken_down',
                'product_returned_quantity': deposit.product_uom_qty,
                'claim_id': claim_id.id,
                'printed': False,
                'substate_id': self.env.ref('crm_claim_rma_custom.substate_checked').id
            }
            claim_line_id = self.env['claim.line'].create(line_vals)
            deposit.claim_id = claim_id.id
