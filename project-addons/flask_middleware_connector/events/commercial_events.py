# -*- coding: utf-8 -*-
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
from openerp.addons.connector.event import on_record_create, on_record_write, \
    on_record_unlink
from openerp.addons.connector.queue.job import job
from ..backend import middleware
from openerp.addons.connector.unit.synchronizer import Exporter
from ..unit.backend_adapter import GenericAdapter
from .rma_events import export_rma, export_rmaproduct
from openerp.addons.connector.event import Event
from .utils import _get_exporter


@middleware
class CommercialExporter(Exporter):

    _model_name = ['res.users']

    def update(self, binding_id, mode):
        commercial = self.model.browse(binding_id)
        vals = {"name": commercial.name,
                "email": commercial.email,
                "odoo_id": commercial.id}
        if mode == "insert":
            return self.backend_adapter.insert(vals)
        else:
            return self.backend_adapter.update(binding_id, vals)

    def delete(self, binding_id):
        return self.backend_adapter.remove(binding_id)


@middleware
class CommercialAdapter(GenericAdapter):
    _model_name = 'res.users'
    _middleware_model = 'commercial'


@on_record_create(model_names='res.users')
def delay_export_commercial_create(session, model_name, record_id, vals):
    if vals.get('web', False):
        export_commercial.delay(session, model_name, record_id, priority=1)


@on_record_write(model_names='res.users')
def delay_export_commercial_write(session, model_name, record_id, vals):
    up_fields = ["name", 'email', 'web']
    if "web" in vals and vals["web"]:
        export_commercial.delay(session, model_name, record_id, priority=1)
    elif "web" in vals and not vals["web"]:
        unlink_commercial.delay(session, model_name, record_id, priority=100)
    else:
        for field in up_fields:
            if field in vals:
                update_commercial.delay(session, model_name, record_id, priority=3)
                break


@on_record_unlink(model_names='res.users')
def delay_unlink_commercial(session, model_name, record_id):
    unlink_commercial.delay(session, model_name, record_id, priority=100)


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def export_commercial(session, model_name, record_id):
    commercial_exporter = _get_exporter(session, model_name, record_id,
                                     CommercialExporter)
    return commercial_exporter.update(record_id, "insert")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def update_commercial(session, model_name, record_id):
    commercial_exporter = _get_exporter(session, model_name, record_id,
                                     CommercialExporter)
    return commercial_exporter.update(record_id, "update")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def unlink_commercial(session, model_name, record_id):
    commercial_exporter = _get_exporter(session, model_name, record_id,
                                     CommercialExporter)
    return commercial_exporter.delete(record_id)
