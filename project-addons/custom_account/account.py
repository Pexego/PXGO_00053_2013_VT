# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Pexego All Rights Reserved
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


class AccountMoveLine(models.Model):

    _inherit = 'account.move.line'

    @api.one
    def get_mandate_scheme(self):
        if self.invoice and self.invoice.mandate_id:
            self.scheme = self.invoice.mandate_id.scheme

    @api.model
    def _mandate_scheme_search(self, operator, operand):
        invoice_obj = self.env['account.invoice']
        invoices = invoice_obj.search([('mandate_id.scheme', operator,
                                        operand),('move_id', '!=', False)])
        moves = [x.move_id.id for x in invoices]
        return [('move_id', 'in', moves)]

    scheme = fields.Selection(selection=[('CORE', 'Basic (CORE)'),
                                         ('B2B', 'Enterprise (B2B)')],
                              string='Scheme',
                              compute='get_mandate_scheme',
                              search='_mandate_scheme_search')
    partner_vat = fields.Char("CIF/NIF/VAT", related="partner_id.vat",
                              readonly=True)


class AccountBankingMandate(models.Model):

    _inherit = 'account.banking.mandate'

    default = fields.Boolean('Set default')


class AccountInvoiceLine(models.Model):

    _inherit = 'account.invoice.line'

    move_id = fields.Many2one('stock.move', 'Move', copy=False)
    picking_id = fields.Many2one("stock.picking", "Picking",
                                 related="move_id.picking_id",
                                 readonly=True)
    purchase_supplier_reference = fields.Char(
        'Supplier reference', related='purchase_line_id.order_id.partner_ref',
        readonly=True)


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    attach_picking = fields.Boolean('Attach picking')
    picking_ids = fields.One2many('stock.picking', string='pickings',
                                  compute='_get_picking_ids')
    country_id = fields.Many2one('res.country', 'Country',
                                 related="partner_id.country_id",
                                 readonly=True, store=True)
    invoice_type_id = fields.\
        Many2one('res.partner.invoice.type', 'Invoice type', readonly=True,
                 related="invoice_line.picking_id.invoice_type_id")

    @api.model
    def create(self, vals):
        if vals.get('partner_id', False):
            partner = self.env["res.partner"].browse(vals["partner_id"])
            if partner.attach_picking:
                vals["attach_picking"] = partner.attach_picking
        if 'type' in vals and 'partner_bank_id' in vals:
            if vals['type'] == 'out_invoice':
                partner_bank = self.env['res.partner.bank'].browse(vals['partner_bank_id'])
                mandate_ids = partner_bank.mandate_ids
                default_mandate = mandate_ids.filtered(
                    lambda r: r.default and r.state == "valid")
                if not default_mandate:
                    default_mandate = mandate_ids.filtered(
                        lambda r: r.state == "valid")
                vals['mandate_id'] = default_mandate and default_mandate[0].id or False
        return super(AccountInvoice, self).create(vals)

    @api.multi
    def onchange_partner_bank_cust(self, partner_bank_id=False):
        mandate_id = False
        if partner_bank_id:
            partner_bank = self.env['res.partner.bank'].browse(partner_bank_id)
            mandate_ids = partner_bank.mandate_ids
            default_mandate = mandate_ids.filtered(
                lambda r: r.default and r.state == "valid")
            if not default_mandate:
                default_mandate = mandate_ids.filtered(
                    lambda r: r.state == "valid")
            mandate_id = default_mandate and default_mandate[0] or False
        return {'value': {'mandate_id': mandate_id and mandate_id.id or False}}


    @api.multi
    def onchange_partner_id(self, type, partner_id, date_invoice=False,
                            payment_term=False, partner_bank_id=False,
                            company_id=False):
        result = super(AccountInvoice, self).onchange_partner_id(
            type, partner_id, date_invoice=date_invoice,
            payment_term=payment_term, partner_bank_id=partner_bank_id,
            company_id=company_id)
        if partner_id:
            partner = self.env["res.partner"].browse(partner_id)
            result['value']['attach_picking'] = partner.attach_picking

        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        res = super(AccountInvoice, self).name_search(name, args=args,
                                                      operator=operator,
                                                      limit=limit)
        args = args or []
        recs = self.browse()
        if not res:
            recs = self.search([('invoice_number', operator, name)] + args, limit=limit)
            res = recs.name_get()
        return res

    @api.multi
    @api.depends('invoice_line')
    def _get_picking_ids(self):
        for invoice in self:
            invoice.picking_ids = invoice.\
                mapped('invoice_line.move_id.picking_id').sorted()
