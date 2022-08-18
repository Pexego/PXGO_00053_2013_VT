##############################################################################
#
#    Copyright (C) 2016 Comunitea Servicios Tecnológicos
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

from odoo import models, api, fields, exceptions, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import time


class ClaimMakePicking(models.TransientModel):

    _inherit = 'claim_make_picking.wizard'

    odoo_management = fields.Boolean('Management in Odoo')
    not_sync = fields.Boolean("Not sync", help="This picking not will be "
                                               "synced with Vstock",
                              readonly=True)

    @api.onchange('claim_line_source_location', 'claim_line_dest_location')
    def onchange_locations(self):
        if self.claim_line_source_location.odoo_management:
            if self.claim_line_dest_location in \
                    [self.env.ref('stock.stock_location_customers'),
                     self.env.ref('stock.stock_location_suppliers')]:
                self.odoo_management = True
            else:
                self.odoo_management = False
        else:
            self.odoo_management = False
        if self.claim_line_dest_location.not_sync:
            self.not_sync = True
        else:
            self.not_sync = False


    @api.multi
    def create_move(self, wizard_line, p_type, picking_id, claim, note):
        type_ids = self.env['stock.picking.type'].search([('code', '=', p_type)]).ids
        claim_line = wizard_line.claim_line_id
        if claim_line.product_id.bom_ids:
            partner_id = claim.delivery_address_id and claim.delivery_address_id.id or claim.partner_id.id
            context = self.env.context
            qty = claim_line.product_returned_quantity
            if context.get('picking_type', 'in') == u'out':
                qty = wizard_line.product_qty
            for bom in claim_line.product_id.bom_ids:
                if bom.type == 'phantom':
                    for bom_line in bom.bom_line_ids:
                        move = self.env['stock.move'].create(
                            {'name': bom_line.product_id.default_code,
                             'priority': '0',
                             'date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                             'date_expected': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                             'product_id': bom_line.product_id.id,
                             'picking_type_id': type_ids and type_ids[0],
                             'product_uom_qty': bom_line.product_qty * qty,
                             'product_uom': bom_line.product_id.uom_id.id,
                             'partner_id': partner_id,
                             'picking_id': picking_id.id,
                             'state': 'draft',
                             'company_id': claim.company_id.id,
                             'location_id': picking_id.location_id.id,
                             'location_dest_id': picking_id.location_dest_id.id,
                             'note': note,
                             'claim_line_id': claim_line.id
                             })
                else:
                    super(ClaimMakePicking, self).create_move(
                        wizard_line, p_type, picking_id, claim, note)
        else:
            return super(ClaimMakePicking, self).create_move(
                wizard_line, p_type, picking_id, claim, note)

    @api.multi
    def action_create_picking(self):
        if not self.env.context.get('bypass_product_incidences_advise', False):
            incidences = self.claim_line_ids.mapped('product_id.incidence_ids').filtered(lambda i:i.warn)
            if incidences:
                return self.env['product.incidences.advise.wiz'].create({
                    'origin_reference':
                        '%s,%s' % ('claim_make_picking.wizard', self.id),
                    'continue_method': 'action_create_picking',
                    'incidence_ids': [(6, 0, incidences.ids)],
                    'claim_id': self.env.context.get('active_id')
                }).action_show()
        res = super(ClaimMakePicking, self).action_create_picking()
        if self.odoo_management or (self.not_sync or
                                    self.claim_line_dest_location.not_sync):
            if self.odoo_management and \
                    not self.claim_line_source_location.odoo_management:
                raise exceptions.Warning(_("The origin location is not managed"
                                           " by Odoo."))
            if res.get('res_id', False):
                pick = self.env["stock.picking"].browse(res['res_id'])
                pick.odoo_management = self.odoo_management
                pick.not_sync = self.not_sync or \
                    self.claim_line_dest_location.not_sync

        return res

    @api.model
    def default_get(self, vals):
        if self.env.context.get('type', False) == 'customer' and \
                self.env.context.get('picking_type', False) == 'out' and \
                self.env.context.get('partner_id', False):
            partner_id = self.env.context.get('partner_id')
            partner = self.env['res.partner'].browse(partner_id)
            claim = self.env['crm.claim'].browse(
                self.env.context.get('active_id', False))
            if partner.commercial_partner_id.blocked_sales and not \
                    claim.allow_confirm_blocked:
                raise exceptions.Warning(
                    _('Customer blocked by lack of payment. Check the maturity dates of their account move lines.'))
        return super(ClaimMakePicking, self).default_get(vals)
