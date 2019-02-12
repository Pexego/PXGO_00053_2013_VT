##############################################################################
#
#    Copyright 2013 Camptocamp
#    Copyright 2009-2013 Akretion,
#    Author: Emmanuel Samyn, Raphaël Valyi, Sébastien Beau,
#            Benoît Guillot, Joel Grand-Guillaume
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

import calendar
import math
from odoo import fields, models, exceptions, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import (DEFAULT_SERVER_DATE_FORMAT,
                           DEFAULT_SERVER_DATETIME_FORMAT)
from odoo import SUPERUSER_ID, api

REPAIR_SELECTION =[
            ('draft', _('Quotation')),
            ('cancel', _('Cancelled')),
            ('confirmed', _('Confirmed')),
            ('under_repair', _('Under Repair')),
            ('ready', _('Ready to Repair')),
            ('2binvoiced', _('To be Invoiced')),
            ('invoice_except', _('Invoice Exception')),
            ('done', _('Repaired'))
            ]

MOVE_STATE_SELECTION = [('draft', _('New')), ('cancel', _('Cancelled')),
                        ('waiting', _('Waiting Another Move')),
                        ('confirmed', _('Waiting Availability')),
                        ('assigned', _('Available')), ('done', _('Done'))]

class SubstateSubstate(models.Model):
    """ To precise a state (state=refused; substates= reason 1, 2,...) """
    _name = "substate.substate"
    _description = "substate that precise a given state"

    active = fields.Boolean('Active', default=True)
    name = fields.Char('Sub state', required=True)
    substate_descr = fields.Text(
            'Description',
            help="To give more information about the sub state")


