# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import Component
from odoo.addons.queue_job.job import job
from odoo import models


class SaleOrderListener(Component):
    _name = 'sale.order.event.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['sale.order']

    def on_record_create(self, record, fields=None):
        if record.partner_id.web or record.partner_id.commercial_partner_id.web:
            record.with_delay(priority=2, eta=80).export_order()

    def on_record_write(self, record, fields=None):
        # He cogido order_line porque no entra amount_total ni amount_untaxed en el write
        up_fields = ["name", "state", "partner_id", "date_order", "client_order_ref",
                     "order_line", "partner_shipping_id", "delivery_type"]
        model_name = 'sale.order'
        if record.partner_id.web or record.partner_id.commercial_partner_id.web:
            job = self.env['queue.job'].sudo().search([('func_string', 'like', '%, ' + str(record.id) + ')%'),
                                                      ('model_name', '=', model_name)],
                                                      order='date_created desc, id desc', limit=1)
            if 'state' in fields and record.state == 'cancel':
                record.with_delay(priority=7, eta=80).unlink_order()
            elif 'state' in fields and record.state in ('draft', 'reserve') \
                    and job.name and 'unlink' in job.name and record.write_date == record.create_date:
                record.with_delay(priority=2, eta=80).export_order()
                for line in record.order_line:
                    line.with_delay(priority=2, eta=120).export_orderproduct()
            elif record.state in ('draft', 'reserve', 'progress', 'done', 'shipping_except', 'invoice_except'):
                for field in up_fields:
                    if field in fields:
                        record.with_delay(priority=5, eta=80).update_order(fields=fields)
                        break

    def on_record_unlink(self, record):
        if record.partner_id.web or record.partner_id.commercial_partner_id.web:
            record.with_delay(priority=7, eta=180).unlink_order()


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def export_order(self):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.update(self, 'insert')
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def update_order(self, fields):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.update(self, 'update')
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def unlink_order(self):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.delete(self)
        return True


class SaleOrderLineListener(Component):
    _name = 'sale.order.line.event.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['sale.order.line']

    def on_record_create(self, record, fields=None):
        if record.order_id.partner_id.web or record.order_id.partner_id.commercial_partner_id.web:
            record.with_delay(priority=2, eta=120).export_orderproduct()

    def on_record_write(self, record, fields=None):
        up_fields = ["product_id", "product_uom_qty", "price_unit", "discount", "order_id",
                     "no_rappel", "deposit", "price_unit",
                     "no_rappel", "deposit", "pack_parent_line_id", "price_unit"]
        if record.order_id.partner_id.web or record.order_id.partner_id.commercial_partner_id.web:
            for field in up_fields:
                if field in fields:
                    record.with_delay(priority=5, eta=120).update_orderproduct(fields=fields)
                    break

    def on_record_unlink(self, record):
        if record.order_id.partner_id.web or record.order_id.partner_id.commercial_partner_id.web:
            record.with_delay(priority=7, eta=180).unlink_orderproduct()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def export_orderproduct(self):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.update(self, 'insert')
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def update_orderproduct(self, fields):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.update(self, 'update')
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def unlink_orderproduct(self):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.delete(self)
        return True

