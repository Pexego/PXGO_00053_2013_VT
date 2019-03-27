from odoo import models, api, tools


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.model
    def invoice_line_move_line_get(self):
        res = super().invoice_line_move_line_get()
        if self.type == 'in_invoice':
            for line_data in res:
                total_qty = 0.0
                moves_price = 0.0
                i_line_id = line_data['invl_id']
                i_line = self.env['account.invoice.line'].browse(i_line_id)
                selected_move = False
                if i_line.move_line_ids and \
                        i_line.product_id.valuation == 'real_time':
                    for move in i_line.move_line_ids.\
                            filtered(lambda x: x.picking_type_code ==
                                     'incoming'):
                        selected_move = move
                        qty = move.product_qty
                        total_qty += qty
                        if move.product_id.cost_method in ['average', 'fifo'] \
                                and move._get_price_unit():
                            price_unit = move._get_price_unit()
                            moves_price += price_unit * qty
                        else:
                            price_unit = move.product_id.standard_price
                            moves_price += price_unit * qty
                    line_data['price_move'] = moves_price
                    if selected_move and selected_move.purchase_line_id and \
                            selected_move.picking_id and \
                            selected_move.picking_id.backorder_id:
                        line_data['create_date'] = \
                            selected_move._get_origin_create_date()
                    else:
                        line_data['create_date'] = selected_move.create_date
            res.extend(self._cost_diff_move_lines(res))
        return res

    @api.model
    def _cost_diff_move_lines(self, res):
        company_currency = self.company_id.currency_id
        diff_res = []
        # calculate and write down the possible price difference
        # between invoice price and product price
        for line in res:
            i_line_id = line['invl_id']
            i_line = self.env['account.invoice.line'].browse(i_line_id)
            fpos = i_line.invoice_id.fiscal_position_id
            # get the price difference account at the product
            acc = i_line.product_id.property_account_creditor_price_difference
            if not acc:
                # if not found on the product get the price difference
                # account at the category
                acc = i_line.product_id.categ_id.\
                    property_account_creditor_price_difference_categ
            acc = fpos.map_account(acc).id
            a = i_line.product_id.product_tmpl_id.\
                get_product_accounts(fiscal_pos=fpos)['stock_input'].id
            if 'price_move' in line and line['price_move'] != \
                    i_line.price_subtotal and acc:
                if tools.float_compare(i_line.invoice_id.currency_id.id,
                                       company_currency.id, 2):
                    price_subtotal = i_line.invoice_id.currency_id.\
                        with_context(date=line['create_date']).\
                        compute(line['price_move'], company_currency,
                                round=True)
                else:
                    price_subtotal = i_line.price_subtotal

                price_diff = \
                    price_subtotal - line['price_move']
                if tools.float_is_zero(price_diff, 2):
                    continue

                diff_res.append({
                    'type': 'src',
                    'name': i_line.name.split('\n')[0][:64],
                    'price_unit': price_diff,
                    'quantity': line['quantity'],
                    'price': price_diff,
                    'account_id': acc,
                    'product_id': line['product_id'],
                    'uom_id': line['uom_id'],
                    'account_analytic_id': line['account_analytic_id']
                    })
                diff_res.append({
                    'type': 'src',
                    'name': i_line.name.split('\n')[0][:64],
                    'price_unit': -price_diff,
                    'quantity': line['quantity'],
                    'price': -price_diff,
                    'account_id': a,
                    'product_id': line['product_id'],
                    'uom_id': line['uom_id'],
                    'account_analytic_id': line['account_analytic_id']
                    })
        return diff_res
