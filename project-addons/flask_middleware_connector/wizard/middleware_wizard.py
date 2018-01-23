# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Visiotech All Rights Reserved
#    $Jesus Garcia Manzanas <jgmanzanas@visiotechsecurity.com>$
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

from openerp import models, fields, api, _
from openerp.addons.connector.session import ConnectorSession
from ..events.partner_events import export_partner, update_partner
from ..events.product_events import update_product, export_product
from ..events.rma_events import export_rma, export_rmaproduct, update_rma, update_rmaproduct
from ..events.invoice_events import export_invoice, update_invoice
from ..events.picking_events import export_picking, update_picking, export_pickingproduct, update_pickingproduct


class MiddlewareBackend(models.TransientModel):
    _name = 'middleware.backend.export'

    type_export = fields.Selection(
        selection=[
            ('partner', 'Partner'),
            ('invoices', 'Invoices'),
            ('pickings', 'Pickings'),
            ('rmas', 'RMAs'),
            ('products', 'Products')
        ],
        string='Export type',
        required=True,
    )
    mode_export = fields.Selection(
        selection=[
            ('export', 'Export'),
            ('update', 'Update')
        ],
        string='Export mode',
        required=True,
    )

    @api.multi
    def do_export(self):
        session = ConnectorSession(self.env.cr, self.env.uid,
                                   context=self.env.context)
        if self.type_export == 'partner':
            partner_obj = self.env['res.partner']
            partner_ids = partner_obj.search([('is_company', '=', True),
                                              ('web', '=', True),
                                              ('customer', '=', True)])
            contact_ids = partner_obj.search([('id', 'child_of', partner_ids.ids),
                                              ('id', 'not in', partner_ids.ids),
                                              ('customer', '=', True),
                                              ('is_company', '=', False)])
            if self.mode_export == 'export':
                for partner in partner_ids:
                    export_partner.delay(session, "res.partner", partner.id)
                for contact in contact_ids:
                    export_partner.delay(session, "res.partner", contact.id)
            else:
                for partner in partner_ids:
                    update_partner.delay(session, "res.partner", partner.id)
                for contact in contact_ids:
                    update_partner.delay(session, "res.partner", contact.id)
        elif self.type_export == 'invoices':
            invoices = self.env['account.invoice']. \
                search([('commercial_partner_id.web', '=', True),
                        ('state', 'in', ['open', 'paid']),
                        ('number', 'not like', '%ef%'),
                        ('number', 'not like', 'VEN%')])
            if self.mode_export == 'export':
                for invoice in invoices:
                    export_invoice.delay(session, 'account.invoice', invoice.id)
            else:
                for invoice in invoices:
                    update_invoice.delay(session, 'account.invoice', invoice.id)
        elif self.type_export == 'pickings':
            partner_obj = self.env['res.partner']
            partner_ids = partner_obj.search([('is_company', '=', True),
                                              ('web', '=', True),
                                              ('customer', '=', True)])
            picking_obj = self.env['stock.picking']
            picking_ids = picking_obj.search([('partner_id', 'child_of', partner_ids.ids),
                                              ('state', '!=', 'cancel'),
                                              ('picking_type_id.code', '=', 'outgoing')])
            if self.mode_export == 'export':
                for picking in picking_ids:
                    export_picking.delay(session, 'stock.picking', picking.id)
                    for line in picking.move_lines:
                        export_pickingproduct.delay(session, 'stock.move', line.id)
            else:
                for picking in picking_ids:
                    update_picking.delay(session, 'stock.picking', picking.id)
                    for line in picking.move_lines:
                        update_pickingproduct.delay(session, 'stock.move', line.id)

        elif self.type_export == 'rmas':
            rma_obj = self.env['crm.claim']
            rmas = rma_obj.search(['|', ('partner_id.web', '=', True),
                                        ('partner_id.commercial_partner_id.web', '=', True)])
            if self.mode_export == 'export':
                for rma in rmas:
                    export_rma.delay(session, 'crm.claim', rma.id)
                    for line in rma.claim_line_ids:
                        export_rmaproduct.delay(session, 'claim.line', line.id)
            else:
                for rma in rmas:
                    update_rma.delay(session, 'crm.claim', rma.id)
                    for line in rma.claim_line_ids:
                        update_rmaproduct.delay(session, 'claim.line', line.id)

        elif self.type_export == 'products':
            product_obj = self.env['product.product']
            product_ids = product_obj.search([])
            if self.mode_export == 'export':
                for product in product_ids:
                    export_product.delay(session, 'product.product', product.id)
            else:
                for product in product_ids:
                    update_product.delay(session, 'product.product', product.id)
            product.web = 'published'