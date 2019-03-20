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
# from .utils import _get_exporter
# from ..backend import middleware
# from openerp.addons.connector.unit.synchronizer import Exporter
# from ..unit.backend_adapter import GenericAdapter

from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.queue_job.job import job
from odoo import models

# TODO:Migrar parte del adapter
# @middleware
# class PartnerExporter(Exporter):
#
#     _model_name = ['res.partner']
#
#     def update(self, binding_id, mode):
#         partner = self.model.browse(binding_id)
#         vals = {"is_company": partner.is_company,
#                 "fiscal_name": partner.name,
#                 "commercial_name": partner.comercial or "",
#                 "odoo_id": partner.id,
#                 "vat": partner.vat or "",
#                 "street": partner.street or "",
#                 "city": partner.city or "",
#                 "zipcode": partner.zip,
#                 "commercial_id": partner.user_id.id,
#                 "country": partner.country_id and partner.country_id.code or
#                 "",
#                 "ref": partner.ref,
#                 "discount": partner.discount,
#                 "pricelist_name": partner.property_product_pricelist and
#                 partner.property_product_pricelist.name or "",
#                 "state": partner.state_id and partner.state_id.name or "",
#                 "email": partner.email_web or "",
#                 "prospective": partner.prospective,
#                 "lang": partner.lang and partner.lang.split("_")[0] or 'es',
#                 "phone1": partner.phone,
#                 "phone2": partner.mobile,
#                 }
#         if not vals['is_company']:
#             vals.update({"type": partner.type, "parent_id": partner.parent_id.id, "email": partner.email})
#         if mode == "insert":
#             return self.backend_adapter.insert(vals)
#         else:
#             return self.backend_adapter.update(binding_id, vals)
#
#     def delete(self, binding_id):
#         return self.backend_adapter.remove(binding_id)
#
#
# @middleware
# class PartnerAdapter(GenericAdapter):
#     _model_name = 'res.partner'
#     _middleware_model = 'customer'


