# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields
from odoo.addons.component.core import Component
from odoo.addons.queue_job.job import job


class ResUsersListener(Component):
    _name = 'res.users.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['res.users']

    def on_record_create(self, record, fields=None):
        if record.web:
            record.with_delay(priority=1).export_commercial()

    def on_record_write(self, record, fields=None):
        up_fields = ["name", 'email', 'web']
        if "web" in fields and record.web:
            record.with_delay(priority=1).export_commercial()
        elif "web" in fields and not record.web:
            record.with_delay(priority=100).unlink_commercial()
        else:
            for field in up_fields:
                if field in fields:
                    record.with_delay(priority=3).update_commercial(fields)
                    break

    def on_record_unlink(self, record):
        record.with_delay(priority=100).unlink_commercial()


class ResUsers(models.Model):
    _inherit = 'res.users'

    web = fields.Boolean()

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def export_commercial(self):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.update(self, 'insert')
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def update_commercial(self, fields):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.update(self, 'update')
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def unlink_commercial(self):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.delete(self)
        return True
