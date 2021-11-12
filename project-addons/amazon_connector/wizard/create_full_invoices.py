from odoo import models, fields, api, _
from stdnum.eu import vat
from zeep.exceptions import Fault


class CreateFullInvoicesAmazonWizard(models.TransientModel):
    _name = 'create.full.invoices.amazon.wizard'

    @api.multi
    def _get_active_orders(self):
        amazon_orders_obj = self.env['amazon.sale.order']
        amazon_orders_ids = self.env.context.get('active_ids', False)
        wiz_lines = []
        for order in amazon_orders_obj.search([('id', 'in', amazon_orders_ids)]):
            wiz_lines.append({'amazon_order': order.id})
        return wiz_lines

    amazon_orders = fields.One2many('create.full.invoices.amazon.lines', "wizard_id", string='Amazon Orders',
                                    default=_get_active_orders)

    @api.multi
    def create_invoices(self):
        amazon_orders = self.env['amazon.sale.order'].search(
            [('id', 'in', self.env.context.get('active_ids', False)), ('state', 'in', ['warning','error']),
             ('partner_vat', '!=', False)])
        for amazon_order in amazon_orders:
            read = False
            vies_response = False
            if not(amazon_order.billing_country_id and amazon_order.billing_name and amazon_order.billing_address):
                while not read:
                    try:
                        vies_response = vat.check_vies(amazon_order.partner_vat)
                        read = True
                    except Fault as e:
                        read = e.message != 'MS_MAX_CONCURRENT_REQ'
                if vies_response and vies_response['valid'] and vies_response['name'] != '---' and vies_response[
                    'address'] != '---':
                    amazon_order.billing_country_id = self.env['res.country'].search(
                        [('code', '=', vies_response['countryCode'])]).id
                    amazon_order.billing_name = vies_response['name']
                    amazon_order.billing_address = vies_response['address']
                    if amazon_order.billing_country_id.code != amazon_order.vat_imputation_country:
                        amazon_order.state = 'error'
                        amazon_order.message_error = _('There country in VIES is different to Amazon order country')
                        continue
                else:
                    amazon_order.state = 'error'
                    amazon_order.message_error = _('There is no billing info in VIES')
                    continue

            if amazon_order.invoice_deposits:
                partner_id = amazon_order.create_partner()
                journal_id = self.env['account.journal'].search([('type', '=', 'sale')], order='id')[0]
                invoice = amazon_order.invoice_deposits.filtered(lambda i: i.state != 'cancel')
                invoice.write({'partner_id': partner_id.id,
                               'partner_shipping_id': partner_id.id,
                               'journal_id': journal_id.id,
                               'payment_term_id': partner_id.property_payment_term_id.id,
                               'payment_mode_id': partner_id.customer_payment_mode_id.id,
                               'partner_bank_id': partner_id.bank_ids and partner_id.bank_ids[0].id or False})

                invoice.action_invoice_open()
                amazon_order.state = 'invoice_open'
            else:
                amazon_order.process_order()


class CreateFullInvoicesAmazonLines(models.TransientModel):
    _name = 'create.full.invoices.amazon.lines'

    wizard_id = fields.Many2one('create.full.invoices.amazon.wizard')
    amazon_order = fields.Many2one('amazon.sale.order', "Amazon Order", readonly=True)
