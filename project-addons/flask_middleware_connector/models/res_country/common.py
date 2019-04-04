# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models
from odoo.addons.component.core import Component
from odoo.addons.queue_job.job import job


class ResCountryListener(Component):
    _name = 'country.event.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['res.country']

    def on_record_create(self, record, fields=None):
        record.with_delay(priority=1).export_country()

    def on_record_write(self, record, fields=None):
        up_fields = ["name", "code"]
        for field in up_fields:
            if field in fields:
                record.with_delay(priority=3).update_country(fields=fields)
                break

    def on_record_unlink(self, record):
        record.with_delay(priority=100).unlink_country()


class ResCountry(models.Model):
    _inherit = 'res.country'

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def export_country(self):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.update(self, 'insert')
        return True


    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def update_country(self, fields):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.update(self, 'update')
        return True


    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def unlink_country(self):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.delete(self)
        return True


class CountryStateListener(Component):
    _name = 'country.state.event.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['res.country.state']

    def on_record_create(self, record, fields=None):
        record.with_delay(priority=1).export_country_state()

    def on_record_write(self, record, fields=None):
        up_fields = ["name", "code", "country_id"]
        for field in up_fields:
            if field in fields:
                record.with_delay(priority=3).update_country_state(fields=fields)
                break

    def on_record_unlink(self, record):
        record.with_delay(priority=5).unlink_country_state()


class ResCountryState(models.Model):
    _inherit = 'res.country.state'

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def export_country_state(self):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.update(self, 'insert')
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def update_country_state(self, fields):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.update(self, 'update')
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def unlink_country_state(self):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.delete(self)
        return True
