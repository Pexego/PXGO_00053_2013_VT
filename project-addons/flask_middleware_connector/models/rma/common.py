# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.queue_job.job import job
from odoo import models, fields


class CrmClaimListener(Component):
    _name = 'claim.event.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['crm.claim']

    def on_record_create(self, record, fields=None):
        if record.partner_id and record.partner_id.web:
            record.with_delay(priority=1).export_rma()

    def on_record_write(self, record, fields):
        rma = record
        model_name = 'crm.claim'
        up_fields = ["date", "date_received", "delivery_type", "delivery_address_id",
                     "partner_id", "stage_id", "number", "name"]
        job = self.env['queue.job'].sudo().search([('func_string', 'like', '%, ' + str(rma.id) + ')%'),
                                                      ('model_name', '=', model_name)], order='date_created desc', limit=1)
        if record.partner_id and rma.partner_id.web and ((job.name and 'unlink' in job.name) or not job.name):
            record.with_delay(priority=1).export_rma()
            for line in rma.claim_line_ids:
                line.with_delay(priority=10, eta=120).export_rmaproduct()
        elif 'partner_id' in fields and not record.partner_id or \
                record. partner_id and not rma.partner_id.web:
            record.with_delay(priority=6, eta=120).unlink_rma()
        elif rma.partner_id.web:
            for field in up_fields:
                if field in fields:
                    record.with_delay(priority=5, eta=120).update_rma()
                    break

    def on_record_unlink(self, record):
        if record.partner_id and record.partner_id.web:
            record.with_delay(priority=25, eta=120).unlink_rma()


class CrmClaim(models.Model):
    _inherit = 'crm.claim'

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def export_rma(self):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.update(self, 'insert')
        return True


    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def update_rma(self, fields):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.update(self, 'update')
        return True


    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def unlink_rma(self):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.delete(self)
        return True


class ClaimLineListener(Component):
    _name = 'claim.line.event.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['claim.line']

    def on_record_create(self, record, fields=None):
        if record.claim_id.partner_id.web and \
                (not record.equivalent_product_id) and \
                record.web:
            record.with_delay(priority=10, eta=120).export_rmaproduct()

    def on_record_write(self, record, fields=None):
        up_fields = ["product_id", "date_in", "date_out", "substate_id",
                     "name", "move_out_customer_state",
                     "internal_description", "product_returned_quantity",
                     "equivalent_product_id", "prodlot_id", "invoice_id"]
        if record.web:
            record.with_delay(priority=10, eta=120).export_rmaproduct()
        elif not record.web:
            record.with_delay(priority=20, eta=180).unlink_rmaproduct()
        elif record.claim_id.partner_id.web and record.web:
            for field in up_fields:
                if field in fields:
                    record.with_delay(priority=15, eta=180).update_rmaproduct()
                    break

    def on_record_unlink(self, record):
        if record.claim_id.partner_id.web and record.web:
            record.with_delay(priority=20, eta=180).unlink_rmaproduct()


class ClaimLine(models.Model):
    _inherit = 'claim.line'

    date_in = fields.Datetime()
    date_out = fields.Datetime()
    web = fields.Boolean(default=True)

    def write(self, vals):
        delete = True
        if vals.get('web', False):
            for record in self:
                if record.web != vals['web']:
                    delete = False
                    break
            if delete:
                del vals['web']
        return super().write(vals)

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def export_rmaproduct(self):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.update(self, 'insert')
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def update_rmaproduct(self, fields):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.update(self, 'update')
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def unlink_rmaproduct(self):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.delete(self)
        return True


class SubstateListener(Component):
    _name = 'substate.event.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['substate.substate']

    def on_record_create(self, record, fields=None):
        record.with_delay(priority=1).export_rma_status()

    def on_record_write(self, record, fields=None):
        up_fields = ["name"]
        for field in up_fields:
            if field in fields:
                record.with_delay(priority=2).update_rma_status()
                break

    def on_record_unlink(self, record):
        record.with_delay(priority=100).unlink_rma_status()


class SubstateSubstate(models.Model):
    _inherit = 'substate.substate'

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def export_rma_status(self):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.update(self, 'insert')
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def update_rma_status(self, fields):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.update(self, 'update')
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def unlink_rma_status(self):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.delete(self)
        return True


class ClaimStageListener(Component):
    _name = 'claim.stage.event.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['crm.claim.stage']

    def on_record_create(self, record, fields=None):
        record.with_delay(priority=1).export_rma_stage()

    def on_record_write(self, record, fields=None):
        up_fields = ["name"]
        for field in up_fields:
            if field in fields:
                record.with_delay(priority=2).update_rma_stage()
                break

    def on_record_unlink(self, record):
        record.with_delay(priority=100).unlink_rma_stage()


class CrmClaimStage(models.Model):
    _inherit = 'crm.claim.stage'

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def export_rma_stage(self):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.update(self, 'insert')
        return True


    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def update_rma_stage(self):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.update(self, 'update')
        return True


    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def unlink_rma_stage(self):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.delete(self)
        return True