class PartnerListener(Component):
    _name = 'partner.event.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['res.partner']

    def on_record_create(self, record, fields=None):
        partner = record
        up_fields = ["name", "comercial", "vat", "city", "street", "zip",
                     "country_id", "state_id", "email_web", "ref", 'user_id',
                     "property_product_pricelist", "lang", "type",
                     "parent_id", "is_company", "email", "prospective", "phone",
                     "mobile"]
        if partner.is_company:

            if partner.web and partner.active or partner.prospective:
                partner.with_delay(priority=1, eta=60).export_partner()
                # TODO: Migrar parte de los tags
                # tags = partner.category_id
                # for tag in tags:
                #     export_partner_tag_rel.delay(session, 'res.partner.res.partner.category.rel', record_id, tag.id, priority=10, eta=120)

                sales = self.env['sale.order'].search([('partner_id', 'child_of', [record.id]),
                                                       ('company_id', '=', 1),
                                                       ('state', 'in', ['done', 'progress', 'draft', 'reserve'])])
                for sale in sales:
                    sale.with_delay(priority=5, eta=120).export_order()
                    for line in sale.order_line:
                        line.with_delay(priority=10, eta=180).export_orderproduct()

                invoices = self.env['account.invoice'].search([('commercial_partner_id', '=', partner.id),
                                                               ('company_id', '=', 1),
                                                               ('number', 'not like', '%ef%')])
                for invoice in invoices:
                    invoice.with_delay(priority=5, eta=120).export_invoice()

                rmas = self.env['crm.claim'].search([('partner_id', '=', partner.id)])
                for rma in rmas:
                    rma.with_delay(priority=5, eta=120).export_rma()
                    for line in rma.claim_line_ids:
                        if line.product_id.web == 'published' and \
                                (line.equivalent_product_id and
                                 line.equivalent_product_id.web == 'published' or
                                 True):
                            line.with_delay(priority=10, eta=240).export_rmaproduct()

                pickings = self.env['stock.picking'].search([
                    ('partner_id', 'child_of', [partner.id]),
                    ('state', '!=', 'cancel'),
                    ('picking_type_id.code', '=', 'outgoing'),
                    ('company_id', '=', 1),
                    ('not_sync', '=', False)
                ])
                for picking in pickings:
                    picking.with_delay(priority=5, eta=120).export_picking()
                    for line in picking.move_lines:
                        line.with_delay(priority=10, eta=240).export_pickingproduct()
            elif (partner.active or partner.prospective) and partner.web:
                partner.with_delay(priority=1, eta=60).export_partner()

                # TODO: Migrar parte de los tags
                # tags = partner.category_id
                # for tag in tags:
                #     export_partner_tag_rel.delay(session, 'res.partner.res.partner.category.rel', record_id, tag.id, priority=10, eta=120)

                sales = self.env['sale.order'].search([('partner_id', 'child_of', [record.id]),
                                                          ('company_id', '=', 1),
                                                          ('state', 'in', ['done', 'progress', 'draft', 'reserve'])])
                for sale in sales:
                    sale.with_delay(priority=5, eta=120).export_order()
                    for line in sale.order_line:
                        line.with_delay(priority=10, eta=180).export_orderproduct()
                invoices = self.env['account.invoice'].search([('commercial_partner_id', '=', partner.id),
                                                               ('company_id', '=', 1),
                                                               ('number', 'not like', '%ef%')])
                for invoice in invoices:
                    invoice.with_delay(priority=5, eta=120).export_invoice()

                rmas = self.env['crm.claim'].search([('partner_id', '=', partner.id)])
                for rma in rmas:
                    rma.with_delay(priority=5, eta=120).export_rma()
                    for line in rma.claim_line_ids:
                        if line.product_id.web == 'published' and \
                                (not line.equivalent_product_id or
                                 line.equivalent_product_id.web == 'published'):
                            line.with_delay(priority=10, eta=240).export_rmaproduct()
                pickings = self.env['stock.picking'].search([
                    ('partner_id', 'child_of', [partner.id]),
                    ('state', '!=', 'cancel'),
                    ('picking_type_id.code', '=', 'outgoing'),
                    ('company_id', '=', 1),
                    ('not_sync', '=', False)
                ])
                for picking in pickings:
                    picking.with_delay(priority=5, eta=120).export_picking()
                    for line in picking.move_lines:
                        line.with_delay(priority=10, eta=240).export_pickingproduct()
            elif partner.web:
                for field in up_fields:
                    if field in fields:
                        partner.with_delay(priority=5, eta=120).update_partner()
                        if 'street' in fields or \
                                'zip' in fields or \
                                'city' in fields or \
                                'country_id' in fields or \
                                'state_id' in fields:
                            sales = self.env['sale.order'].search([
                                ('partner_id', '=', partner.id),
                                '|',
                                ('state', '!=', 'cancel'),
                                ('state', '!=', 'done'),
                                ('company_id', '=', 1)
                            ])
                            for sale in sales:
                                sale.with_delay(priority=5, eta=180).update_order()
                        break
        else:
            if partner.parent_id.web and 'active' in fields and partner.active or \
                                         'prospective' in fields and partner.prospective:
                partner.with_delay(priority=1, eta=120).export_partner()

    def on_record_write(self, record, fields=None):
        partner = record
        up_fields = ["name", "comercial", "vat", "city", "street", "zip",
                     "country_id", "state_id", "email_web", "ref", "user_id",
                     "property_product_pricelist", "lang", "sync", "type",
                     "parent_id", "is_company", "email", "active", "prospective",
                     "phone", "mobile"]

        if partner.is_company:
            contacts = self.env['res.partner'].search([('parent_id', 'child_of', [record.id]),
                                                       ('is_company', '=', False),
                                                       ('active', '=', True)])
            if partner.web and (partner.active or partner.prospective) and partner.is_company:
                partner.with_delay(priority=1, eta=60).export_partner()
                for contact in contacts:
                    contact.with_delay(priority=1, eta=120).export_partner()
                # TODO: Migrar parte de los tags
                # tags = partner.category_id
                # for tag in tags:
                #     tag.with_delay(priority=10, eta=120).export_partner_tag_rel()

                sales = self.env['sale.order'].search([('partner_id', 'child_of', [record.id]),
                                                      ('company_id', '=', 1),
                                                      ('state', 'in', ['done', 'progress', 'draft', 'reserve'])])
                for sale in sales:
                    sale.with_delay(priority=5, eta=120).export_order()
                    for line in sale.order_line:
                        line.with_delay(priority=10, eta=180).export_orderproduct()

                invoices = self.env['account.invoice'].search([('commercial_partner_id', '=', partner.id),
                                                                  ('company_id', '=', 1),
                                                                  ('number', 'not like', '%ef%')])
                for invoice in invoices:
                    invoice.with_delay(priority=5, eta=120).export_invoice()

                rmas = self.env['crm.claim'].search([('partner_id', '=', partner.id)])
                for rma in rmas:
                    rma.with_delay(priority=5, eta=120).export_rma()
                    for line in rma.claim_line_ids:
                        if line.product_id.web == 'published' and \
                                (not line.equivalent_product_id or
                                 line.equivalent_product_id.web == 'published'):
                            line.with_delay(priority=10, eta=240).export_rmaproduct()
                pickings = self.env['stock.picking'].search([
                    ('partner_id', 'child_of', [partner.id]),
                    ('state', '!=', 'cancel'),
                    ('picking_type_id.code', '=', 'outgoing'),
                    ('company_id', '=', 1),
                    ('not_sync', '=', False)
                ])
                for picking in pickings:
                    picking.with_delay(priority=5, eta=120).export_picking()
                    for line in picking.move_lines:
                        line.with_delay(priority=10, eta=240).export_pickingproduct()

            elif (partner.active or partner.prospective) and partner.web and partner.is_company:
                record.with_delay(priority=1, eta=60).export_partner()
                for contact in contacts:
                    contact.with_delay(priority=1, eta=120).export_partner()
                # TODO: Migrar parte de los tags
                # tags = partner.category_id
                # for tag in tags:
                #     tag.with_delay(priority=10, eta=120).export_partner_tag_rel()

                sales = self.env['sale.order'].search([('partner_id', 'child_of', [record.id]),
                                                      ('company_id', '=', 1),
                                                      ('state', 'in', ('done', 'progress', 'draft', 'reserve'))])
                for sale in sales:
                    sale.with_delay(priority=5, eta=120).export_order()
                    for line in sale.order_line:
                        line.with_delay(priority=10, eta=180).export_orderproduct()

                invoices = self.env['account.invoice'].search([('commercial_partner_id', '=', partner.id),
                                                               ('company_id', '=', 1),
                                                               ('number', 'not like', '%ef%')])
                for invoice in invoices:
                    invoice.with_delay(priority=5, eta=120).export_invoice()

                rmas = self.env['crm.claim'].search([('partner_id', '=', partner.id)])
                for rma in rmas:
                    rma.with_delay(priority=5, eta=120).export_rma()
                    for line in rma.claim_line_ids:
                        if line.product_id.web == 'published' and \
                                (not line.equivalent_product_id or
                                 line.equivalent_product_id.web == 'published'):
                            line.with_delay(priority=10, eta=240).export_rmaproduct()
                pickings = self.env['stock.picking'].search([
                    ('partner_id', 'child_of', [partner.id]),
                    ('state', '!=', 'cancel'),
                    ('picking_type_id.code', '=', 'outgoing'),
                    ('company_id', '=', 1),
                    ('not_sync', '=', False)
                ])
                for picking in pickings:
                    picking.with_delay(priority=5, eta=120).export_picking()
                    for line in picking.move_lines:
                        line.with_delay(priority=10, eta=240).export_pickingproduct()

            elif "web" in fields and not partner.web:
                for contact in contacts:
                    contact.with_delay(priority=1, eta=60).unlink_partner()
                partner.with_delay(priority=1, eta=60).unlink_partner()

            elif partner.web and ("active" in fields and not partner.active and not partner.prospective or \
                                  "prospective" in fields and not partner.prospective and not partner.active):
                for contact in contacts:
                    contact.with_delay(priority=1, eta=60).unlink_partner()
                partner.with_delay(priority=1, eta=60).unlink_partner()

            elif 'child_ids' in fields:
                    for child in partner.child_ids:
                        # 2 is the state when the child is delete from the partner
                        if 2 in child:
                            # child estructure is [number, record_id, data] the number indicate
                            # de status of the object and the second position is the record of the
                            # object. The third position is the data of the object, if the object
                            # is created is False, else if the object is creating in this moment
                            # this position have all the data from the object and the second position
                            # is null because the object is not created yet
                            partner.with_delay(priority=2).unlink_partner()

            elif partner.web and partner.is_company:
                # TODO: Migrar parte de los tags
                # if 'category_id' in fields:
                #     unlink_partner_tag_rel.delay(session, 'res.partner.res.partner.category.rel', record_id, priority=5, eta=60)
                #     for tag_id in vals.get('category_id', False)[0][2]:
                #         export_partner_tag_rel.delay(session, 'res.partner.res.partner.category.rel', record_id, tag_id, priority=10, eta=120)
                for field in up_fields:
                    if field in vals:
                        partner.with_delay(priority=2, eta=120).update_partner(fields)
                        if 'street' in fields or \
                                'zip' in fields or \
                                'city' in fields or \
                                'country_id' in fields or \
                                'state_id' in fields:
                            sales = self.env['sale.order'].search([
                                ('partner_id', '=', partner.id),
                                '|',
                                ('state', '!=', 'cancel'),
                                ('state', '!=', 'done'),
                                ('company_id', '=', 1)
                            ])
                            for sale in sales:
                                sale.with_delay(priority=5, eta=180).update_order()
                        break
        else:
            if partner.commercial_partner_id and \
                    partner.commercial_partner_id.web and \
                    partner.commercial_partner_id.active:
                if 'active' in fields and partner.active:
                    partner.with_delay(priority=1, eta=120).export_partner()
                elif 'active' in fields and not partner.active:
                    partner.with_delay(priority=1, eta=60).unlink_partner()
                else:
                    for field in up_fields:
                        if field in fields:
                            if partner.active:
                                partner.with_delay(priority=3, eta=180).update_partner()

                            if 'street' in fields or \
                                    'zip' in fields or \
                                    'city' in fields or \
                                    'country_id' in fields or \
                                    'state_id' in fields:
                                sales = self.env['sale.order'].search([
                                    ('partner_shipping_id', '=', partner.id),
                                    '|',
                                    ('state', '!=', 'cancel'),
                                    ('state', '!=', 'done'),
                                    ('company_id', '=', 1)
                                ])
                                for sale in sales:
                                    sale.with_delay(priority=5, eta=180).update_order()
                            break

    def on_record_unlink(self, record):
        contacts = self.env['res.partner'].search([('parent_id', 'child_of', [record.id]),
                                                   ('is_company', '=', False)])
        if record.web:
            for contact in contacts:
                contact.with_delay(eta=60).unlink_partner()
            record.with_delay(eta=60).unlink_partner()

        elif record.commercial_partner_id.web:
            for contact in contacts:
                contact.with_delay(eta=60).unlink_partner()
            record.with_delay(eta=60).unlink_partner()


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def export_partner(self):
        # partner_exporter = _get_exporter(session, model_name, record_id,
        #                                  PartnerExporter)
        # return partner_exporter.update(record_id, "insert")
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def update_partner(self, fields):
        # partner_exporter = _get_exporter(session, model_name, record_id,
        #                                  PartnerExporter)
        # return partner_exporter.update(record_id, "update")
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def unlink_partner(self):
        # partner_exporter = _get_exporter(session, model_name, record_id,
        #                                  PartnerExporter)
        # return partner_exporter.delete(record_id)
        return True


