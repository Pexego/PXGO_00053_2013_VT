from odoo import models, fields, api


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
    # fuel = fields.Float(string="Fuel", related="transporter_id.¿fuel?", readonly=True)
    sequence = fields.Integer(string="Sequence")
    volume = fields.Float(string="Max volume/palet")
    sale_order_id = fields.Many2one("sale.order", string="Sale order")

    order_volume = fields.Float(compute="get_order_volume", string="Order volume")

    # TODO: review if many2many
    fee_ids = fields.One2many("shipping.cost.fee", "shipping_cost_id", string="Fees")
    supplement_ids = fields.One2many(
        "shipping.cost.suplement",
        "shipping_cost_id",
        string="Supplements"
    )

    @api.onchange('campo con las lineas de pedido')
    def get_sale_order_volume(self):
        """
        Calculates and returns the total volume of the sale order related to the shipping cost
        """
        # FIXME: obtain each product in sale order lines
        for product in self.sale_order_id:
            sum(product.volume)
            pass


# TODO: review if TansientModel
class ShippingCostFee(models.Model):
    """
    Models a fee in shipping costs
    """
    _name = "shipping.cost.fee"
    # TODO: review if many2many
    shipping_cost_id = fields.Many2one("shipping.cost", string="Shipping cost")
    type = fields.Selection(string="Type", selection=[
        ("a", "Palet"), ("b", "Bulto"),
        ("c", "Peso total"), ("d", "Servicio paletizado")
    ])
    max_qty = fields.Float(string="Quantity Max")
    price = fields.Float(string="Price")


# TODO: review if TransientModel
class ShippingCostSupplement(models.Model):
    """
    Models a suplement in shipping costs
    """
    _name = "shipping.cost.supplement"

    # TODO: review if many2many
    shipping_cost_id = fields.Many2one("shipping.cost", string="Shipping cost")
    service = fields.Selection(string="Service", selection=[
        ("a", "servicio urgente"), ("b", "servicio especial"), ("", "servicio paletizado")
    ])
    added_percentage = fields.Float(string="Added percentage")
