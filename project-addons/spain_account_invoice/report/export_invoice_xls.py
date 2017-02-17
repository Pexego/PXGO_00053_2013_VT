# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
try:
    import xlwt
except ImportError:
    xlwt = None
from datetime import datetime
from openerp.report import report_sxw
from openerp.tools.translate import translate, _
import ipdb

_ir_translation_name = 'account.invoice.export.xls'


class AccountInvoiceExportReportXlsParser(report_sxw.rml_parse):
    def set_context(self, objects, data, ids, report_type=None):
        super(AccountInvoiceExportReportXlsParser, self).set_context(
            objects, data, ids, report_type=report_type)
        self.invoice_type = data['invoice_type']
        self.company_id = data['company_id']
        self.period_ids = data['period_ids']

    def __init__(self, cr, uid, name, context=None):
        if context is None:
            context = {}
        super(AccountInvoiceExportReportXlsParser, self).__init__(
            cr, uid, name, context=context)
        invoice_pool = self.pool['account.invoice']
        wanted_list = invoice_pool._report_xls_fields(cr, uid, context)
        template_changes = invoice_pool._report_xls_template(cr, uid, context)
        self.localcontext.update({
            'datetime': datetime,
            'title': self._title,
            'wanted_list': wanted_list,
            'invoice_type': self._invoice_type,
            'template_changes': template_changes,
            'lines': self._lines,
            '_': self._
        })
        self.context = context

    def _(self, src):
        lang = self.context.get('lang', 'en_US')
        return translate(self.cr, _ir_translation_name, 'report', lang, src) \
               or src

    def _title(self):
        return self._(self.invoice_type)

    def _invoice_type(self):
        return self.invoice_type

    # In this function, we do a query to obtain all de Customer
    # Invoices and the Customer Refund Invoices at the same time.
    def _lines(self, object):
        additional_where = ""
        if self.period_ids:
            additional_where += self.cr.mogrify(
                "AND i.period_id in %s", (tuple(self.period_ids),))
        sql = (
            "SELECT "
            "i.number as number, "
            "i.date_invoice as date_invoice, "
            "p.vat as partner_vat, "
            "CASE WHEN p.parent_id IS NULL THEN "
            "   p.name "
            "WHEN p.parent_id IS NOT NULL THEN "
            "   p2.name "
            "END "
            "as partner_name, "
            "t.amount as tax_amount, "
            "t.base as tax_base, "
            "t.amount as tax_percent, "
            "i.amount_total as amount_total, "
            "it.value as country_name, "
            "t.name as tax_description, "
            "afp.name as fiscal_name "
            "FROM("
            "account_invoice i "
            "LEFT JOIN res_partner p "
            "   ON (i.partner_id = p.id) "
            "LEFT JOIN res_partner p2 "
            "   ON (p.parent_id = p2.id) "
            "LEFT JOIN res_country c "
            "   ON (p.country_id = c.id) "
            "LEFT JOIN account_invoice_tax t "
            "   ON (i.id = t.invoice_id) "
            "LEFT JOIN ir_property pr "
            "   ON (pr.res_id = 'res.partner,'||i.partner_id) "
            "LEFT JOIN account_fiscal_position afp "
            "   ON (afp.id = cast(substring(pr.value_reference FROM '[0-9]+') as int))"
            "LEFT JOIN ir_translation it "
            "   ON (c.name = it.src)) "
            "WHERE (i.type = 'out_refund' "
            "    OR i.type = 'out_invoice') "
            "    AND (i.state = 'paid' "
            "    OR i.state = 'open') "
            "    AND i.number NOT LIKE '%_ef%' "
            "    AND i.company_id = 1"
            "    AND substring(pr.value_reference FROM '[a-z\.]+') = 'account.fiscal.position' "
            "    AND it.lang = 'es_ES' "
            "    AND it.module = 'base' "
            " {} "
            "ORDER BY date_invoice ASC").format(additional_where)

        self.cr.execute(sql)
        lines = self.cr.dictfetchall()

        return lines