class PricelistListener(Component):
    _name = 'pricelist.event.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['product.pricelist.version']
    # Se controla los cambios en versiones de tarifa, cuando hay cambios en 1
    # item tambien se modifica version

    def on_record_create(self, record, fields=None):
        partners = self.env['res.partner'].search(
            [('property_product_pricelist', '=',
              record.pricelist_id.id), ('web', '=', True)])
        for partner in partners:
            partner.with_delay().update_partner

    def on_record_write(self, record, fields=None):
        pricelist_version = self.env['product.pricelist.version'].browse(record.id)
        partners = self.env['res.partner'].search(
            [('property_product_pricelist', '=',
              pricelist_version.pricelist_id.id), ('web', '=', True)])
        for partner in partners:
            partner.with_delay().update_partner

# TODO: Migrar parte del adapter
# @middleware
# class PartnerTagExporter(Exporter):
#
#     _model_name = ['res.partner.category']
#
#     def update(self, binding_id, mode):
#         tag = self.model.browse(binding_id)
#         vals = {"odoo_id": tag.id,
#                 "name": tag.name,
#                 "parent_id": tag.parent_id.id,
#                 }
#         if mode == "insert":
#             return self.backend_adapter.insert(vals)
#         else:
#             return self.backend_adapter.update(binding_id, vals)
#
#     def delete(self, binding_id):
#         return self.backend_adapter.remove(binding_id)
#
#
# @middleware
# class PartnerTagAdapter(GenericAdapter):
#     _model_name = 'res.partner.category'
#     _middleware_model = 'customertag'


