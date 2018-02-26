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
from .rma_events import unlink_rma, unlink_rmaproduct, export_rma, export_rmaproduct
from .invoice_events import unlink_invoice, export_invoice
from .picking_events import export_picking, unlink_picking, export_pickingproduct, unlink_pickingproduct
from .order_events import export_order, update_order, unlink_order, export_orderproduct, unlink_orderproduct

@middleware
class PartnerExporter(Exporter):

    _model_name = ['res.partner']

    def update(self, binding_id, mode):
        partner = self.model.browse(binding_id)
        vals = {"is_company": partner.is_company,
                "fiscal_name": partner.name,
                "commercial_name": partner.comercial or "",
                "odoo_id": partner.id,
                "vat": partner.vat or "",
                "street": partner.street or "",
                "city": partner.city or "",
                "zipcode": partner.zip,
                "commercial_id": partner.user_id.id,
                "country": partner.country_id and partner.country_id.code or
                "",
                "ref": partner.ref,
                "discount": partner.discount,
                "pricelist_name": partner.property_product_pricelist and
                partner.property_product_pricelist.name or "",
                "state": partner.state_id and partner.state_id.name or "",
                "email": partner.email_web or "",
                "prospective": partner.prospective,
                "lang": partner.lang and partner.lang.split("_")[0] or 'es'}
        if not vals['is_company']:
            vals.update({"type": partner.type, "parent_id": partner.parent_id.id, "email": partner.email})
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
                 "country_id", "state_id", "email_web", "ref", 'user_id',
                 "property_product_pricelist", "lang", "type",
                 "parent_id", "is_company", "email", "prospective"]
    if vals.get('is_company', False) or partner.is_company:

        if vals.get("web", False) and ((vals.get('active', False) or \
                                       partner.active) or \
                                       (vals.get('prospective', False) or \
                                        partner.prospective)):
            export_partner.delay(session, model_name, record_id, priority=1,
                                 eta=60)
            tags = partner.category_id
            for tag in tags:
                export_partner_tag_rel.delay(session, 'res.partner.res.partner.category.rel',
                                             record_id, tag.id, priority=10, eta=60)

            sales = session.env['sale.order'].search([('partner_id', 'child_of', [record_id]),
                                                      ('company_id', '=', 1),
                                                      ('state', 'in', ['done', 'progress', 'draft', 'reserve'])])
            for sale in sales:
                export_order.delay(session, 'sale.order', sale.id, priority=5, eta=120)
                for line in sale.order_line:
                    export_orderproduct.delay(session, 'sale.order.line', line.id, priority=10, eta=180)

            invoices = session.env['account.invoice'].search([('commercial_partner_id', '=', partner.id),
                                                              ('company_id', '=', 1),
                                                              ('number', 'not like', '%ef%')])
            for invoice in invoices:
                export_invoice.delay(session, 'account.invoice', invoice.id, priority=5, eta=120)

            rmas = session.env['crm.claim'].search(
                [('partner_id', '=', partner.id)])
            for rma in rmas:
                export_rma.delay(session, 'crm.claim', rma.id, priority=5, eta=120)
                for line in rma.claim_line_ids:
                    if line.product_id.web == 'published' and \
                            (line.equivalent_product_id and
                             line.equivalent_product_id.web == 'published' or
                             True):
                        export_rmaproduct.delay(session, 'claim.line', line.id,
                                                priority=10, eta=240)

            pickings = session.env['stock.picking'].search([
                ('partner_id', 'child_of', [partner.id]),
                ('state', '!=', 'cancel'),
                ('picking_type_id.code', '=', 'outgoing'),
                ('company_id', '=', 1),
                ('not_sync', '=', False)
            ])
            for picking in pickings:
                export_picking.delay(session, 'stock.picking', picking.id, priority=5, eta=120)
                for line in picking.move_lines:
                        export_pickingproduct.delay(session, 'stock.move', line.id,
                                                    priority=10, eta=240)
        elif vals.get("active", False) or vals.get("prospective", False) and partner.web:
            export_partner.delay(session, model_name, record_id, priority=1,
                                 eta=60)

            tags = partner.category_id
            for tag in tags:
                export_partner_tag_rel.delay(session, 'res.partner.res.partner.category.rel',
                                             record_id, tag.id, priority=10, eta=60)

            sales = session.env['sale.order'].search([('partner_id', 'child_of', [record_id]),
                                                      ('company_id', '=', 1),
                                                      ('state', 'in', ['done', 'progress', 'draft', 'reserve'])])
            for sale in sales:
                export_order.delay(session, 'sale.order', sale.id, priority=5, eta=120)
                for line in sale.order_line:
                    export_orderproduct.delay(session, 'sale.order.line', line.id, priority=10, eta=180)
            invoices = session.env['account.invoice'].search([('commercial_partner_id', '=', partner.id),
                                                              ('company_id', '=', 1),
                                                              ('number', 'not like', '%ef%')])
            for invoice in invoices:
                export_invoice.delay(session, 'account.invoice', invoice.id, priority=5, eta=120)

            rmas = session.env['crm.claim'].search(
                [('partner_id', '=', partner.id)])
            for rma in rmas:
                export_rma.delay(session, 'crm.claim', rma.id, priority=5, eta=120)
                for line in rma.claim_line_ids:
                    if line.product_id.web == 'published' and \
                            (not line.equivalent_product_id or
                             line.equivalent_product_id.web == 'published'):
                        export_rmaproduct.delay(session, 'claim.line', line.id,
                                                priority=10, eta=240)
            pickings = session.env['stock.picking'].search([
                ('partner_id', 'child_of', [partner.id]),
                ('state', '!=', 'cancel'),
                ('picking_type_id.code', '=', 'outgoing'),
                ('company_id', '=', 1),
                ('not_sync', '=', False)
            ])
            for picking in pickings:
                export_picking.delay(session, 'stock.picking', picking.id, priority=5, eta=120)
                for line in picking.move_lines:
                    export_pickingproduct.delay(session, 'stock.move', line.id,
                                                priority=10, eta=240)
        elif partner.web:
            for field in up_fields:
                if field in vals:
                    update_partner.delay(session, model_name, record_id, priority=5, eta=120)

                    if 'street' in vals or \
                            'zip' in vals or \
                            'city' in vals or \
                            'country_id' in vals or \
                            'state_id' in vals:
                        sales = session.env['sale.order'].search([
                            ('partner_id', '=', partner.id),
                            '|',
                            ('state', '!=', 'cancel'),
                            ('state', '!=', 'done'),
                            ('company_id', '=', 1)
                        ])
                        for sale in sales:
                            update_order.delay(session, 'sale.order', sale.id, priority=5, eta=180)
                    break
    else:
        if partner.parent_id.web and 'active' in vals and vals.get('active', False) or \
                                     'prospective' in vals and vals.get('prospective', False):
            export_partner.delay(session, model_name, record_id, priority=1,
                                 eta=120)


