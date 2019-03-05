##############################################################################
#
#    Copyright (C) 2016 Comunitea All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@comunitea.com>$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
# from ..backend import middleware
# from openerp.addons.connector.unit.synchronizer import Exporter
# from ..unit.backend_adapter import GenericAdapter
# from openerp.addons.connector.event import Event
# from .utils import _get_exporter

from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.queue_job.job import job
from odoo import models

# TODO: Migrar parte del adapter
# @middleware
# class RappelExporter(Exporter):
#
#     _model_name = ['rappel']
#
#     def update(self, rappel_id, mode):
#         rappel = self.model.browse(rappel_id)
#         vals = {"odoo_id": rappel.id,
#                 "name": rappel.name,
#                 }
#         if mode == "insert":
#             return self.backend_adapter.insert(vals)
#         else:
#             return self.backend_adapter.update(rappel_id, vals)
#
#     def delete(self, binding_id):
#         return self.backend_adapter.remove(binding_id)
#
#
# @middleware
# class RappelAdapter(GenericAdapter):
#     _model_name = 'rappel'
#     _middleware_model = 'rappel'


class RappelListener(Component):
    _name = 'rappel.event.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['rappel']

    def on_record_create(self, record):
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
        # rappel_exporter = _get_exporter(session, model_name, record_id, RappelExporter)
        # return rappel_exporter.update(record_id, "insert")


    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def update_rappel(self, fields):
        # rappel_exporter = _get_exporter(session, model_name, record_id, RappelExporter)
        # return rappel_exporter.update(record_id, "update")


    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def unlink_rappel(self):
        # rappel_exporter = _get_exporter(session, model_name, record_id, RappelExporter)
        # return rappel_exporter.delete(record_id)


# @middleware
# class RappelInfoExporter(Exporter):
#
#     _model_name = ['rappel.current.info']
#
#     def update(self, rappel_info_id, mode):
#         rappel_info = self.model.browse(rappel_info_id)
#         vals = {"odoo_id": rappel_info.id,
#                 "partner_id": rappel_info.partner_id.id,
#                 "rappel_id": rappel_info.rappel_id.id,
#                 "date_start": rappel_info.date_start,
#                 "date_end": rappel_info.date_end,
#                 "amount": rappel_info.amount,
#                 "amount_est": rappel_info.amount_est,
#                 }
#         if mode == "insert":
#             return self.backend_adapter.insert(vals)
#         else:
#             return self.backend_adapter.update(rappel_info, vals)
#
#     def delete(self, rappel_info):
#         return self.backend_adapter.remove(rappel_info)
#
#
# @middleware
# class RappelInfoAdapter(GenericAdapter):
#     _model_name = 'rappel.current.info'
#     _middleware_model = 'rappelcustomerinfo'

class RappelInfoListener(Component):
    _name = 'rappel.info.event.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['rappel.current.info']

    def on_record_create(self, record):
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
        # rappel_info_exporter = _get_exporter(session, model_name, record_id, RappelInfoExporter)
        # return rappel_info_exporter.update(record_id, "insert")


    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def update_rappel_info(self, fields):
        # rappel_info_exporter = _get_exporter(session, model_name, record_id, RappelInfoExporter)
        # return rappel_info_exporter.update(record_id, "update")


    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def unlink_rappel_info(self):
        # rappel_info_exporter = _get_exporter(session, model_name, record_id, RappelInfoExporter)
        # return rappel_info_exporter.delete(record_id)

# @middleware
# class RappelSectionExporter(Exporter):
#
#     _model_name = ['rappel.section']
#
#     def update(self, rappel_section_id, mode):
#         rappel_section = self.model.browse(rappel_section_id)
#         vals = {"odoo_id": rappel_section.id,
#                 "rappel_id": rappel_section.rappel_id.id,
#                 "percent": rappel_section.percent,
#                 "rappel_from": rappel_section.rappel_from,
#                 "rappel_until": rappel_section.rappel_until,
#                 }
#         if mode == "insert":
#             return self.backend_adapter.insert(vals)
#         else:
#             return self.backend_adapter.update(rappel_section, vals)
#
#     def delete(self, rappel_section):
#         return self.backend_adapter.remove(rappel_section)
#
#
# @middleware
# class RappelSectionAdapter(GenericAdapter):
#     _model_name = 'rappel.section'
#     _middleware_model = 'rappelsection'

class RappelSectionListener(Component):
    _name = 'rappel.section.event.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['rappel.section']

    def on_record_create(self, record):
        record.with_delay(priority=1, eta=60).export_rappel_section()

    def on_record_write(self, record, fields=None):
        record.with_delay(priority=2, eta=120).update_rappel_section(fields=fields)

    def on_record_unlink(self, record):
        record.with_delay(priority=3, eta=120).unlink_rappel_section()


class RappelSection(models.Model):
    _inherit = 'rappel.section'

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def export_rappel_section(self):
        # rappel_section_exporter = _get_exporter(session, model_name, record_id, RappelSectionExporter)
        # return rappel_section_exporter.update(record_id, "insert")

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def update_rappel_section(self, fields):
        # rappel_section_exporter = _get_exporter(session, model_name, record_id, RappelSectionExporter)
        # return rappel_section_exporter.update(record_id, "update")

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def unlink_rappel_section(self):
        # rappel_section_exporter = _get_exporter(session, model_name, record_id, RappelSectionExporter)
        # return rappel_section_exporter.delete(record_id)

