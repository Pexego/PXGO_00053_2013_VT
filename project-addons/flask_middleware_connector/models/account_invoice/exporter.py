# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import Component
import base64


class AccountInvoiceExporter(Component):
    _name = 'account.invoice.exporter'
    _inherit = ['base.exporter']
    _apply_on = ['account.invoice']
    _usage = 'record.exporter'

    def update(self, binding, mode):
        invoice_report_action = self.env.ref(
            'custom_report_link.action_report_invoice_custom')
        result = invoice_report_action.render_qweb_pdf(res_ids=binding.id)
        result_encode = base64.b64encode(result[0])
        if not binding.state_web:
            binding._get_state_web()

        vals = {'odoo_id': binding.id,
                'number': binding.number,
                'partner_id': binding.partner_id.commercial_partner_id.id,
                'client_ref': binding.name or "",
                'date_invoice': binding.date_invoice,
                'date_due': binding.date_due,
                'subtotal_wt_rect': binding.amount_untaxed_signed,
                'total_wt_rect': binding.amount_total_signed,
                'pdf_file_data': result_encode,
                'state': binding.state_web,  # Llamada a _get_state_web para evitar problemas en facturas que no tienen inicializado ese valor
                'payment_mode_id': binding.payment_mode_id.name,
                'orders': binding.orders}
        if mode == 'insert':
            return self.backend_adapter.insert(vals)
        else:
            return self.backend_adapter.update(binding.id, vals)

    def delete(self, binding):
        return self.backend_adapter.remove(binding.id)


class AccountInvoiceAdapter(Component):

    _name = 'invoice.general.adapter'
    _inherit = 'middleware.adapter'
    _apply_on = 'account.invoice'
    _middleware_model = 'invoice'
