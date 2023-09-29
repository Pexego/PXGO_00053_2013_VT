# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import Component
from odoo.addons.queue_job.job import job
from odoo import models, api, fields, _


class PartnerListener(Component):
    _name = 'partner.event.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['res.partner']

    def export_partner_data(self, record):
        record.with_delay(priority=8).export_partner()

        sales = self.env['sale.order'].search(
            [('partner_id', 'child_of', [record.id]),
                ('company_id', '=', 1),
                ('state', 'in', ['done', 'sale'])])
        for sale in sales:
            sale.with_delay(priority=11, eta=120).export_order()
            for line in sale.order_line:
                line.with_delay(priority=11, eta=180).export_orderproduct()

        invoices = self.env['account.invoice'].search(
            [('commercial_partner_id', '=', record.id),
                ('company_id', '=', 1),
                ('number', 'not like', '%ef%')])
        for invoice in invoices:
            invoice.with_delay(priority=11, eta=120).export_invoice()

        rmas = self.env['crm.claim'].search(
            [('partner_id', '=', record.id)])
        for rma in rmas:
            rma.with_delay(priority=11, eta=120).export_rma()
            for line in rma.claim_line_ids:
                if line.product_id.web == 'published' and \
                        (not line.equivalent_product_id or
                            line.equivalent_product_id.web ==
                            'published'):
                    line.with_delay(priority=11, eta=240).export_rmaproduct()
        pickings = self.env['stock.picking'].search([
            ('partner_id', 'child_of', [record.id]),
            ('state', '!=', 'cancel'),
            ('picking_type_id.code', '=', 'outgoing'),
            ('company_id', '=', 1),
            ('not_sync', '=', False)
        ])
        for picking in pickings:
            picking.with_delay(priority=11, eta=120).export_picking()
            for line in picking.move_lines:
                line.with_delay(priority=11, eta=240).export_pickingproduct()

    def on_record_create(self, record, fields=None):
        partner = record
        up_fields = ["name", "comercial", "vat", "city", "street", "zip",
                     "country_id", "state_id", "email_web", "email3", "ref",
                     'user_id', "property_product_pricelist", "lang", "type",
                     "parent_id", "is_company", "email", "area_id",
                     "prospective", "phone", "mobile","csv_connector_access", "pricelist_brand_ids", "category_id"]
        if partner.is_company:

            if partner.web and (partner.active or partner.prospective):
                self.export_partner_data(record)
            elif partner.web:
                for field in up_fields:
                    if field in fields:
                        partner.with_delay(priority=11, eta=120).update_partner()
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
                                sale.with_delay(priority=11, eta=180).update_order()
                        break
        else:
            if partner.web and (('active' in fields and partner.active) or
                                ('prospective' in fields and partner.prospective)):
                partner.with_delay(priority=8).export_partner()

    def on_record_write(self, record, fields=None):
        partner = record
        up_fields = [
            "name", "comercial", "vat", "city", "street", "zip", "country_id",
            "state_id", "email_web", "email3", "ref", "user_id",
            "property_product_pricelist", "lang", "sync", "type", "parent_id",
            "is_company", "email", "active", "prospective", "phone", "mobile",
            "property_payment_term_id", "last_sale_date", "csv_connector_access",
            "pricelist_brand_ids", "category_id", "area_id"
        ]
        if 'web' in fields and record.web and \
                (partner.active or partner.prospective):
            self.export_partner_data(record)

        elif "web" in fields and not record.web:
            record.with_delay(priority=11, eta=60).unlink_partner()

        elif partner.web and ('active' in fields or
                              'prospective' in fields) and not \
                (partner.active or partner.prospective):
            record.with_delay(priority=11, eta=60).unlink_partner()
        elif partner.web and ('active' in fields and partner.active
                              or 'prospective' in fields and partner.prospective):
            self.export_partner_data(record)

        elif partner.web:
            for field in up_fields:
                if field in fields:
                    if field == 'last_sale_date' and not partner.csv_connector_access:
                        break
                    partner.with_delay(priority=11, eta=120).update_partner()
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
                            sale.with_delay(priority=11, eta=180).update_order()
                    break

    def on_record_unlink(self, record):
        if record.web:
            record.with_delay(priority=11, eta=60).unlink_partner()


