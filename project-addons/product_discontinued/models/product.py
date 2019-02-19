# -*- coding: utf-8 -*-

from openerp import fields, models, api, _
from openerp.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.product'

    discontinued = fields.Boolean(string="Discontinued", default=False, help="If marked, product not more available")

    @api.multi
    @api.constrains('discontinued')
    def allow_discontinued(self):
        for item in self:
            if item.product_tmpl_id and item.discontinued:
                if (item.state == 'end' and item.qty_available == 0):
                    item.sale_ok = False
                    item.purchase_ok = False
                else:
                    raise ValidationError(_("The product can not be discontinued. Currently exist stock or the status is not - End of lifecycle"))
            return True

    @api.multi
    @api.onchange('discontinued')
    def warning_catalog(self):
        for item in self:
            if item.product_tmpl_id:
                if not item.discontinued:
                    item.sale_ok = True
                    if item.qty_available == 0:
                        result = {'warning': {'title': _('Warning'), 'message': _('The product does not have stock.')}}
                        return result
