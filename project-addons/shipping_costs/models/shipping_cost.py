from odoo import models, fields, api, _
from odoo.exceptions import UserError


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
    # TODO
    # fuel = fields.Float(string="Fuel", related="transporter_id.¿fuel?", readonly=True)
    sequence = fields.Integer(string="Sequence")
    volume = fields.Float(string="Max volume/palet")

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

    @api.model
    def create(self, vals):
        # don't allow to save if services are not from transporter selected
        transporter_id = vals.get('transporter_id', False)
        supplements = vals.get('supplement_ids', False)

        if not transporter_id or not supplements:
            return super().create(vals)

        transporter_services = self.env['transportation.transporter'].browse(
            transporter_id
        ).service_ids.ids

        for supplement_list in supplements:
            supplement_service = supplement_list[2]['service_id']
            if supplement_service not in transporter_services:
                raise UserError(_("Cannot save with Services that doesn't belong to the transporter. "
                                  "Please, check the services chosen."))
        return super().create(vals)

    @api.multi
    def write(self, vals):
        # don't allow to save if services are not from transporter selected
        for shipping_cost in self:
            old_service_list = []
            transporter_id = shipping_cost.transporter_id.id
            # case new transporter, we get old services
            if 'transporter_id' in vals:
                transporter_id = vals['transporter_id']
                supplement_id_list = shipping_cost.supplement_ids
                supplement_id_to_rm = [
                    elem[1] for elem in vals.get('supplement_ids', []) if elem[0] in [2, 1]
                ]
                supplement_id_list = supplement_id_list.filtered(lambda supp: supp.id not in supplement_id_to_rm)
                old_service_list = supplement_id_list.mapped('service_id').ids
            # we add new services
            service_list = old_service_list + [
                elem[2]['service_id'] for elem in vals.get('supplement_ids', []) if elem[0] in [0, 1]
            ]
            transporter_services = self.env['transportation.transporter'].browse(
                transporter_id
            ).service_ids.ids

            for service_id in service_list:
                if service_id not in transporter_services:
                    raise UserError(_("Cannot save with Services that doesn't belong to the transporter. "
                                      "Please, check the services chosen."))

        return super().write(vals)


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
        Returns a list of tuples containing sale.order fields and the name of that field.
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
        ("pallet", "Pallet"), ("package", "Package"),
        ("total_weight", "Total weight"), ("palletized", "Palletized service")
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
