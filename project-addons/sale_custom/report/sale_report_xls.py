# © 2018 Visiotech
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

try:
    import xlwt
except ImportError:
    xlwt = None
from datetime import datetime
from openerp.report import report_sxw
from openerp.tools.translate import translate, _

_ir_translation_name = 'xls.daily.sale'


class DailySaleExportReportXlsParser(report_sxw.rml_parse):

    def set_context(self, objects, data, ids, report_type=None):
        super(DailySaleExportReportXlsParser, self).set_context(
            objects, data, ids, report_type=report_type)
        wanted_list = ['date', 'daily_sales', 'daily_benefit', 'daily_margin',
                       'monthly_margin', 'inventory_value', 'autocartera', 'thirty_days_sales',
                       'paydays', 'thirty_days_stock']
        self.data = data
        self.localcontext.update({
            'wanted_list': wanted_list
        })

    def __init__(self, cr, uid, name, context=None):
        if context is None:
            context = {}
        super(DailySaleExportReportXlsParser, self).__init__(cr, uid, name, context=context)
        # template_changes = invoice_pool._report_xls_template(cr, uid, context)
        self.localcontext.update({
            'datetime': datetime,
            'title': 'Daily Sales',
            # 'invoice_type': self._invoice_type,
            # 'template_changes': template_changes,
            'lines': self._lines,
            '_': self._
        })
        self.context = context

    def _(self, src):
        lang = self.context.get('lang', 'en_US')
        return translate(self.cr, _ir_translation_name, 'report', lang, src) \
               or src

    def _title(self):
        return 'Daily Sales'

    def _lines(self, object):
        return self.data['data']


