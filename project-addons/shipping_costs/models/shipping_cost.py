from odoo import models, fields, api, _
import math


COMPARATORS = [
    ('==', _('equals')),
    ('!=', _('not equal to')),
    ('>', _('greater than')),
    ('>=', _('greater than or equal to')),
    ('<', _('less than')),
    ('<=', _('less than or equal to')),
    ('in', _('is in')),
    ('not in', _('is not in')),
]


class ShippingCost(models.Model):
    """
    Models the static cost that a country or client has
    """
    _name = "shipping.cost"
    _description = "shipping cost"
    _rec_name = "cost_name"

    cost_name = fields.Char(string="Name")
    is_active = fields.Boolean(string="Active")
    transporter_id = fields.Many2one("transportation.transporter", string="Transporter")
    fuel = fields.Float(string="Fuel", related="transporter_id.fuel", readonly=True)
    sequence = fields.Integer(string="Sequence")
    volume = fields.Float(string="Max volume/pallet")

    condition_ids = fields.One2many(
        "shipping.cost.condition",
        "shipping_cost_id",
        string="Conditions"
    )
    fee_ids = fields.One2many("shipping.cost.fee", "shipping_cost_id", string="Fees")
    supplement_ids = fields.One2many(
        "shipping.cost.supplement",
        "shipping_cost_id",
        string="Supplements"
    )
    shipping_zone_id = fields.Many2one("shipping.zone", string="Shipping zone")

    note = fields.Text("Notes", copy=False)

    @api.multi
    @api.constrains('transporter_id', 'supplement_ids', 'shipping_zone_id')
    def check_transporter_services(self):
        """
        Checks if the services are from the transporter selected and if the shipping_zone
        matches with the transporter selected.
        """
        for shipping_cost in self:
            if (
                shipping_cost.shipping_zone_id.transporter_id.id and
                shipping_cost.transporter_id.id and
                shipping_cost.shipping_zone_id.transporter_id.id != shipping_cost.transporter_id.id
            ):
                raise Warning(
                    _('Error!:: Shipping zone assigned is not for the transporter selected.')
                )
            transporter_services = shipping_cost.transporter_id.service_ids.ids
            for supplement in shipping_cost.supplement_ids:
                if supplement.service_id.id not in transporter_services:
                    raise Warning(
                        _('Error!:: Services must be offered by the transporter selected.')
                    )


class ShippingCostCondition(models.Model):
    """
    Models conditions for sale orders
    """
    _name = "shipping.cost.condition"

    shipping_cost_id = fields.Many2one("shipping.cost", string="Shipping cost")
    filter_by = fields.Selection(
        string="Filter by",
        selection=lambda self: self._get_filter_by_fields()
    )
    operator = fields.Selection(string="Operator", selection=COMPARATORS)
    arguments = fields.Text(string="Arguments")

    def _get_filter_by_fields(self):
        """
        Returns a list of tuples containing sale_order fields and the name of that field.
        Tuple shape: (field, field_string_name)
        """
        # we get all fields with no context in order to get the field string with the user language
        fields_dict = self.env['sale.order'].fields_get()
        fields_ordered_list = sorted(list(fields_dict))

        return [(field, fields_dict[field]["string"]) for field in fields_ordered_list]


class ShippingCostFee(models.Model):
    """
    Models a fee in shipping costs
    """
    _name = "shipping.cost.fee"

    shipping_cost_id = fields.Many2one("shipping.cost", string="Shipping cost")
    type = fields.Selection(string="Type", selection=[
        ("pallet", "Pallet"),  # ("package", "Package"),
        ("total_weight", "Total weight")  # , ("palletized", "Palletized service")
    ])
    max_qty = fields.Float(string="Quantity Max")
    price = fields.Float(string="Price")


class ShippingCostSupplement(models.Model):
    """
    Models a supplement in shipping costs
    """
    _name = "shipping.cost.supplement"

    shipping_cost_id = fields.Many2one("shipping.cost", string="Shipping cost")
    service_id = fields.Many2one(
        "transportation.service",
        string="Service"
    )
    added_percentage = fields.Float(string="Added percentage")


class SaleOrderShippingCost(models.TransientModel):
    """
    Calculates the shipping cost of a sale order
    """
    _name = "sale.order.shipping.cost"

    sale_order_id = fields.Many2one("sale.order", "Sale Order")
    shipping_cost_id = fields.Many2one("shipping.cost", "Shipping Cost")
    pallet_number = fields.Integer(string="Pallet number", compute="_get_pallet_number")
    sale_order_weight = fields.Float(string="Sale order weight", compute="_get_sale_order_weight")
    sale_order_volume = fields.Float(string="Sale order volume", compute="_get_sale_order_volume")

    def calculate_shipping_cost(self, pallet_mode=True):
        """
        Returns the final cost list of the sale order shipping
        """
        if pallet_mode:
            base_fee_price = self._get_fee_price(mode='pallet')
        else:
            base_fee_price = self._get_fee_price(mode='total_weight')
        # if no base_fee_price, then no fee
        if base_fee_price is None:
            return []

        fuel_added_price = base_fee_price * (1 + self.shipping_cost_id.fuel / 100)
        service_price_list = [
            {
                'price': round(fuel_added_price * (1 + supplement.added_percentage / 100), 2),
                'service_name': f'{supplement.service_id.name}',
                'sale_order_shipping_cost_id': self.id
            }
            for supplement in self.sudo().shipping_cost_id.supplement_ids
        ]

        return service_price_list

    def _get_fee_price(self, mode):
        """
        Searches among fees where type is mode and selects the one that fits more to the sale order
        Returns the price of that fee.
        """
        fee_ids = self.sudo().shipping_cost_id.fee_ids.filtered(lambda fee: fee.type == mode)
        if mode == 'pallet':
            fee_ids = fee_ids.sudo().filtered(lambda fee: fee.max_qty >= self.sudo().pallet_number)
        if mode == 'total_weight':
            fee_ids = fee_ids.sudo().filtered(lambda fee: fee.max_qty >= self.sudo().sale_order_weight)
        if len(fee_ids) == 0:
            return None
        fee_sorted = fee_ids.sorted(lambda fee: fee.max_qty)
        return fee_sorted[0].price

    def _get_pallet_number(self):
        """
        Returns the pallet number of the sale_order shipping
        """
        self.pallet_number = math.ceil(self.sale_order_volume * (1 / self.shipping_cost_id.volume))

    def _get_sale_order_weight(self):
        """
        Calculates sale_order weight
        """
        self.sale_order_weight = self.sale_order_id.get_sale_order_weight()

    def _get_sale_order_volume(self):
        """
        Calculates sale_order volume
        """
        self.sale_order_volume = self.sale_order_id.get_sale_order_volume()
