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
            if item.discontinued:
                if (item.state == 'end' and item.qty_available == 0):
                    item.sale_ok = False
                    item.purchase_ok = False
                else:
                    raise ValidationError(_('El producto no cumple los requisitos para ser descatalogado. '
                                            'Stock existente o su estado actual no es "Fin de ciclo de vida" '
                                            '(Pestaña inventario).'))
        return True

    @api.multi
    @api.onchange('discontinued')
    def warning_catalog(self):
        for item in self:
            if not item.discontinued:
                item.sale_ok = True
                if item.qty_available == 0:
                    result = {'warning': {'title': _('Warning'), 'message': _('El producto no tiene stock, por favor '
                                          'revise !!!')}}
                    return result