class PartnerCategoryListener(Component):
    _name = 'partner.category.event.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['res.partner.category']

    def on_record_create(self, record, fields=None):
        record.with_delay(priority=1, eta=60).export_partner_tag()

    # TODO: revisar esta función
    def on_record_write(self, record, fields=None):
        up_fields = ["name", "parent_id", "active"]
        if 'active' in fields and not record.active:
            partner_ids = self.env['res.partner'].search([('is_company', '=', True),
                                                         ('web', '=', True),
                                                         ('customer', '=', True),
                                                         ('category_id', 'in', record.id)])
            record.with_delay(priority=3, eta=120).unlink_partner_tag

            for partner in partner_ids:
                partner.with_delay(priority=5, eta=60).unlink_partner_tag_rel()
                tags = partner.category_id
                # TODO: Migrar parte de los tags
                # for tag in tags:
                #     tag.with_delay(priority=10, eta=120).export_partner_tag_rel()
        elif 'active' in fields and record.active or \
             'prospective' in fields and record.prospective:
            partner_ids = self.env['res.partner'].search([('is_company', '=', True),
                                                         ('web', '=', True),
                                                         ('customer', '=', True),
                                                         ('category_id', 'in', record.id)])
            record.with_delay(priority=1, eta=60).export_partner_tag()
            # TODO: Migrar parte de los tags
            # for partner in partner_ids:
            #     unlink_partner_tag_rel.delay(session, 'res.partner.res.partner.category.rel', partner.id, priority=5, eta=60)
            #     tags = partner.category_id
            #     for tag_id in tags.ids:
            #         export_partner_tag_rel.delay(session, 'res.partner.res.partner.category.rel', partner.id, tag_id, priority=10, eta=120)
        elif record.active:
            record.with_delay(priority=2, eta=120).update_partner_tag()

    def on_record_unlink(self, record):
        record.with_delay(priority=3, eta=120).unlink_partner_tag()


