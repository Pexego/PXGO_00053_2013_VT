# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from dateutil.relativedelta import relativedelta


class ResPartnerRappelRel(models.Model):

    _inherit = 'res.partner.rappel.rel'

    def _get_next_period(self):
        self.ensure_one()
        if self.last_settlement_date and \
                self.last_settlement_date > self.date_start:
            date_start = fields.Date.from_string(self.last_settlement_date) + \
                relativedelta(days=1)
        else:
            date_start = fields.Date.from_string(self.date_start)

        date_stop = date_start + relativedelta(
            months=self.PERIODICITIES_MONTHS[self.periodicity], days=-1)
        if self.date_end:
            date_end = fields.Date.from_string(self.date_end)
            if date_end < date_stop:
                date_stop = date_end

        if date_start != date_stop:
            period = [date_start, date_stop]
        else:
            period = False
        return period

    def _get_excluded_invoice_lines(self, period):
        """
        Returns excluded invoice lines from rappel because of the definition of the rappel

        Parameter:
        ---------
        period: List[datetime]
            Invoice search period

        Returns:
        -------
            List[Int]
        Excluded invoice lines
        """
        if self.rappel_id.global_application:
            # if rappel has global_application there is nothing excluded
            return []
        invoices, refunds = self._get_invoices_for_rappel(period)
        products = self.rappel_id.get_products()
        domain_lines = [('invoice_id', 'in', refunds.ids + invoices.ids),
                        ('product_id', 'not in', products)]

        pricelist_ids = tuple(self.rappel_id.pricelist_ids.ids)
        if pricelist_ids:
            domain_lines += [('sale_line_ids.order_id.pricelist_id', 'in', pricelist_ids)]

        invoice_lines = self.env['account.invoice.line'].search(domain_lines)
        return invoice_lines.ids

    def _get_invoices_for_rappel(self, period):
        """
        Returns invoices related to the rappel

        Parameter:
        ---------
        period: List[datetime]
            Invoice search period
        Returns:
        -------
            Tuple[account.invoice]
        Invoices and refunds
        """
        search_invoices = self.env['account.invoice'].search
        company_id = self.rappel_id.company_id.id
        invoices = search_invoices(
            [('type', '=', 'out_invoice'),
             ('date_invoice', '>=', period[0]),
             ('date_invoice', '<=', period[1]),
             ('state', 'in', ['open', 'paid']),
             ('commercial_partner_id', '=', self.partner_id.id),
             ('company_id', '=', company_id)])
        refunds = search_invoices(
            [('type', '=', 'out_refund'),
             ('date_invoice', '>=', period[0]),
             ('date_invoice', '<=', period[1]),
             ('state', 'in', ['open', 'paid']),
             ('commercial_partner_id', '=', self.partner_id.id),
             ('company_id', '=', company_id)])
        return invoices, refunds

    def _get_invoices(self, period, products):
        super()._get_invoices(period, products)
        invoices, refunds = self._get_invoices_for_rappel(period)
        pricelist_ids = tuple(self.rappel_id.pricelist_ids.ids)
        domain_lines = []
        if pricelist_ids:
            domain_lines += [('sale_line_ids.order_id.pricelist_id','in',pricelist_ids)]
        # Si el rappel afecta al catalago entero,
        # no hacer la comprobacion por producto
        if self.rappel_id.global_application:
            refund_lines = self.env['account.invoice.line'].search(
                [('invoice_id', 'in', refunds.ids)] + domain_lines)
            invoice_lines = self.env['account.invoice.line'].search(
                [('invoice_id', 'in', invoices.ids)]+ domain_lines)
        else:
            refund_lines = self.env['account.invoice.line'].search(
                [('invoice_id', 'in', refunds.ids),
                 ('product_id', 'in', products)]+ domain_lines)
            invoice_lines = self.env['account.invoice.line'].search(
                [('invoice_id', 'in', invoices.ids),
                 ('product_id', 'in', products)]+ domain_lines)

        return invoice_lines, refund_lines

    def get_orders(self):
        return self.env['sale.order'].search(
            [('partner_id', 'child_of', self.partner_id.id),
             ('state', 'in', ('done', 'sale'))])

    def _calculate_pending_to_invoice(self):
        products = self.rappel_id.get_products()
        orders = self.get_orders()
        order_lines = self.env['sale.order.line'].search(
            [('order_id', 'in', orders.ids),
             ('product_id', 'in', products),
             ('invoice_status', '=', 'to invoice'),
             ('no_rappel', '=', False)])
        return sum([x.qty_to_invoice * (x.price_subtotal / (x.product_uom_qty or 1)) for x in order_lines])

    @staticmethod
    def _get_total_amount_for_lines(field, invoice_lines, refund_lines):
        """
        Calculates total amount for given lines and field.
        Total is the difference of the summations of invoice_lines and refund_lines.

        Parameters:
        ----------
        field: str
            Rappel field from where to calculate summations
        invoice_lines: account.invoice.line
            Lines from invoices
        refund_lines: account.invoice.line
            Lines from refund
        Returns:
        -------
            Float
        Difference of the summation of invoice_lines and the summation of refund_lines
        """
        invoice_lines_for_rappel_quantity = invoice_lines.filtered(
            lambda line: not line.no_rappel
        )
        refund_lines_for_rappel_quantity = refund_lines.filtered(
            lambda line: not line.no_rappel
        )
        total = sum(invoice_lines_for_rappel_quantity.mapped(field)) - \
                sum(refund_lines_for_rappel_quantity.mapped(field))

        return total

    def _compute_rappel_fixed_mode(self, rappel_info, field, invoice_lines, refund_lines):
        """
        Calculates total_rappel and goal_percentage for fixed rappels

        Parameters:
        ----------
        rappel_info: Dict[str, Any]
            Rappel fields in dictionary format
        field: str
            Rappel field to calculate total amount
        invoice_lines: account.invoice.line
            Lines from invoices
        refund_lines: account.invoice.line
            Lines from refund

        Returns:
        -------
            Tuple[Float, Float]
        Amounts of total_rappel and goal_percentage
        """
        total_rappel = 0.0
        total_rappel_est = 0.0
        goal_percentage = 0
        if self.rappel_id.calc_amount == 'qty':
            total_rappel = self.rappel_id.fix_qty
        else:
            total = self._get_total_amount_for_lines(field, invoice_lines, refund_lines)
            pending_to_invoice = self._calculate_pending_to_invoice()
            total_est = total + pending_to_invoice
            rappel_info["curr_qty"] = total
            rappel_info["curr_qty_pickings"] = pending_to_invoice
            if total:
                total_rappel = total * self.rappel_id.fix_qty / 100.0
            if total_est:
                total_rappel_est = total_est * self.rappel_id.fix_qty / 100.0

        rappel_info['amount'] = total_rappel
        rappel_info['amount_est'] = total_rappel_est
        return total_rappel, goal_percentage

    def _compute_rappel_variable_mode(self, rappel_info, field, invoice_lines, refund_lines):
        """
        Calculates total_rappel and goal_percentage for variable rappels

        Parameters:
        ----------
        rappel_info: Dict[str, Any]
            Rappel fields in dictionary format
        field: str
            Rappel field to calculate total amount
        invoice_lines: account.invoice.line
            Lines from invoices
        refund_lines: account.invoice.line
            Lines from refund

        Returns:
        -------
            Tuple[Float, Float]
        Amounts of total_rappel and goal_percentage
        """
        total_rappel = 0.0
        goal_percentage = 0
        if self.rappel_id.qty_type != 'value':
            field = 'quantity'
        total = self._get_total_amount_for_lines(field, invoice_lines, refund_lines)
        pending_to_invoice = self._calculate_pending_to_invoice()
        total_est = total + pending_to_invoice
        rappel_info["curr_qty"] = total
        rappel_info["curr_qty_pickings"] = pending_to_invoice

        if self.partner_id.invoice_type_id.name in \
            ('Mensual', 'Quincenal', 'Semanal') and total_est:
            rappel_info, goal_percentage, total_rappel = self.compute_total(
                self, total_est, rappel_info, True)
        else:
            rappel_info['amount_est'] = 0.0

        if total:
            rappel_info, goal_percentage, total_rappel = self.compute_total(
                self, total, rappel_info, False)
        else:
            rappel_info['amount'] = 0.0
        return total_rappel, goal_percentage

    @api.model
    def compute(self, period, invoice_lines, refund_lines, tmp_model=False):
        rappel_calculated_obj = self.env['rappel.calculated']
        for rappel in self:
            excluded_line_ids = rappel._get_excluded_invoice_lines(period)
            rappel_info = {'rappel_id': rappel.rappel_id.id,
                           'partner_id': rappel.partner_id.id,
                           'date_start': period[0],
                           'amount': 0.0,
                           'amount_est': 0.0,
                           'date_end': period[1],
                           'excluded_invoice_line_ids': [(6, 0, excluded_line_ids)]}
            field = 'price_subtotal'
            if rappel.rappel_id.calc_mode == 'fixed':
                total_rappel, goal_percentage = rappel._compute_rappel_fixed_mode(
                    rappel_info,
                    field,
                    invoice_lines,
                    refund_lines
                )
            else:
                total_rappel, goal_percentage = rappel._compute_rappel_variable_mode(
                    rappel_info,
                    field,
                    invoice_lines,
                    refund_lines
                )
            total_invoice_ids = [(6, 0, (invoice_lines + refund_lines).ids)]
            rappel_info['invoice_line_ids'] = total_invoice_ids

            if period[1] < fields.Date.from_string(fields.Date.today()):
                if total_rappel:
                    rappel_calculated_obj.create({
                        'partner_id': rappel.partner_id.id,
                        'date_start': period[0],
                        'date_end': period[1],
                        'quantity': total_rappel,
                        'rappel_id': rappel.rappel_id.id,
                        'goal_percentage': goal_percentage,
                        'invoice_line_ids': total_invoice_ids,
                        'excluded_invoice_line_ids': [(6, 0, excluded_line_ids)]
                    })
                    if rappel.rappel_id.discount_voucher and total_rappel > 0:
                        rappel_to_invoice = []
                        rappel_old = rappel_calculated_obj.search_read(
                            [('partner_id', '=', rappel.partner_id.id),
                             ('rappel_id.discount_voucher', '=', True),
                             ('invoice_id', '=', False)], ['id', 'quantity'])
                        amount_total = 0
                        for rp in rappel_old:
                            rappel_to_invoice.append(rp['id'])
                            amount_total += rp['quantity']
                        if amount_total > 0:
                            rappel_calculated_obj.create_rappel_invoice(
                                rappel_to_invoice)
                rappel.last_settlement_date = period[1]
            else:
                if tmp_model and rappel_info:
                    self.env['rappel.current.info'].create(rappel_info)

        return True

    def compute_total(self, rappel, total, rappel_info, estimated):
        total_rappel = 0.0
        section = self.env['rappel.section'].search(
            [('rappel_id', '=', rappel.rappel_id.id),
             ('rappel_from', '<=', total),
             ('rappel_until', '>=', total)])
        if not section:
            section = self.env['rappel.section'].search(
                [('rappel_id', '=', rappel.rappel_id.id),
                 ('rappel_from', '<=', total),
                 ('rappel_until', '=', False)],
                order='rappel_from desc', limit=1)
        if section:
            goal_percentage = 100
        else:
            # Check if goal percentage is more than 80% to get the rappel
            section = self.env['rappel.section'].search(
                [('rappel_id', '=', rappel.rappel_id.id),
                 ('rappel_from', '<=', total / 0.8),
                 ('rappel_from', '>', total)])
            if section.rappel_from:
                goal_percentage = (total / section.rappel_from) * 100
            else:
                goal_percentage = 0

        if not section:
            if estimated:
                rappel_info['amount_est'] = 0.0
            else:
                rappel_info['amount'] = 0.0
        else:
            rappel_info['section_id'] = section.id
            section = section[0]
            if rappel.rappel_id.calc_amount == 'qty':
                total_rappel = section.percent
            else:
                total_rappel = total * section.percent / 100.0
                if estimated:
                    rappel_info['amount_est'] = total_rappel
                else:
                    rappel_info['amount'] = total_rappel
                    rappel_info['amount_est'] = total_rappel

        return rappel_info, goal_percentage, total_rappel
