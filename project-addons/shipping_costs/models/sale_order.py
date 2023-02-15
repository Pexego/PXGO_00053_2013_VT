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
        When we have special shipping costs, calculates pallet and weight shipping costs.
        If we don't have special shipping costs, calculates all shipping costs.
        """
        action_to_return = {
            'name': 'Shipping Data Information',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'picking.rated.wizard',
            'src_model': 'stock.picking',
            'res_id': '',
            'type': 'ir.actions.act_window',
            'id': 'action_picking_rated_status',
        }
        picking_rated = self.env['picking.rated.wizard'].create({'sale_order_id': self})
        services_to_add = []
        available_shipping_costs = self._get_available_shipping_costs()
        # calculate pallet & weight shipping costs
        for shipping_cost in available_shipping_costs:
            new_so_sc = self.env['sale.order.shipping.cost'].create({
                'sale_order_id': self.id,
                'shipping_cost_id': shipping_cost.id
            })

            service_cost_list = new_so_sc.calculate_shipping_cost()
            service_cost_list += new_so_sc.calculate_shipping_cost(pallet_mode=False)
            services_to_add += [
                (0, 0, {
                    'currency': 'EUR',
                    'transit_time': '',
                    'amount': service['price'],
                    'service': service['service_name'],
                    'order_id': self.id,
                    'wizard_id': picking_rated.id,
                    'sequence': 0
                }) for service in service_cost_list
            ]
        # if we have special shipping costs we only need pallet & weight service costs
        if self.is_special_shipping_costs:
            picking_rated = self.env['picking.rated.wizard'].create({'sale_order_id': self})
            picking_rated.write({'data': services_to_add})
            action_to_return['res_id'] = picking_rated.id
            return action_to_return

        response = super().compute_variables()
        new_id = response['res_id']
        picking_rated = self.env['picking.rated.wizard'].browse(new_id)
        picking_rated.write({'data': services_to_add})
        action_to_return['res_id'] = picking_rated.id

        return action_to_return

    def get_sale_order_zone(self):
        """
        Returns shipping_zone(s) where the sale_order is going to be delivered
        """
        shipping_zones = self.env['shipping.zone'].search([
            ('transporter_id', '=', self.transporter_id.id),
            ('country_id', '=', self.partner_shipping_id.country_id.id)
        ])
        filtered_shipping_zones = shipping_zones.filtered(
            lambda zone: zone.is_postal_code_in_zone(self.partner_shipping_id.zip)
        )
        return filtered_shipping_zones

    def _get_available_shipping_costs(self):
        """
        Returns a list of all shipping_cost that fit with the sale_order
        """
        shipping_cost_list = self.env['shipping.cost'].search(
            [('is_active', '=', 'True'), ('shipping_zone_id.id', 'in', self.get_sale_order_zone().ids)]
        )
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