class ResPartnerCategory(models.Model):
    _inherit = 'res.partner.category'

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def export_partner_tag(self):
        # partner_tag_exporter = _get_exporter(session, model_name, record_id,
        #                                      PartnerTagExporter)
        # return partner_tag_exporter.update(record_id, "insert")
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def update_partner_tag(self, fields):
        # partner_tag_exporter = _get_exporter(session, model_name, record_id,
        #                                      PartnerTagExporter)
        # return partner_tag_exporter.update(record_id, "update")
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def unlink_partner_tag(self):
        # partner_tag_exporter = _get_exporter(session, model_name, record_id,
        #                                      PartnerTagExporter)
        # return partner_tag_exporter.delete(record_id)
        return True

# TODO: Migrar parte del adapter
# @middleware
# class PartnerTagRelExporter(Exporter):
#
#     _model_name = ['res.partner.res.partner.category.rel']
#
#     def update(self, partner_record_id, category_record_id, mode):
#         vals = {"odoo_id": partner_record_id,
#                 "customertag_id": category_record_id,
#                 }
#         if mode == "insert":
#             return self.backend_adapter.insert(vals)
#         else:
#             return self.backend_adapter.update(partner_record_id, category_record_id, vals)
#
#     def delete(self, partner_record_id):
#         return self.backend_adapter.remove(partner_record_id)
#
#
# @middleware
# class PartnerTagRelAdapter(GenericAdapter):
#     _model_name = 'res.partner.res.partner.category.rel'
#     _middleware_model = 'customertagcustomerrel'
#
#
# def delay_export_partner_tag_rel_create(session, model_name, partner_record_id, vals):
#     if 'category_id' in vals:
#         return True
#     elif 'web' in vals and vals.get('web', False):
#         partner = session.env['res.partner'].browse(partner_record_id)
#         for tag in partner.category_id:
#             export_partner_tag_rel.delay(session, 'res.partner.res.partner.category.rel', partner_record_id, tag, priority=2, eta=120)

