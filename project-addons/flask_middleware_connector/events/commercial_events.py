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
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.queue_job.job import job
from odoo import models

# TODO: Migrar parte del adapter
# @middleware
# class CommercialExporter(Exporter):
#
#     _model_name = ['res.users']
#
#     def update(self, binding_id, mode):
#         commercial = self.model.browse(binding_id)
#         vals = {"name": commercial.name,
#                 "email": commercial.email,
#                 "odoo_id": commercial.id}
#         if mode == "insert":
#             return self.backend_adapter.insert(vals)
#         else:
#             return self.backend_adapter.update(binding_id, vals)
#
#     def delete(self, binding_id):
#         return self.backend_adapter.remove(binding_id)

#
# @middleware
# class CommercialAdapter(GenericAdapter):
#     _model_name = 'res.users'
#     _middleware_model = 'commercial'

class CommercialListener(Component):
    _name = 'commercial.event.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['res.users']

    def on_record_create(self, record):
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

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def export_commercial(self):
        # commercial_exporter = _get_exporter(session, model_name, record_id,
        #                                  CommercialExporter)
        # return commercial_exporter.update(record_id, "insert")


    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def update_commercial(self, fields):
        # commercial_exporter = _get_exporter(session, model_name, record_id,
        #                                  CommercialExporter)
        # return commercial_exporter.update(record_id, "update")


    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def unlink_commercial(self):
        # commercial_exporter = _get_exporter(session, model_name, record_id,
        #                                  CommercialExporter)
        # return commercial_exporter.delete(record_id)
