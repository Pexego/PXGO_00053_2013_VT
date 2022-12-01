from odoo import fields, models


class ImportSheets(models.Model):
    """
    Class that models Importation Sheets. Registers import costs linked to shipping.
    """
    _name = "import.sheets"

    container_id = fields.Many2One(
        'stock.container',
        string="Container",
        ondelete="restrict",
        required=True
    )
    dua = fields.Char(string="DUA")
    dua_date = fields.Date(string="DUA date")

    kgs = fields.Float(related="container_id.kgs", string="KGS", store=True)
    Cbm = fields.Float(realted="container_id.cbm", string="CBM", store=True)
    incoterm = fields.Char(related="container_id.incoterm.code", readonly=True)
    destination_port = fields.Char(
        related="container_id.destination_port.port_code",
        string="NAV/PTO",
        readonly=True
    )
    forwarder_comercial = fields.Char(
        realted="container_id.forwarded_comercial",
        string="Forwarded",
        readonly=True
    )
    track = fields.Selection([
        ("option1", "Option 1"),
        ("option2", "Option 2"),
        ("option3", "Option 3")
    ])

    treasury = fields.Char(string="Treasury")
    freight = fields.Float(string="Freight")
    fee = fields.Float(string="Fee")
    inspection = fields.Float(string="Inspection")
    arrival_cost = fields.Float(string="Arrival costs")
    destination_cost = fields.Float(string="Destination costs")
