from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    sim_serial_ids = fields.One2many('sim.package', 'partner_id')

    def invoice_sim_package(self, partner_id, sims, voice, sms):
        partner = self.env['res.partner'].browse(partner_id)
        price_tags = {'M2M0,7euro': 0.7, 'M2M1euro': 1, 'M2M2euro': 2}
        product_sim = self.env['product.product'].search([('default_code', '=', 'M2M_COMMUNICATION')])
        product_sms = self.env['product.product'].search([('default_code', '=', 'M2M_COMMUNICATION_EXTRA_SMS')])
        product_voz = self.env['product.product'].search([('default_code', '=', 'M2M_COMMUNICATION_EXTRA_MINUTE')])
        company = self.env['res.company'].browse(1)
        price_unit = 1.5
        line_account = self.env['account.invoice.line']. \
            get_invoice_line_account('out_invoice', product_sim, partner.property_account_position_id, company)
        for tag in price_tags:
            if tag in [x.name for x in partner.category_id]:
                price_unit = price_tags[tag]
        inv_data = {'type': 'out_invoice', 'partner_id': partner.id, 'journal_id': 1, 'currency_id': 1,
                    'company_id': 1, 'not_send_email': True}
        invoice = self.env['account.invoice'].create(inv_data)
        invoice._onchange_partner_id()
        line_data = {'sequence': 1, 'product_id': product_sim.id, 'name': product_sim.default_code,
                     'quantity': sims, 'discount': 0, 'uom_id': 1, 'price_unit': price_unit,
                     'account_id': line_account.id, 'invoice_id': invoice.id}
        line = self.env['account.invoice.line'].create(line_data)
        line._onchange_product_id()
        line._onchange_account_id()
        line.price_unit = price_unit
        if sms > 0:
            line_data_sms = {'sequence': 1, 'product_id': product_sms.id, 'name': product_sms.default_code,
                             'quantity': sms, 'discount': 0, 'uom_id': 1, 'price_unit': 0.08,
                             'account_id': line_account.id, 'invoice_id': invoice.id}
            line_sms = self.env['account.invoice.line'].create(line_data_sms)
            line_sms._onchange_product_id()
            line_sms._onchange_account_id()
            line_sms.price_unit = 0.08
        if voice > 0:
            line_data_voz = {'sequence': 1, 'product_id': product_voz.id, 'name': product_voz.default_code,
                             'quantity': voice, 'discount': 0, 'uom_id': 1, 'price_unit': 0.15,
                             'account_id': line_account.id, 'invoice_id': invoice.id}
            line_voz = self.env['account.invoice.line'].create(line_data_voz)
            line_voz._onchange_product_id()
            line_voz._onchange_account_id()
            line_voz.price_unit = 0.15
        invoice.compute_taxes()
        invoice.action_invoice_open()
        return invoice.number
