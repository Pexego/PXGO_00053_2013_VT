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
from openerp.addons.connector.event import Event
from .utils import _get_exporter


@middleware
class CountryExporter(Exporter):

    _model_name = ['res.country']

    def update(self, binding_id, mode):
        country = self.model.browse(binding_id)
        vals = {"name": country.name,
                "code": country.code,
                "odoo_id": country.id}
        if mode == "insert":
            return self.backend_adapter.insert(vals)
        else:
            return self.backend_adapter.update(binding_id, vals)

    def delete(self, binding_id):
        return self.backend_adapter.remove(binding_id)


@middleware
class CountryAdapter(GenericAdapter):
    _model_name = 'res.country'
    _middleware_model = 'country'


@on_record_create(model_names='res.country')
def delay_export_country_create(session, model_name, record_id, vals):
    export_country.delay(session, model_name, record_id, priority=1)


@on_record_write(model_names='res.country')
def delay_export_country_write(session, model_name, record_id, vals):
    up_fields = ["name", "code"]
    for field in up_fields:
        if field in vals:
            update_country.delay(session, model_name, record_id, priority=3)
            break


@on_record_unlink(model_names='res.country')
def delay_unlink_country(session, model_name, record_id):
    unlink_country.delay(session, model_name, record_id, priority=100)


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def export_country(session, model_name, record_id):
    country_exporter = _get_exporter(session, model_name, record_id,
                                     CountryExporter)
    return country_exporter.update(record_id, "insert")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def update_country(session, model_name, record_id):
    country_exporter = _get_exporter(session, model_name, record_id,
                                     CountryExporter)
    return country_exporter.update(record_id, "update")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def unlink_country(session, model_name, record_id):
    country_exporter = _get_exporter(session, model_name, record_id,
                                     CountryExporter)
    return country_exporter.delete(record_id)


@middleware
class CountryStateExporter(Exporter):

    _model_name = ['res.country.state']

    def update(self, binding_id, mode):
        country_state = self.model.browse(binding_id)
        vals = {"name": country_state.name,
                "code": country_state.code,
                "country_id": country_state.country_id.id,
                "odoo_id": country_state.id}
        if mode == "insert":
            return self.backend_adapter.insert(vals)
        else:
            return self.backend_adapter.update(binding_id, vals)

    def delete(self, binding_id):
        return self.backend_adapter.remove(binding_id)


@middleware
class CountryStateAdapter(GenericAdapter):
    _model_name = 'res.country.state'
    _middleware_model = 'countrystate'


@on_record_create(model_names='res.country.state')
def delay_export_country_state_create(session, model_name, record_id, vals):
    export_country_state.delay(session, model_name, record_id, priority=1)


@on_record_write(model_names='res.country.state')
def delay_export_country_state_write(session, model_name, record_id, vals):
    up_fields = ["name", "code", "country_id"]
    for field in up_fields:
        if field in vals:
            update_country_state.delay(session, model_name, record_id, priority=3)
            break


@on_record_unlink(model_names='res.country.state')
def delay_unlink_country_state(session, model_name, record_id):
    unlink_country_state.delay(session, model_name, record_id, priority=5)


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def export_country_state(session, model_name, record_id):
    country_state_exporter = _get_exporter(session, model_name, record_id, CountryStateExporter)
    return country_state_exporter.update(record_id, "insert")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def update_country_state(session, model_name, record_id):
    country_state_exporter = _get_exporter(session, model_name, record_id, CountryStateExporter)
    return country_state_exporter.update(record_id, "update")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def unlink_country_state(session, model_name, record_id):
    country_state_exporter = _get_exporter(session, model_name, record_id, CountryStateExporter)
    return country_state_exporter.delete(record_id)
