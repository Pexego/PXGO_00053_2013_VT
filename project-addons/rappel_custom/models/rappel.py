# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, exceptions, _
from datetime import datetime
from calendar import monthrange
from dateutil.relativedelta import relativedelta


class Rappel(models.Model):

    _inherit = 'rappel'

    brand_ids = fields.Many2many('product.brand', 'rappel_product_brand_rel',
                                 'rappel_id', 'product_brand_id', 'Brand')
    discount_voucher = fields.Boolean()
    pricelist_ids = fields.Many2many('product.pricelist',
                                     'rappel_product_pricelist_rel',
                                     'rappel_id', 'product_pricelist_id',
                                     'Pricelist')
    description = fields.Char(translate=True)
    sequence = fields.Integer(default=100)

    def get_products(self):
        product_obj = self.env['product.product']
        product_ids = self.env['product.product']
        for rappel in self:
            if not rappel.global_application:
                if rappel.product_id:
                    product_ids += rappel.product_id
                elif rappel.brand_ids:
                    product_ids += product_obj.search(
                        [('product_brand_id', 'in', rappel.brand_ids.ids)])
                elif rappel.product_categ_id:
                    product_ids += product_obj.search(
                        [('categ_id', '=', rappel.product_categ_id.id)])
            else:
                product_ids += product_obj.search([])
        return product_ids.ids

    @api.constrains('global_application', 'product_id',
                    'brand_ids', 'product_categ_id')
    def _check_application(self):
        if not self.global_application and not self.product_id \
                and not self.product_categ_id and not self.brand_ids:
            raise exceptions. \
                ValidationError(_('Product, brand and category are empty'))

    @api.model
    def update_partner_rappel_pricelist(self):
        partner_rappel_obj = self.env['res.partner.rappel.rel']

        now = datetime.now()
        now_str = now.strftime("%Y-%m-%d")
        yesterday_str = (now - relativedelta(days=1)).strftime("%Y-%m-%d")
        end_actual_month = now.strftime("%Y-%m") + '-' + str(
            monthrange(now.year, now.month)[1])
        start_next_month = (
            now + relativedelta(months=1)).strftime("%Y-%m") + '-01'

        discount_voucher_rappels = self.env['rappel'].search(
            [('discount_voucher', '=', True)])

        for rappel in discount_voucher_rappels:
            pricelist_ids = tuple(rappel.pricelist_ids.ids)
            partner_pricelist = tuple(self.env['res.partner'].search(
                [('property_product_pricelist', 'in', pricelist_ids),
                 ('prospective', '=', False), ('active', '=', True),
                 ('is_company', '=', True), ('parent_id', '=', False)]).ids)
            partner_rappel = tuple(partner_rappel_obj.search(
                [('rappel_id', '=', rappel.id),
                 '|', ('date_end', '=', False),
                 ('date_end', '>=', now_str),
                 ('date_start', '<=', now_str)]).mapped('partner_id.id'))

            #  Clientes que faltan en el rappel -> Se crean dos entradas en
            #  el rappel:
            #      - Una para liquidar en el mes actual
            #      - Otra que empiece en fecha 1 del mes siguiente
            add_partners = set(partner_pricelist) - set(partner_rappel)
            if add_partners:
                new_line1 = {'rappel_id': rappel.id,
                             'periodicity': 'monthly',
                             'date_start': now_str,
                             'date_end': end_actual_month}
                new_line2 = {'rappel_id': rappel.id, 'periodicity': 'monthly',
                             'date_start': start_next_month}
                for partner in add_partners:
                    new_line1.update({'partner_id': partner})
                    partner_rappel_obj.create(new_line1)
                    new_line2.update({'partner_id': partner})
                    partner_rappel_obj.create(new_line2)

            # Clientes a los que ya no les corresponde
            # el rappel -> Se actualiza fecha fin con la fecha actual
            remove_partners = set(partner_rappel) - set(partner_pricelist)
            if remove_partners:
                vals = {'date_end': yesterday_str}
                partner_to_update = partner_rappel_obj.search(
                    [('rappel_id', '=', rappel.id),
                     ('partner_id', 'in', tuple(remove_partners)),
                     '|', ('date_end', '=', False),
                     ('date_end', '>', now), ('date_start', '<=', now_str)])
                partner_to_update.write(vals)

    @api.model
    def compute_rappel(self):
        if not self.ids:
            ordered_rappels = self.search([], order='sequence')
        else:
            ordered_rappels = self.sorted(key=lambda x: x.sequence)
        return super(Rappel, ordered_rappels).compute_rappel()
