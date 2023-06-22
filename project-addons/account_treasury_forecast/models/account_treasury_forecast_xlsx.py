from odoo import models, fields, api, _


class AccountTreasuryForecastXlsx(models.AbstractModel):
    """
    Models the xlsx file with purchase suggestion report to be downloaded
    """
    _name = 'report.account_treasury_forecast.account_treasury_forecast'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, account_treasury_forecasts):
        """
        Writes the content into the excell report.

        Parameters
        ----------
        workbook:
            Workbook object from xlsxwriter library where the report is going to be written
        data:
            Dictionary with data and token
        account_treasury_forecasts:
            Objects from where we are going to get the values needed to create the report
        """
        worksheet_row_values, worksheet_headers = self._get_rows_and_headers_for_report(
            account_treasury_forecasts
        )
        self.write_on_report_file(workbook, worksheet_row_values, worksheet_headers)

    @staticmethod
    def _get_rows_and_headers_for_report(wizard):
        """
        Returns two dictionaries. One with worksheet name as key and rows content as value.
        The second with headers as value.

        Parameters
        ----------
        wizard:
            Purchase Suggestions instance from where we want to get row_values

        Return
        ------
        row_dict, headers_dict
        """
        row_dict = {
            'Partner': [
                (
                    line.date_due, line.invoice_id.number, line.partner_id.name,
                    line.journal_id.name, line.payment_mode_id.name, line.payment_term_id.name,
                    line.invoice_type, line.base_amount, line.tax_amount,
                    line.total_amount, line.residual_amount, line.state
                ) for line in wizard.out_invoice_ids
            ],
            'Supplier': [
                (
                    line.date_due, line.invoice_id.number, line.partner_id.name,
                    line.journal_id.name, line.payment_mode_id.name, line.payment_term_id.name,
                    line.invoice_type, line.base_amount, line.tax_amount,
                    line.total_amount, line.residual_amount, line.state
                ) for line in wizard.in_invoice_ids
            ]
        }
        header_dict = {
            'Partner': [
                'Date Due', 'Invoice', 'Partner',
                'Journal', 'Payment Mode', 'Payment Term',
                'Invoice Type', 'Base Amount', 'Tax Amount',
                'Total Amount', 'Residual Amount', 'State'
            ],
            'Supplier': [
                'Date Due', 'Invoice', 'Partner',
                'Journal', 'Payment Mode', 'Payment Term',
                'Invoice Type', 'Base Amount', 'Tax Amount',
                'Total Amount', 'Residual Amount', 'State'
            ]
        }
        return row_dict, header_dict

    def write_on_report_file(self, workbook, worksheet_row_values, worksheet_headers):
        """
        Writes the content of the report file

        Parameters
        ----------
        workbook:
            Workbook where we want to write sheets and content
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
            worksheet = workbook.add_worksheet(worksheet_name)
            row_values = worksheet_row_values[worksheet_name]
            self._write_worksheet(worksheet, headers, row_values)

    @staticmethod
    def _write_headers_on_report_file(worksheet, headers):
        """
        Writes the column headers in worksheet

        Parameters
        ----------
        worksheet:
            Worksheet where the headers are going to be writen
        headers: List[str]
            Headers we want to write
        """
        column = 0
        for value in headers:
            worksheet.write(0, column, value)
            column += 1

    @staticmethod
    def _write_row_on_report_file(worksheet, row_values, row_index):
        """
        Writes a row in the report

        Parameters
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
            worksheet.write(row_index, column, value)
            column += 1

    def _write_worksheet(self, worksheet, headers, row_values):
        """
        Writes a complete sheet of the report

        Parameters
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
