# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea All Rights Reserved
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

import logging
from datetime import datetime, date, timedelta
from openerp import models, fields, api, _
from openerp.addons.connector.session import ConnectorSession
from openerp.addons.connector.connector import ConnectorUnit
from openerp.addons.connector.unit.mapper import mapping, ImportMapper
from ..unit.backend_adapter import GenericAdapter
from ..events.partner_events import export_partner
from ..events.country_events import export_country
from ..events.commercial_events import export_commercial
from ..events.product_events import export_product, export_product_category, export_product_brand, export_product_brand_rel
from ..events.rma_events import export_rma, export_rmaproduct, export_rma_status
from ..events.invoice_events import export_invoice
from ..connector import get_environment
import ast
import xmlrpclib

from ..backend import middleware

_logger = logging.getLogger(__name__)

IMPORT_DELTA_BUFFER = 30  # seconds


class MiddlewareBackend(models.Model):
    _name = 'middleware.backend'
    _description = 'Middleware Backend'
    _inherit = 'connector.backend'
    _rec_name = "location"

    _backend_type = 'middleware'

    @api.model
    def _get_stock_field_id(self):
        field = self.env['ir.model.fields'].search(
            [('model', '=', 'product.product'),
             ('name', '=', 'virtual_stock_conservative')],
            limit=1)
        return field

    @api.model
    def _get_price_field_id(self):
        field = self.env['ir.model.fields'].search(
            [('model', '=', 'product.product'),
             ('name', '=', 'list_price3')],
            limit=1)
        return field

    @api.model
    def _select_versions(self):
        return [('1.0', 'Middleware 1.0')]

    version = fields.Selection(
        selection='_select_versions',
        string='Version',
        required=True,
    )
    location = fields.Char(
        string='Location',
        required=True,
        help="Url to middleware application xmlrpc api",
    )
    username = fields.Char(
        string='Username',
        help="Webservice user", required=True
    )
    password = fields.Char(
        string='Password', required=True,
        help="Webservice password",
    )
    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Warehouse',
        required=True,
        help='Warehouse used to compute the '
             'stock quantities.',
    )
    default_lang_id = fields.Many2one(
        comodel_name='res.lang',
        string='Default Language',
        help="If a default language is selected, the records "
             "will be imported in the translation of this language."
    )
    product_stock_field_id = fields.Many2one(
        comodel_name='ir.model.fields',
        string='Stock Field',
        default=_get_stock_field_id,
        domain="[('model', '=', 'product.product'),"
               " ('ttype', '=', 'float')]",
        help="Choose the field of the product which will be used for "
             "stock inventory updates.", required=True
    )
    '''price_unit_field_id = fields.Many2one(
        comodel_name='ir.model.fields',
        string='Price Field',
        default=_get_price_field_id,
        domain="[('model', '=', 'product.product'),"
               " ('ttype', '=', 'float')]",
        help="Choose the field of the product which will be used for "
             "sale price unit updates.", required=True
    )'''

    @api.multi
    def export_current_web_data(self):
        session = ConnectorSession(self.env.cr, self.env.uid,
                                   context=self.env.context)
        for midd in self:
            #~ countries = self.env['res.country'].search([])
            #~ for country in countries:
                #~ export_country(session, 'res.country', country.id)
            #~ brands = self.env['product.brand'].search([])
            #~ for brand in brands:
                #~ export_product_brand(session, 'product.brand', brand.id)
            #~ brand_country_rels = self.env['brand.country.rel'].search([])
            #~ for rel in brand_country_rels:
                #~ export_product_brand_rel(session, 'brand.country.rel', rel.id)
            #~ categories = self.env['product.category'].search([])
            #~ for category in categories:
                #~ export_product_category(session, 'product.category', category.id)
            #~ products = self.env["product.product"].\
                #~ search([('web', '=', 'published')])
            #~ for product in products:
                #~ export_product(session, "product.product", product.id)
            #~ users = self.env['res.users'].search([('web', '=', True)])
            #~ for user in users:
                #~ export_commercial(session, 'res.users', user.id)
            partner_obj = self.env['res.partner']
            partner_ids = partner_obj.search([('is_company', '=', True),
                                              ('web', '=', True),
                                              ('customer', '=', True)])
            for partner in partner_ids:
                contact_ids = partner_obj.search([('parent_id', '=', partner.id),
                                                  ('active', '=', True),
                                                  ('customer', '=', True)])
                for contact in contact_ids:
                    export_partner(session, "res.partner", contact.id)
            #~ substates = self.env['substate.substate'].search([])
            #~ for substate in substates:
                #~ export_rma_status(session, 'substate.substate', substate.id)
            #~ rmas = self.env['crm.claim'].search([('partner_id.web', '=', True)])
            #~ for rma in rmas:
                #~ export_rma(session, 'crm.claim', rma.id)
                #~ for line in rma.claim_line_ids:
                    #~ if line.product_id.web == 'published':
                        #~ export_rmaproduct(session, 'claim.line', line.id)
            #~ invoices = self.env['account.invoice'].\
                #~ search([('commercial_partner_id.web', '=', True),
                        #~ ('state', 'in', ['open', 'paid']),
                        #~ ('number', 'not like', '%ef%')])
            #~ for invoice in invoices:
                #~ export_invoice.delay(session, 'account.invoice', invoice.id)
            #~ products = self.env["product.product"]. \
                #~ search([('web', '=', 'not_published')])
            #~ for product in products:
                #~ export_product.delay(session, "product.product", product.id)
                #~ product.web = 'published'

        return True