@on_record_write(model_names='res.partner')
def delay_export_partner_write(session, model_name, record_id, vals):
    partner = session.env[model_name].browse(record_id)
    up_fields = ["name", "comercial", "vat", "city", "street", "zip",
                 "country_id", "state_id", "email_web", "ref", "user_id",
                 "property_product_pricelist", "lang", "sync", "type",
                 "parent_id", "is_company", "email", "active", "prospective"]

    if vals.get('is_company', False) or partner.is_company:
        contacts = session.env[model_name].search([('parent_id', 'child_of', [record_id]),
                                                   ('is_company', '=', False),
                                                   ('active', '=', True)])
        if (vals.get("web", False) and \
                (vals.get('active', partner.active) or \
                 vals.get('active', partner.prospective))and \
                vals.get('is_company', partner.is_company)):
            export_partner.delay(session, model_name, record_id, priority=1, eta=60)
            for contact in contacts:
                export_partner.delay(session, model_name, contact.id, priority=1,
                                     eta=120)
            tags = partner.category_id
            for tag in tags:
                export_partner_tag_rel.delay(session, 'res.partner.res.partner.category.rel',
                                             record_id, tag.id, priority=10, eta=60)

            sales = session.env['sale.order'].search([('partner_id', 'child_of', [record_id]),
                                                      ('company_id', '=', 1),
                                                      ('state', 'in', ['done','progress','draft','reserve'])])
            for sale in sales:
                export_order.delay(session, 'sale.order', sale.id, priority=5, eta=120)
                for line in sale.order_line:
                    export_orderproduct.delay(session, 'sale.order.line', line.id, priority=10, eta=180)

            invoices = session.env['account.invoice'].search([('commercial_partner_id', '=', partner.id),
                                                              ('company_id', '=', 1),
                                                              ('number', 'not like', '%ef%')])
            for invoice in invoices:
                export_invoice.delay(session, 'account.invoice', invoice.id, priority=5, eta=120)

            rmas = session.env['crm.claim'].search(
                [('partner_id', '=', partner.id)])
            for rma in rmas:
                export_rma.delay(session, 'crm.claim', rma.id, priority=5, eta=120)
                for line in rma.claim_line_ids:
                    if line.product_id.web == 'published' and \
                            (not line.equivalent_product_id or
                             line.equivalent_product_id.web == 'published'):
                        export_rmaproduct.delay(session, 'claim.line', line.id,
                                                priority=10, eta=240)
            pickings = session.env['stock.picking'].search([
                ('partner_id', 'child_of', [partner.id]),
                ('state', '!=', 'cancel'),
                ('picking_type_id.code', '=', 'outgoing'),
                ('company_id', '=', 1),
                ('not_sync', '=', False)
            ])
            for picking in pickings:
                export_picking.delay(session, 'stock.picking', picking.id, priority=5, eta=120)
                for line in picking.move_lines:
                    export_pickingproduct.delay(session, 'stock.move', line.id,
                                                priority=10, eta=240)

        elif ((vals.get("active", False) or vals.get('prospective', False)) and partner.web and \
                vals.get('is_company', partner.is_company)):
            export_partner.delay(session, model_name, record_id, priority=1, eta=60)
            for contact in contacts:
                export_partner.delay(session, model_name, contact.id, priority=1,
                                     eta=120)
            tags = partner.category_id
            for tag in tags:
                export_partner_tag_rel.delay(session, 'res.partner.res.partner.category.rel',
                                             record_id, tag.id, priority=10, eta=60)

            sales = session.env['sale.order'].search([('commercial_partner_id', '=', partner.id),
                                                      ('company_id', '=', 1),
                                                      ('state', 'in', ('done', 'progress', 'draft', 'reserve'))])
            for sale in sales:
                export_order.delay(session, 'sale.order', sale.id, priority=5, eta=120)
                for line in sale.order_line:
                    export_orderproduct.delay(session, 'sale.order.line', line.id, priority=10, eta=180)

            invoices = session.env['account.invoice'].search([('commercial_partner_id', '=', partner.id),
                                                              ('company_id', '=', 1),
                                                              ('number', 'not like', '%ef%')])
            for invoice in invoices:
                export_invoice.delay(session, 'account.invoice', invoice.id, priority=5, eta=120)

            rmas = session.env['crm.claim'].search(
                [('partner_id', '=', partner.id)])
            for rma in rmas:
                export_rma.delay(session, 'crm.claim', rma.id, priority=5, eta=120)
                for line in rma.claim_line_ids:
                    if line.product_id.web == 'published' and \
                            (not line.equivalent_product_id or
                             line.equivalent_product_id.web == 'published'):
                        export_rmaproduct.delay(session, 'claim.line', line.id,
                                                priority=10, eta=240)
            pickings = session.env['stock.picking'].search([
                ('partner_id', 'child_of', [partner.id]),
                ('state', '!=', 'cancel'),
                ('picking_type_id.code', '=', 'outgoing'),
                ('company_id', '=', 1),
                ('not_sync', '=', False)
            ])
            for picking in pickings:
                export_picking.delay(session, 'stock.picking', picking.id, priority=5, eta=120)
                for line in picking.move_lines:
                    export_pickingproduct.delay(session, 'stock.move', line.id,
                                                priority=10, eta=240)

        elif "web" in vals and not vals["web"]:
            for contact in contacts:
                unlink_partner.delay(session, model_name, contact.id, priority=1,
                                     eta=60)

            unlink_partner.delay(session, model_name, record_id, priority=1, eta=60)

        elif partner.web and ("active" in vals and not vals["active"] and not partner.prospective or \
                              "prospective" in vals and not vals["prospective"] and not partner.active):
            for contact in contacts:
                unlink_partner.delay(session, model_name, contact.id, priority=1,
                                     eta=60)

            unlink_partner.delay(session, model_name, record_id, priority=1, eta=60)

        elif 'child_ids' in vals:
                for child in vals['child_ids']:
                    # 2 is the state when the child is delete from the partner
                    if 2 in child:
                        # child estructure is [number, record_id, data] the number indicate
                        # de status of the object and the second position is the record of the
                        # object. The third position is the data of the object, if the object
                        # is created is False, else if the object is creating in this moment
                        # this position have all the data from the object and the second position
                        # is null because the object is not created yet
                        unlink_partner.delay(session, model_name, child[1], priority=2)

        elif partner.web and (vals.get('is_company', False) or partner.is_company):
            if 'category_id' in vals.keys():
                unlink_partner_tag_rel.delay(session, 'res.partner.res.partner.category.rel',
                                             record_id, priority=5, eta=60)
                for tag_id in vals.get('category_id', False)[0][2]:
                    export_partner_tag_rel.delay(session, 'res.partner.res.partner.category.rel',
                                                 record_id, tag_id, priority=10, eta=120)
            for field in up_fields:
                if field in vals:
                    update_partner.delay(session, model_name, record_id, priority=2, eta=120)
                    if 'street' in vals or \
                            'zip' in vals or \
                            'city' in vals or \
                            'country_id' in vals or \
                            'state_id' in vals:
                        sales = session.env['sale.order'].search([
                            ('partner_id', '=', partner.id),
                            '|',
                            ('state', '!=', 'cancel'),
                            ('state', '!=', 'done'),
                            ('company_id', '=', 1)
                        ])
                        for sale in sales:
                            update_order.delay(session, 'sale.order', sale.id, priority=5, eta=180)
                    break
    else:
        if partner.commercial_partner_id and \
                partner.commercial_partner_id.web and \
                partner.commercial_partner_id.active:
            if 'active' in vals and vals.get('active', False):
                export_partner.delay(session, model_name, record_id, priority=1,
                                     eta=120)
            elif 'active' in vals and not vals.get('active', False):
                unlink_partner.delay(session, model_name, record_id, priority=1,
                                     eta=60)
            else:
                for field in up_fields:
                    if field in vals:
                        if partner.active:
                            update_partner.delay(session, model_name, record_id, priority=3,
                                                 eta=180)

                        if 'street' in vals or \
                                'zip' in vals or \
                                'city' in vals or \
                                'country_id' in vals or \
                                'state_id' in vals:
                            sales = session.env['sale.order'].search([
                                ('partner_shipping_id', '=', partner.id),
                                '|',
                                ('state', '!=', 'cancel'),
                                ('state', '!=', 'done'),
                                ('company_id', '=', 1)
                            ])
                            for sale in sales:
                                update_order.delay(session, 'sale.order', sale.id, priority=5, eta=180)
                        break

