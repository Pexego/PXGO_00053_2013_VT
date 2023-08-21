from odoo import models, fields, _


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def get_last_purchase_price(self):
        """
        Calculates last purchase price of the product.
        If there is no last purchase raises NoLastPurchaseException

        Return:
        ------
        Float
        """
        res = self.env['purchase.order.line'].search([('product_id', '=', self.id)])
        res_filtered = res.filtered(lambda self: self.order_id.state in ['purchase', 'purchase_order'])
        if not res_filtered:
            raise NoLastPurchaseException(self.default_code)
        last_line = res_filtered.sorted(key=lambda self: self.order_id.write_date, reverse=True)[0]
        return last_line.price_unit

    @staticmethod
    def calculate_product_price_variation(old_price, new_price):
        """
        Returns the percentage of variation between old price and new_price

        Parameters:
        ----------
        old_price: Float
            Base price to calculate the percentage variation
        new_price: Float
            Price to calculate the difference that gives the percentage

        Return:
        ------
        Float
            100 * abs(old_price - new_price) / old_price
        """
        return abs(old_price - new_price) / old_price * 100


class NoLastPurchaseException(Exception):
    """
    This error should be raised when a product does not belong to any purchase order line
    """
    def __init__(self, product_code, *args):
        self.message = _('The product "%s" has not last purchase') % product_code

    def __str__(self):
        return 'NoLastPurchaseException: ' + self.message