# TODO: Migrar parte de los tags
# class PartnerTagRelListener(Component):
#
#     def on_record_write(self, record, fields=None):
#         """
#         - [[6, 0, [ids]]]: Borra las asociaciones actuales del campo y le asocia los identificadores
#     contenidos en ids (int[])
#     - [[4, id]]: Asocia el identificador contenido en id (int) al campo.
#     - [[3, id]]: Desasocia el identificador contenido en id (int) del campo.
#     - [[3, id]]: Desasocia el identificador contenido en id (int) del campo.
#     - [[2, id]]: Desasocia y borra el identificador contenido en id (int) del campo y de la base de
#     datos.
#         """
#         record.with_delay(priority=2, eta=60).update_partner_tag_rel()
#
#     def on_record_unlink(self, record):
#         record.with_delay(priority=5, eta=120).unlink_partner_tag_rel()
#
#
# class ResPartnerResPartnerCategoryRel(models.Model):
#     _inherit = 'res.partner.res.partner.category.rel'
#
#     @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
#     def export_partner_tag_rel(self):
#         # partner_tag_rel_exporter = _get_exporter(session, model_name, partner_record_id,
#         #                                          PartnerTagRelExporter)
#         # return partner_tag_rel_exporter.update(partner_record_id, category_record_id, "insert")
#         return True
#
#     @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
#     def update_partner_tag_rel(self, fields):
#         # partner_tag_rel_exporter = _get_exporter(session, model_name, partner_record_id,
#         #                                          PartnerTagRelExporter)
#         # return partner_tag_rel_exporter.update(partner_record_id, category_record_id, "update")
#         return True
#
#     @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
#     def unlink_partner_tag_rel(self):
#         # partner_tag_rel_exporter = _get_exporter(session, model_name, partner_record_id,
#         #                                          PartnerTagRelExporter)
#         # return partner_tag_rel_exporter.delete(partner_record_id)
#         return True
