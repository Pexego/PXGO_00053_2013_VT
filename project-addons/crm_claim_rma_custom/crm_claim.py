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

    @api.model
    def create(self, vals):
        if vals.get('name', False):
            vals['name'] = vals['name'].split(' ')[0]
        return super(CrmClaimRma, self).create(vals)

    def calculate_invoices(self, cr, uid, ids, context=None):
        """
        Calculate invoices using data "Product Return of SAT"
        """
        claim_obj = self.browse(cr, uid, ids)
        claim_inv_line_obj = self.pool.get('claim.invoice.line')
        claim_inv_lines = claim_inv_line_obj.search(cr, uid,
                                 [('claim_id', '=', claim_obj.id)])
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
                            'qty': inv_line.quantity,
                            'price_unit': inv_line.price_unit,
                            'price_subtotal': inv_line.price_subtotal,
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
                fp_obj = self.pool.get('account.fiscal.position')
                fiscal_position = claim_obj.partner_id.property_account_position

                taxes = account_tax.browse(cr, uid,
                        map(lambda x: x.id,
                        claim_line.product_id.supplier_taxes_id))
                fpos = fiscal_position and account_fiscal_position.browse(\
                        cr, uid, fiscal_position.id, context=context) or False
                taxes_ids = account_fiscal_position.map_tax(cr, uid,
                                                            fpos, taxes)
                price_subtotal = quantity * price
                vals = {
                    'claim_id': claim_line.claim_id.id,
                    'claim_number': claim_line.claim_id.number,
                    'product_id': product,
                    'claim_line_id': claim_line.id,
                    'product_description': claim_line.product_id.name,
                    'qty': quantity,
                    'price_unit': price,
                    'price_subtotal': price_subtotal,
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
                    raise exceptions.Warning(_("Claim is just invoiced"))
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
                account_id = line.product_id.property_account_income.id
                if not account_id:
                    account_id = \
                      line.product_id.categ_id.property_account_income_categ.id
                else:
                  account_id = line.product_id.property_account_expense.id
                  if not account_id:
                    account_id = \
                      line.product_id.categ_id.property_account_expense_categ.id
                fiscal_position = claim_obj.partner_id.property_account_position
                account_id = fp_obj.map_account(cr, uid,
                                                fiscal_position, account_id)
                vals = {
                    'invoice_id': inv_id,
                    'name': line.claim_number,
                    'product_id': line.product_id.id,
                    'account_id': account_id,
                    'quantity': line.qty,
                    'claim_line_id': line.claim_line_id.id,
                    'price_unit': line.price_unit,
                    'uos_id': line.product_id.uos_id.id,
                    'discount': line.discount,
                    'account_analytic_id': False
                }
                if line.tax_ids:
                    taxes_ids = [tax.id for tax in line.tax_ids]
                    vals['invoice_line_tax_id'] = [(6, 0, taxes_ids)],
                line_obj = self.pool.get('account.invoice.line')
                line_id = line_obj.create(cr, uid, vals, context=context)
            invoice_id.write({
                         'origin_invoices_ids': [(6, 0, rectified_invoice_ids)]
                         })


class ClaimInvoiceLine(models.Model):

    _name = "claim.invoice.line"

    claim_id = fields.Many2one('crm.claim', 'Claim')
    claim_number = fields.Char("Claim Number")
    claim_line_id = fields.Many2one('claim.line', 'Claim lne')
    product_id = fields.Many2one("product.product", "Product Code")
    product_description = fields.Char("Product Description")
    invoice_id = fields.Many2one("account.invoice", "Invoice")
    price_unit = fields.Float("Price Unit")
    price_subtotal = fields.Float("Price Subtotal", readonly=True)
    tax_ids = fields.Many2many("account.tax","claim_line_tax","claimline_id",
                               "tax_id", string="Taxes ID")
    tax_name = fields.Char("Tax")
    discount = fields.Float("Discount")
    qty = fields.Float("Quantity")

    def onchange_product_id(self, cr, uid, ids, product, invoice=False,
            context=None):
        if product:
            product_id = self.pool.get('product.product').browse(cr, uid,
                                                                 product)
            res = {'value': {}}
            if invoice:
                res['value'] = {'invoice_id': invoice}
                invoice_id = self.pool.get('account.invoice').browse(cr, uid,
                                                                 invoice)
                any_line = True
                for line in invoice_id.invoice_line:
                    if not product_id == line.product_id:
                        any_line = False
                if any_line == False:
                    raise exceptions.Warning(_('Selected product is not \
                                                in the invoice'))
            claim_line_ids = self.browse(cr, uid, ids)
            qty = claim_line_ids.qty or 1.0
            claim_obj = self.pool.get('crm.claim').browse(cr, uid,
                                                      claim_line_ids.claim_id)
            pricelist = claim_obj.partner_id.property_product_pricelist.id
            import ipdb; ipdb.set_trace()
            price = self.pool.get('product.pricelist').price_get(cr, uid,
                    [pricelist],product, qty or 1.0,
                    claim_obj.partner_id, {
                        'uom': claim_line_ids.product_id.uom_id.id or \
                                                       product_id.uom_id.id,
                        'date': claim_obj.date,
                        })[pricelist]
            price_unit = price or 0.0
            discount = claim_line_ids.discount or 0.0
            price_subtotal = claim_line_ids.calculate_price_subtotal(qty,
                                                       price_unit, discount)

            res['value'].update({
                'product_id': product_id.id,
                'product_description': product_id.name,
                'qty': qty,
                'price_unit': price_unit,
                'discount': discount,
                'price_subtotal': price_subtotal
            })
            claim_ids = self.pool.get('crm.claim').browse(cr, uid,
                                                       claim_line_ids.claim_id)
            return res

    def onchange_values(self, cr, uid, ids, qty, price_unit, discount,
                        context=None):
        claim_inv_line_id = self.browse(cr, uid, ids)
        price_subtotal = claim_inv_line_id.calculate_price_subtotal(qty,
                                             price_unit, discount)
        res = {'value': {'price_subtotal': price_subtotal}}
        return res

    def calculate_price_subtotal(self, cr, uid, qty, price_unit, discount=None):
        return discount and qty * price_unit - (discount * price_unit/100) or \
                         qty * price_unit

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