try:
    from openerp.addons.report_xls.report_xls import report_xls
    from openerp.addons.report_xls.utils import _render

    class DailySaleExportReportXls(report_xls):

        def __init__(self, name, table, rml=False, parser=False, header=True, store=False):
            super(DailySaleExportReportXls,
                  self).__init__(name, table, rml, parser, header, store)

            # Cell Styles
            _xs = self.xls_styles
            # header
            rh_cell_format = _xs['bold'] + _xs['fill'] + _xs['borders_all']
            self.rh_cell_style = xlwt.easyxf(rh_cell_format)
            self.rh_cell_style_center = xlwt.easyxf(
                rh_cell_format + _xs['center'])
            self.rh_cell_style_right = xlwt.easyxf(
                rh_cell_format + _xs['right'])
            # lines
            aml_cell_format = _xs['borders_all']
            self.aml_cell_style = xlwt.easyxf(aml_cell_format)

            self.aml_cell_style_center = xlwt.easyxf(
                aml_cell_format + _xs['center'])
            self.aml_cell_style_date = xlwt.easyxf(
                aml_cell_format + _xs['left'],
                num_format_str=report_xls.date_format)
            self.aml_cell_style_decimal = xlwt.easyxf(
                aml_cell_format + _xs['right'],
                num_format_str=report_xls.decimal_format)
            # totals
            rt_cell_format = _xs['bold'] + _xs['fill'] + _xs['borders_all']
            self.rt_cell_style = xlwt.easyxf(rt_cell_format)
            self.rt_cell_style_right = xlwt.easyxf(rt_cell_format + _xs['right'])
            self.rt_cell_style_decimal = xlwt.easyxf(
                rt_cell_format + _xs['right'],
                num_format_str=report_xls.decimal_format)

        def _prepare_col_spec_lines_template(self):
            # This is needed for translate tool to catch correctly lang handled

            user = self.pool['res.users'].browse(self.cr, self.uid, self.uid)
            context = {}
            context.update({'lang': user.lang})

            # XLS Template
            # [Cell columns span, cell width, content type, ??]
            spec_lines_template = {
                'date': {
                    'header': [1, 20, 'text', _render("_('Date')")],
                    'lines': [1, 0, 'text', _render(str("l['date']"))],
                    'totals': [1, 0, 'text', None]},
                'daily_sales': {
                    'header': [1, 50, 'text', _render("_('Daily Sales')")],
                    'lines': [1, 0, 'number', _render(str("(l['daily_sales'])"))],
                    'totals': [1, 0, 'text', None]},
                'daily_benefit': {
                    'header': [1, 50, 'text', _render("_('Daily Benefit')")],
                    'lines': [1, 0, 'number', _render(str("(l['daily_benefit'])"))],
                    'totals': [1, 0, 'text', None]},
                'daily_margin': {
                    'header': [1, 20, 'text', _render("_('Daily Margin')")],
                    'lines': [1, 0, 'number', _render(str("l['daily_margin']"))],
                    'totals': [1, 0, 'text', None]},
                'monthly_margin': {
                    'header': [1, 20, 'text', _render("_('Monthly Margin')")],
                    'lines': [1, 0, 'number', _render(str("l['monthly_margin']"))],
                    'totals': [1, 0, 'text', None]},
                'inventory_value': {
                    'header': [1, 50, 'text', _render("_('Stock')")],
                    'lines': [1, 0, 'number', _render(str("l['inventory_value']"))],
                    'totals': [1, 0, 'text', None]},
                'autocartera': {
                    'header': [1, 50, 'text', _render("_('Autocartera')")],
                    'lines': [1, 0, 'number', _render(str("l['autocartera']"))],
                    'totals': [1, 0, 'text', None]},
                'thirty_days_sales': {
                    'header': [1, 50, 'text', _render("_('30D Sales')")],
                    'lines': [1, 0, 'number', _render(str("l['thirty_days_sales']"))],
                    'totals': [1, 0, 'text', None]},
                'paydays': {
                    'header': [1, 50, 'text', _render("_('Paydays')")],
                    'lines': [1, 0, 'number', _render(str("l['paydays']"))],
                    'totals': [1, 0, 'text', None]},
                'thirty_days_stock': {
                    'header': [1, 50, 'text', _render("_('30D Stock')")],
                    'lines': [1, 0, 'number', _render(str("l['thirty_days_stock']"))],
                    'totals': [1, 0, 'text', None]},
            }

            return spec_lines_template

        def get_new_ws(self, _p, _xs, sheet_name, wb):
            wanted_list = _p.wanted_list
            self.wanted_list = wanted_list
            title = _p.title
            report_name = title
            ws = wb.add_sheet(sheet_name)
            ws.panes_frozen = True
            ws.remove_splits = True
            ws.portrait = 0  # Landscape
            ws.fit_width_to_pages = 1
            # set print header/footer
            ws.header_str = self.xls_headers['standard']
            ws.footer_str = self.xls_footers['standard']
            row_pos = 0
            # Title
            cell_style = xlwt.easyxf(_xs['xls_title'])
            c_specs = [
                ('report_name', 1, 0, 'text', report_name),
            ]
            row_data = self.xls_row_template(c_specs, ['report_name'])
            row_pos = self.xls_write_row(ws, row_pos, row_data,
                                         row_style=cell_style)
            row_pos += 1
            # Column headers
            c_specs = [self.render(
                x, self.col_specs_lines_template, 'header',
                render_space={'_': _p._}) for x in wanted_list]
            row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = self.xls_write_row(
                ws, row_pos, row_data, row_style=self.rh_cell_style,
                set_column_size=True)
            ws.set_horz_split_pos(row_pos)

            return ws, row_pos

        def generate_xls_report(self, _p, _xs, data, objects, wb):
            wanted_list = _p.wanted_list
            self.wanted_list = wanted_list
            self.col_specs_lines_template = \
                self._prepare_col_spec_lines_template()
            # self.col_specs_lines_template.update(_p.template_changes)
            title = _p.title
            sheet_name = title[:31]
            ws, row_pos = self.get_new_ws(_p, _xs, sheet_name, wb)

            ws_count = 0
            line_count = 0
            for o in objects:
                lines = _p.lines(o)
                for l in lines:
                    line_count += 1
                    if row_pos >= 65536:
                        ws_count += 1
                        new_sheet_name = "%s_%s" % (sheet_name, ws_count)
                        ws, row_pos = self.get_new_ws(_p, _xs, new_sheet_name,
                                                      wb)

                    cslt = self.col_specs_lines_template
                    c_specs = [self.render(x, cslt, 'lines') for x in wanted_list]
                    row_data = self.xls_row_template(c_specs,
                                                     [str(x[0]) for x in c_specs])
                    row_pos = self.xls_write_row(ws, row_pos, row_data)

    DailySaleExportReportXls(
        'report.xls.daily.sale', 'xls.sale.report.wizard',
        parser=DailySaleExportReportXlsParser)

except ImportError:
    pass