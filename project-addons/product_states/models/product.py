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

from odoo import fields, models, api, fields, _


class ProductTemplate(models.Model):

    _inherit = "product.template"

    state2 = fields.Selection([
            ('active', 'Active'),
            ('edition', 'In edition'),
            ('published', 'Published')], 'Status',
            readonly=True, required=True, default='active')
    sale_ok = fields.Boolean(
        'Can be Sold', default=False,
        help="Specify if the product can be selected in a sales order line.")


    @api.multi
    def signal_edition(self):
        self.write({'state2': 'edition'})
        for product in self:
            vals = {
                'body':
                _(u'The product %s is in edition state') % product.name,
                'model': 'product.template',
                'res_id': product.id,
                'type': 'comment'
            }
            self.env['mail.message'].create(vals)

    @api.multi
    def signal_publish(self):
        self.write({'state2': 'published', 'sale_ok': True})
        for product in self:
            vals = {
                'body':
                _(u'The product %s has been published') % product.name,
                'model': 'product.template',
                'res_id': product.id,
                'type': 'comment'
            }
            self.env['mail.message'].create(vals)