try:
    from openerp.addons.report_xls.report_xls import report_xls
    from openerp.addons.report_xls.utils import _render


    class AccountInvoiceExportReportXls(report_xls):

        def __init__(self, name, table, rml=False, parser=False, header=True, store=False):
            super(AccountInvoiceExportReportXls,
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

        def _prepare_col_spec_lines_template(self, invoice_type=None):
            # This is needed for translate tool to catch correctly lang handled

            user = self.pool['res.users'].browse(self.cr, self.uid, self.uid)
            context = {}
            context.update({'lang': user.lang})
            # XLS Template
            # [Cell columns span, cell width, content type, ??]
            spec_lines_template = {
                'number': {
                    'header': [1, 15, 'text', _render("_('N de factura')")],
                    'lines': [1, 0, 'text', _render("l['number']")],
                    'totals': [1, 0, 'text', None]},
                'date_invoice': {
                    'header': [1, 20, 'text', _render("_('Fecha factura')")],
                    'lines': [1, 0, 'text', _render("(l['date_invoice'])")],
                    'totals': [1, 0, 'text', None]},
                'partner_vat': {
                    'header': [1, 20, 'text', _render("_('Empresa/NIF')")],
                    'lines': [1, 0, 'text', _render("(l['partner_vat'])")],
                    'totals': [1, 0, 'text', None]},
                'partner_name': {
                    'header': [1, 40, 'text', _render("_('Empresa/Nombre')")],
                    'lines': [1, 0, 'text', _render("l['partner_name']")],
                    'totals': [1, 0, 'text', None]},
                'tax_base': {
                    'header': [1, 20, 'text', _render("_('Base imponible')")],
                    'lines': [1, 0, 'number', _render("l['tax_base']"),
                              None, self.aml_cell_style_decimal],
                    'totals': [1, 0, 'text', None]},
                'tax_amount': {
                    'header': [1, 20, 'text', _render("_('Cuota IVA')")],
                    'lines': [1, 0, 'number', _render("l['tax_amount']"),
                              None, self.aml_cell_style_decimal],
                    'totals': [1, 0, 'text', None]},
                'tax_percent': {
                    'header': [1, 20, 'text', _render("_('% IVA')")],
                    'lines': [1, 0, 'number', _render("l['tax_percent']"),
                              None, self.aml_cell_style_decimal],
                    'totals': [1, 0, 'text', None]},
                'tax_amount_rec': {
                    'header': [1, 20, 'text', _render("_('Recargo de equivalencia')")],
                    'lines': [1, 0, 'number', _render("l['tax_amount_rec']"),
                              None, self.aml_cell_style_decimal],
                    'totals': [1, 0, 'text', None]},
                'tax_amount_ret': {
                    'header': [1, 20, 'text', _render("_('Retenciones')")],
                    'lines': [1, 0, 'number', _render("l['tax_amount_ret']"),
                              None, self.aml_cell_style_decimal],
                    'totals': [1, 0, 'text', None]},
                'amount_total': {
                    'header': [1, 20, 'text', _render("_('Total')")],
                    'lines': [1, 0, 'number', _render("l['amount_total']"),
                              None, self.aml_cell_style_decimal],
                    'totals': [1, 0, 'text', None]},
                'country_name': {
                    'header': [1, 20, 'text', _render("_('Empresa/País/Nombre del país')")],
                    'lines': [1, 0, 'text', _render("l['country_name']")],
                    'totals': [1, 0, 'text', None]},
                'tax_description': {
                    'header': [1, 40, 'text', _render("_('Líneas de impuestos/Descripción impuesto')")],
                    'lines': [1, 0, 'text', _render("l['tax_description']")],
                    'totals': [1, 0, 'text', None]},
                'fiscal_name': {
                    'header': [1, 40, 'text', _render("_('Empresa/Posición fiscal/Posición fiscal')")],
                    'lines': [1, 0, 'text', _render("l['fiscal_name']")],
                    'totals': [1, 0, 'text', None]},

            }

            if invoice_type == 'in_invoice':
                spec_lines_template.update({
                    'invoice_number': {
                        'header': [1, 13, 'text', _('Number')],
                        'lines': [1, 0, 'text', _render(
                            "l['supplier_invoice_number'] "
                            "or l['invoice_number']")],
                        'totals': [1, 0, 'text', None]
                    }
                })

            return spec_lines_template

        def get_new_ws(self, _p, _xs, sheet_name, wb):
            wanted_list = _p.wanted_list
            self.wanted_list = wanted_list
            title = _p.title()
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
            c_specs = map(lambda x: self.render(
                x, self.col_specs_lines_template, 'header',
                render_space={'_': _p._}), wanted_list)
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
                self._prepare_col_spec_lines_template(
                    invoice_type=_p.invoice_type())
            self.col_specs_lines_template.update(_p.template_changes)
            title = _p.title()
            sheet_name = title[:31]
            ws, row_pos = self.get_new_ws(_p, _xs, sheet_name, wb)

            ws_count = 0
            line_datas = {}
            line_count = 0
            for o in objects:
                length = len(_p.lines(o))
                lines = sorted(_p.lines(o), key=self.orderByNumber)
                for l in lines:
                    check = False
                    line_count += 1
                    if row_pos >= 65536:
                        ws_count += 1
                        new_sheet_name = "%s_%s" % (sheet_name, ws_count)
                        ws, row_pos = self.get_new_ws(_p, _xs, new_sheet_name,
                                                      wb)

                    if l['number'] == 'FV/138416':
                        ipdb.set_trace()

                    #We separate the taxes to display all in diferent columns.
                    #If the invoice is a refund, we need to display the amount
                    #in negative

                    if l['tax_description'] == "5.2% Recargo Equivalencia Ventas":
                        if 'tax_percent' not in line_datas:
                            line_datas['tax_percent'] = 0

                        if 'R' in l['number']:
                            line_datas['tax_amount_rec'] = float(l['tax_amount'])
                            line_datas['tax_amount_rec'] = -line_datas['tax_amount_rec']
                            line_datas['tax_base'] = float(l['tax_base'])
                            line_datas['tax_base'] = -line_datas['tax_base']
                            line_datas['amount_total'] = float(l['amount_total'])
                            line_datas['amount_total'] = -line_datas['amount_total']
                        else:
                            line_datas['tax_amount_rec'] = l['tax_amount']
                            line_datas['tax_base'] = l['tax_base']
                            line_datas['amount_total'] = l['amount_total']

                    elif l['tax_description'] == "Retenciones a cuenta 19% (Arrendamientos)":
                        if 'tax_percent' not in line_datas:
                            line_datas['tax_percent'] = 0

                        if 'R' in l['number']:
                            line_datas['tax_amount_ret'] = float(l['tax_amount'])
                            line_datas['tax_amount_ret'] = -line_datas['tax_amount_ret']
                            line_datas['tax_base'] = float(l['tax_base'])
                            line_datas['tax_base'] = -line_datas['tax_base']
                            line_datas['amount_total'] = float(l['amount_total'])
                            line_datas['amount_total'] = -line_datas['amount_total']
                        else:
                            line_datas['tax_amount_ret'] = l['tax_amount']
                            line_datas['tax_base'] = l['tax_base']
                            line_datas['amount_total'] = l['amount_total']

                    elif l['tax_description'] == "IVA 21% (Bienes)":
                        line_datas['tax_percent'] = 21.00
                        line_datas['tax_description'] = l['tax_description']

                        if 'R' in l['number']:
                            # ipdb.set_trace()
                            line_datas['tax_amount'] = float(l['tax_amount'])
                            line_datas['tax_amount'] = -line_datas['tax_amount']
                            line_datas['tax_base'] = float(l['tax_base'])
                            line_datas['tax_base'] = -line_datas['tax_base']
                        else:
                            line_datas['tax_amount'] = l['tax_amount']
                            line_datas['tax_base'] = l['tax_base']


                    # We have some taxes as IVA 0% and they are different
                    # so we need a else for all of them, because their
                    # execution is the same
                    else:
                        if not l['tax_base']:
                            l['tax_base'] = 0.0

                        # If the previous line of the xls is the same invoice and their taxes are the
                        # same, the code recalculate the tax_base
                        if (length <= line_count) or ((l['number'] == lines[line_count - 2]['number'])
                                and l['tax_description'] == lines[line_count - 2]['tax_description']):
                            line_datas['tax_base'] = l['tax_base'] + lines[line_count - 2]['tax_base']
                            if 'R' in l['number']:
                                line_datas['tax_base'] = float(line_datas['tax_base'])
                                line_datas['tax_base'] = -line_datas['tax_base']

                        else:
                            line_datas['tax_base'] = l['tax_base']
                            if 'R' in l['number']:
                                line_datas['tax_base'] = float(line_datas['tax_base'])
                                line_datas['tax_base'] = -line_datas['tax_base']

                        if 'tax_percent' not in line_datas:
                            line_datas['tax_percent'] = 0

                        if 'tax_amount' not in line_datas:
                            line_datas['tax_amount'] = 0.0

                        if 'tax_amount_rec' not in line_datas:
                            line_datas['tax_amount_rec'] = 0.0

                        if 'tax_amount_ret' not in line_datas:
                            line_datas['tax_amount_ret'] = 0.0
                        if (length <= line_count) or ((l['number'] == lines[line_count]['number'])
                                and l['tax_description'] != lines[line_count]['tax_description'] and
                                lines[line_count]['tax_description'] == "IVA 21% (Bienes)"):

                            if (l['tax_description'] != "IVA 21% (Bienes)") and ('R' not in l['number']):
                                line_datas['amount_total'] = 0.0

                            check = True
                            cslt = self.col_specs_lines_template
                            if 'tax_percent' not in line_datas:
                                line_datas['tax_percent'] = 0

                            if 'tax_amount' not in line_datas:
                                line_datas['tax_amount'] = 0.0

                            if 'tax_amount_rec' not in line_datas:
                                line_datas['tax_amount_rec'] = 0.0

                            if 'tax_amount_ret' not in line_datas:
                                line_datas['tax_amount_ret'] = 0.0

                            if 'R' in l['number']:
                                if 'amount_total' in line_datas:
                                    line_datas['amount_total'] = float(line_datas['amount_total'])
                                    if line_datas['amount_total'] > 0:
                                        line_datas['amount_total'] = -line_datas['amount_total']
                                else:
                                    line_datas['amount_total'] = float(l['amount_total'])
                                    if line_datas['amount_total'] > 0:
                                        line_datas['amount_total'] = -line_datas['amount_total']

                            # Set de data in the line to write the line in the xls
                            for tax in line_datas:
                                l[tax] = line_datas[tax]

                            c_specs = map(lambda x: self.render(x, cslt, 'lines'),
                                          wanted_list)
                            row_data = self.xls_row_template(c_specs,
                                                             [x[0] for x in c_specs])
                            row_pos = self.xls_write_row(ws, row_pos, row_data)
                            line_datas = {}

                    # if the next line is a IVA 0%, then we set the amount_total to 0.0
                    if not check and ((length <= line_count) or ((l['number'] == lines[line_count]['number'])
                            and l['tax_description'] != lines[line_count]['tax_description'] and
                            (lines[line_count]['tax_description'] != "Retenciones a cuenta 19% (Arrendamientos)"
                            and lines[line_count]['tax_description'] != "5.2% Recargo Equivalencia Ventas")
                            and lines[line_count]['tax_description'] != "IVA 21% (Bienes)")):
                        if (l['tax_description'] != "IVA 21% (Bienes)") and ('R' not in l['number']):
                            line_datas['amount_total'] = 0.0

                        cslt = self.col_specs_lines_template
                        if 'tax_percent' not in line_datas:
                            line_datas['tax_percent'] = 0

                        if 'tax_amount' not in line_datas:
                            line_datas['tax_amount'] = 0.0

                        if 'tax_amount_rec' not in line_datas:
                            line_datas['tax_amount_rec'] = 0.0

                        if 'tax_amount_ret' not in line_datas:
                            line_datas['tax_amount_ret'] = 0.0

                        if 'R' in l['number']:
                            if 'amount_total' in line_datas:
                                line_datas['amount_total'] = float(line_datas['amount_total'])
                                if line_datas['amount_total'] > 0:
                                    line_datas['amount_total'] = -line_datas['amount_total']
                            else:
                                line_datas['amount_total'] = float(l['amount_total'])
                                if line_datas['amount_total'] > 0:
                                    line_datas['amount_total'] = -line_datas['amount_total']

                        # Set de data in the line to write the line in the xls
                        for tax in line_datas:
                            l[tax] = line_datas[tax]

                        c_specs = map(lambda x: self.render(x, cslt, 'lines'),
                                      wanted_list)
                        row_data = self.xls_row_template(c_specs,
                                                         [x[0] for x in c_specs])
                        row_pos = self.xls_write_row(ws, row_pos, row_data)
                        line_datas = {}

                    # If the next line isn't the same invoice, we print the line
                    elif not check and ((length <= line_count) or (l['number'] != lines[line_count]['number'])):
                        cslt = self.col_specs_lines_template

                        # We leeok at the previous line to set the total of the actual line
                        if l['number'] == lines[line_count - 2]['number']:
                            if lines[line_count - 2]['tax_description'] == "IVA 21% (Bienes)" \
                                    and (l['tax_description'] != "Retenciones a cuenta 19% (Arrendamientos)"\
                                    and l['tax_description'] != "5.2% Recargo Equivalencia Ventas"):
                                line_datas['amount_total'] = 0.0

                        if 'tax_base' not in line_datas:
                            line_datas['tax_base'] = l['tax_base']

                        if 'tax_percent' not in line_datas:
                            line_datas['tax_percent'] = 0

                        if 'tax_amount' not in line_datas:
                            line_datas['tax_amount'] = 0.0

                        if 'tax_amount_rec' not in line_datas:
                            line_datas['tax_amount_rec'] = 0.0

                        if 'tax_amount_ret' not in line_datas:
                            line_datas['tax_amount_ret'] = 0.0

                        if 'R' in l['number']:
                            if 'amount_total' in line_datas:
                                line_datas['amount_total'] = float(line_datas['amount_total'])
                                if line_datas['amount_total'] > 0:
                                    line_datas['amount_total'] = -line_datas['amount_total']
                            else:
                                line_datas['amount_total'] = float(l['amount_total'])
                                if line_datas['amount_total'] > 0:
                                    line_datas['amount_total'] = -line_datas['amount_total']

                        # Set de data in the line to write the line in the xls
                        for tax in line_datas:
                            l[tax] = line_datas[tax]

                        c_specs = map(lambda x: self.render(x, cslt, 'lines'),
                                      wanted_list)
                        row_data = self.xls_row_template(c_specs,
                                                         [x[0] for x in c_specs])
                        row_pos = self.xls_write_row(ws, row_pos, row_data)
                        line_datas = {}

        def orderByNumber(self, list):
            return list['number']


    AccountInvoiceExportReportXls(
        'report.account.invoice.export.xls', 'xls.invoice.report.wizard',
        parser=AccountInvoiceExportReportXlsParser)

except ImportError:
    pass
