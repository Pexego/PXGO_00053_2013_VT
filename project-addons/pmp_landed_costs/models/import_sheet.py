from odoo import fields, models, api


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
    channel = fields.Selection("Channel", related="container_id.customs_channel", readonly=True)

    treasury = fields.Char(string="Treasury")
    freight = fields.Float(string="Freight")
    fee = fields.Float(string="Fee")
    inspection = fields.Float(string="Inspection")
    arrival_cost = fields.Float(string="Arrival costs")

    landed_cost_ids = fields.One2many("stock.landed.cost", "import_sheet_id", string="Landed costs")
    landed_cost_count = fields.Integer("Landed cost count", compute="_get_landed_cost_count", default=0)

    invoice_ids = fields.Many2many('account.invoice', string='Invoices', domain=[('type', '=', 'in_invoice')])

    sheet_state = fields.Selection([('pending', 'Pending'), ('in_process', 'In process'), ('done', 'Done')],
                                   string='Status', default='pending', compute="_get_sheet_state", store=True)

    @api.multi
    @api.depends("landed_cost_ids.state", "invoice_ids.state")
    def _get_sheet_state(self):
        for sheet in self:
            cost_state = sheet.calculate_sheet_state(sheet.landed_cost_ids)
            invoice_state = sheet.calculate_sheet_state(sheet.invoice_ids)

            if cost_state == 'done' and invoice_state == 'done':
                sheet.sheet_state = 'done'
            elif cost_state in ('done', 'in_process') or invoice_state in ('done', 'in_process'):
                sheet.sheet_state = 'in_process'
            else:
                sheet.sheet_state = 'pending'

    @api.multi
    def calculate_sheet_state(self, sheet_list):
        line_done = False
        line_state = ''

        for line in sheet_list:
            if line.state == 'draft':
                line_state = 'in_process'
                break
            elif line.state in ('cancel', 'history') and not line_done:
                line_state = 'pending'
            else:
                line_state = 'done'
                line_done = True

        return line_state

    def _get_landed_cost_count(self):
        """
        Calculates count of landed costs that are associated to this import sheet
        """
        for sheet in self:
            count = self.env['stock.landed.cost'].search_count([('import_sheet_id', '=', sheet.id)])
            sheet.landed_cost_count = count

    def action_open_landed_cost_creator(self):
        """
        Returns action with the view of the create_landed_cost_wizard model

        Returns:
        -------
        action
        """
        wizard = self.get_landed_cost_creator_wizard()
        action = self.env.ref(
            'pmp_landed_costs.action_open_landed_cost_creator_wizard_view'
        ).read()[0]
        action['res_id'] = wizard.id
        return action

    def action_open_landed_cost_by_sheet(self):
        """
        Returns action with the view of the landed cost list related with this import sheet

        Returns:
        -------
        action
        """
        action = self.env.ref(
            'pmp_landed_costs.action_open_landed_cost_view'
        ).read()[0]
        action['domain'] = [('import_sheet_id', '=', self.id)]
        return action

    def get_landed_cost_creator_wizard(self):
        """
        Creates a landed_cost_creator_wizard associated to the import_sheet

        Returns:
        -------
        landed.cost.creator.wizard
        """
        product_ids = self.container_id.get_products_for_landed_cost_warning()
        wizard = self.env['landed.cost.creator.wizard'].create({
            'import_sheet_id': self.id,
            'product_ids': [(6, 0, product_ids.ids)]
        })
        return wizard

    def calculate_fee_price(self):
        """
        Calculates the price by fee

        Returns:
        -------
        Float:
            Fee price
        """
        return self.fee

    def calculate_destination_cost_price(self):
        """
        Calculates price by destination cost

        Returns:
        -------
        Float:
            Freight + inspection + arrival cost prices
        """
        return self.freight + self.inspection + self.arrival_cost


