from odoo import models, api


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def _compute_stock_value(self):
        StockMove = self.env['stock.move']
        to_date = self.env.context.get('to_date')

        real_time_product_ids = [product.id for product in self
                                 if product.product_tmpl_id.
                                 valuation == 'real_time']
        if real_time_product_ids:
            self.env['account.move.line'].check_access_rights('read')
            fifo_automated_values = {}
            query = """SELECT aml.product_id, aml.account_id, sum(aml.debit) -
                         sum(aml.credit), sum(quantity), array_agg(aml.id)
                         FROM account_move_line AS aml
                        WHERE aml.product_id IN %%s AND aml.company_id=%%s %s
                     GROUP BY aml.product_id, aml.account_id"""
            params = (tuple(real_time_product_ids),
                      self.env.user.company_id.id)
            if to_date:
                query = query % ('AND aml.date <= %s',)
                params = params + (to_date,)
            else:
                query = query % ('',)
            self.env.cr.execute(query, params=params)

            res = self.env.cr.fetchall()
            for row in res:
                fifo_automated_values[(row[0], row[1])] = \
                    (row[2], row[3], list(row[4]))

        product_values = {product: 0 for product in self}
        product_move_ids = {product: [] for product in self}
        if to_date:
            domain = [('product_id', 'in', self.ids),
                      ('date', '<=', to_date)] + \
                StockMove._get_all_base_domain()
            for move in StockMove.search(domain).\
                    with_context(prefetch_fields=False):
                product_values[move.product_id] += move.value
                product_move_ids[move.product_id].append(move.id)
        else:
            domain = [('product_id', 'in', self.ids)] + \
                StockMove._get_all_base_domain()
            for move in StockMove.search(domain).\
                    with_context(prefetch_fields=False):
                product_values[move.product_id] += move.remaining_value
                product_move_ids[move.product_id].append(move.id)

        for product in self:
            qty_available = product.with_context(company_owned=True,
                                                 owner_id=False).qty_available
            if product.cost_method in ['standard', 'average']:
                price_used = product.standard_price
                if to_date:
                    price_used = product.get_history_price(
                        self.env.user.company_id.id,
                        date=to_date,
                    )
                product.stock_value = price_used * qty_available
                product.qty_at_date = qty_available
            elif product.cost_method == 'fifo':
                if product.product_tmpl_id.valuation == 'manual_periodic':
                    product.stock_value = product_values[product]
                    product.qty_at_date = qty_available
                    product.stock_fifo_manual_move_ids = \
                        StockMove.browse(product_move_ids[product])
                elif product.product_tmpl_id.valuation == 'real_time':
                    valuation_account_id = product.categ_id.\
                        property_stock_valuation_account_id.id
                    value, quantity, aml_ids = \
                        fifo_automated_values.get((product.id,
                                                   valuation_account_id)) \
                        or (0, 0, [])
                    product.stock_value = value
                    product.qty_at_date = qty_available
                    product.stock_fifo_real_time_aml_ids = \
                        self.env['account.move.line'].browse(aml_ids)
