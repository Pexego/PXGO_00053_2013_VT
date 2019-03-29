from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    discontinued = fields.Boolean(string="Discontinued", default=False, help="If marked, product not more available")

    @api.multi
    @api.constrains('discontinued')
    def allow_discontinued(self):
        for item in self:
            if (item.qty_available != 0):
                if item.discontinued:   # and if (item.state != 'end' or item.qty_available != 0):
                    raise ValidationError(_(
                        "The product can not be discontinued. Currently exist stock or the status is not - End of lifecycle"))
            elif item.qty_available == 0 and (item.product_variant_count is 0):
                if item.discontinued:
                    item.sale_ok = False
                    item.purchase_ok = False

    @api.multi
    @api.onchange('discontinued')
    def warning_catalog(self):
        for item in self:
            if item.qty_available != 0:
                if not item.discontinued:
                    item.sale_ok = True
            elif item.qty_available == 0:
                if item.discontinued:
                    item.sale_ok = False
                    item.purchase_ok = False
                if item.product_variant_count is 1:
                    if not item.discontinued:
                        item.sale_ok = True
                        result = {'warning': {'title': _('Warning'), 'message': _('The product does not have stock.')}}
                        return result