@on_record_unlink(model_names='res.partner')
def delay_unlink_partner(session, model_name, record_id):
    partner = session.env[model_name].browse(record_id)
    contacts = session.env[model_name].search([('parent_id', 'child_of', [record_id]),
                                               ('is_company', '=', False)])
    if partner.web:
        for contact in contacts:
            unlink_partner.delay(session, model_name, contact.id, eta=60)
        unlink_partner.delay(session, model_name, record_id, eta= 60)

    elif partner.commercial_partner_id.web:
        for contact in contacts:
            unlink_partner.delay(session, model_name, contact.id, eta=60)
        unlink_partner.delay(session, model_name, record_id, eta=60)


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


@middleware
class PartnerTagExporter(Exporter):

    _model_name = ['res.partner.category']

    def update(self, binding_id, mode):
        tag = self.model.browse(binding_id)
        vals = {"odoo_id": tag.id,
                "name": tag.name,
                "parent_id": tag.parent_id.id,
                }
        if mode == "insert":
            return self.backend_adapter.insert(vals)
        else:
            return self.backend_adapter.update(binding_id, vals)

    def delete(self, binding_id):
        return self.backend_adapter.remove(binding_id)


@middleware
class PartnerTagAdapter(GenericAdapter):
    _model_name = 'res.partner.category'
    _middleware_model = 'customertag'