class ResPartner(models.Model):
    _inherit = 'res.partner'

    discount = fields.Float(compute='_compute_discount')
    sync = fields.Boolean(readonly=True,
                          help="System field to allow resync all partners")

    def _compute_discount(self):
        for partner in self:
            discount = 0.0
            if partner.property_product_pricelist:
                pricelist = partner.property_product_pricelist
                item = pricelist.item_ids[-1]
                if item:
                    discount = item.price_discount
                partner.discount = discount

    csv_connector_access = fields.Selection(string="CSV Connector Access",
                                            help="System field to allow csv connector access",
                                            selection=[
                                                ("no_connector", "No connector"),
                                                ("only_networking", "Only networking"),
                                                ("only_online_store", "Only online security store"),
                                                ("premium", "Premium")
                                            ],
                                            default="no_connector"
                                            )

    @api.model
    def create(self, vals):
        if vals.get('user_id', False) and 'web' in vals.keys() and vals['web']:
            user = self.env['res.users'].browse(vals['user_id'])
            if not user.web:
                user.web = True
        res = super().create(vals)
        if vals.get('csv_connector_access',False):
            res.message_post(body=_('CSV connector access checked by %s') % self.env.user.name)
        return res

    @api.multi
    def write(self, vals):
        delete = True
        deletea = True
        for partner in self:
            if 'web' in vals.keys() and vals['web']:
                user_id = vals.get('user_id', False)
                if user_id:
                    user = self.env['res.users'].browse(user_id)
                else:
                    user = partner.user_id
                if user and not user.web:
                    user.web = True
            if 'web' in vals.keys():
                if partner.web != vals['web']:
                    delete = False
                if delete:
                    del vals['web']
            if 'active' in vals.keys():
                if partner.active != vals['active']:
                    deletea = False
                if deletea:
                    del vals['active']
            if 'csv_connector_access' in vals.keys():
                partner.message_post(
                    body=_('<p>CSV conector access has been changed by %s </p>'
                           '<ul><li>  %s &#10137; %s </li></ul>')
                         % (self.env.user.name, partner.csv_connector_access,vals['csv_connector_access']))


        return super().write(vals)

    @job(retry_pattern={
        1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def export_partner(self):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.update(self, 'insert')
        return True

    @job(retry_pattern={
        1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def update_partner(self):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.update(self, 'update')
        return True

    @job(retry_pattern={
        1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def unlink_partner(self):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.delete(self)
        return True


class PartnerCategoryListener(Component):
    _name = 'partner.category.event.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['res.partner.category']

    def on_record_create(self, record, fields=None):
        record.with_delay(priority=11, eta=30).export_partner_tag()

    # TODO: revisar esta función
    def on_record_write(self, record, fields=None):
        if 'active' in fields and not record.active:
            partner_ids = self.env['res.partner'].search(
                [('is_company', '=', True), ('web', '=', True),
                 ('customer', '=', True), ('category_id', 'in', record.id)])
            record.with_delay(priority=1).unlink_partner_tag()

            for partner in partner_ids:
                partner.with_delay(priority=11).update_partner()
        elif 'active' in fields and record.active or \
             'prospective' in fields and record.prospective:
            partner_ids = self.env['res.partner'].search(
                [('is_company', '=', True),
                 ('web', '=', True),
                 ('customer', '=', True),
                 ('category_id', 'in', record.id)])
            record.with_delay(priority=11, eta=60).export_partner_tag()
            for partner in partner_ids:
                partner.update_partner()
        elif record.active:
            record.with_delay(priority=11, eta=60).update_partner_tag()

    def on_record_unlink(self, record):
        record.with_delay(priority=1).unlink_partner_tag()


class ResPartnerCategory(models.Model):
    _inherit = 'res.partner.category'

    @job(retry_pattern={
        1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def export_partner_tag(self):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.update(self, 'insert')
        return True

    @job(retry_pattern={
        1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def update_partner_tag(self):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.update(self, 'update')
        return True

    @job(retry_pattern={
        1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def unlink_partner_tag(self):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.delete(self)
        return True


class PartnerAreaListener(Component):
    _name = 'partner.area.event.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['res.partner.area']

    def on_record_write(self, record, fields=None):
        if 'name' in fields:
            partner_ids = self.env['res.partner'].search([
                ('web', '=', True), ('area_id', '=', record.id)
            ])

            for partner in partner_ids:
                partner.with_delay(priority=11).update_partner()
