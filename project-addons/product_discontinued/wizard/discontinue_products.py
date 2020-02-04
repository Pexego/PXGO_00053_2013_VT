from odoo import models, fields, api, exceptions, _

class CreatePickingMove(models.TransientModel):

    _name = 'discontinue.products.wizard'


    @api.model
    def _get_products(self):
        product_ids = self.env.context.get('active_ids', [])
        products = self.env['product.product'].search([('id','in',product_ids)])
        wiz_lines = []
        for product in products:
            wiz_lines.append({'product_id': product})
        return wiz_lines

    product_ids = fields.One2many('discontinue.product.info.wizard', 'wizard_id', default=_get_products)


    @api.multi
    def action_discontinue_products(self):
        context = self.env.context
        if not context.get('active_ids', False):
            return
        for product in self.env['product.product'].browse(context.get('active_ids')):
            try:
                product.write({'discontinued': True})
            except Exception as ex :
                message = product.default_code +" --> " + str(ex)[2:-8]
                self.env.user.notify_warning(message = message, sticky=True)
                pass

class ProductProductWizard(models.TransientModel):

    _name = 'discontinue.product.info.wizard'

    wizard_id = fields.Many2one('discontinue.products.wizard', 'wizard')

    product_id = fields.Many2one('product.product', 'Product')

