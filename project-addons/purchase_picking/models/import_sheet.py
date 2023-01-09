from odoo import fields, models


class ImportSheet(models.Model):
    """
    Class that models Importation Sheets. Registers import costs linked to shipping.
    """
    _name = "import.sheet"
    _rec_name = "dua"

    container_id = fields.Many2one('stock.container', string="Container")
    dua = fields.Char(string="DUA")
    dua_date = fields.Date(string="DUA date")

    kgs = fields.Float(
        related="container_id.kilograms",
        string="KGS",
        store=True,
        help="Kilograms"
    )
    cbm = fields.Float(
        related="container_id.cubic_meters",
        string="CBM",
        store=True,
        help="Cubic Meters"
    )
    incoterm = fields.Char(related="container_id.incoterm.code", readonly=True, string="Incoterm")
    destination_port = fields.Char(
        related="container_id.destination_port.port_code",
        string="NAV/PTO",
        readonly=True
    )
    forwarder_comercial = fields.Char(
        related="container_id.forwarder_comercial",
        string="Forwarded",
        readonly=True
    )
    container_type = fields.Char(
        string="Container Type",
        related="container_id.container_type",
        readonly=True
    )

    treasury = fields.Char(string="Treasury")
    freight = fields.Float(string="Freight")
    fee = fields.Float(string="Fee")
    inspection = fields.Float(string="Inspection")
    arrival_cost = fields.Float(string="Arrival costs")
    destination_cost = fields.Float(string="Destination costs")