@on_record_create(model_names='res.partner.category')
def delay_export_partner_tag_create(session, model_name, record_id, vals):
    export_partner_tag.delay(session, model_name, record_id, priority=1, eta=60)


@on_record_write(model_names='res.partner.category')
def delay_export_partner_tag_write(session, model_name, record_id, vals):
    tag = session.env[model_name].browse(record_id)
    up_fields = ["name", "parent_id", "active"]
    if 'active' in vals and not vals.get('active', False):
        partner_obj = session.env['res.partner']
        partner_ids = partner_obj.search([('is_company', '=', True),
                                          ('web', '=', True),
                                          ('customer', '=', True),
                                          ('category_id', 'in', record_id)])
        unlink_partner_tag.delay(session, model_name, record_id, priority=3, eta=120)
        for partner in partner_ids:
            unlink_partner_tag_rel.delay(session, 'res.partner.res.partner.category.rel',
                                         partner.id, priority=5, eta=60)
            tags = partner.category_id
            for tag_id in tags.ids:
                export_partner_tag_rel.delay(session, 'res.partner.res.partner.category.rel',
                                             partner.id, tag_id, priority=10, eta=120)
    elif 'active' in vals and vals.get('active', False) or \
         'prospective' in vals and vals.get('prospective', False):
        partner_obj = session.env['res.partner']
        partner_ids = partner_obj.search([('is_company', '=', True),
                                        ('web', '=', True),
                                        ('customer', '=', True),
                                        ('category_id', 'in', record_id)])
        export_partner_tag.delay(
            session, model_name, record_id, priority=1, eta=60)
        for partner in partner_ids:
            unlink_partner_tag_rel.delay(session, 'res.partner.res.partner.category.rel',
                                         partner.id, priority=5, eta=60)
            tags = partner.category_id
            for tag_id in tags.ids:
                export_partner_tag_rel.delay(session, 'res.partner.res.partner.category.rel',
                                             partner.id, tag_id, priority=10, eta=120)
    elif tag.active:
        update_partner_tag.delay(session, model_name, record_id, priority=2, eta=120)