class ImportSheetXlsx(models.AbstractModel):
    """
    Models the xlsx file with import sheets report to be downloaded

    Parameters:
    ----------
    workbook:
        Workbook object from xlsxwriter library where the report is going to be written
    """
    _name = 'report.purchase_picking.import_sheet'
    _inherit = 'report.report_xlsx.abstract'

    workbook = None

    def generate_xlsx_report(self, workbook, data, import_sheets):
        """
        Writes the content into the excell report.

        Parameters:
        ----------
        workbook:
            Workbook object from xlsxwriter library where the report is going to be written
        data:
            Dictionary with data and token
        import_sheets:
            Objects from where we are going to get the values needed to create the report
        """
        self.workbook = workbook
        worksheet_row_values, worksheet_headers = self._get_rows_and_headers_for_report(import_sheets)
        self.write_on_report_file(worksheet_row_values, worksheet_headers)

    @staticmethod
    def _get_rows_and_headers_for_report(import_sheets):
        """
        Returns two dictionaries. One with worksheet name as key and rows content as value.
        The second with headers as value.

        Parameters:
        ----------
        import_sheets:
            Import Sheet instances from where we want to get row_values

        Return:
        ------
        row_dict, headers_dict
        """
        row_dict = {
            'Import Sheets': [
                (
                    sheet.dua, sheet.container_id.name, sheet.dua_date, sheet.treasury,
                    sheet.kgs, sheet.cbm, sheet.incoterm, sheet.destination_port,
                    sheet.forwarder_comercial, sheet.container_type, sheet.channel, sheet.freight,
                    sheet.fee, sheet.inspection, sheet.arrival_cost
                ) for sheet in import_sheets
            ]
        }
        header_dict = {
            'Import Sheets': [
                'DUA', 'Container', 'DUA date', 'Treasury', 'Kilograms', 'CBM', 'Incoterm',
                'NAV/PTO', 'Forwarded', 'Container Type', 'Channel', 'Freight', 'Fee',
                'Inspection', 'Arrival costs'
            ]
        }
        return row_dict, header_dict

    def write_on_report_file(self, worksheet_row_values, worksheet_headers):
        """
        Writes the content of the report file

        Parameters:
        ----------
        worksheet_row_values: Dict[str, List[Tuple[Any]]]
            Are the values we want to write on each worksheet.
            Key is the name of the worksheet and values a list with the row values we want to write
            into that sheet.
        worksheet_headers: Dict[str, List[str]]
            Headers we want to write on each worksheet.
            Key is the name of the worksheet and values a list with the headers we want to write
            into that sheet
        """
        for worksheet_name, headers in worksheet_headers.items():
            worksheet = self.workbook.add_worksheet(worksheet_name)
            row_values = worksheet_row_values[worksheet_name]
            self._write_worksheet(worksheet, headers, row_values)

    def _write_headers_on_report_file(self, worksheet, headers):
        """
        Writes the column headers in worksheet

        Parameters:
        ----------
        worksheet:
            Worksheet where the headers are going to be writen
        headers: List[str]
            Headers we want to write
        """
        column = 0
        header_format = self._get_cell_format('header')
        for value in headers:
            worksheet.write(0, column, value, header_format)
            column += 1

    def _write_row_on_report_file(self, worksheet, row_values, row_index):
        """
        Writes a row in the report

        Parameters:
        ----------
        worksheet:
            Worksheet where the row is going to be writen
        row_values: List[Any]
            Values to write in the row
        row_index: Int
            The number of the row where we are going to write
        """
        column = 0
        for value in row_values:
            # If we have False as value we don't write it
            if value or type(value) != bool:
                cell_format = self._get_cell_format(value)
                worksheet.write(row_index, column, value, cell_format)
            column += 1

    def _get_cell_format(self, value):
        """
        Returns the correct cell format to write the value into the worksheet.
        This function checks if the value is a color and returns the format to paint
        the report cell with that colour

        Parameters:
        ----------
        value:
            Value we want to write in the report. This is the value we are going to
            check to obtain the format

        Returns:
        -------
        Format object from xlsxwriter library we are going to use to write value
        """
        if value in ['red', 'orange', 'yellow', 'green']:
            return self.workbook.add_format({'bg_color': value})
        if value == 'header':
            return self.workbook.add_format({'bold': True})
        return self.workbook.add_format()

    def _write_worksheet(self, worksheet, headers, row_values):
        """
        Writes a complete sheet of the report

        Parameters:
        ----------
        worksheet:
            Worksheet that is going to be writen
        headers: List[str]
            Headers of the columns that we want to write
        row_values: List[List[Any]]
            Content in rows we want to write in the worksheet
        """
        self._write_headers_on_report_file(worksheet, headers)
        for index, row_elements in enumerate(row_values):
            self._write_row_on_report_file(worksheet, row_elements, index + 1)