class ClaimLine(models.Model):
    """
    Class to handle a product return line (corresponding to one invoice line)
    """
    _name = "claim.line"
    _description = "List of product to return"

    # Comment written in a claim.line to know about the warranty status
    WARRANT_COMMENT = {
        'valid': "Valid",
        'expired': "Expired",
        'not_define': "Not Defined"}

    # Method to calculate total amount of the line : qty*UP
    def _line_total_amount(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = (line.unit_sale_price *
                            line.product_returned_quantity)
        return res

    def copy_data(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        std_default = {
            'move_in_id': False,
            'move_out_id': False,
            'refund_line_id': False,
        }
        std_default.update(default)
        return super(ClaimLine, self).copy_data(
            cr, uid, id, default=std_default, context=context)

    @api.model
    def get_warranty_return_partner(self):
        seller = self.env['product.supplierinfo']
        result = seller.get_warranty_return_partner()
        return result

    name = fields.Char('Description', required=True)
    claim_origine = fields.Selection(
            [('broken_down', 'Broken down product'),
             ('not_appropiate', 'Not appropiate product'),
             ('none', 'Not specified'),
             ('legal', 'Legal retractation'),
             ('cancellation', 'Order cancellation'),
             ('damaged', 'Damaged delivered product'),
             ('error', 'Shipping error'),
             ('exchange', 'Exchange request'),
             ('lost', 'Lost during transport'),
             ('other', 'Other')
             ],
            'Claim Subject', default='broken_down',
            required=True,
            help="To describe the line product problem")
    claim_descr = fields.Text(
            'Claim description',
            help="More precise description of the problem")
    product_id = fields.Many2one(
            'product.product',
            string='Product',
            help="Returned product")
    equivalent_product_id = fields.Many2one(
            'product.product', 'Replacement')
    product_returned_quantity = fields.Float(
            'Quantity', digits=(12, 2), default=1.0,
            help="Quantity of product returned")
    unit_sale_price = fields.Float(
            'Unit sale price', digits=(12, 2),
            help="Unit sale price of the product. Auto filled if retrun done "
                 "by invoice selection. Be careful and check the automatic "
                 "value as don't take into account previous refunds, invoice "
                 "discount, can be for 0 if product for free,...")
    return_value = fields.Float(
            compute="_line_total_amount", string='Total return',
            help="Quantity returned * Unit sold price")
    prodlot_id = fields.Many2one(
            'stock.production.lot',
            string='Serial/Lot n°',
            help="The serial/lot of the returned product")
    applicable_guarantee = fields.Selection(
            [('us', 'Company'),
             ('supplier', 'Supplier'),
             ('brand', 'Brand manufacturer')],
            'Warranty type')
    guarantee_limit = fields.Date(
            'Warranty limit',
            readonly=True,
            help="The warranty limit is computed as: invoice date + warranty "
                 "defined on selected product.")
    warning = fields.Char(
            'Warranty',
            readonly=True,
            help="If warranty has expired")
    warranty_type = fields.Selection(
            selection=get_warranty_return_partner,
            string='Warranty type',
            readonly=True,
            help="Who is in charge of the warranty return treatment towards "
                 "the end customer. Company will use the current company "
                 "delivery or default address and so on for supplier and brand"
                 " manufacturer. Does not necessarily mean that the warranty "
                 "to be applied is the one of the return partner (ie: can be "
                 "returned to the company and be under the brand warranty")
    warranty_return_partner = fields.Many2one(
            'res.partner',
            string='Warranty Address',
            help="Where the customer has to send back the product(s)")
    claim_id = fields.Many2one(
            'crm.claim', string='Related claim',
            help="To link to the case.claim object")
    state = fields.Selection(
            [('draft', 'Draft'),
             ('refused', 'Refused'),
             ('confirmed', 'Confirmed')],
            string='State', default='draft')
    substate_id = fields.Many2one(
            'substate.substate',
            string='Sub state',
            help="Select a sub state to precise the standard state. Example 1:"
                 " state = refused; substate could be warranty over, not in "
                 "warranty, no problem,... . Example 2: state = to treate; "
                 "substate could be to refund, to exchange, to repair,...")
    last_state_change = fields.Date(
            string='Last change',
            help="To set the last state / substate change")
    invoice_line_id = fields.Many2one(
            'account.invoice.line',
            string='Invoice Line',
            help='The invoice line related to the returned product')
    refund_line_id = fields.Many2one(
            'account.invoice.line',
            string='Refund Line',
            help='The refund line related to the returned product')

    move_in_customer_id = fields.Many2one(
            'stock.move',
            string='Move Line from customer picking in',
            help='The move line related to the returned product')
    move_out_customer_id = fields.Many2one(
            'stock.move',
            string='Move Line from customer picking out',
            help='The move line related to the returned product')

    move_in_customer_state = fields.Selection(
            related='move_in_customer_id.state',
            string='picking in state', readonly=True,
            selection=MOVE_STATE_SELECTION)
    move_out_customer_state = fields.Selection(
            related="move_out_customer_id.state",
            string='picking out state', readonly=True,
            selection=MOVE_STATE_SELECTION)
    repair_id = fields.Many2one('mrp.repair', 'Repair')
    repair_state = fields.Selection(related='repair_id.state',
                                       selection = REPAIR_SELECTION,
                                       string='repair state', readonly=True)
    supplier_id = fields.Many2one('res.partner', 'Supplier')

    supplier_line_id = fields.Many2one('claim.line',
                                            'Supplier claim line')
    original_line_id = fields.Many2one('claim.line',
                                            'original claim line',
                                            readonly=True)

    claim_type = fields.Selection(related='claim_id.claim_type',
                                     string='Claim type', readonly=True)

    move_in_supplier_state = fields.Selection(
            related='supplier_line_id.move_in_customer_state',
            string='supplier picking in state', readonly=True,
            selection=MOVE_STATE_SELECTION)

    move_out_supplier_state = fields.Selection(
            related='supplier_line_id.move_out_customer_state',
            string='supplier picking out state', readonly=True,
            selection=MOVE_STATE_SELECTION)

    user_id = fields.Many2one("res.users",
            related='claim_id.user_id',
            string='Responsible', readonly=True,
            store=True)

    partner_id = fields.Many2one("res.partner",
            related='claim_id.partner_id',
            string='Customer', readonly=True,
            store=True)

    location_dest_id = fields.Many2one(
            'stock.location',
            string='Return Stock Location',
            help='The return stock location of the returned product')

    internal_description = fields.Text(string='Internal Description')

    @api.onchange('product_id')
    def _get_default_supplier(self):
        if self.product_id and len(self.product_id.seller_ids):
            self.supplier_id = self.product_id.seller_ids[0].name
            partners = self.product_id.seller_ids
        else:
            self.supplier_id = False
            partners = self.env['res.partner'].search([('supplier', '=',
                                                        True)])
        return {'domain': {'partner_id': [('id', 'in', [x.id for x in
                                                        partners])]}}

    @staticmethod
    def warranty_limit(start, warranty_duration):
        """ Take a duration in float, return the duration in relativedelta

        ``relative_delta(months=...)`` only accepts integers.
        We have to extract the decimal part, and then, extend the delta with
        days.

        """
        decimal_part, months = math.modf(warranty_duration)
        months = int(months)
        # If we have a decimal part, we add the number them as days to
        # the limit.  We need to get the month to know the number of
        # days.
        delta = relativedelta(months=months)
        monthday = start + delta
        __, days_month = calendar.monthrange(monthday.year, monthday.month)
        # ignore the rest of the days (hours) since we expect a date
        days = int(days_month * decimal_part)
        return start + relativedelta(months=months, days=days)

    # Method to calculate warranty limit
    def set_warranty_limit(self, cr, uid, ids, claim_line, context=None):
        date_invoice = claim_line.invoice_line_id.invoice_id.date_invoice
        if not date_invoice:
            raise exceptions.UserError(
                _('Cannot find any date for invoice. '
                  'Must be a validated invoice.'))
        warning = _(self.WARRANT_COMMENT['not_define'])
        date_inv_at_server = datetime.strptime(date_invoice,
                                               DEFAULT_SERVER_DATE_FORMAT)
        if claim_line.claim_id.claim_type == 'supplier':
            suppliers = claim_line.product_id.seller_ids
            if not suppliers:
                raise exceptions.UserError(
                    _('The product has no supplier configured.'))
            supplier = suppliers[0]
            warranty_duration = supplier.warranty_duration
        else:
            warranty_duration = claim_line.product_id.warranty
        limit = self.warranty_limit(date_inv_at_server, warranty_duration)
        # If waranty period was defined
        if warranty_duration > 0:
            claim_date = datetime.strptime(claim_line.claim_id.date,
                                           DEFAULT_SERVER_DATETIME_FORMAT)
            if limit < claim_date:
                warning = _(self.WARRANT_COMMENT['expired'])
            else:
                warning = _(self.WARRANT_COMMENT['valid'])
        self.write(
            cr, uid, ids,
            {'guarantee_limit': limit.strftime(DEFAULT_SERVER_DATE_FORMAT),
             'warning': warning},
            context=context)
        return True

    def auto_set_warranty(self, cr, uid, ids, context):
        """ Set warranty automatically
        if the user has not himself pressed on 'Calculate warranty state'
        button, it sets warranty for him"""
        for line in self.browse(cr, uid, ids, context=context):
            if not line.warning:
                self.set_warranty(cr, uid, [line.id], context=context)
        return True

    def get_destination_location(self, cr, uid, product_id,
                                 warehouse_id, context=None):
        """Compute and return the destination location ID to take
        for a return. Always take 'Supplier' one when return type different
        from company."""
        prod_obj = self.pool.get('product.product')
        prod = prod_obj.browse(cr, uid, product_id, context=context)
        wh_obj = self.pool.get('stock.warehouse')
        wh = wh_obj.browse(cr, uid, warehouse_id, context=context)
        location_dest_id = wh.lot_stock_id.id
        if prod:
            seller = prod.seller_id
            if seller:
                location_dest_id = seller.property_stock_supplier.id
        return location_dest_id

    # Method to calculate warranty return address
    def set_warranty_return_address(self, cr, uid, ids, claim_line,
                                    context=None):
        """Return the partner to be used as return destination and
        the destination stock location of the line in case of return.

        We can have various case here:
            - company or other: return to company partner or
              crm_return_address_id if specified
            - supplier: return to the supplier address

        """
        return_address = None
        seller = claim_line.product_id.seller_id
        if seller:
            return_address_id = seller.warranty_return_address.id
            return_type = seller.warranty_return_partner
        else:
            # when no supplier is configured, returns to the company
            company = claim_line.claim_id.company_id
            return_address = (company.crm_return_address_id or
                              company.partner_id)
            return_address_id = return_address.id
            return_type = 'company'
        location_dest_id = self.get_destination_location(
            cr, uid, claim_line.product_id.id,
            claim_line.claim_id.warehouse_id.id,
            context=context)
        self.write(cr, uid, ids,
                   {'warranty_return_partner': return_address_id,
                    'warranty_type': return_type,
                    'location_dest_id': location_dest_id},
                   context=context)
        return True

    def set_warranty(self, cr, uid, ids, context=None):
        """ Calculate warranty limit and address """
        return True

    def equivalent_products(self, cr, uid, ids, context=None):
        if not ids:
            return False
        line = self.browse(cr, uid, ids[0], context)
        wiz_obj = self.pool.get("equivalent.products.wizard")
        context['line_id'] = line.id
        wizard_id = wiz_obj.create(cr, uid, {'line_id': ids[0]},
                                   context=context)
        return {
            'name': _("Equivalent products"),
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'equivalent.products.wizard',
            'res_id': wizard_id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': context
        }


# TODO add the option to split the claim_line in order to manage the same
# product separately
class CrmClaim(models.Model):
    _inherit = "crm.claim"

    _rec_name = "number"

    @api.onchange('claim_type')
    def onchange_claim_type(self):
        if self.claim_type == 'customer':
            return {'domain': {'partner_id': [('customer', '=', True)]}}
        else:
            return {'domain': {'partner_id': [('supplier', '=', True)]}}

    def _get_sequence_number(self, cr, uid, context=None):
        seq_obj = self.pool.get('ir.sequence')
        res = seq_obj.get(cr, uid, 'crm.claim.rma', context=context) or '/'
        return res

    @api.model
    def _get_default_warehouse(self):
        company_id = self.env.user.company_id.id
        wh_obj = self.env['stock.warehouse']
        wh_ids = wh_obj.search([('company_id', '=', company_id)])
        if not wh_ids:
            raise exceptions.UserError(
                _('There is no warehouse for the current user\'s company.'))
        return wh_ids[0]

    def create(self, cr, uid, vals, context=None):
        if ('number' not in vals) or (vals.get('number') == '/'):
            vals['number'] = self._get_sequence_number(cr, uid,
                                                       context=context)
        new_id = super(CrmClaim, self).create(cr, uid, vals, context=context)
        return new_id

    def copy_data(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        std_default = {
            'invoice_ids': False,
            'picking_ids': False,
            'number': self._get_sequence_number(cr, uid, context=context),
        }
        std_default.update(default)
        return super(CrmClaim, self).copy_data(
            cr, uid, id, default=std_default, context=context)

    number = fields.Char(
            'Number', readonly=True,
            required=True,
            index=True, default='/',
            help="Company internal claim unique number")
    categ_id = fields.Many2one('crm.case.categ', 'Category')
    supplier_number = fields.Char(
            'Supplier Number',
            index=True,
            help="Supplier claim number")
    claim_type = fields.Selection(
            [('customer', 'Customer'),
             ('supplier', 'Supplier')],
            string='Claim type',
            required=True, default='customer',
            help="Customer: from customer to company.\n "
                 "Supplier: from company to supplier.")
    claim_line_ids = fields.One2many(
            'claim.line', 'claim_id',
            string='Return lines')
    planned_revenue = fields.Float('Expected revenue')
    planned_cost = fields.Float('Expected cost')
    real_revenue = fields.Float('Real revenue')
    real_cost = fields.Float('Real cost')
    invoice_ids = fields.One2many(
            'account.invoice', 'claim_id', 'Refunds')
    picking_ids = fields.One2many('stock.picking', 'claim_id', 'RMA')
    invoice_id = fields.Many2one(
            'account.invoice', string='Invoice',
            help='Related original Cusotmer invoice')
    delivery_address_id = fields.Many2one(
            'res.partner', string='Partner delivery address',
            help="This address will be used to deliver repaired or replacement"
                 "products.")
    warehouse_id = fields.Many2one(
            'stock.warehouse', string='Warehouse',
            required=True, default=_get_default_warehouse)
    state_show_buttons = fields.Boolean(related='stage_id.show_buttons',
                                        store=True, string="show buttons",
                                        readonly=True)
    rma_cost = fields.Float('RMA cost')
    invoice_type = fields.Selection([('invoice', 'Invoice'),
                                     ('refund', 'Refund')],
                                    'Invoice type', required=True,
                                    default='invoice')
    invoice_method = fields.Selection([('none', 'Not invoice'),
                                       ('b4repair', 'Before repair'),
                                       ('after_repair', 'After repair')],
                                      'Invoice method', default='none')

    _sql_constraints = [
        ('number_uniq', 'unique(number, company_id)',
         'Number/Reference must be unique per Company!'),
    ]

    def write(self, cr, uid, ids, vals, context=None):
        if context is None: context = {}
        update_vals = {}
        if vals.get('partner_id', False) or vals.get('invoice_method', False):
            for claim in self.browse(cr, uid, ids):
                if vals.get('partner_id', False) and vals['partner_id'] != \
                        claim.partner_id.id:
                    update_vals['partner_id'] = vals['partner_id']
                if vals.get('invoice_method', False) and \
                        vals['invoice_method'] != claim.invoice_method:
                    update_vals['invoice_method'] = vals['invoice_method']

        res = super(CrmClaim, self).write(cr, uid, ids, vals, context=context)
        if update_vals:
            for claim in self.browse(cr, uid, ids):
                for line in claim.claim_line_ids:
                    if line.repair_id and line.repair_id.state == 'draft':
                        line.repair_id.write(update_vals)

        return res

    def onchange_partner_address_id(self, cr, uid, ids, add, email=False,
                                    context=None):
        res = super(CrmClaim, self
                    ).onchange_partner_address_id(cr, uid, ids, add,
                                                  email=email)
        if add:
            if (not res['value']['email_from']
                    or not res['value']['partner_phone']):
                partner_obj = self.pool.get('res.partner')
                address = partner_obj.browse(cr, uid, add, context=context)
                for other_add in address.partner_id.address:
                    if other_add.email and not res['value']['email_from']:
                        res['value']['email_from'] = other_add.email
                    if other_add.phone and not res['value']['partner_phone']:
                        res['value']['partner_phone'] = other_add.phone
        return res

    def onchange_invoice_id(self, cr, uid, ids, invoice_id, warehouse_id,
                            context=None):
        invoice_line_obj = self.pool.get('account.invoice.line')
        invoice_obj = self.pool.get('account.invoice')
        claim_line_obj = self.pool.get('claim.line')
        invoice_line_ids = invoice_line_obj.search(
            cr, uid,
            [('invoice_id', '=', invoice_id)],
            context=context)
        claim_lines = []
        value = {}
        if not warehouse_id:
            warehouse_id = self._get_default_warehouse()
        invoice_lines = invoice_line_obj.browse(cr, uid, invoice_line_ids,
                                                context=context)
        for invoice_line in invoice_lines:
            location_dest_id = claim_line_obj.get_destination_location(
                cr, uid, invoice_line.product_id.id,
                warehouse_id, context=context)
            claim_lines.append({
                'name': invoice_line.name,
                'claim_origine': "none",
                'invoice_line_id': invoice_line.id,
                'product_id': invoice_line.product_id.id,
                'product_returned_quantity': invoice_line.quantity,
                'unit_sale_price': invoice_line.price_unit,
                'location_dest_id': location_dest_id,
                'state': 'draft',
            })
        value = {'claim_line_ids': claim_lines}
        delivery_address_id = False
        if invoice_id:
            invoice = invoice_obj.browse(cr, uid, invoice_id, context=context)
            delivery_address_id = invoice.partner_id.id
        value['delivery_address_id'] = delivery_address_id

        return {'value': value}

    def message_get_reply_to(self, cr, uid, ids, context=None):
        """ Override to get the reply_to of the parent project. """
        return [claim.section_id.message_get_reply_to()[0]
                if claim.section_id else False
                for claim in self.browse(cr, SUPERUSER_ID, ids,
                                         context=context)]

    def message_get_suggested_recipients(self, cr, uid, ids, context=None):
        recipients = super(CrmClaim, self
                           ).message_get_suggested_recipients(cr, uid, ids,
                                                              context=context)
        try:
            for claim in self.browse(cr, uid, ids, context=context):
                if claim.partner_id:
                    self._message_add_suggested_recipient(
                        cr, uid, recipients, claim,
                        partner=claim.partner_id, reason=_('Customer'))
                elif claim.email_from:
                    self._message_add_suggested_recipient(
                        cr, uid, recipients, claim,
                        email=claim.email_from, reason=_('Customer Email'))
        except Exception:
            # no read access rights -> just ignore suggested recipients
            # because this imply modifying followers
            pass
        return recipients


class CrmClaimStage(models.Model):

    _inherit = "crm.claim.stage"

    show_buttons = fields.Boolean('Show buttons')
    closed = fields.Boolean('closed')
