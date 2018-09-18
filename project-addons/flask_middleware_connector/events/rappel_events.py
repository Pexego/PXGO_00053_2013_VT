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
class RappelExporter(Exporter):

    _model_name = ['rappel']

    def update(self, rappel_id, mode):
        rappel = self.model.browse(rappel_id)
        vals = {"odoo_id": rappel.id,
                "name": rappel.name,
                }
        if mode == "insert":
            return self.backend_adapter.insert(vals)
        else:
            return self.backend_adapter.update(rappel_id, vals)

    def delete(self, binding_id):
        return self.backend_adapter.remove(binding_id)


@middleware
class RappelAdapter(GenericAdapter):
    _model_name = 'rappel'
    _middleware_model = 'rappel'


@on_record_create(model_names='rappel')
def delay_create_rappel(session, model_name, record_id, vals):
    export_rappel.delay(session, model_name, record_id, priority=1, eta=60)


@on_record_write(model_names='rappel')
def delay_write_rappel(session, model_name, record_id, vals):
    up_fields = ["name"]
    for field in up_fields:
        if field in vals:
            update_rappel.delay(session, model_name, record_id, priority=2, eta=120)


@on_record_unlink(model_names='rappel')
def delay_unlink_rappel(session, model_name, record_id):
    unlink_rappel.delay(session, model_name, record_id, priority=3, eta=120)


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def export_rappel(session, model_name, record_id):
    rappel_exporter = _get_exporter(session, model_name, record_id, RappelExporter)
    return rappel_exporter.update(record_id, "insert")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def update_rappel(session, model_name, record_id):
    rappel_exporter = _get_exporter(session, model_name, record_id, RappelExporter)
    return rappel_exporter.update(record_id, "update")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def unlink_rappel(session, model_name, record_id):
    rappel_exporter = _get_exporter(session, model_name, record_id, RappelExporter)
    return rappel_exporter.delete(record_id)


@middleware
class RappelInfoExporter(Exporter):

    _model_name = ['rappel.current.info']

    def update(self, rappel_info_id, mode):
        rappel_info = self.model.browse(rappel_info_id)
        vals = {"odoo_id": rappel_info.id,
                "partner_id": rappel_info.partner_id.id,
                "rappel_id": rappel_info.rappel_id.id,
                "date_start": rappel_info.date_start,
                "date_end": rappel_info.date_end,
                "amount": rappel_info.amount,
                }
        if mode == "insert":
            return self.backend_adapter.insert(vals)
        else:
            return self.backend_adapter.update(rappel_info, vals)

    def delete(self, rappel_info):
        return self.backend_adapter.remove(rappel_info)


@middleware
class RappelInfoAdapter(GenericAdapter):
    _model_name = 'rappel.current.info'
    _middleware_model = 'rappelcustomerinfo'


@on_record_create(model_names='rappel.current.info')
def delay_create_rappel_info(session, model_name, record_id, vals):
    rappel_info = session.env[model_name].browse(record_id)
    if rappel_info.partner_id.commercial_partner_id.web:
        export_rappel_info.delay(session, model_name, record_id, priority=1, eta=60)


@on_record_write(model_names='rappel.current.info')
def delay_write_rappel_info(session, model_name, record_id, vals):
    rappel_info = session.env[model_name].browse(record_id)
    if rappel_info.partner_id.commercial_partner_id.web:
        update_rappel_info.delay(session, model_name, record_id, priority=2, eta=120)


@on_record_unlink(model_names='rappel.current.info')
def delay_unlink_rappel_info(session, model_name, record_id):
    rappel_info = session.env[model_name].browse(record_id)
    if rappel_info.partner_id.commercial_partner_id.web:
        unlink_rappel_info.delay(session, model_name, record_id, priority=3, eta=120)


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def export_rappel_info(session, model_name, record_id):
    rappel_info_exporter = _get_exporter(session, model_name, record_id, RappelInfoExporter)
    return rappel_info_exporter.update(record_id, "insert")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def update_rappel_info(session, model_name, record_id):
    rappel_info_exporter = _get_exporter(session, model_name, record_id, RappelInfoExporter)
    return rappel_info_exporter.update(record_id, "update")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def unlink_rappel_info(session, model_name, record_id):
    rappel_info_exporter = _get_exporter(session, model_name, record_id, RappelInfoExporter)
    return rappel_info_exporter.delete(record_id)

@middleware
class RappelSectionExporter(Exporter):

    _model_name = ['rappel.section']

    def update(self, rappel_section_id, mode):
        rappel_section = self.model.browse(rappel_section_id)
        vals = {"odoo_id": rappel_section.id,
                "rappel_id": rappel_section.rappel_id.id,
                "percent": rappel_section.percent,
                "rappel_from": rappel_section.rappel_from,
                "rappel_until": rappel_section.rappel_until,
                }
        if mode == "insert":
            return self.backend_adapter.insert(vals)
        else:
            return self.backend_adapter.update(rappel_section, vals)

    def delete(self, rappel_section):
        return self.backend_adapter.remove(rappel_section)


@middleware
class RappelSectionAdapter(GenericAdapter):
    _model_name = 'rappel.section'
    _middleware_model = 'rappelsection'

@on_record_create(model_names='rappel.section')
def delay_create_rappel_section(session, model_name, record_id, vals):
    export_rappel_section.delay(session, model_name, record_id, priority=1, eta=60)

@on_record_write(model_names='rappel.section')
def delay_write_rappel_section(session, model_name, record_id, vals):
    update_rappel_section.delay(session, model_name, record_id, priority=2, eta=120)

@on_record_unlink(model_names='rappel.section')
def delay_unlink_rappel_section(session, model_name, record_id):
    unlink_rappel_section.delay(session, model_name, record_id, priority=3, eta=120)

@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def export_rappel_section(session, model_name, record_id):
    rappel_section_exporter = _get_exporter(session, model_name, record_id, RappelSectionExporter)
    return rappel_section_exporter.update(record_id, "insert")

@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def update_rappel_section(session, model_name, record_id):
    rappel_section_exporter = _get_exporter(session, model_name, record_id, RappelSectionExporter)
    return rappel_section_exporter.update(record_id, "update")

@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def unlink_rappel_section(session, model_name, record_id):
    rappel_section_exporter = _get_exporter(session, model_name, record_id, RappelSectionExporter)
    return rappel_section_exporter.delete(record_id)

