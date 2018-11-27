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
from openerp.exceptions import except_orm


class equivalent_products_wizard(models.TransientModel):
    _inherit = "equivalent.products.wizard"

    tag_ids = fields.Many2many('product.tag',
                               'equivalent_products_tag_rel2',
                               'prod_id', 'tag_id',
                               'Tags')

class CrmClaimRma(models.Model):
    _inherit = "crm.claim"
    _order = "id desc"

    @api.one
    def _has_category(self, expected_category):
        has_category = False
        for category in self.category_id:
            if category.parent_id.id == expected_category.id:
                has_category = True
        self.bool_category_id = has_category

    @api.multi
    def _check_category_id(self):
        expected_category = self.env['res.partner.category'].search([('name', '=', 'Certificado')])
        for claim in self:
            self._has_category(expected_category)

    name = fields.Selection([('return', 'Return'),
                             ('rma', 'RMA')], 'Claim Subject',
                            required=True, default='rma')
    priority = fields.Selection(default='1', required=True, selection=[('1', 'No priority'), 
                                                                       ('2', 'High'),
                                                                       ('3', 'Critical')])
    comercial = fields.Many2one("res.users", string="Comercial")
    country = fields.Many2one("res.country", string="Country")
    date = fields.Date('Claim Date', select=True,
                       default=fields.Date.context_today)
    write_date = fields.Datetime("Update date", readonly=True)
    date_received = fields.Date('Received Date')
    category_id = fields.Many2many(related='partner_id.category_id', readonly=True)
    bool_category_id = fields.Boolean(string="Category", compute=_check_category_id)
    aditional_notes = fields.Text("Aditional Notes")
    claim_inv_line_ids = fields.One2many("claim.invoice.line", "claim_id")
    allow_confirm_blocked = fields.Boolean('Allow confirm', copy=False)

    check_states = ['substate_received', 'substate_process', 'substate_due_receive']

    @api.multi
    def button_update_lines_wizard(self):
        if not self.claim_line_ids:
            return False

        view_id_wizard = self.env.ref('crm_claim_rma_custom.claim_line_update_view').id

        return {
            'name': _('Data update in common in all RMA lines'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'claim.line',
            'type': 'ir.actions.act_window',
            'res_id': self.claim_line_ids[0].id,
            'view_id': view_id_wizard,
            'target': 'new',
        }

    @api.onchange('claim_type')
    def onchange_claim_type(self):
        if self.claim_type == 'customer':
            return {'domain': {'partner_id': [('customer', '=', True),
                                              ('is_company', '=', True)]}}
        else:
            return {'domain': {'partner_id': [('supplier', '=', True),
                                              ('is_company', '=', True)]}}

    @api.multi
    def write(self, vals):
        if 'stage_id' in vals:
            stage_ids = []
            stage_repaired_id = self.env.ref('crm_claim.stage_claim2').id
            stage_ids.append(stage_repaired_id)
            stage_pending_shipping_id = self.env.ref('crm_claim_rma_custom.stage_claim6').id
            stage_ids.append(stage_pending_shipping_id)
            if vals['stage_id'] in stage_ids:
                for line in self.claim_line_ids:
                    line_state = self.env['ir.model.data'].search([('model', '=', 'substate.substate'),
                                                                   ('module', '=', 'crm_claim_rma_custom'),
                                                                   ('res_id', '=', line.substate_id.id)])
                    if vals['stage_id'] == stage_repaired_id:
                        if line_state.name in self.check_states:
                            raise except_orm(_('Warning!'),
                                             _("One or more products aren't review yet!"))
                    else:
                        if line_state.name != 'substate_pending_shipping':
                            raise except_orm(_('Warning!'),
                                             _("One or more products aren't pending shipping yet!"))

        return super(CrmClaimRma, self).write(vals)

    @api.model
    def create(self, vals):
        if vals.get('name', False):
            vals['name'] = vals['name'].split(' ')[0]
        return super(CrmClaimRma, self).create(vals)

    def _get_sequence_number(self, cr, uid, context=None):
        seq_obj = self.pool.get('ir.sequence')
        if 'claim_type' in context and context['claim_type'] == 'supplier':
            res = seq_obj.get(cr, uid, 'crm.claim.rma.supplier',
                              context=context) or '/'
        else:
            res = seq_obj.get(cr, uid, 'crm.claim.rma',
                              context=context) or '/'
        return res

    def calculate_invoices(self, cr, uid, ids, context=None):
        """
        Calculate invoices using data "Product Return of SAT"
        """
        claim_obj = self.browse(cr, uid, ids)
        claim_inv_line_obj = self.pool.get('claim.invoice.line')
        for invoice_line in claim_obj.claim_inv_line_ids:
            if not invoice_line.invoiced:
                invoice_line.unlink()
        for claim_line in claim_obj.claim_line_ids:
            vals = {}
            taxes_ids = []
            if claim_line.invoice_id:
                claim_inv_lines = claim_inv_line_obj.search(cr, uid,
                                                            [('claim_line_id', '=',
                                                              claim_line.id)])
                if claim_inv_lines:
                    continue
                for inv_line in claim_line.invoice_id.invoice_line:
                    if inv_line.product_id == claim_line.product_id:
                        if inv_line.invoice_line_tax_id:
                            taxes_ids = \
                                [x.id for x in inv_line.invoice_line_tax_id]
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
                        break
                if not vals:
                    raise exceptions.Warning(
                        _("There is at least one line of the claim with \
                           an incorrect invoice"))
            if vals:
                claim_inv_line_obj.create(cr, uid, vals, context)

    def onchange_partner_id(self, cr, uid, ids, partner_id, email=False, context=None):
        res = super(CrmClaimRma, self).onchange_partner_id(cr, uid, ids, partner_id, email=email, context=context)

        if partner_id:
            partner = self.pool["res.partner"].browse(cr, uid, partner_id)
            res['value']['delivery_address_id'] = partner_id
            res['value']['section_id'] = partner.section_id   # Get section_id from res.partner
            res['value']['country'] = partner.country_id      # Get country_id from res.partner
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

            invoice = False
            for line in claim_obj.claim_inv_line_ids:
                if not line.invoiced:
                    invoice = True

            if not invoice:
                raise exceptions.Warning(_("Any line to invoice"))

            domain_journal = [('type', '=', 'sale_refund')]
            acc_journal_obj = self.pool.get('account.journal')
            acc_journal_ids = acc_journal_obj.search(cr, uid, domain_journal)
            partner_bank_id = False
            for banks in claim_obj.partner_id.bank_ids:
                for mandate in banks.mandate_ids:
                    if mandate.state == 'valid':
                        partner_bank_id = banks.id
                        break
                    else:
                        partner_bank_id = False
            header_vals = {
                'partner_id': claim_obj.partner_id.id,
                'fiscal_position':
                    claim_obj.partner_id.property_account_position.id,
                'date_invoice': datetime.now().strftime('%Y-%m-%d'),
                'journal_id': acc_journal_ids[0],
                'account_id':
                    claim_obj.partner_id.property_account_receivable.id,
                'currency_id':
                    claim_obj.partner_id.property_product_pricelist.currency_id.id,
                'company_id': claim_obj.company_id.id,
                'user_id': uid,
                'section_id': claim_obj.partner_id.section_id.id,
                'claim_id': claim_obj.id,
                'type': 'out_refund',
                'payment_term': claim_obj.partner_id.property_payment_term.id,
                'payment_mode_id':
                    claim_obj.partner_id.customer_payment_mode.id,
                'partner_bank_id': partner_bank_id
            }
            inv_obj = self.pool.get('account.invoice')
            inv_id = inv_obj.create(cr, uid, header_vals, context=context)
            invoice_id = inv_obj.browse(cr, uid, inv_id)
            rectified_invoice_ids = []
            fp_obj = self.pool.get('account.fiscal.position')
            for line in claim_obj.claim_inv_line_ids:
                if line.invoiced:
                    continue
                if line.invoice_id:
                    rectified_invoice_ids.append(line.invoice_id.id)
                if line.product_id:
                    account_id = line.product_id.property_account_income.id
                    if not account_id:
                        account_id = \
                            line.product_id.categ_id. \
                            property_account_income_categ.id
                    else:
                        account_id = line.product_id. \
                            property_account_expense.id
                        if not account_id:
                            account_id = \
                                line.product_id.categ_id. \
                                property_account_expense_categ.id
                else:
                    prop = self.pool.get('ir.property'). \
                        get(cr, uid,
                            'property_account_income_categ',
                            'product.category', context=context)
                    account_id = prop and prop.id or False
                fiscal_position = claim_obj.partner_id. \
                    property_account_position
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
                    fiscal_position = claim_obj.partner_id. \
                        property_account_position
                    taxes_ids = fp_obj.map_tax(cr, uid, fiscal_position,
                                               line.tax_ids)
                    vals['invoice_line_tax_id'] = [(6, 0, taxes_ids)]
                line_obj = self.pool.get('account.invoice.line')
                line_obj.create(cr, uid, vals, context=context)

                line.invoiced = True

            invoice_id. \
                write({'origin_invoices_ids':
                           [(6, 0, list(set(rectified_invoice_ids)))]})
            invoice_id.button_reset_taxes()

            data_pool = self.pool.get('ir.model.data')
            action_id = data_pool. \
                xmlid_to_res_id(cr, uid, 'account.action_invoice_tree3')
            if action_id:
                action_pool = self.pool['ir.actions.act_window']
                action = action_pool.read(cr, uid, action_id, context=context)
                action['domain'] = \
                    "[('id','in', [" + str(invoice_id.id) + "])]"
                return action


class ClaimInvoiceLine(models.Model):
    _name = "claim.invoice.line"
    _rec_name = "product_description"
    _order = 'sequence,id'

    sequence = fields.Integer()
    claim_id = fields.Many2one('crm.claim', 'Claim')
    claim_number = fields.Char("Claim Number")
    claim_line_id = fields.Many2one('claim.line', 'Claim lne')
    product_id = fields.Many2one("product.product", "Product Code")
    product_description = fields.Char("Product Description", required=True)
    invoice_id = fields.Many2one("account.invoice", "Invoice")
    price_unit = fields.Float("Price Unit")
    price_subtotal = fields.Float("Price Subtotal", compute="_get_subtotal",
                                  readonly=True)
    tax_ids = fields.Many2many("account.tax", "claim_line_tax",
                               "claimline_id", "tax_id", string="Taxes")
    discount = fields.Float("Discount")
    qty = fields.Float("Quantity", default="1")
    invoiced = fields.Boolean("Invoiced")

    @api.one
    def _get_subtotal(self):
        self.price_subtotal = self.qty * self.price_unit * ((100.0 - self.discount) / 100.0)

    @api.onchange("product_id", "invoice_id")
    def onchange_product_id(self):
        if self.claim_id.partner_id:
            if self.product_id:
                taxes_ids = []
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
                    if not any_line:
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
                if taxes_ids:
                    self.tax_ids = taxes_ids
                else:
                    fpos = self.claim_id.partner_id.property_account_position
                    self.tax_ids = fpos.map_tax(self.product_id.product_tmpl_id.taxes_id)
            else:
                self.price_subtotal = self.discount and \
                                      self.qty * self.price_unit - (self.discount *
                                                                    self.price_unit / 100) or \
                                      self.qty * self.price_unit
        else:
            raise exceptions.Warning(_('Partner not selected'))

    @api.onchange("qty", "price_unit", "discount")
    def onchange_values(self):
        if self.product_id and self.invoice_id:
            for line in self.invoice_id.invoice_line:
                if line.product_id == self.product_id and line.quantity < self.qty:
                    raise exceptions.Warning(_('Quantity cannot be bigger than the quantity specified on invoice'))
        price_subtotal = self.qty * self.price_unit * ((100.0 - self.discount) / 100.0)
        res = {'value': {'price_subtotal': price_subtotal}}
        return res

    @api.multi
    def unlink(self):
        for line in self:
            if line.invoiced:
                raise exceptions.Warning(_("Cannot delete an invoiced line"))
        return super(ClaimInvoiceLine, self).unlink()


class CrmClaimLine(models.Model):
    _inherit = "claim.line"

    comercial = fields.Many2one("res.users", String="Comercial", related="claim_id.comercial")
    date_received = fields.Date(related="claim_id.date_received")
    name = fields.Char(required=False)
    invoice_id = fields.Many2one("account.invoice", string="Invoice")
    substate_id = fields. \
        Many2one(default=lambda self:
    self.env.ref('crm_claim_rma_custom.substate_due_receive').id)
    claim_name = fields.Selection(related='claim_id.name', readonly=True)

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
                for x in range(1, int(line.product_returned_quantity)):
                    line.copy(default={'product_returned_quantity': 1.0})
                line.product_returned_quantity = 1
        return {'type': 'ir.actions.client',
                'tag': 'reload'}

    @api.multi
    def create_repair(self):
        self.ensure_one()
        wzd = self.env["claim.make.repair"].create({'line_id': self.id})
        res = wzd.make()
        return res

    @api.multi
    def button_update_lines(self):
        # Get the parameters of action wizard
        substate_id_wizard = self.substate_id
        claim_origine_wizard = self.claim_origine
        invoice_id_wizard = self.invoice_id

        # Rewrite the parameters of claim_lines
        for rma_line in self.claim_id.claim_line_ids:
            rma_line.write({'substate_id': substate_id_wizard.id, 'claim_origine': claim_origine_wizard,
                            'invoice_id': invoice_id_wizard.id})







