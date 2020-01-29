from odoo import api, fields, models, _


class Inventory(models.Model):
    _inherit = "stock.inventory"

    def action_done(self):
        res = super(Inventory, self).action_done()
        max_diff = self.env['ir.config_parameter'].sudo().get_param('max_diff_stock')
        lines=self.env['stock.inventory.line']
        for line in self.mapped('line_ids'):
            if abs(line.theoretical_qty - line.product_qty)>=int(max_diff):
                lines+=line
        if lines:
            ctx={'lines':lines,
                 'lang': 'es_ES',
                 'max_diff': int(max_diff)}
            template = self.env.ref('stock_custom.send_mail_stock_inventory')
            template.with_context(ctx).send_mail(self.id)
        return res



