# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.queue_job.job import job
from odoo import models


class RappelListener(Component):
    _name = 'rappel.event.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['rappel']

    def on_record_create(self, record, fields=None):
        record.with_delay(priority=1, eta=60).export_rappel()

    def on_record_write(self, record, fields=None):
        up_fields = ["name"]
        for field in up_fields:
            if field in fields:
                record.with_delay(priority=2, eta=120).update_rappel(fields=fields)

    def on_record_unlink(self, record):
        record.with_delay(priority=3, eta=120).unlink_rappel()


class Rappel(models.Model):
    _inherit = 'rappel'

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def export_rappel(self):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.update(self, 'insert')
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def update_rappel(self, fields):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.update(self, 'update')
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def unlink_rappel(self):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.delete(self)
        return True


class RappelInfoListener(Component):
    _name = 'rappel.info.event.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['rappel.current.info']

    def on_record_create(self, record, fields=None):
        if record.partner_id.commercial_partner_id.web:
            record.with_delay(priority=1, eta=60).export_rappel_info()

    def on_record_write(self, record, fields=None):
        if record.partner_id.commercial_partner_id.web:
            record.with_delay(priority=2, eta=120).update_rappel_info(fields=fields)

    def on_record_unlink(self, record):
        if record.partner_id.commercial_partner_id.web:
            record.with_delay(priority=3, eta=120).unlink_rappel_info()


class RappelInfo(models.Model):
    _inherit = 'rappel.current.info'

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def export_rappel_info(self):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.update(self, 'insert')
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def update_rappel_info(self, fields):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.update(self, 'update')
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def unlink_rappel_info(self):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.delete(self)
        return True


class RappelSectionListener(Component):
    _name = 'rappel.section.event.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['rappel.section']

    def on_record_create(self, record, fields=None):
        record.with_delay(priority=1, eta=60).export_rappel_section()

    def on_record_write(self, record, fields=None):
        record.with_delay(priority=2, eta=120).update_rappel_section(fields=fields)

    def on_record_unlink(self, record):
        record.with_delay(priority=3, eta=120).unlink_rappel_section()


class RappelSection(models.Model):
    _inherit = 'rappel.section'

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def export_rappel_section(self):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.update(self, 'insert')
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def update_rappel_section(self, fields):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.update(self, 'update')
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def unlink_rappel_section(self):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.delete(self)
        return True

