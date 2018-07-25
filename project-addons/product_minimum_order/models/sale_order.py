from openerp import models, fields, api, exceptions, _


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    @api.multi
    def product_id_change_with_wh(self, pricelist, product, qty=0,
                                      uom=False, qty_uos=0, uos=False, name='', partner_id=False,
                                      lang=False, update_tax=True, date_order=False, packaging=False,
                                      fiscal_position=False, flag=False, warehouse_id=False, context=None):
        warning_msgs = ''
        warning = ''

        res = super(SaleOrderLine, self).product_id_change_with_wh(pricelist, product, qty=qty,
                                      uom=uom, qty_uos=qty_uos, uos=uos, name=name, partner_id=partner_id,
                                      lang=lang, update_tax=update_tax, date_order=date_order, packaging=packaging,
                                      fiscal_position=fiscal_position, flag=flag, warehouse_id=warehouse_id)

        if product:
            product_obj = self.env['product.product'].browse(product)
            if qty % product_obj.sale_in_groups_of != 0:

                warning_msgs = (_('The product %s can only be sold in groups of %s') %
                                (product_obj.name, product_obj.sale_in_groups_of))

        if warning_msgs:
            warning = {
                'title': 'Warning',
                'message': warning_msgs
            }
            res.update({'warning': warning})

        return res


class SaleOrder(models.Model):

    _inherit = "sale.order"

    @api.multi
    def action_button_confirm(self):

        for sale in self:
            for line in sale.order_line:
                if line.product_uom_qty % line.product_id.sale_in_groups_of != 0:
                    raise exceptions.Warning(
                        _('The product %s can only be sold in groups of %s') %
                        (line.product_id.name, line.product_id.sale_in_groups_of))

        res = super(SaleOrder, self).action_button_confirm()

        return res
