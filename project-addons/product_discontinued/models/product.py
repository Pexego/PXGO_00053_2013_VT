from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class ProductProduct(models.Model):
    _inherit = 'product.product'
    discontinued = fields.Boolean(string="Discontinued", default=False,
                                  help="If marked, product not more available")

    @api.multi
    @api.constrains('discontinued', 'state')
    def allow_discontinued(self):
        for item in self:
            if item.state != 'end' and item.discontinued:
                raise ValidationError(_(
                    "The product can not be discontinued. Currently the status is not - End of lifecycle"))
            elif item.qty_available == 0:
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
                if item.discontinued and item.product_variant_count is 0:
                    item.sale_ok = False
                    item.purchase_ok = False
                if not item.discontinued and item.product_variant_count is 1:
                    item.sale_ok = True
                    result = {'warning': {'title': _('Warning'),
                              'message': _('The product does not have stock.')}}
                    return result

    @api.model
    def cron_send_mail_to_commercials_products_discontinued(self):
        discontinued_products = self.env['product.product'].search([('product_tmpl_id.state', 'ilike', 'end'), ('qty_available', '<=', 0)])
        moves = self.env['stock.move'].search([('state','in',('partially_available','confirmed','waiting')),('product_id','in',discontinued_products.mapped('id')),('sale_line_id','!=',False)])
        moves_group_by_commercial=dict()
        for move in moves:
            if move.sale_line_id.salesman_id in moves_group_by_commercial:
                moves_group_by_commercial[move.sale_line_id.salesman_id]+=move
            else:
                moves_group_by_commercial[move.sale_line_id.salesman_id] = move
        for commercial,values in moves_group_by_commercial.items():
            template = self.env.ref('product_discontinued.alert_cron_send_mail_to_commercials_products_discontinued')

            ctx = dict(self._context)
            ctx.update({
                'email_to': commercial.login,
                'moves':values,
                'lang':commercial.lang
            })
            template.with_context(ctx).send_mail(self.id)




