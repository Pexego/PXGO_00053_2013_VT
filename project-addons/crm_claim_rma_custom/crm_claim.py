# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea Servicios Tecnológicos All Rights Reserved
#    $Omar Castiñeira Saavedra <omar@comunitea.com>$
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

from openerp import models, fields, api, exceptions, _
from datetime import datetime


class CrmClaimRma(models.Model):

    _inherit = "crm.claim"
    _order = "id desc"

    name = fields.Selection([('return', 'Return'),
                             ('rma', 'RMA')], 'Claim Subject',
                            required=True, default='rma')
    # priority = fields.Selection(default=0)
    priority = fields.Selection(default=0,
        selection=[('1', 'High'),
                   ('2', 'Critical')])
    comercial = fields.Many2one("res.users",string="Comercial")
    # date_received = fields.Datetime('Received Date', default=lambda *a:datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    date_received = fields.Datetime('Received Date')
    aditional_notes = fields.Text("Aditional Notes")
    claim_inv_line_ids = fields.One2many("claim.invoice.line", "claim_id")

    @api.onchange('claim_type')
    def onchange_claim_type(self):
        if self.claim_type == 'customer':
            return {'domain': {'partner_id': [('customer', '=', True),('is_company', '=', 't')]}}
        else:
            return {'domain': {'partner_id': [('supplier', '=', True),('is_company', '=', 't')]}}

    @api.model
    def create(self, vals):
        if vals.get('name', False):
            vals['name'] = vals['name'].split(' ')[0]
        return super(CrmClaimRma, self).create(vals)

    def _get_sequence_number(self, cr, uid, context=None):
        seq_obj = self.pool.get('ir.sequence')
        res = seq_obj.get(cr, uid, 'crm.claim.rma', context=context) or '/'
        if context['claim_type'] == 'supplier' and not res == '/':
            seq = res.split('-')[1]
            res = u'RMP' + '-' + seq
        return res

    def calculate_invoices(self, cr, uid, ids, context=None):
        """
        Calculate invoices using data "Product Return of SAT"
        """
        claim_obj = self.browse(cr, uid, ids)
        claim_inv_line_obj = self.pool.get('claim.invoice.line')
        claim_inv_lines = claim_inv_line_obj.search(cr, uid,
                                                    [('claim_id', '=',
                                                      claim_obj.id)])
        claim_inv_line_obj.unlink(cr, uid, claim_inv_lines)
        for claim_line in claim_obj.claim_line_ids:
            vals = {}
            taxes_ids = []
            if claim_line.invoice_id:
                for inv_line in claim_line.invoice_id.invoice_line:
                    if inv_line.product_id == claim_line.product_id:
                        if inv_line.invoice_line_tax_id:
                            taxes_ids = \
                               [tax.id for tax in inv_line.invoice_line_tax_id]
                        vals = {
                            'invoice_id': inv_line.invoice_id.id,
                            'claim_id': claim_line.claim_id.id,
                            'claim_number': claim_line.claim_id.number,
                            'claim_line_id': claim_line.id,
                            'product_id': inv_line.product_id.id,
                            'product_description': inv_line.product_id.name,
                            'discount': inv_line.discount,
                            'qty': claim_line.product_returned_quantity,
                            'price_unit': inv_line.price_unit,
                            'tax_ids': [(6, 0, taxes_ids)]
                        }
                    else:
                        raise exceptions.Warning(
                            _("There is at least one line of the claim with \
                               an incorrect invoice"))
            else:
                product = claim_line.product_id.id
                pricelist = claim_obj.partner_id.property_product_pricelist.id
                quantity = claim_line.product_returned_quantity
                price = self.pool.get('product.pricelist').price_get(cr, uid,
                        [pricelist],product, quantity or 1.0,
                        claim_obj.partner_id, {
                            'uom': claim_line.product_id.uom_id.id or \
                                result.get('product_uom'),
                            'date': claim_obj.date,
                            })[pricelist]
                account_tax = self.pool.get('account.tax')
                account_fiscal_position = \
                    self.pool.get('account.fiscal.position')
                fiscal_position = claim_obj.partner_id.property_account_position
                taxes_ids = account_fiscal_position.\
                    map_tax(cr, uid, fiscal_position,
                            claim_line.product_id.taxes_id)
                price_subtotal = quantity * price
                vals = {
                    'claim_id': claim_line.claim_id.id,
                    'claim_number': claim_line.claim_id.number,
                    'product_id': product,
                    'claim_line_id': claim_line.id,
                    'product_description': claim_line.product_id.name,
                    'qty': quantity,
                    'price_unit': price,
                    'tax_ids': [(6, 0, taxes_ids)]
                }
            claim_inv_line_obj.create(cr, uid, vals, context)

    def onchange_partner_id(self, cr, uid, ids, partner_id, email=False,
                            context=None):
        res = super(CrmClaimRma, self).onchange_partner_id(cr, uid, ids,
                                                           partner_id,
                                                           email=email,
                                                           context=context)
        if partner_id:
            partner = self.pool["res.partner"].browse(cr, uid, partner_id)
            res['value']['delivery_address_id'] = partner_id
            if partner.user_id:
                res['value']['comercial'] = partner.user_id.id

        return res

    def onchange_name(self, cr, uid, ids, name, context=None):
        if name == 'return':
            return {'value': {'invoice_type': 'refund'}}
        elif name == 'rma':
            return {'value': {'invoice_type': 'invoice'}}

    def make_refund_invoice(self, cr, uid, ids, context=None):
        for claim_obj in self.browse(cr, uid, ids):
            domain_acc_inv = [('type', '=', 'out_refund'),
                              ('partner_id', '=', claim_obj.partner_id.id)]
            accinv_refund_obj = self.pool.get('account.invoice')
            accinv_refund_ids = accinv_refund_obj.search(cr, uid,
                                                         domain_acc_inv)
            for ai in accinv_refund_obj.browse(cr, uid, accinv_refund_ids):
                if ai.claim_id == claim_obj:
                    raise exceptions.Warning(_("There is already an invoice \
                                                with this claim"))
            domain_journal = [('name','like','Sales Refund')]
            acc_journal_obj = self.pool.get('account.journal')
            acc_journal_ids = acc_journal_obj.search(cr, uid, domain_journal)
            header_vals = {
              'partner_id': claim_obj.partner_id.id,
              'fiscal_position': \
                             claim_obj.partner_id.property_account_position.id,
              'date_invoice': datetime.now().strftime('%Y-%m-%d'),
              'journal_id': acc_journal_ids[0],
              'account_id': claim_obj.partner_id.property_account_receivable.id,
              'currency_id': \
                claim_obj.partner_id.property_product_pricelist.currency_id.id,
              'company_id': claim_obj.company_id.id,
              'user_id': uid,
              'claim_id': claim_obj.id,
              'type': 'out_refund'
            }
            inv_obj = self.pool.get('account.invoice')
            inv_id = inv_obj.create(cr, uid, header_vals, context=context)
            invoice_id = inv_obj.browse(cr, uid, inv_id)
            rectified_invoice_ids = []
            fp_obj = self.pool.get('account.fiscal.position')
            for line in claim_obj.claim_inv_line_ids:
                if line.invoice_id:
                    rectified_invoice_ids.append(line.invoice_id.id)
                if line.product_id:
                    account_id = line.product_id.property_account_income.id
                    if not account_id:
                        account_id = \
                          line.product_id.categ_id.property_account_income_categ.id
                    else:
                      account_id = line.product_id.property_account_expense.id
                      if not account_id:
                        account_id = \
                          line.product_id.categ_id.property_account_expense_categ.id
                else:
                    prop = self.pool.get('ir.property').get(cr, uid,
                            'property_account_income_categ', 'product.category',
                            context=context)
                    account_id = prop and prop.id or False
                fiscal_position = claim_obj.partner_id.property_account_position
                account_id = fp_obj.map_account(cr, uid,
                                                fiscal_position, account_id)
                vals = {
                    'invoice_id': inv_id,
                    'name': line.product_description,
                    'product_id': line.product_id.id,
                    'account_id': account_id,
                    'quantity': line.qty,
                    'claim_line_id': line.claim_line_id.id,
                    'price_unit': line.price_unit,
                    'uos_id': line.product_id.uom_id.id,
                    'discount': line.discount,
                    'account_analytic_id': False
                }
                if line.tax_ids:
                    fiscal_position = claim_obj.partner_id.\
                        property_account_position
                    taxes_ids = fp_obj.map_tax(cr, uid, fiscal_position,
                                               line.tax_ids)
                    vals['invoice_line_tax_id'] = [(6, 0, taxes_ids)]
                line_obj = self.pool.get('account.invoice.line')
                line_id = line_obj.create(cr, uid, vals, context=context)
            invoice_id.write({
                         'origin_invoices_ids': [(6, 0, rectified_invoice_ids)]
                         })
            invoice_id.button_reset_taxes()

            data_pool = self.pool.get('ir.model.data')
            action_id = data_pool.xmlid_to_res_id(cr, uid,
                                               'account.action_invoice_tree3')
            if action_id:
                action_pool = self.pool['ir.actions.act_window']
                action = action_pool.read(cr, uid, action_id, context=context)
                action['domain'] = "[('id','in', [" + str(invoice_id.id) + "])]"
                return action


