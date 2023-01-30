from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = "sale.order"

    sale_order_shipping_cost_id = fields.One2many(
        "sale.order.shipping.cost",
        "sale_order_id",
        "Shipping Cost"
    )

    @api.multi
    def compute_variables(self):
        """
        Overrides compute_variables in sale_order_board module
        Calculates the shipping costs.
        When we have special shipping costs, calculates pallet shipping costs.
        If we don't have special shipping costs, calculates all shipping costs.
        """
        picking_rated = self.env['picking.rated.wizard'].create({})
        pallet_services_to_add = []
        available_shipping_costs = self._get_available_shipping_costs()
        products_without_weight = self.get_product_list_without_weight()
        products_without_volume = self.get_product_list_without_volume()
        number_product_without_weight = len(products_without_weight)
        number_product_without_volume = len(products_without_volume)
        product_names_without_weight = ", ".join(products_without_weight.mapped('default_code'))
        product_names_without_volume = ", ".join(products_without_volume.mapped('default_code'))
        # calculate pallet & weight shipping costs
        for shipping_cost in available_shipping_costs:
            new_so_sc = self.env['sale.order.shipping.cost'].create({
                'sale_order_id': self.id,
                'shipping_cost_id': shipping_cost.id
            })

            pallet_service_cost_list = new_so_sc.calculate_shipping_cost()
            pallet_service_cost_list += new_so_sc.calculate_shipping_cost(pallet_mode=False)
            pallet_services_to_add = [
                (0, 0, {
                    'currency': 'EUR',
                    'transit_time': '',
                    'amount': service['price'],
                    'service': service['service_name'],
                    'order_id': self.id,
                    'wizard_id': picking_rated.id
                }) for service in pallet_service_cost_list
            ]
        # if we have special shipping costs we only need pallet & weight service costs
        if self.is_special_shipping_costs:
            message_products_weight = ''
            message_products_volume = ''
            if number_product_without_weight != 0:
                message_products_weight = (
                    "%s of the product(s) of the order don't have set the weights,"
                    " please take the shipping cost as an approximation"
                ) % number_product_without_weight
            if number_product_without_volume != 0:
                message_products_volume = (
                    "%s of the product(s) of the order don't have set the weights,"
                    " please take the shipping cost as an approximation"
                ) % number_product_without_volume

            picking_rated.write({
                'data': pallet_services_to_add,
                'total_weight': self.get_sale_order_weight(),
                'products_wo_weight': message_products_weight,
                'products_without_weight': product_names_without_weight,
                'total_volume': self.get_sale_order_volume(),
                'products_wo_volume': message_products_volume,
                'product_names_without_volume': product_names_without_volume
            })
            return {
                'name': 'Shipping Data Information',
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new',
                'res_model': 'picking.rated.wizard',
                'src_model': 'stock.picking',
                'res_id': picking_rated.id,
                'type': 'ir.actions.act_window',
                'id': 'action_picking_rated_status',
            }

        response = super().compute_variables()
        new_id = response['res_id']
        picking_rated = self.env['picking.rated.wizard'].browse(new_id)
        picking_rated.write({'data': pallet_services_to_add})

        return {
            'name': 'Shipping Data Information',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'picking.rated.wizard',
            'src_model': 'stock.picking',
            'res_id': picking_rated.id,
            'type': 'ir.actions.act_window',
            'id': 'action_picking_rated_status',
        }

    def _get_available_shipping_costs(self):
        """
        Returns a list of all shipping_cost that fit with the sale_order
        """
        shipping_cost_list = self.env['shipping.cost'].search([('is_active', '=', 'True')])
        shipping_cost_available = []
        # we get shipping_cost that verifies shipping_conditions - empty conditions are included
        for shipping_cost in shipping_cost_list:
            checker_list = [
                eval(
                    f'"{getattr(self, condition.filter_by).name}" {condition.operator} "{condition.arguments}"'
                ) if self._fields[condition.filter_by].type in ('many2one', 'one2many', 'many2many') else eval(
                    f'"{getattr(self, condition.filter_by)}" {condition.operator} "{condition.arguments}"'
                ) for condition in shipping_cost.condition_ids
            ]
            if all(checker_list):
                shipping_cost_available.append(shipping_cost)
        return shipping_cost_available
