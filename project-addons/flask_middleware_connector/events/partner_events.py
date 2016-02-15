# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea All Rights Reserved
#    $Omar Castiñeira Saavedra <omar@comunitea.com>$
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
from .utils import _get_exporter
from ..backend import middleware
from openerp.addons.connector.unit.synchronizer import Exporter
from ..unit.backend_adapter import GenericAdapter
from .rma_events import export_rma, export_rmaproduct
from openerp.addons.connector.event import Event


@middleware
class PartnerExporter(Exporter):

    _model_name = ['res.partner']

    def update(self, binding_id, mode):
        partner = self.model.browse(binding_id)
        vals = {"fiscal_name": partner.name,
                "commercial_name": partner.comercial or "",
                "odoo_id": partner.id,
                "vat": partner.vat or "",
                "street": partner.street or "",
                "city": partner.city or "",
                "zipcode": partner.zip,
                "country": partner.country_id and partner.country_id.name or
                "",
                "commercial_id": partner.user_id.id,
                "ref": partner.ref,
                "discount": partner.discount,
                "state": partner.state_id and partner.state_id.name or "",
                "email": partner.email or ""}
        if mode == "insert":
            return self.backend_adapter.insert(vals)
        else:
            return self.backend_adapter.update(binding_id, vals)

    def delete(self, binding_id):
        return self.backend_adapter.remove(binding_id)


@middleware
class PartnerAdapter(GenericAdapter):
    _model_name = 'res.partner'
    _middleware_model = 'customer'


@on_record_create(model_names='res.partner')
def delay_export_partner_create(session, model_name, record_id, vals):
    partner = session.env[model_name].browse(record_id)
    up_fields = ["name", "comercial", "vat", "city", "street", "zip",
                 "country_id", "state_id", "email", "ref", 'user_id']
    if vals.get("web", False) and (vals.get('active', False) or
                                   partner.active):
        export_partner.delay(session, model_name, record_id, priority=2)
        rmas = session.env['crm.claim'].search(
            [('partner_id', '=', partner.id)])
        for rma in rmas:
            export_rma.delay(session, 'crm.claim', rma.id, priority=5, eta=120)
            for line in rma.claim_line_ids:
                if line.product_id.web == 'published':
                    export_rmaproduct.delay(session, 'claim.line', line.id,
                                            priority=10, eta=240)
    elif vals.get("active", False) and partner.web:
        export_partner.delay(session, model_name, record_id, priority=1)
        rmas = session.env['crm.claim'].search(
            [('partner_id', '=', partner.id)])
        for rma in rmas:
            export_rma.delay(session, 'crm.claim', rma.id, priority=5, eta=120)
            for line in rma.claim_line_ids:
                if line.product_id.web == 'published':
                    export_rmaproduct.delay(session, 'claim.line', line.id,
                                            priority=10, eta=240)
    elif partner.web:
        for field in up_fields:
            if field in vals:
                update_partner.delay(session, model_name, record_id)
                break


@on_record_write(model_names='res.partner')
def delay_export_partner_write(session, model_name, record_id, vals):
    partner = session.env[model_name].browse(record_id)
    up_fields = ["name", "comercial", "vat", "city", "street", "zip",
                 "country_id", "state_id", "email", "ref"]
    if vals.get("web", False) and (vals.get('active', False) or
                                   partner.active):
        export_partner.delay(session, model_name, record_id, priority=2)
        rmas = session.env['crm.claim'].search(
            [('partner_id', '=', partner.id)])
        for rma in rmas:
            export_rma.delay(session, 'crm.claim', rma.id, priority=5, eta=120)
            for line in rma.claim_line_ids:
                if line.product_id.web == 'published':
                    export_rmaproduct.delay(session, 'claim.line', line.id,
                                            priority=10, eta=240)
    elif "web" in vals and not vals["web"]:
        unlink_partner.delay(session, model_name, record_id, priority=100)
    elif vals.get("active", False) and partner.web:
        export_partner(session, model_name, record_id, priority=2)
        rmas = session.delay.env['crm.claim'].search(
            [('partner_id', '=', partner.id)])
        for rma in rmas:
            export_rma.delay(session, 'crm.claim', rma.id, priority=5, eta=120)
            for line in rma.claim_line_ids:
                if line.product_id.web == 'published':
                    export_rmaproduct.delay(session, 'claim.line', line.id,
                                            priority=10, eta=240)
    elif "active" in vals and not vals["active"] and partner.web:
        unlink_partner(session, model_name, record_id)
    elif partner.web:
        for field in up_fields:
            if field in vals:
                update_partner.delay(session, model_name, record_id, priority=5)
                break


@on_record_unlink(model_names='res.partner')
def delay_unlink_partner(session, model_name, record_id):
    partner = session.env[model_name].browse(record_id)
    if partner.web:
        unlink_partner.delay(session, model_name, record_id)


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def export_partner(session, model_name, record_id):
    partner_exporter = _get_exporter(session, model_name, record_id,
                                     PartnerExporter)
    return partner_exporter.update(record_id, "insert")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def update_partner(session, model_name, record_id):
    partner_exporter = _get_exporter(session, model_name, record_id,
                                     PartnerExporter)
    return partner_exporter.update(record_id, "update")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def unlink_partner(session, model_name, record_id):
    partner_exporter = _get_exporter(session, model_name, record_id,
                                     PartnerExporter)
    return partner_exporter.delete(record_id)


# Se controla los cambios en versiones de tarifa, cuando hay cambios en 1
# item tambien se modifica version
@on_record_create(model_names='product.pricelist.version')
def delay_export_pricelist_version_create(session, model_name, record_id,
                                          vals):
    pricelist_version = session.env[model_name].browse(record_id)
    partners = session.env['res.partner'].search(
        [('property_product_pricelist', '=',
          pricelist_version.pricelist_id.id), ('web', '=', True)])
    for partner in partners:
        update_partner.delay(session, 'res.partner', partner.id)


@on_record_write(model_names='product.pricelist.version')
def delay_export_pricelist_version_write(session, model_name, record_id, vals):
    pricelist_version = session.env[model_name].browse(record_id)
    partners = session.env['res.partner'].search(
        [('property_product_pricelist', '=',
          pricelist_version.pricelist_id.id), ('web', '=', True)])
    for partner in partners:
        update_partner.delay(session, 'res.partner', partner.id)
