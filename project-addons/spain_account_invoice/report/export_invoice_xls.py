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

_ir_translation_name = 'account.invoice.export.xls'


class AccountInvoiceExportReportXlsParser(report_sxw.rml_parse):
    def set_context(self, objects, data, ids, report_type=None):
        super(AccountInvoiceExportReportXlsParser, self).set_context(
            objects, data, ids, report_type=report_type)
        invoice_pool = self.pool['account.invoice']
        invoice_type = data['invoice_type']
        wanted_list = invoice_pool._report_xls_fields(self.cr, self.uid, invoice_type, self.context)
        self.invoice_type = data['invoice_type']
        self.country_group = data['country_group']
        self.company_id = data['company_id']
        self.period_ids = data['period_ids']
        self.localcontext.update({
            'wanted_list': wanted_list
        })

    def __init__(self, cr, uid, name, context=None):
        if context is None:
            context = {}
        super(AccountInvoiceExportReportXlsParser, self).__init__(
            cr, uid, name, context=context)
        invoice_pool = self.pool['account.invoice']
        template_changes = invoice_pool._report_xls_template(cr, uid, context)
        self.localcontext.update({
            'datetime': datetime,
            'title': self._title,
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
        sql = ""
        if self.period_ids:
            additional_where += self.cr.mogrify(
                "AND i.period_id in %s", (tuple(self.period_ids),))

        if self.invoice_type == 'out_invoice':
            sql = (
                "SELECT i.id as invoice_id, "
                "i.number as number, "
                "i.date_invoice as date_invoice, "
                "p.vat as partner_vat, "
                "CASE WHEN p.parent_id IS NULL THEN "
                "   p.name "
                "WHEN p.parent_id IS NOT NULL THEN "
                "   p2.name "
                "END "
                "as partner_name, "
                "p.id as partner_id, "
                "t.tax_amount as tax_amount, "
                "t.base_amount as tax_base, "
                "it.value as country_name, "
                "t.name as tax_description, "
                "afp.name as fiscal_name, "
                "i.type as type "
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
                "    AND i.company_id = " + str(self.company_id) +
                "    AND substring(pr.value_reference FROM '[a-z\.]+') = 'account.fiscal.position' "
                "    AND afp.company_id = " + str(self.company_id) +
                "    AND it.lang = 'es_ES' "
                "    AND it.module = 'base' "
                " {} "
                "ORDER BY date_invoice ASC").format(additional_where)

        elif self.invoice_type == 'in_invoice':
            additional_where += self.cr.mogrify(
                "AND rcr.res_country_group_id = %s", (tuple(self.country_group),))

            sql = (
                "SELECT i.id as invoice_id, "
                "i.number as number, "
                "i.date_invoice as date_invoice, "
                "i.supplier_invoice_number as supplier_number, "
                "p.vat as partner_vat, "
                "CASE WHEN p.parent_id IS NULL THEN "
                "   p.name "
                "WHEN p.parent_id IS NOT NULL THEN "
                "   p2.name "
                "END "
                "as partner_name, "
                "p.id as partner_id, "
                "t.tax_amount as tax_amount, "
                "t.base_amount as tax_base, "
                "it.value as country_name, "
                "t.name as tax_description, "
                "i.type as type "
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
                "LEFT JOIN ir_translation it "
                "   ON (c.name = it.src)) "
                "LEFT JOIN res_country_res_country_group_rel rcr "
                "   ON (rcr.res_country_id = c.id) "
                "WHERE (i.type = 'in_refund' "
                "    OR i.type = 'in_invoice') "
                "    AND (i.state = 'paid' "
                "    OR i.state = 'open') "
                "    AND i.number NOT LIKE '%_ef%' "
                "    AND i.company_id = 1"
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
            spec_lines_template = {}
            if invoice_type == 'out_invoice':
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
            elif invoice_type == 'in_invoice':
                spec_lines_template = {
                    'date_invoice': {
                        'header': [1, 20, 'text', _render("_('Fecha factura')")],
                        'lines': [1, 0, 'text', _render("(l['date_invoice'])")],
                        'totals': [1, 0, 'text', None]},
                    'number': {
                        'header': [1, 15, 'text', _render("_('N de factura')")],
                        'lines': [1, 0, 'text', _render("l['number']")],
                        'totals': [1, 0, 'text', None]},
                    'supplier_number': {
                        'header': [1, 15, 'text', _render("_('N de factura del proveedor')")],
                        'lines': [1, 0, 'text', _render("l['supplier_number']")],
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
                    'tax_description': {
                        'header': [1, 40, 'text', _render("_('Líneas de impuestos/Descripción impuesto')")],
                        'lines': [1, 0, 'text', _render("l['tax_description']")],
                        'totals': [1, 0, 'text', None]},
                    'tax_amount': {
                        'header': [1, 20, 'text', _render("_('Cuota IVA')")],
                        'lines': [1, 0, 'number', _render("l['tax_amount']"),
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
                }

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

        def _compute_amounts_in_invoice_currency(self, cr, uid, ids, user_id, invoice_id):
            """Compute the amounts in the currency of the invoice
            """
            currency_obj = self.pool.get('res.currency')
            currency_rate_obj = self.pool.get('res.currency.rate')
            user = self.pool['res.partner'].browse(cr, uid, user_id)
            invoice = self.pool['account.invoice'].browse(cr, uid, invoice_id)
            invoice_currency_id = invoice.currency_id.id
            base_currency_id = user.company_id.currency_id.id
            ctx = {'date': invoice.date_invoice}
            price_total = currency_obj.compute(cr, uid, invoice_currency_id, base_currency_id, invoice.amount_total,
                                               context=ctx)
            amount_total = float(price_total)
            return amount_total

        def _compute_tax_amounts_in_invoice_currency(self, cr, uid, ids, user_id, invoice_id, tax_amount_origin):
            """Compute the tax_amounts in the currency of the invoice
            """
            currency_obj = self.pool.get('res.currency')
            currency_rate_obj = self.pool.get('res.currency.rate')
            user = self.pool['res.partner'].browse(cr, uid, user_id)
            invoice = self.pool['account.invoice'].browse(cr, uid, invoice_id)
            invoice_currency_id = invoice.currency_id.id
            base_currency_id = user.company_id.currency_id.id
            ctx = {'date': invoice.date_invoice}
            price_total = currency_obj.compute(cr, uid, invoice_currency_id, base_currency_id, tax_amount_origin,
                                               context=ctx)
            tax_amount = float(price_total)
            return tax_amount

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
            if data['invoice_type'] == 'out_invoice':
                for o in objects:
                    length = len(_p.lines(o))
                    lines = sorted(_p.lines(o), key=self.orderByNumber)
                    for l in lines:
                        amount_total = self._compute_amounts_in_invoice_currency(self.cr, self.uid, [], l['partner_id'],
                                                                                 l['invoice_id'])

                        check = False
                        line_count += 1
                        if row_pos >= 65536:
                            ws_count += 1
                            new_sheet_name = "%s_%s" % (sheet_name, ws_count)
                            ws, row_pos = self.get_new_ws(_p, _xs, new_sheet_name,
                                                          wb)

                        # We separate the taxes to display all in diferent columns.
                        # If the invoice is a refund, we need to display the amount
                        # in negative

                        if l['tax_description'] == "5.2% Recargo Equivalencia Ventas":
                            if 'tax_percent' not in line_datas:
                                line_datas['tax_percent'] = 0

                            line_datas['amount_total'] = amount_total
                            if 'refund' in l['type']:
                                line_datas['amount_total'] = -line_datas['amount_total']

                            line_datas['tax_amount_rec'] = l['tax_amount']
                            line_datas['tax_base'] = l['tax_base']

                        elif l['tax_description'] == "Retenciones a cuenta 19% (Arrendamientos)":
                            if 'tax_percent' not in line_datas:
                                line_datas['tax_percent'] = 0

                            line_datas['amount_total'] = amount_total
                            if 'refund' in l['type']:
                                line_datas['amount_total'] = -line_datas['amount_total']

                            line_datas['tax_amount_ret'] = l['tax_amount']
                            line_datas['tax_base'] = l['tax_base']

                        elif l['tax_description'] == "IVA 21% (Bienes)":
                            line_datas['tax_percent'] = 21.00
                            line_datas['tax_description'] = l['tax_description']
                            line_datas['tax_amount'] = l['tax_amount']
                            line_datas['tax_base'] = l['tax_base']

                        else:
                            if not l['tax_base']:
                                l['tax_base'] = 0.0

                        # If the previous line of the xls is the same invoice and their taxes are the
                        # same, the code recalculate the tax_base
                            if (length <= line_count) or ((l['number'] == lines[line_count - 2]['number'])
                                    and l['tax_description'] == lines[line_count - 2]['tax_description']):
                                line_datas['tax_base'] = l['tax_base'] + lines[line_count - 2]['tax_base']
                                if 'refund' in l['type']:
                                    line_datas['tax_base'] = float(line_datas['tax_base'])
                                    line_datas['tax_base'] = -line_datas['tax_base']

                            else:
                                line_datas['tax_base'] = l['tax_base']

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

                                if 'refund' in l['type']:
                                    if 'amount_total' in line_datas:
                                        line_datas['amount_total'] = float(line_datas['amount_total'])
                                        if line_datas['amount_total'] > 0:
                                            line_datas['amount_total'] = -line_datas['amount_total']
                                    else:
                                        line_datas['amount_total'] = amount_total
                                        if line_datas['amount_total'] > 0:
                                            line_datas['amount_total'] = -line_datas['amount_total']

                                elif 'amount_total' not in line_datas:
                                    line_datas['amount_total'] = amount_total

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
                            if (l['tax_description'] != "IVA 21% (Bienes)") or ('R' in l['number']):
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

                            if 'refund' in l['type']:
                                if 'amount_total' in line_datas:
                                    line_datas['amount_total'] = float(line_datas['amount_total'])
                                    if line_datas['amount_total'] > 0:
                                        line_datas['amount_total'] = -line_datas['amount_total']
                                else:
                                    line_datas['amount_total'] = amount_total
                                    if line_datas['amount_total'] > 0:
                                        line_datas['amount_total'] = -line_datas['amount_total']

                            elif 'amount_total' not in line_datas:
                                line_datas['amount_total'] = amount_total

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

                            if 'refund' in l['type']:
                                if 'amount_total' in line_datas:
                                    line_datas['amount_total'] = float(line_datas['amount_total'])
                                    if line_datas['amount_total'] > 0:
                                        line_datas['amount_total'] = -line_datas['amount_total']
                                else:
                                    line_datas['amount_total'] = amount_total
                                    if line_datas['amount_total'] > 0:
                                        line_datas['amount_total'] = -line_datas['amount_total']

                            elif 'amount_total' not in line_datas:
                                line_datas['amount_total'] = amount_total

                                # Set de data in the line to write the line in the xls
                            for tax in line_datas:
                                l[tax] = line_datas[tax]

                            c_specs = map(lambda x: self.render(x, cslt, 'lines'),
                                          wanted_list)
                            row_data = self.xls_row_template(c_specs,
                                                             [x[0] for x in c_specs])
                            row_pos = self.xls_write_row(ws, row_pos, row_data)
                            line_datas = {}

            elif data['invoice_type'] == 'in_invoice':
                for o in objects:
                    length = len(_p.lines(o))
                    lines = sorted(_p.lines(o), key=self.orderByNumber)
                    for l in lines:
                        amount_total = self._compute_amounts_in_invoice_currency(self.cr, self.uid, [], l['partner_id'],
                                                                                 l['invoice_id'])
                        line_count += 1
                        if row_pos >= 65536:
                            ws_count += 1
                            new_sheet_name = "%s_%s" % (sheet_name, ws_count)
                            ws, row_pos = self.get_new_ws(_p, _xs, new_sheet_name,
                                                          wb)

                        l['tax_amount'] = self._compute_tax_amounts_in_invoice_currency(self.cr, self.uid, [], l['partner_id'],
                                                                                   l['invoice_id'], l['tax_amount'])

                        if 'refund' in l['type']:
                            if amount_total > 0:
                                l['amount_total'] = -amount_total
                        else:
                            l['amount_total'] = amount_total

                        l['tax_amount_ret'] = 0.0
                        if l['tax_description'] == 'Retenciones IRPF 15%':
                            l['tax_amount_ret'] = -float(l['tax_amount'])
                            l['tax_amount'] = 0.0
                            l['tax_base'] = 0.0
                            l['amount_total'] = 0.0
                        elif l['tax_description'] == 'IVA 21% Intracomunitario. Bienes corrientes (2)':
                            l['tax_amount'] = -l['tax_amount']
                        elif l['tax_description'] == "Retenciones 19% (Arrendamientos)":
                            if 'tax_percent' not in l:
                                l['tax_percent'] = 0

                            l['amount_total'] = amount_total
                            if 'refund' in l['type']:
                                l['amount_total'] = -l['amount_total']

                            l['tax_amount_ret'] = -float(l['tax_amount'])
                            l['tax_amount'] = 0.0
                            l['tax_base'] = 0.0

                        if (length < line_count) and (l['number'] == lines[line_count]['number']):
                            if l['tax_description'] != '21% IVA soportado (operaciones corrientes)':
                                l['amount_total'] = 0.0
                        elif (length < line_count) or (l['number'] == lines[line_count-2]['number']):
                            if l['tax_description'] != '21% IVA soportado (operaciones corrientes)':
                                l['amount_total'] = 0.0

                        cslt = self.col_specs_lines_template
                        c_specs = map(lambda x: self.render(x, cslt, 'lines'),
                                      wanted_list)
                        row_data = self.xls_row_template(c_specs,
                                                         [x[0] for x in c_specs])
                        row_pos = self.xls_write_row(ws, row_pos, row_data)



        def orderByNumber(self, list):
            return list['number']


    AccountInvoiceExportReportXls(
        'report.account.invoice.export.xls', 'xls.invoice.report.wizard',
        parser=AccountInvoiceExportReportXlsParser)

except ImportError:
    pass
