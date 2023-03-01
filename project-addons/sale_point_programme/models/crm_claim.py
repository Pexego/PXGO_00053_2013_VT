##############################################################################
#
#    Copyright (C) 2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Omar Castiñeira Saavedra <omar@pexego.es>$
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

from odoo import models, api, fields


class CrmClaimRma(models.Model):
    _inherit = 'crm.claim'

    @api.multi
    def make_refund_invoice(self):
        for claim_obj in self:
            dicc_claim_line_invoice = {}
            for line in claim_obj.claim_inv_line_ids:
                if line.invoiced or not line.invoice_id:
                    continue
                dicc_claim_line_invoice[line.invoice_id] = dicc_claim_line_invoice.setdefault(line.invoice_id, self.env[
                    'claim.invoice.line']) | line
            dicc_claim_line_order = {}
            for invoice in dicc_claim_line_invoice:
                lines = dicc_claim_line_invoice[invoice]
                for order in invoice.sale_order_ids:
                    dicc_claim_line_order[order] = dicc_claim_line_order.setdefault(order, self.env[
                        'claim.invoice.line']) | lines
            obj_bag = self.env['res.partner.point.programme.bag']
            for order in dicc_claim_line_order:
                bag_ids = obj_bag.search([('order_id', '=', order.id)])
                if not bag_ids:
                    continue
                rules = bag_ids.mapped('point_rule_id')
                rules_with_points, brands, products, categories = order.compute_points_programme_bag(
                    dicc_claim_line_order.get(order), rules, "claim")
                for rule, points in rules_with_points.items():
                    if points and rule.modality == 'point' and (
                        rule.product_brand_id.id in brands or rule.product_id.id in products or
                        rule.category_id.id in categories):
                        obj_bag.create({'name': rule.name,
                                        'point_rule_id': rule.id,
                                        'order_id': order.id,
                                        'points': -points,
                                        'partner_id': order.partner_id.id})
        return super(CrmClaimRma, self).make_refund_invoice()
