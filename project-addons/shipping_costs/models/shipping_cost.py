from odoo import models, fields, api, _
import math
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp


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
    weight_volume_translation = fields.Float(
        string="Translation (kg/cbm)",
        related="transporter_id.weight_volume_translation",
        readonly=True
    )

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

    def get_fee_price_by_weight(self, shipping_weight):
        """
        Searches among fees where type is weight and selects the one that fits more to the sale order
        Returns the price of that fee.

        Parameters:
        ----------
        shipping_weight:
            Shipping weight
        """
        fee_ids = self.fee_ids.filtered(
            lambda fee: fee.type == 'total_weight' and fee.max_qty >= shipping_weight
        )
        if len(fee_ids) == 0:
            return None
        fee_sorted = fee_ids.sorted(lambda fee: fee.max_qty)
        return fee_sorted[0].price

    def get_fee_price_by_pallet(self, pallet_number):
        """
        Searches among fees where type is pallet and selects the one that fits more to the sale order
        Returns the price of that fee.

        Parameters:
        ----------
        pallet_number:
            Number of pallets of the shipping
        """
        fee_ids = self.fee_ids.filtered(
            lambda fee: fee.type == 'pallet' and fee.max_qty >= pallet_number
        )
        if len(fee_ids) == 0:
            return None
        fee_sorted = fee_ids.sorted(lambda fee: fee.max_qty)
        return fee_sorted[0].price


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

    def calculate_shipping_cost(self, shipping_volume, shipping_weight, mode):
        """
        Returns the final cost list of the sale order shipping

        Parameters:
        ----------
        pallet_number:
            Number of pallets of the shipping
        shipping_weight:
            Shipping weight
        mode:
            Tipe of price calculator
        """
        base_fee_price = self.get_fee_price(
            self._get_pallet_number(shipping_volume),
            shipping_weight,
            mode
        )
        if base_fee_price is None:
            return []

        return self.get_service_price_list(base_fee_price)

    def get_service_price_list(self, base_fee_price):
        """
        Returns a list with services and its final price based on the price given.

        Parameters:
        ----------
        base_fee_price:
            Price on which fuel and supplements fees are going to be applied
        """

        fuel_added_price = base_fee_price * (1 + self.shipping_cost_id.fuel / 100)
        service_price_list = [
            {
                'price': round(fuel_added_price * (1 + supplement.added_percentage / 100), 2),
                'service_name': f'{supplement.service_id.name}',
                'sale_order_shipping_cost_id': self.id,
                'weight_volume_translation': self.shipping_cost_id.weight_volume_translation
            }
            for supplement in self.shipping_cost_id.supplement_ids
        ]
        return service_price_list

    def get_fee_price(self, pallet_number, shipping_weight, mode):
        """
        Calls the correct fee price calculator depending on mode.
        Returns the fee price that fits the best to the parameters given

        Parameters:
        ----------
        pallet_number:
            Number of pallets of the shipping
        shipping_weight:
            Shipping weight
        mode:
            Tipe of price calculator
        """
        if mode == 'pallet':
            return self.shipping_cost_id.get_fee_price_by_pallet(pallet_number)
        if mode == 'total_weight':
            return self.shipping_cost_id.get_fee_price_by_weight(shipping_weight)

    def _get_pallet_number(self, shipping_volume):
        """
        Returns the pallet number of the shipping. Divides the volume by pallet volume

        Parameters:
        ----------
        shipping_volume:
            Volume that the shipping has
        """
        try:
            return math.ceil(
                shipping_volume * (
                    1 / self.shipping_cost_id.volume
                )
            )
        except ZeroDivisionError:
            # we consider as default pallet volume 1 cbm
            return shipping_volume


class ShippingCostCalculator(models.TransientModel):
    _name = 'shipping.cost.calculator'

    shipping_weight = fields.Float(
        'Shipping weight (kg)', required=True, digits=dp.get_precision('Stock Weight')
    )
    shipping_volume = fields.Float(
        'Shipping volume (m3)', required=True, digits=dp.get_precision('Stock Weight')
    )
    zip_code = fields.Char('Zip code', required=True)
    country_id = fields.Many2one('res.country', string='Country', required=True)

    def calculate_shipping_cost(self):
        """
        Calculates shipping costs given shipping weight, shipping volume and
        destination's zip code

        Returns an action that opens a picking_rated_wizard model
        """
        if self.shipping_volume < 0 or self.shipping_weight < 0:
            raise UserError(_(
                'Invalid values to calculate shipping costs. Please, try changing values.'
            ))
        zones = self.env['shipping.zone'].sudo().search(
            [('country_id', '=', self.country_id.id)]
        ).filtered(
            lambda zone: zone.is_postal_code_in_zone(self.zip_code)
        )
        if not zones:
            raise UserError(_(
                'There are no zones embedding "%s". Please, try with another zip code.'
            ) % self.zip_code)

        services = []
        shipping_costs = self.env['shipping.cost'].sudo().search([('shipping_zone_id', 'in', zones.ids)])
        create_so_sc = self.env['sale.order.shipping.cost'].create
        picking_rated = self.env['picking.rated.wizard'].create({
            'total_weight': self.shipping_weight,
            'total_volume': self.shipping_volume,
        })
        action_to_return = self.env.ref('sale_order_board.action_open_picking_rated_wizard').read()[0]
        action_to_return['res_id'] = picking_rated.id

        for sc in shipping_costs:
            new_so_sc = create_so_sc({'shipping_cost_id': sc.id})
            shipping_weight = self.get_shipping_weight(sc.weight_volume_translation)
            services += new_so_sc.sudo().calculate_shipping_cost(
                self.shipping_volume,
                shipping_weight,
                mode='pallet'
            )
            services += new_so_sc.sudo().calculate_shipping_cost(
                self.shipping_volume,
                shipping_weight,
                mode='total_weight'
            )

        services_to_add = [
            (0, 0, {
                'currency': 'EUR',
                'transit_time': '',
                'amount': service['price'],
                'service': service['service_name'],
                'shipping_weight': self.get_shipping_weight(service['weight_volume_translation']),
                'wizard_id': picking_rated.id,
                'sequence': 0
            }) for service in services
        ]
        picking_rated.write({'data': services_to_add})
        return action_to_return

    def get_shipping_weight(self, weight_volume_translator):
        """
        Calculates the shipping weight. This will be the maximun of the shipping weight and
        the volume weight

        Parameters:
        ----------
        weight_volume_translator: Float
            Translator to obtain volume_weight
        """
        volume_weight = self.shipping_volume * weight_volume_translator
        return max(volume_weight, self.shipping_weight)

