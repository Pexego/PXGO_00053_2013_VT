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
from datetime import datetime, timedelta
from openerp import models, fields, api, _
from openerp.addons.connector.session import ConnectorSession
from openerp.addons.connector.connector import ConnectorUnit
from openerp.addons.connector.unit.mapper import mapping, ImportMapper
from .unit.backend_adapter import GenericAdapter
from .events import export_partner, export_product
from .rma_events import export_rma, export_rmaproduct

from .backend import middleware

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
    price_unit_field_id = fields.Many2one(
        comodel_name='ir.model.fields',
        string='Price Field',
        default=_get_price_field_id,
        domain="[('model', '=', 'product.product'),"
               " ('ttype', '=', 'float')]",
        help="Choose the field of the product which will be used for "
             "sale price unit updates.", required=True
    )

    @api.multi
    def export_current_web_data(self):
        session = ConnectorSession(self.env.cr, self.env.uid,
                                   context=self.env.context)
        for midd in self:
            products = self.env["product.product"].\
                search([('web', '=', 'published')])
            for product in products:
                export_product(session, "product.product", product.id)

            partners = self.env["res.partner"].search([('web', '=', True)])
            for partner in partners:
                export_partner(session, "res.partner", partner.id)
            rmas = self.env['crm.claim'].search([('partner_id.web', '=', True)])
            for rma in rmas:
                export_rma(session, 'crm.claim', rma.id)
                for line in rma.claim_line_ids:
                    if line.product_id.web == 'published':
                        export_rmaproduct(session, 'claim.line', line.id)
        return True