class ClaimInvoiceLine(models.Model):

    _name = "claim.invoice.line"
    _rec_name = "product_description"

    claim_id = fields.Many2one('crm.claim', 'Claim')
    claim_number = fields.Char("Claim Number")
    claim_line_id = fields.Many2one('claim.line', 'Claim lne')
    product_id = fields.Many2one("product.product", "Product Code")
    product_description = fields.Char("Product Description", required=True)
    invoice_id = fields.Many2one("account.invoice", "Invoice")
    price_unit = fields.Float("Price Unit")
    price_subtotal = fields.Float("Price Subtotal", compute="_get_subtotal",
                                  readonly=True)
    tax_ids = fields.Many2many("account.tax","claim_line_tax","claimline_id",
                               "tax_id", string="Taxes")
    discount = fields.Float("Discount")
    qty = fields.Float("Quantity", default="1")

    @api.one
    def _get_subtotal(self):
        self.price_subtotal = self.discount and \
            self.qty * self.price_unit - (self.discount *
                                          self.price_unit/100) or \
            self.qty * self.price_unit

    @api.onchange("product_id", "invoice_id")
    def onchange_product_id(self):
        if self.claim_id.partner_id:
            if self.product_id:
                domain_taxes = [('type_tax_use', '=', 'sale')]
                taxes_ids = [1,]
                if self.invoice_id:
                    # res['value'] = {'invoice_id': self.invoice_id.id}
                    any_line = False
                    for line in self.invoice_id.invoice_line:
                        if not self.product_id == line.product_id:
                            any_line = False
                        else:
                            any_line = True
                            price = line.price_unit
                            taxes_ids = line.invoice_line_tax_id
                            break
                    if any_line == False:
                        raise exceptions.Warning(_('Selected product is not \
                                                    in the invoice'))
                else:
                    pricelist_obj = \
                        self.claim_id.partner_id.property_product_pricelist
                    price = pricelist_obj.price_get(self.product_id.id, 1.0)
                    if price:
                        price = price[pricelist_obj.id]
                self.product_description = self.product_id.name
                self.qty = 1.0
                self.price_unit = price
                self.price_subtotal = price
                self.discount = 0.0
                self.tax_ids = taxes_ids
            else:
                self.price_subtotal = self.discount and \
                    self.qty * self.price_unit - (self.discount *
                                                  self.price_unit/100) or \
                    self.qty * self.price_unit
        else:
            raise exceptions.Warning(_('Partner not selected'))

    def onchange_values(self, cr, uid, ids, qty, price_unit, discount,
                        context=None):
        claim_inv_line_id = self.browse(cr, uid, ids)
        price_subtotal = discount and \
                         qty * price_unit - (discount * price_unit/100) or \
                                                              qty * price_unit
        res = {'value': {'price_subtotal': price_subtotal}}
        return res

class CrmClaimLine(models.Model):

    _inherit = "claim.line"

    name = fields.Char(required=False)
    invoice_id = fields.Many2one("account.invoice", string="Invoice")
    res = {}


    @api.model
    def create(self, vals):
        if 'substate_id' not in vals.keys():
            vals['substate_id'] = self.env.ref(
                'crm_claim_rma_custom.substate_due_receive').id
        return super(CrmClaimLine, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'repair_id' in vals.keys():
            vals['substate_id'] = self.env.ref(
                'crm_claim_rma_custom.substate_repaired').id
        return super(CrmClaimLine, self).write(vals)

    @api.multi
    def action_split(self):
        for line in self:
            if line.product_returned_quantity > 1:
                for x in range(1,int(line.product_returned_quantity)):
                    line.copy(default={'product_returned_quantity': 1.0})
                line.product_returned_quantity = 1
        return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }

    @api.multi
    def create_repair(self):
        self.ensure_one()
        wzd = self.env["claim.make.repair"].create({'line_id': self.id})
        res = wzd.make()
        return res
