from odoo import models, fields, api, _


class RetryAmazonRefunds(models.TransientModel):
    _name = 'retry.amazon.refunds.wizard'

    @api.multi
    def _get_active_refunds(self):
        amazon_refund_obj = self.env['amazon.sale.refund']
        amazon_refund_ids = self.env.context.get('active_ids', False)
        wiz_lines=[]
        for refund in amazon_refund_obj.search([('id', 'in', amazon_refund_ids),('state','=','error')]):
            wiz_lines.append({'refund_id': refund.id})
        return wiz_lines

    amazon_refund_line_ids = fields.One2many('retry.amazon.refunds.lines', "wizard_id", string='Amazon Orders', default=_get_active_refunds)

    @api.multi
    def retry_refunds(self):
        if self.amazon_refund_line_ids:
            self.amazon_refund_line_ids.mapped('refund_id').retry_refund()




class RetryAmazonOrdersLines(models.TransientModel):
    _name = 'retry.amazon.refunds.lines'

    wizard_id = fields.Many2one('retry.amazon.refunds.wizard')
    refund_id = fields.Many2one('amazon.sale.refund', "Amazon Refund")

