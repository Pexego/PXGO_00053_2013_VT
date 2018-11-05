from odoo import models, fields, api, exceptions, _


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    @api.multi
    def product_id_change_with_wh(self, pricelist, product, qty=0,
                                      uom=False, qty_uos=0, uos=False, name='', partner_id=False,
                                      lang=False, update_tax=True, date_order=False, packaging=False,
                                      fiscal_position=False, flag=False, warehouse_id=False, context=None):
        warning_msgs = ''
        warning = ''

        import ipdb
        ipdb.set_trace()

        res = super(SaleOrderLine, self).product_id_change_with_wh(pricelist, product, qty=qty,
                                      uom=uom, qty_uos=qty_uos, uos=uos, name=name, partner_id=partner_id,
                                      lang=lang, update_tax=update_tax, date_order=date_order, packaging=packaging,
                                      fiscal_position=fiscal_position, flag=flag, warehouse_id=warehouse_id)

        if product:
            product_obj = self.env['product.product'].browse(product)
            description = lambda s: "" if not s else "\n" + s
            if qty % product_obj.sale_in_groups_of != 0 \
                    and name and name == product_obj.default_code + description(product_obj.description_sale):
                warning_msgs = (_("The product {0} can only be sold in groups of {1}")
                                .format(product_obj.name, product_obj.sale_in_groups_of))
            elif not name:
                res['value'].update({'product_uom_qty': product_obj.sale_in_groups_of})
                if product_obj.sale_in_groups_of > 1.0:
                    res['warning'] = {}

        if warning_msgs:
            warning = {
                'title': 'Warning',
                'message': warning_msgs
            }
            res.update({'warning': warning})

        return res


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    @api.multi
    def action_button_confirm(self):

        for sale in self:
            for line in sale.order_line:
                if line.product_id and line.product_id.sale_in_groups_of != 0.0:
                    if line.product_uom_qty % line.product_id.sale_in_groups_of != 0:
                        raise exceptions.Warning(
                            _("The product {0} can only be sold in groups of {1}")
                            .format(line.product_id.name, line.product_id.sale_in_groups_of))

        res = super(SaleOrder, self).action_button_confirm()

        return res
