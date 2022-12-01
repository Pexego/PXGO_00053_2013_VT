from odoo import fields, models


class ImportSheets(models.Model):
    """
    Class that models Importation Sheets. Registers import costs linked to shipping.
    """
    _name = "import.sheets"