@on_record_unlink(model_names='res.partner.category')
def delay_export_partner_tag_unlink(session, model_name, record_id):
    unlink_partner_tag.delay(session, model_name, record_id, priority=3, eta=120)


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def export_partner_tag(session, model_name, record_id):
    partner_tag_exporter = _get_exporter(session, model_name, record_id,
                                         PartnerTagExporter)
    return partner_tag_exporter.update(record_id, "insert")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def update_partner_tag(session, model_name, record_id):
    partner_tag_exporter = _get_exporter(session, model_name, record_id,
                                         PartnerTagExporter)
    return partner_tag_exporter.update(record_id, "update")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def unlink_partner_tag(session, model_name, record_id):
    partner_tag_exporter = _get_exporter(session, model_name, record_id,
                                         PartnerTagExporter)
    return partner_tag_exporter.delete(record_id)


@middleware
class PartnerTagRelExporter(Exporter):

    _model_name = ['res.partner.res.partner.category.rel']

    def update(self, partner_record_id, category_record_id, mode):
        vals = {"odoo_id": partner_record_id,
                "customertag_id": category_record_id,
                }
        if mode == "insert":
            return self.backend_adapter.insert(vals)
        else:
            return self.backend_adapter.update(partner_record_id, category_record_id, vals)

    def delete(self, partner_record_id):
        return self.backend_adapter.remove(partner_record_id)


@middleware
class PartnerTagRelAdapter(GenericAdapter):
    _model_name = 'res.partner.res.partner.category.rel'
    _middleware_model = 'customertagcustomerrel'


def delay_export_partner_tag_rel_create(session, model_name, partner_record_id, vals):
    if 'category_id' in vals:
        return True
    elif 'web' in vals and vals.get('web', False):
        partner = session.env['res.partner'].browse(partner_record_id)
        for tag in partner.category_id:
            export_partner_tag_rel.delay(session, 'res.partner.res.partner.category.rel', partner_record_id, tag, priority=2, eta=120)


def delay_export_partner_tag_rel_write(session, model_name, partner_record_id, vals):
    """
    - [[6, 0, [ids]]]: Borra las asociaciones actuales del campo y le asocia los identificadores
contenidos en ids (int[])
- [[4, id]]: Asocia el identificador contenido en id (int) al campo.
- [[3, id]]: Desasocia el identificador contenido en id (int) del campo.
- [[3, id]]: Desasocia el identificador contenido en id (int) del campo.
- [[2, id]]: Desasocia y borra el identificador contenido en id (int) del campo y de la base de
datos.
    """
    update_partner_tag_rel.delay(session, model_name, partner_record_id, priority=2, eta=60)


def delay_export_partner_tag_rel_unlink(session, model_name, partner_record_id):
    unlink_partner_tag_rel.delay(session, 'res.partner.res.partner.category.rel', partner_record_id, priority=5, eta=120)


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def export_partner_tag_rel(session, model_name, partner_record_id, category_record_id):
    partner_tag_rel_exporter = _get_exporter(session, model_name, partner_record_id,
                                             PartnerTagRelExporter)
    return partner_tag_rel_exporter.update(partner_record_id, category_record_id, "insert")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def update_partner_tag_rel(session, model_name, partner_record_id, category_record_id):
    partner_tag_rel_exporter = _get_exporter(session, model_name, partner_record_id,
                                             PartnerTagRelExporter)
    return partner_tag_rel_exporter.update(partner_record_id, category_record_id, "update")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def unlink_partner_tag_rel(session, model_name, partner_record_id):
    partner_tag_rel_exporter = _get_exporter(session, model_name, partner_record_id,
                                             PartnerTagRelExporter)
    return partner_tag_rel_exporter.delete(partner_record_id)
