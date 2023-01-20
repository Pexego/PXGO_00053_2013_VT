from odoo import fields, models, api


class ProductEquivalentWizard(models.TransientModel):
    """ Wizard to create Equivalent Products.
    """

    _name = "product.equivalent.wizard"
    _description = 'Wizard to create equivalent products'

    equivalent_product_type = \
        fields.Selection([
            ('exist', 'Product'),
            ('text', 'Text'), ], string="Equivalent Product Type")
    product_id = fields.Many2one('product.product', 'Product', domain=lambda self:self.get_products_domain())
    product_name = fields.Char('Product')

    def get_products_domain(self):
        product = self.env['product.product'].browse(self.env.context.get('active_id'))
        return [('id','not in', product.equivalent_products.ids)]

    def action_done(self):
        """
            This method allows you to create an equivalent product of different types (text or existing product)
        :return: product equivalent created
        """
        product_id = self.env.context.get('active_id')
        if not self.product_name:
            self.product_name = self.product_id.default_code
        res = self.env['product.equivalent'].create(
            {'product_id': product_id, 'equivalent_id': self.product_id.id, 'product_name': self.product_name})
        return res

    def action_done_add_another(self):
        """
            This method allows you to create an equivalent product of different types (text or existing product)
            and reopen wizard in order to create more equivalent products
        :return: An act-multi with two actions. Update products equivalent tree and reopen the wizard
        """
        res = self.action_done()
        if res:
            action = self.env.ref('associated_products.action_view_add_equivalent_product_wizard').read()[0]
            action['context'] = self.env.context
            return {
                'type': 'ir.actions.act_multi',
                'actions': [
                    {'type': 'ir.actions.act_view_reload'},
                    action
                ]
            }

