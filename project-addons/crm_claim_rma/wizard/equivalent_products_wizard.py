##############################################################################
#
#    Copyright (C) 2014 Pexego Sistemas Informáticos All Rights Reserved
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


from odoo import fields, models, api


class EquivalentProductsWizard(models.TransientModel):

    _name = "equivalent.products.wizard"
    _description = "Wizard for change products in claim."

    product_tag_ids = fields.Many2many("product.tag",
                                       "product_tag_wzf_equivalent_rel",
                                       "wizard_id", "tag_id", "Tags")
    product_id = fields.Many2one('product.product', 'Product selected')
    line_id = fields.Many2one('claim.line', 'Line')
    real_stock = fields.Float("Real Stock", readonly=True)
    virtual_stock = fields.Float("Virtual Stock", readonly=True)

    def default_get(self, cr, uid, fields, context=None):
        res = super(EquivalentProductsWizard, self).default_get(cr, uid, fields, context=context)
        if context.get('line_id'):
            claim_line_id = self.pool.get('claim.line').browse(cr, uid, context['line_id'])
            res['product_id'] = claim_line_id.product_id.id
            res['real_stock'] = claim_line_id.product_id.qty_available
            res['virtual_stock'] = claim_line_id.product_id.virtual_available
            res['product_tag_ids'] = [(6, 0, claim_line_id.product_id.tag_ids.ids)]
        return res

    @api.onchange('product_id')
    @api.multi
    def onchange_product_id(self):
        for prod in self:
            self.virtual_stock = prod.virtual_available
            self.real_stock = prod.qty_available

    @api.multi
    def select_product(self):
        for wiz in self:
            wiz.equivalent_product_id = wiz.product_id.id


